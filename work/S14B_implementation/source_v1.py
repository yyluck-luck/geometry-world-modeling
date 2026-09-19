#!/usr/bin/env python3
"""S14B fixed-event, frame-equal descriptive measurement. No scoring imports.

Only the 24 named historical inputs may be opened as data. All are cached and
hashed before any data decoding. Controls are verified by the external caller.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import platform
import re
import resource
import sys
import time
import traceback
import zipfile

import numpy as np

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
SCHEMA = 's14b-observation-disagreement-v1'
ATOL, RTOL = 1e-12, 1e-10
BLOCKS = [(phase, b, f'results/{directory}/block{b}_stride8')
          for phase, directory in [('S7', 'S7_event_replay'), ('S8', 'S8_event_replay_v2')]
          for b in range(3)]
NAMES = ('observations.npz', 'A0_events.json', 'A0P0.npz', 'A0P0_sources.json')
INPUT_PATHS = {f'{prefix}/{name}' for _, _, prefix in BLOCKS for name in NAMES}
METRICS = ['W', 'B', 'A', 'D'] + [x + '_over_radius2' for x in ['W', 'B', 'A', 'D']]
POINT_COLUMNS = ['phase', 'block', 'stride', 'point_id', 'm', 'n_obs', 'single_source',
                 'birth_frame', 'birth_flat_index', 'birth_u', 'birth_v',
                 'mem_x', 'mem_y', 'mem_z', 'radius'] + METRICS
FRAME_COLUMNS = ['phase', 'block', 'stride', 'point_id', 'frame', 'n_obs',
                 'c_x', 'c_y', 'c_z', 'within_variance']


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value, name, lo=0, hi=None):
    require(type(value) is int, f'{name}: expected JSON integer, not bool/float')
    require(value >= lo and (hi is None or value <= hi), f'{name}: outside domain')
    return value


def strict_json(data):
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, f'Duplicate JSON key: {key}')
            out[key] = value
        return out
    def invalid(value):
        raise ValueError(f'Non-finite JSON literal: {value}')
    return json.loads(data, object_pairs_hook=pairs, parse_constant=invalid)


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def load_npz(data, members, expected, counters):
    # Merely list unused normals/colors; they never become numerical arrays.
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = z.namelist()
        require(len(names) == len(set(names)), 'Duplicate NPZ member')
        require(set(names) == {x + '.npy' for x in expected}, 'Unexpected NPZ members')
    out = {}
    with np.load(io.BytesIO(data), allow_pickle=False) as z:
        for name in members:
            out[name] = z[name]
            counters['numerical_arrays_decoded'] += 1
    counters['npz_files_decoded'] += 1
    return out


def array(value, name, shape, kind):
    require(isinstance(value, np.ndarray) and value.shape == shape, f'{name}: wrong shape')
    require(value.dtype.kind in kind, f'{name}: wrong numerical dtype')
    require(np.isfinite(value).all(), f'{name}: non-finite number')
    return value


def measure_block(obs, memory, events, sources, phase, block):
    """Pure array/JSON computation; suitable for small, labelled artificial tests."""
    n = len(obs['points'])
    p = len(memory['points'])
    require(n > 0 and p > 0, 'Empty observation/map domain')
    xyz = array(obs['points'], 'observations.points', (n, 3), 'f')
    ids = array(obs['ids'], 'observations.ids', (n, 3), 'iu')
    radii = array(obs['radii'], 'observations.radii', (n,), 'f')
    offsets = array(obs['offsets'], 'observations.offsets', (21,), 'iu')
    mem = array(memory['points'], 'memory.points', (p, 3), 'f')
    radius = array(memory['radii'], 'memory.radii', (p,), 'f')
    counts = array(memory['counts'], 'memory.counts', (p,), 'iu')
    require((radii > 0).all() and (radius > 0).all(), 'Radius must be positive')
    require((counts >= 1).all() and (counts <= 20).all(), 'Map counts outside 1..20')
    require(int(offsets[0]) == 0 and int(offsets[-1]) == n, 'Offsets do not span observations')
    require(all(0 <= int(offsets[i]) <= int(offsets[i+1]) <= n for i in range(20)),
            'Offsets not monotonic/in range')
    require((ids[:, 0] < 20).all() and (ids >= 0).all(), 'Invalid identity frame/domain')
    require((ids[:, 1:] < 224).all() and (ids[:, 1:] % 8 == 0).all(), 'Invalid stride8 pixel')
    require(isinstance(events, list) and len(events) == 20, 'Expected 20 events')
    require(isinstance(sources, dict) and set(sources) == {str(j) for j in range(p)},
            'Sources point identities do not exactly span map')
    groups = {}
    births = {}
    old = 0
    for f, event in enumerate(events):
        require(isinstance(event, dict) and set(event) ==
                {'frame', 'old_n', 'targets', 'matches', 'new_n', 'threshold'}, 'Event schema')
        require(integer(event['frame'], 'event.frame', 0, 19) == f, 'Frame order mismatch')
        require(integer(event['old_n'], 'event.old_n', 0, p) == old, 'Old map boundary mismatch')
        new = integer(event['new_n'], 'event.new_n', old, p)
        threshold = event['threshold']
        require(type(threshold) in (int, float) and np.isfinite(threshold) and threshold > 0,
                'Invalid saved threshold')
        a, b = int(offsets[f]), int(offsets[f+1])
        require(np.all(ids[a:b, 0] == f), 'Offset/frame identity mismatch')
        pixel_order = ids[a:b, 2].astype(np.int64) * 224 + ids[a:b, 1].astype(np.int64)
        require(np.all(pixel_order[1:] > pixel_order[:-1]), 'Pixel identities not unique/raster ordered')
        targets, matches = event['targets'], event['matches']
        require(isinstance(targets, list) and isinstance(matches, list)
                and len(targets) == len(matches) == b-a, 'Event/observation length mismatch')
        next_birth = old
        for index, (target, match) in enumerate(zip(targets, matches), a):
            target = integer(target, 'target', 0, p-1)
            match = integer(match, 'match', -1, p-1)
            if match == -1:
                require(target == next_birth, 'Birth target not in observation order')
                require(target not in births, 'Repeated birth')
                births[target] = index
                next_birth += 1
            else:
                require(target == match and target < old, 'Matched target did not exist before frame')
            groups.setdefault((target, f), []).append(index)
        require(next_birth == new, 'New map boundary mismatch')
        old = new
    require(old == p and set(births) == set(range(p)), 'Final map/birth coverage mismatch')
    flat_used = [i for values in groups.values() for i in values]
    require(len(flat_used) == n and sorted(flat_used) == list(range(n)), 'Dropped/repeated observation')
    points, frames, associations = [], [], []
    for j in range(p):
        frame_ids = [f for f in range(20) if (j, f) in groups]
        source = sources[str(j)]
        require(isinstance(source, list), 'Source frame list required')
        for f in source:
            integer(f, 'source frame', 0, 19)
        require(source == frame_ids and len(source) == int(counts[j]), 'Frame sources/count mismatch')
        m = len(frame_ids)
        require(m > 0, 'Empty point group')
        birth = births[j]
        require(np.array_equal(mem[j], xyz[birth]), 'First-write map position mismatch')
        require(radius[j] == radii[birth], 'First-write map radius mismatch')
        centroids, within, num_obs = [], [], 0
        for f in frame_ids:
            indices = groups[(j, f)]
            values = xyz[indices].astype(np.float64)
            centroid = np.mean(values, axis=0)
            w = float(np.mean(np.sum((values-centroid)**2, axis=1)))
            centroids.append(centroid)
            within.append(w)
            num_obs += len(indices)
            frames.append(dict(phase=phase, block=block, stride=8, point_id=j, frame=f,
                               n_obs=len(indices), c_x=float(centroid[0]), c_y=float(centroid[1]),
                               c_z=float(centroid[2]), within_variance=w))
            associations.append(dict(point_id=j, frame=f, flat_indices=indices))
        c = np.asarray(centroids)
        mu = np.mean(c, axis=0)
        W = float(np.mean(within))
        B = 0.0 if m == 1 else float(np.mean(np.sum((c-mu)**2, axis=1)))
        A = float(np.sum((mu-mem[j])**2))
        D = float(np.mean(np.sum((c-mem[j])**2, axis=1)))
        require(np.isclose(D, B+A, atol=ATOL, rtol=RTOL), 'D != B + A at preset tolerance')
        r2 = float(radius[j])**2
        require(np.isfinite(r2) and r2 > 0, 'Radius square invalid; no epsilon permitted')
        values = [W, B, A, D] + [v/r2 for v in [W, B, A, D]]
        require(np.isfinite(values).all() and min(values) >= 0, 'Metric invalid')
        row = dict(phase=phase, block=block, stride=8, point_id=j, m=m, n_obs=num_obs,
                   single_source=int(m == 1), birth_frame=int(ids[birth, 0]), birth_flat_index=birth,
                   birth_u=int(ids[birth, 1]), birth_v=int(ids[birth, 2]),
                   mem_x=float(mem[j, 0]), mem_y=float(mem[j, 1]), mem_z=float(mem[j, 2]),
                   radius=float(radius[j]))
        row.update(zip(METRICS, values))
        points.append(row)
    summary = dict(phase=phase, block=block, stride=8, n_points=p, n_observations=n,
                   n_frame_groups=len(frames), single_source_points=sum(r['single_source'] for r in points),
                   multi_source_points=sum(1-r['single_source'] for r in points), by_m=[])
    for m in sorted({r['m'] for r in points}):
        subset = [r for r in points if r['m'] == m]
        metrics = {}
        for key in METRICS:
            values = np.array([r[key] for r in subset], dtype=np.float64)
            q = np.quantile(values, [.5, .9], method='linear')
            metrics[key] = dict(mean=float(np.mean(values)), median=float(q[0]), p90=float(q[1]))
        summary['by_m'].append(dict(m=m, n_points=len(subset), metrics=metrics))
    return points, frames, associations, summary


def write_csv(path, columns, rows):
    with path.open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def run(manifest_path, output, root):
    started = time.perf_counter()
    # Existing result directories are refused before writing anything into them.
    output.mkdir(parents=True, exist_ok=False)
    meta = dict(schema=SCHEMA, status='RUNNING', started_utc=now(),
                scope='Historical prediction disagreement only; no error/benefit/novelty inference',
                root=str(root), output=str(output), manifest_path=str(manifest_path),
                environment=dict(python=sys.version, numpy=np.__version__, platform=platform.platform(),
                                 executable=sys.executable),
                tolerances=dict(atol=ATOL, rtol=RTOL), controls_verification='external caller',
                counters=dict(input_files_cached=0, input_bytes_cached=0, npz_files_decoded=0,
                              numerical_arrays_decoded=0, prediction_json_files_decoded=0,
                              completed_blocks=0, gt_scoring_query_feature_reads=0, model_runs=0),
                input_sha256_before={}, input_sha256_after={})
    source_path = Path(__file__).resolve()
    cache, paths = {}, {}
    manifest_data = source_data = None
    error = None
    try:
        source_data = source_path.read_bytes()
        meta['source_sha256_before'] = sha(source_data)
        (output/'source_snapshot.py').write_bytes(source_data)
        manifest_data = manifest_path.read_bytes()
        meta['manifest_sha256_before'] = sha(manifest_data)
        (output/'execution_manifest.json').write_bytes(manifest_data)
        manifest = strict_json(manifest_data)
        require(isinstance(manifest, dict) and manifest.get('schema') == SCHEMA, 'Manifest schema mismatch')
        require(manifest.get('source_sha256') == sha(source_data), 'Frozen source SHA mismatch')
        inputs = manifest.get('inputs')
        require(isinstance(inputs, list) and len(inputs) == 24, 'Manifest requires exactly 24 inputs')
        expected = {}
        for item in inputs:
            require(isinstance(item, dict) and set(item) == {'path', 'sha256'}, 'Input record schema')
            name, digest = item['path'], item['sha256']
            require(isinstance(name, str) and name in INPUT_PATHS and name not in expected,
                    'Unapproved/duplicate input path')
            require(isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest), 'Invalid SHA')
            expected[name] = digest
        require(set(expected) == INPUT_PATHS, 'Frozen inputs differ from 6 stride8 blocks')
        for name in sorted(expected):
            path = root/name
            require(path.resolve() == path, 'Symlink or noncanonical input path forbidden')
            paths[name] = path
            data = path.read_bytes()
            digest = sha(data)
            meta['input_sha256_before'][name] = digest
            require(digest == expected[name], f'Input SHA mismatch: {name}')
            cache[name] = data
            meta['counters']['input_files_cached'] += 1
            meta['counters']['input_bytes_cached'] += len(data)
        meta['inputs_cached_utc'] = now()
        require(len(cache) == 24, 'All input bytes must precede decoding')
        all_points, all_frames, association_blocks, summaries = [], [], [], []
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            for phase, block, prefix in BLOCKS:
                obs = load_npz(cache[prefix+'/observations.npz'], ['ids', 'points', 'radii', 'offsets'],
                               ['ids', 'points', 'normals', 'radii', 'colors', 'offsets'], meta['counters'])
                mem = load_npz(cache[prefix+'/A0P0.npz'], ['points', 'radii', 'counts'],
                               ['points', 'normals', 'radii', 'colors', 'counts'], meta['counters'])
                events = strict_json(cache[prefix+'/A0_events.json'])
                meta['counters']['prediction_json_files_decoded'] += 1
                sources = strict_json(cache[prefix+'/A0P0_sources.json'])
                meta['counters']['prediction_json_files_decoded'] += 1
                points, frames, indices, summary = measure_block(obs, mem, events, sources, phase, block)
                all_points.extend(points)
                all_frames.extend(frames)
                association_blocks.append(dict(phase=phase, block=block, stride=8, groups=indices))
                summaries.append(summary)
                meta['counters']['completed_blocks'] += 1
        meta['counters'].update(points=len(all_points), frame_groups=len(all_frames),
                                observations=sum(x['n_observations'] for x in summaries))
        write_csv(output/'points.csv', POINT_COLUMNS, all_points)
        write_csv(output/'frame_centroids.csv', FRAME_COLUMNS, all_frames)
        dump(output/'association_indices.json', dict(schema=SCHEMA, blocks=association_blocks))
        dump(output/'summary.json', dict(schema=SCHEMA, quantile_method='linear', blocks=summaries))
        meta['measurement_completed_utc'] = now()
    except BaseException as exc:
        error = exc
        meta['error'] = dict(type=type(exc).__name__, message=str(exc), traceback=traceback.format_exc())
    finally:
        identity_errors = []
        for name, path in paths.items():
            try:
                digest = sha(path.read_bytes())
                meta['input_sha256_after'][name] = digest
                if digest != meta['input_sha256_before'].get(name):
                    identity_errors.append('input changed: '+name)
            except Exception as exc:
                identity_errors.append(f'input recheck failed: {name}: {exc}')
        for label, path, before in [('source', source_path, source_data), ('manifest', manifest_path, manifest_data)]:
            try:
                digest = sha(path.read_bytes())
                meta[label+'_sha256_after'] = digest
                if before is not None and digest != sha(before):
                    identity_errors.append(label+' changed')
            except Exception as exc:
                identity_errors.append(f'{label} recheck failed: {exc}')
        meta['identity_errors'] = identity_errors
        meta['identity_unchanged'] = not identity_errors and len(cache) == 24
        meta['status'] = 'SUCCESS' if error is None and meta['identity_unchanged'] else 'FAILED'
        meta['finished_utc'] = now()
        meta['elapsed_seconds'] = time.perf_counter()-started
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        meta['peak_rss_bytes'] = int(rss if sys.platform == 'darwin' else rss*1024)
        meta['output_sha256'] = {p.name: sha(p.read_bytes()) for p in sorted(output.iterdir()) if p.is_file()}
        dump(output/'metadata.json', meta)
    if meta['status'] != 'SUCCESS':
        raise RuntimeError(f'S14B failed; preserved metadata: {output}/metadata.json') from error
    return meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    meta = run(args.manifest.resolve(), args.output.resolve(), args.root.resolve())
    print(json.dumps(dict(status=meta['status'], counters=meta['counters'], output=meta['output'])))


if __name__ == '__main__':
    main()
