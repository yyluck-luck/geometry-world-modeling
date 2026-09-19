#!/usr/bin/env python3
"""Independent S14B verification: no production import, no GT/query/model reads.

NumPy is used solely to deserialize NPZ. Numerical reconstruction uses Python
dict/list, centered coordinates, math.fsum and explicit linear order statistics.
All float comparisons use |observed-reference| <= 1e-12 + 1e-10*|reference|.
"""
import argparse
import csv
import hashlib
import json
import math
import platform
from pathlib import Path
import sys
import traceback
from datetime import datetime, timezone

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ATOL, RTOL = 1e-12, 1e-10
METRICS = ['W', 'B', 'A', 'D'] + [x + '_over_radius2' for x in ['W', 'B', 'A', 'D']]
POINT_FIELDS = ('phase block stride point_id m n_obs single_source birth_frame birth_flat_index '
                'birth_u birth_v mem_x mem_y mem_z radius').split() + METRICS
FRAME_FIELDS = 'phase block stride point_id frame n_obs c_x c_y c_z within_variance'.split()
INT_FIELDS = set('block stride point_id m n_obs single_source birth_frame birth_flat_index birth_u birth_v frame'.split())
FILES = ['observations.npz', 'A0_events.json', 'A0P0.npz', 'A0P0_sources.json']
BLOCKS = [('S7', b, 'results/S7_event_replay') for b in range(3)] + [('S8', b, 'results/S8_event_replay_v2') for b in range(3)]


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda: f.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def read_json(path):
    def unique(pairs):
        out = {}
        for key, val in pairs:
            if key in out:
                raise ValueError(f'duplicate JSON key: {key}')
            out[key] = val
        return out
    return json.loads(Path(path).read_text(), object_pairs_hook=unique,
                      parse_constant=lambda val: (_ for _ in ()).throw(ValueError(val)))


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False, default=repr) + '\n')


class Audit:
    def __init__(self):
        self.checks = 0
        self.float_checks = 0
        self.max_abs_difference = 0.0
        self.errors = []

    def exact(self, actual, expected, label):
        self.checks += 1
        if actual != expected:
            self.errors.append({'kind': 'exact', 'label': label,
                                'actual': actual, 'expected': expected})
            raise ValueError(f'exact mismatch: {label}')

    def require(self, condition, label):
        self.exact(bool(condition), True, label)

    def close(self, actual, expected, label):
        self.float_checks += 1
        actual, expected = float(actual), float(expected)
        difference = abs(actual - expected)
        if not (math.isfinite(actual) and math.isfinite(expected)):
            self.errors.append({'kind': 'nonfinite', 'label': label,
                                'actual': repr(actual), 'expected': repr(expected)})
            raise ValueError(f'nonfinite: {label}')
        self.max_abs_difference = max(self.max_abs_difference, difference)
        limit = ATOL + RTOL * abs(expected)
        if difference > limit:
            self.errors.append({'kind': 'float', 'label': label, 'actual': actual,
                                'expected': expected, 'abs_difference': difference,
                                'limit': limit})
            raise ValueError(f'float mismatch: {label}')


def integer(value, label):
    if type(value) is not int:
        raise ValueError(f'not a strict integer: {label}: {value!r}')
    return value


def mean(values):
    if not values:
        raise ValueError('empty mean')
    return math.fsum(values) / len(values)


def squared(vector):
    return math.fsum(x * x for x in vector)


def center(points):
    anchor = points[0]
    local = [[x[k] - anchor[k] for k in range(3)] for x in points]
    offset = [mean([x[k] for x in local]) for k in range(3)]
    absolute = [anchor[k] + offset[k] for k in range(3)]
    variance = mean([squared([x[k] - offset[k] for k in range(3)]) for x in local])
    return absolute, variance


def measure(groups, anchor, radius):
    if not math.isfinite(radius) or radius <= 0 or not math.isfinite(radius * radius) or radius * radius == 0:
        raise ValueError('radius or radius squared is invalid')
    # Translate everything by immutable first-write anchor before centering.
    local_groups = [[[x[k] - anchor[k] for k in range(3)] for x in g] for g in groups]
    centers_and_w = [center(g) for g in local_groups]
    centroids = [c for c, _ in centers_and_w]
    mu = [mean([c[k] for c in centroids]) for k in range(3)]
    raw = {'W': mean([w for _, w in centers_and_w]),
           'B': mean([squared([c[k] - mu[k] for k in range(3)]) for c in centroids]),
           'A': squared(mu), 'D': mean([squared(c) for c in centroids])}
    if not all(math.isfinite(v) and v >= 0 for v in raw.values()):
        raise ValueError('nonfinite or negative measure')
    raw.update({key + '_over_radius2': val / (radius * radius) for key, val in list(raw.items())})
    return raw, [([c[k] + anchor[k] for k in range(3)], w) for c, w in centers_and_w]


def quantile(values, probability):
    ordered = sorted(values)
    pos = (len(ordered) - 1) * probability
    lower = int(math.floor(pos))
    upper = int(math.ceil(pos))
    frac = pos - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * frac


def compare_tree(actual, expected, label, audit):
    if isinstance(expected, dict):
        audit.require(isinstance(actual, dict), label + ':dict')
        audit.exact(sorted(actual), sorted(expected), label + ':keys')
        for key, value in expected.items():
            compare_tree(actual[key], value, label + '.' + key, audit)
    elif isinstance(expected, list):
        audit.require(isinstance(actual, list), label + ':list')
        audit.exact(len(actual), len(expected), label + ':length')
        for i, value in enumerate(expected):
            compare_tree(actual[i], value, f'{label}[{i}]', audit)
    elif type(expected) is float:
        audit.require(type(actual) in (int, float), label + ':numeric')
        audit.close(actual, expected, label)
    else:
        audit.exact(type(actual).__name__, type(expected).__name__, label + ':type')
        audit.exact(actual, expected, label)


def reconstruct(directory, phase, block, audit):
    # Only needed NPZ entries are decoded; no normals/colors/query features.
    with np.load(directory / 'observations.npz', allow_pickle=False) as z:
        obs = {key: z[key] for key in ['ids', 'points', 'radii', 'offsets']}
    with np.load(directory / 'A0P0.npz', allow_pickle=False) as z:
        memory = {key: z[key] for key in ['points', 'radii', 'counts']}
    for name in ['ids', 'offsets']:
        audit.require(obs[name].dtype.kind in 'iu', name + ':dtype')
    audit.require(memory['counts'].dtype.kind in 'iu', 'counts:dtype')
    for name in ['points', 'radii']:
        audit.require(bool(np.isfinite(obs[name]).all()), 'observations:' + name + ':finite')
        audit.require(bool(np.isfinite(memory[name]).all()), 'memory:' + name + ':finite')
    n, npoints = len(obs['points']), len(memory['points'])
    for name in ['ids', 'points']:
        audit.exact(list(obs[name].shape), [n, 3], 'observations:' + name + ':shape')
    audit.exact(list(obs['radii'].shape), [n], 'observations:radii:shape')
    audit.exact(list(memory['points'].shape), [npoints, 3], 'memory:points:shape')
    for name in ['radii', 'counts']:
        audit.exact(list(memory[name].shape), [npoints], 'memory:' + name + ':shape')
    offsets = obs['offsets'].tolist()
    audit.exact(list(obs['offsets'].shape), [21], 'offsets:shape')
    audit.exact((offsets[0], offsets[-1]), (0, n), 'offsets:endpoints')
    audit.require(all(0 <= x <= y <= n for x, y in zip(offsets, offsets[1:])), 'offsets:monotonic')
    x, ids, radii = obs['points'].tolist(), obs['ids'].tolist(), obs['radii'].tolist()
    mem, mradii, counts = memory['points'].tolist(), memory['radii'].tolist(), memory['counts'].tolist()
    events, sources = read_json(directory / 'A0_events.json'), read_json(directory / 'A0P0_sources.json')
    audit.exact(len(events), 20, 'events:length')
    audit.exact(set(sources), set(map(str, range(npoints))), 'sources:all_point_ids')
    groups, births, seen, next_id = {}, {}, set(), 0
    for frame in range(20):
        event = events[frame]
        for key in ['frame', 'old_n', 'new_n']:
            integer(event[key], f'event{frame}:{key}')
        audit.exact(event['frame'], frame, 'event:frame')
        audit.exact(event['old_n'], next_id, 'event:old_n')
        old_n = next_id
        lo, hi = offsets[frame:frame + 2]
        audit.exact(len(event['targets']), hi - lo, 'event:targets:length')
        audit.exact(len(event['matches']), hi - lo, 'event:matches:length')
        previous_pixel = -1
        for local, flat in enumerate(range(lo, hi)):
            identity = ids[flat]
            audit.exact(identity[0], frame, f'ids[{flat}]:frame')
            u, v = identity[1:]
            audit.require(0 <= u < 224 and 0 <= v < 224 and u % 8 == 0 and v % 8 == 0, f'ids[{flat}]:pixel')
            audit.require(v * 224 + u > previous_pixel, f'ids[{flat}]:row_major_order')
            previous_pixel = v * 224 + u
            audit.require(tuple(identity) not in seen, f'ids[{flat}]:unique')
            seen.add(tuple(identity))
            target = integer(event['targets'][local], 'target')
            match = integer(event['matches'][local], 'match')
            if match < 0:
                audit.exact(match, -1, f'event{frame}:birth_match')
                audit.exact(target, next_id, f'event{frame}:birth_order')
                births[target] = flat
                next_id += 1
            else:
                audit.require(0 <= target < old_n, f'event{frame}:preexisting')
                audit.exact(target, match, f'event{frame}:match_target')
            groups.setdefault((target, frame), []).append(flat)
        audit.exact(event['new_n'], next_id, 'event:new_n')
    audit.exact(next_id, npoints, 'map:number_of_births')
    audit.exact(len(seen), n, 'observations:coverage')
    audit.exact(sorted(i for indices in groups.values() for i in indices), list(range(n)), 'observations:exactly_once')
    point_frames = {}
    for point, frame in groups:
        point_frames.setdefault(point, []).append(frame)
    prefix = {'phase': phase, 'block': block, 'stride': 8}
    prows, frows, associations = [], [], []
    for point in range(npoints):
        frames = sorted(point_frames.get(point, []))
        audit.require(bool(frames), f'point{point}:nonempty')
        source_frames = sources[str(point)]
        audit.require(all(type(f) is int for f in source_frames), f'point{point}:source_types')
        audit.exact(source_frames, frames, f'point{point}:sources')
        audit.exact(counts[point], len(frames), f'point{point}:counts')
        birth = births[point]
        audit.exact(mem[point], x[birth], f'point{point}:first_write_position')
        audit.exact(mradii[point], radii[birth], f'point{point}:first_write_radius')
        indices = [groups[(point, f)] for f in frames]
        values, centers = measure([[x[i] for i in g] for g in indices], mem[point], mradii[point])
        audit.close(values['D'], values['B'] + values['A'], f'point{point}:D=B+A')
        if len(frames) == 1:
            audit.exact(values['B'], 0.0, f'point{point}:single_source_B')
        prows.append(dict(prefix, point_id=point, m=len(frames), n_obs=sum(map(len, indices)),
                          single_source=int(len(frames) == 1), birth_frame=ids[birth][0],
                          birth_flat_index=birth, birth_u=ids[birth][1], birth_v=ids[birth][2],
                          mem_x=mem[point][0], mem_y=mem[point][1], mem_z=mem[point][2],
                          radius=mradii[point], **values))
        for frame, inds, (c, w) in zip(frames, indices, centers):
            frows.append(dict(prefix, point_id=point, frame=frame, n_obs=len(inds),
                              c_x=c[0], c_y=c[1], c_z=c[2], within_variance=w))
            associations.append({'point_id': point, 'frame': frame, 'flat_indices': inds})
    strata = []
    for m in sorted({p['m'] for p in prows}):
        selected = [p for p in prows if p['m'] == m]
        metric_summary = {}
        for metric in METRICS:
            values = [p[metric] for p in selected]
            metric_summary[metric] = {'mean': mean(values), 'median': quantile(values, .5),
                                      'p90': quantile(values, .9)}
        strata.append({'m': m, 'n_points': len(selected), 'metrics': metric_summary})
    singles = sum(p['single_source'] for p in prows)
    summary = dict(prefix, n_points=npoints, n_observations=n, n_frame_groups=len(groups),
                   single_source_points=singles, multi_source_points=npoints - singles, by_m=strata)
    return prows, frows, dict(prefix, groups=associations), summary


def compare_csv(path, fields, expected, audit):
    with path.open(newline='') as f:
        reader = csv.DictReader(f)
        audit.exact(reader.fieldnames, fields, path.name + ':header')
        actual = list(reader)
    audit.exact(len(actual), len(expected), path.name + ':rows')
    for index, (row, reference) in enumerate(zip(actual, expected)):
        audit.exact(set(row), set(fields), path.name + ':fields')
        for name in fields:
            label = f'{path.name}:{index}:{name}'
            if name == 'phase':
                audit.exact(row[name], reference[name], label)
            elif name in INT_FIELDS:
                audit.exact(row[name], str(reference[name]), label)
            else:
                audit.close(float(row[name]), reference[name], label)


def run(result, output):
    output.mkdir(parents=True, exist_ok=False)
    audit = Audit()
    started = now()
    source_before = sha(__file__)
    (output / 'verifier_source_snapshot.py').write_bytes(Path(__file__).read_bytes())
    receipt = {'schema': 's14b-independent-verification-v1', 'started_utc': started,
               'atol': ATOL, 'rtol': RTOL, 'comparison': 'abs(actual-reference)<=atol+rtol*abs(reference)',
               'source_sha256_before': source_before, 'python': sys.version,
               'numpy': np.__version__, 'platform': platform.platform(),
               'result': str(result), 'status': 'RUNNING', 'input_hashes_before': {}}
    write_json(output / 'verification.json', receipt)
    try:
        manifest_path = result / 'execution_manifest.json'
        result_files = [manifest_path, result / 'source_snapshot.py', result / 'points.csv',
                        result / 'frame_centroids.csv', result / 'association_indices.json', result / 'summary.json']
        result_hashes_before = {p.name: sha(p) for p in result_files}
        receipt['result_hashes_before'] = result_hashes_before
        manifest = read_json(manifest_path)
        audit.exact(manifest['schema'], 's14b-observation-disagreement-v1', 'manifest:schema')
        audit.exact(manifest['independent_verifier_sha256'], source_before, 'manifest:verifier_identity')
        audit.exact(sha(result / 'source_snapshot.py'), manifest['source_sha256'], 'manifest:production_snapshot_identity')
        allowed = [f'{base}/block{block}_stride8/{name}' for _, block, base in BLOCKS for name in FILES]
        inputs = manifest['inputs']
        audit.exact(len(inputs), 24, 'manifest:24_inputs')
        audit.exact(sorted(item['path'] for item in inputs), sorted(allowed), 'manifest:fixed_input_paths')
        for item in inputs:
            digest = sha(ROOT / item['path'])
            receipt['input_hashes_before'][item['path']] = digest
            audit.exact(digest, item['sha256'], 'manifest:input_hash:' + item['path'])
        all_points, all_frames, all_associations, all_summaries = [], [], [], []
        for phase, block, base in BLOCKS:
            points, frames, association, summary = reconstruct(ROOT / base / f'block{block}_stride8', phase, block, audit)
            all_points.extend(points)
            all_frames.extend(frames)
            all_associations.append(association)
            all_summaries.append(summary)
            receipt['completed_blocks'] = len(all_summaries)
            write_json(output / 'verification.json', receipt)
        compare_csv(result / 'points.csv', POINT_FIELDS, all_points, audit)
        compare_csv(result / 'frame_centroids.csv', FRAME_FIELDS, all_frames, audit)
        association = read_json(result / 'association_indices.json')
        audit.exact(set(association), {'schema', 'blocks'}, 'association:top_keys')
        audit.require(isinstance(association['schema'], str) and bool(association['schema']), 'association:schema')
        compare_tree(association['blocks'], all_associations, 'association.blocks', audit)
        summary = read_json(result / 'summary.json')
        audit.exact(set(summary), {'schema', 'quantile_method', 'blocks'}, 'summary:top_keys')
        audit.exact(summary['quantile_method'], 'linear', 'summary:quantile_method')
        audit.require(isinstance(summary['schema'], str) and bool(summary['schema']), 'summary:schema')
        compare_tree(summary['blocks'], all_summaries, 'summary.blocks', audit)
        receipt['input_hashes_after'] = {p: sha(ROOT / p) for p in allowed}
        compare_tree(receipt['input_hashes_after'], receipt['input_hashes_before'], 'input_identity_after', audit)
        receipt['result_hashes_after'] = {p.name: sha(p) for p in result_files}
        compare_tree(receipt['result_hashes_after'], result_hashes_before, 'result_identity_after', audit)
        audit.exact(sha(__file__), source_before, 'verifier_source_after')
        receipt.update(status='PASS', points=len(all_points), frame_groups=len(all_frames),
                       observations=sum(b['n_observations'] for b in all_summaries),
                       completed_blocks=len(all_summaries), independent_summary=all_summaries)
    except BaseException as exc:
        receipt.update(status='FAIL', exception=repr(exc), traceback=traceback.format_exc())
        raise
    finally:
        # Preserve the identity evidence available even when a numerical check fails.
        receipt['input_hashes_after'] = {p: sha(ROOT / p) for p in receipt['input_hashes_before']}
        receipt.update(ended_utc=now(), source_sha256_after=sha(__file__), exact_checks=audit.checks,
                       float_checks=audit.float_checks, max_abs_difference=audit.max_abs_difference,
                       errors=audit.errors)
        write_json(output / 'verification.json', receipt)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--result', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.result.resolve(), args.output.resolve())
