#!/usr/bin/env python3
"""Two-stage, fixed-input S14C exploratory diagnostic; never fit or select images."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import itertools
import json
import math
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

SCHEMA = 's14c-selection-disagreement-v1'
ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
POINT_PATH = 'results/S14B_observation_disagreement/points.csv'
FRAME_PATH = 'results/S14B_observation_disagreement/frame_centroids.csv'
SCORE_PATH = 'results/S12_matched_budget/records.json'
KEYS = ['stage', 'block', 'query', 'split', 'arm', 'stride']
METRICS = ['disagreement_g_minus_p', 'source_count_p_minus_g',
           'camera_pair_p_minus_g', 'query_distance_g_minus_p']
ROW_COLUMNS = KEYS + ['n_points', 'eligible_g', 'eligible_p', 'common_points',
    'common_fraction', 'common_fraction_of_g', 'common_fraction_of_p', 'same_selected_set',
    'status',
    'disagreement_g', 'disagreement_p',
    'disagreement_g_minus_p', 'source_count_g', 'source_count_p',
    'source_count_p_minus_g', 'camera_pair_g', 'camera_pair_p',
    'camera_pair_p_minus_g', 'query_distance_g', 'query_distance_p',
    'query_distance_g_minus_p']
LABEL_COLUMNS = ['g_supported_pixels', 'p_supported_pixels', 'valid_pixels',
                 'g_support', 'p_support', 'y_pose_minus_geometry_pp']


def now():
    return datetime.now(timezone.utc).isoformat()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def unique_pairs(pairs):
    out = {}
    for key, value in pairs:
        require(key not in out, f'Duplicate JSON key {key}')
        out[key] = value
    return out


def decode(data):
    return json.loads(data, object_pairs_hook=unique_pairs)


def save(path, obj):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(obj, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write('\n')


def write_csv(path, columns, rows):
    with path.open('x', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def number(value, label, nonnegative=False):
    require(type(value) in (int, float), f'Not numeric: {label}')
    value = float(value)
    require(math.isfinite(value), f'Nonfinite: {label}')
    require(not nonnegative or value >= 0, f'Negative: {label}')
    return value


def integer(value, label, low=0, high=None):
    require(type(value) is int and value >= low and (high is None or value <= high),
            f'Invalid integer: {label}')
    return value


def csv_int(value, label, low=0, high=None):
    parsed = int(value)
    require(str(parsed) == value, f'Noncanonical integer: {label}')
    return integer(parsed, label, low, high)


def frame_ids(value, n):
    require(type(value) is list and len(value) == n and len(set(value)) == n,
            'Wrong/duplicate frame domain')
    return [integer(v, 'frame', 0, 19) for v in value]


def prediction_path(stage, block):
    folder = 'S7_event_replay' if stage == 'S7' else 'S8_event_replay_v2'
    return f'results/{folder}/block{block}_stride8/prediction_only_selection.json'


def pose_path(stage, block, query):
    return f'results/S12_matched_budget/selections/{stage}_block{block}_query{query}.json'


def expected_paths():
    paths = {POINT_PATH, FRAME_PATH}
    for stage in ('S7', 'S8'):
        for block in range(3):
            paths.add(prediction_path(stage, block))
            paths.update(pose_path(stage, block, query) for query in range(20, 24))
    return paths


def digest(value):
    return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def input_path(root, rel):
    path = root / rel
    require(path.resolve() == path and path.is_file(), f'Redirected or absent input: {rel}')
    return path


def validate_manifest(manifest, source_sha):
    require(manifest['schema'] == SCHEMA and manifest['source_sha256'] == source_sha,
            'Manifest schema/source mismatch')
    require(type(manifest['inputs']) is list and len(manifest['inputs']) == 32,
            'Exactly 32 measurement inputs required')
    mapping = {}
    for entry in manifest['inputs']:
        require(set(entry) == {'path', 'sha256'} and entry['path'] in expected_paths()
                and entry['path'] not in mapping and digest(entry['sha256']), 'Invalid allowlist')
        mapping[entry['path']] = entry['sha256']
    require(set(mapping) == expected_paths(), 'Input domain mismatch')
    label = manifest['score_input']
    require(set(label) == {'path', 'sha256'} and label['path'] == SCORE_PATH
            and digest(label['sha256']), 'Invalid separately gated score input')
    return mapping


def read_table(payload, required):
    reader = csv.DictReader(io.StringIO(payload.decode('utf-8'), newline=''))
    require(reader.fieldnames is not None and len(set(reader.fieldnames)) == len(reader.fieldnames)
            and set(required) <= set(reader.fieldnames), 'CSV schema mismatch')
    rows = list(reader)
    require(all(None not in row and None not in row.values() for row in rows), 'Malformed CSV row')
    return rows


def parse_maps(point_bytes, frame_bytes, counters=None):
    maps = {(stage, block): {} for stage in ('S7', 'S8') for block in range(3)}
    point_rows = read_table(point_bytes, ['phase', 'block', 'stride', 'point_id', 'm', 'radius'])
    if counters is not None:
        counters['measurement_csv_decoded'] += 1
    for row in point_rows:
        key = row['phase'], csv_int(row['block'], 'block', 0, 2)
        require(key in maps and csv_int(row['stride'], 'stride') == 8, 'Wrong point case')
        point = csv_int(row['point_id'], 'point_id')
        require(point not in maps[key], 'Duplicate point')
        radius = number(float(row['radius']), 'radius')
        require(radius > 0 and math.isfinite(radius * radius) and radius * radius > 0,
                'Nonpositive or unrepresentable radius squared')
        maps[key][point] = dict(radius=radius, m=csv_int(row['m'], 'm', 1, 20), frames={})
    frame_rows = read_table(frame_bytes, ['phase', 'block', 'stride', 'point_id', 'frame', 'n_obs',
                                        'c_x', 'c_y', 'c_z'])
    if counters is not None:
        counters['measurement_csv_decoded'] += 1
    for row in frame_rows:
        key = row['phase'], csv_int(row['block'], 'block', 0, 2)
        require(key in maps and csv_int(row['stride'], 'stride') == 8, 'Wrong centroid case')
        point, frame = csv_int(row['point_id'], 'point_id'), csv_int(row['frame'], 'frame', 0, 19)
        require(point in maps[key] and frame not in maps[key][point]['frames'], 'Missing/duplicate centroid')
        maps[key][point]['frames'][frame] = dict(
            xyz=np.array([number(float(row[f'c_{axis}']), f'c_{axis}') for axis in 'xyz'], dtype=np.float64),
            n_obs=csv_int(row['n_obs'], 'frame n_obs', 1))
    for points in maps.values():
        require(points and sorted(points) == list(range(len(points))), 'Point IDs must be complete contiguous domain')
        for point in points.values():
            require(len(point['frames']) == point['m'], 'Point/source count mismatch')
    return maps


def trace_info(trace, distance_map):
    candidates = frame_ids(trace['expanded_candidates'], 14)
    selected = frame_ids(trace['selected'], 4)
    require(set(selected) <= set(candidates) and trace['nms'] is True, 'Selection/candidate/NMS mismatch')
    ranked = frame_ids(trace['sorted_frames'], 14)
    require(set(ranked) == set(candidates), 'Ranked candidate domain')
    require([distance_map[i] for i in ranked] == sorted(distance_map[i] for i in candidates), 'Ranked distance order')
    require(len(trace['distances_float32']) == 14 and
            all(number(v, 'saved distance', True) == distance_map[i]
                for i, v in zip(candidates, trace['distances_float32'])), 'Saved query distances differ')
    accepted, pairs = [], []
    for index, step in enumerate(trace['steps']):
        require(not step.get('fallback_added'), 'NMS fallback lacks selected-pair evidence')
        if 'frame' not in step:
            continue
        integer(step['frame'], 'NMS step frame', 0, 19)
        require(type(step['accepted']) is bool, 'Nonboolean acceptance')
        if step['accepted']:
            accepted.append((index, step))
    require([s['frame'] for _, s in accepted] == selected[1:], 'Accepted order differs')
    for position, (index, step) in enumerate(accepted, start=1):
        comparisons = step['comparisons']
        require(type(comparisons) is list and all(type(c) is list and len(c) == 2 for c in comparisons),
                'Malformed NMS pairs')
        require([c[0] for c in comparisons] == selected[:position], 'Missing selected pair')
        for ci, (other, value) in enumerate(comparisons):
            pairs.append(dict(pair=sorted([step['frame'], other]), saved_distance=number(value, 'pair', True),
                              step_index=index, comparison_index=ci))
    require(len(pairs) == 6 and {tuple(p['pair']) for p in pairs} ==
            set(itertools.combinations(sorted(selected), 2)), 'Selected-pair set differs')
    return dict(selected=selected, candidates=candidates, pairs=pairs,
                camera_pair=float(np.mean([p['saved_distance'] for p in pairs])),
                query_distance=float(np.mean([distance_map[i] for i in selected])))


def selections(stage, block, query, source, pose):
    split = 'development' if stage == 'S7' and block == 0 else 'test'
    require((source['block'], source['stride'], source['split']) == (block, 8, split), 'Source metadata')
    require([q['frame'] for q in source['queries']] == list(range(20, 24)), 'Source query domain')
    require((pose['stage'], pose['block'], pose['query'], pose['split']) ==
            (stage, block, query, split), 'Pose metadata')
    frame_order = frame_ids(pose['full20_frame_order'], 20)
    require(frame_order == list(range(20)) and len(pose['full20_distances_float32']) == 20, 'Full20 distance domain')
    distances = {i: number(v, 'full20 distance', True) for i, v in zip(frame_order, pose['full20_distances_float32'])}
    ranked = frame_ids(pose['full20_sorted_frames'], 20)
    require(len(set(distances.values())) == 20 and
            [distances[i] for i in ranked] == sorted(distances.values()), 'Full20 rank/tie mismatch')
    choice = source['queries'][query-20]['maps']['A0P0']
    g, p = trace_info(choice['readouts']['official'], distances), trace_info(pose['trace'], distances)
    require(choice['official_trace']['selected'] == g['selected'] and
            choice['official_trace']['candidates'] == g['candidates'], 'G official IDs differ')
    counts = choice['official_trace']['candidate_counts']
    require(type(counts) is list and len(counts) == 20 and
            all(type(c) is list and len(c) == 2 and type(c[0]) is int and
                type(c[1]) is int and c[1] in (0, 1) for c in counts), 'G allocation schema')
    require([c[0] for c in counts] == frame_order and
            [frame for frame, count in counts if count] == g['candidates'], 'G allocation identities')
    require(frame_ids(pose['pose14_ranked_candidates'], 14) == ranked[:14] and
            set(p['candidates']) == set(ranked[:14]), 'P14 identity differs')
    p['ranked_candidates'] = pose['pose14_ranked_candidates']
    return dict(stage=stage, block=block, query=query, split=split, arm='A0P0', stride=8), g, p


def point_disagreement(point, selected):
    chosen = sorted(set(selected) & set(point['frames']))
    if len(chosen) < 2:
        return chosen, None, []
    pairs = []
    for a, b in itertools.combinations(chosen, 2):
        delta = point['frames'][a]['xyz'] - point['frames'][b]['xyz']
        squared = float(np.dot(delta, delta)) / (point['radius'] * point['radius'])
        require(math.isfinite(squared) and squared >= 0, 'Invalid pair squared distance')
        pairs.append(dict(frames=[a, b], normalized_squared_distance=squared))
    value = float(np.mean([p['normalized_squared_distance'] for p in pairs]))
    require(math.isfinite(value) and value >= 0, 'Invalid normalized disagreement')
    return chosen, value, pairs


def measure_query(meta, points, g, p):
    details, eligible_g, eligible_p = [], 0, 0
    counts = {(kg, kp): 0 for kg in range(5) for kp in range(5)}
    for point_id in sorted(points):
        gf = sorted(set(points[point_id]['frames']) & set(g['selected']))
        pf = sorted(set(points[point_id]['frames']) & set(p['selected']))
        counts[len(gf), len(pf)] += 1
        eligible_g += int(len(gf) >= 2)
        eligible_p += int(len(pf) >= 2)
        if len(gf) >= 2 and len(pf) >= 2:
            gf, gv, gpairs = point_disagreement(points[point_id], g['selected'])
            pf, pv, ppairs = point_disagreement(points[point_id], p['selected'])
            details.append(dict(point_id=point_id, g_frames=gf, p_frames=pf, k_g=len(gf), k_p=len(pf),
                                disagreement_g=gv, disagreement_p=pv, g_pairs=gpairs, p_pairs=ppairs))
    common = len(details)
    g_mean = float(np.mean([d['disagreement_g'] for d in details])) if common else None
    p_mean = float(np.mean([d['disagreement_p'] for d in details])) if common else None
    kg = float(np.mean([d['k_g'] for d in details])) if common else None
    kp = float(np.mean([d['k_p'] for d in details])) if common else None
    row = dict(**meta, n_points=len(points), eligible_g=eligible_g, eligible_p=eligible_p,
               common_points=common, common_fraction=common/len(points),
               common_fraction_of_g=common/eligible_g if eligible_g else None,
               common_fraction_of_p=common/eligible_p if eligible_p else None,
               same_selected_set=set(g['selected']) == set(p['selected']),
               status='OK' if common else 'NO_COMMON_MULTISOURCE_POINTS',
               disagreement_g=g_mean, disagreement_p=p_mean,
               disagreement_g_minus_p=g_mean-p_mean if common else None,
               source_count_g=kg, source_count_p=kp,
               source_count_p_minus_g=float(np.mean([d['k_p']-d['k_g'] for d in details])) if common else None,
               camera_pair_g=g['camera_pair'], camera_pair_p=p['camera_pair'],
               camera_pair_p_minus_g=p['camera_pair']-g['camera_pair'],
               query_distance_g=g['query_distance'], query_distance_p=p['query_distance'],
               query_distance_g_minus_p=g['query_distance']-p['query_distance'])
    return row, dict(**meta, g_selected=g['selected'], p_selected=p['selected'],
                     g_candidates=g['candidates'], p_candidates=p['candidates'],
                     p_ranked_candidates=p['ranked_candidates'], points=details,
                     pair_visits=sum(len(d['g_pairs']) + len(d['p_pairs']) for d in details),
                     source_count_grid=[dict(k_g=kg, k_p=kp, n_points=counts[kg, kp])
                                        for kg in range(5) for kp in range(5)])


def tied_ranks(values):
    values = np.asarray(values, dtype=np.float64)
    require(bool(np.isfinite(values).all()), 'Nonfinite ranks')
    order = np.argsort(values, kind='stable')
    ranks = np.empty(len(values), dtype=np.float64)
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and values[order[end]] == values[order[start]]:
            end += 1
        ranks[order[start:end]] = (start + 1 + end) / 2
        start = end
    return ranks


def spearman(x, y):
    require(len(x) == len(y), 'Rank pair count differs')
    kept = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
    result = dict(n_total=len(x), n_usable=len(kept), n_missing=len(x)-len(kept), rho=None, reason=None)
    if len(kept) < 3:
        result['reason'] = 'fewer_than_three_usable'
        return result
    xr, yr = tied_ranks([a for a, _ in kept]), tied_ranks([b for _, b in kept])
    xd, yd = xr-xr.mean(), yr-yr.mean()
    den = float(np.linalg.norm(xd)*np.linalg.norm(yd))
    if den == 0:
        result['reason'] = 'constant_x_or_y'
        return result
    result['rho'] = float(np.dot(xd, yd)/den)
    return result


def join_labels(rows, details, scores):
    require(type(scores) is list, 'Score file must be an array')
    selected = [r for r in scores if r.get('main_comparison') is True and
                r.get('arm') == 'A0P0' and r.get('stride') == 8]
    require(len(selected) == 24, 'Expected 24 main labels')
    index = {}
    for r in selected:
        key = r['stage'], r['block'], r['query']
        require(key not in index, 'Duplicate label')
        index[key] = r
    joined = []
    require(len(rows) == len(details) == 24, 'Measurement row count')
    for row, detail in zip(rows, details):
        key = row['stage'], row['block'], row['query']
        require(key in index and all(row[k] == detail[k] for k in KEYS), 'Label/detail key differs')
        label = index.pop(key)
        require(all(label[k] == row[k] for k in KEYS), 'Label metadata differs')
        g, p = label['old_readouts']['official'], label['pose14']
        require(g['selected'] == detail['g_selected'] and p['selected'] == detail['p_selected'], 'Label selected IDs differ')
        require(label['geometry14_candidates'] == detail['g_candidates'] and
                label['pose14_ranked_candidates'] == detail['p_ranked_candidates'], 'Label candidate IDs differ')
        gn, pn = integer(g['supported_pixels'], 'G numerator'), integer(p['supported_pixels'], 'P numerator')
        gd, pd = integer(g['valid_pixels'], 'G denominator', 1), integer(p['valid_pixels'], 'P denominator', 1)
        require(gd == pd and gn <= gd and pn <= pd, 'Invalid paired counts')
        gs, ps = number(g['support'], 'G support', True), number(p['support'], 'P support', True)
        require(gs == gn/gd and ps == pn/pd, 'Saved supports differ from numerator/denominator')
        delta = number(label['geometry14_minus_pose14_pp'], 'saved signed pp')
        y = -delta
        require(y == 100*(ps-gs), 'Stored signed pp differs from saved-support arithmetic')
        joined.append(dict(**row, g_supported_pixels=gn, p_supported_pixels=pn, valid_pixels=gd,
                           g_support=gs, p_support=ps, y_pose_minus_geometry_pp=y))
    require(not index, 'Extra label keys')
    return joined


def associations(rows):
    results = []
    for stage in ('S7', 'S8'):
        for block in (None, 0, 1, 2):
            subset = [r for r in rows if r['stage'] == stage and (block is None or r['block'] == block)]
            require(len(subset) == (12 if block is None else 4), 'Stratum row count')
            usable = [r for r in subset if all(r[m] is not None and math.isfinite(r[m]) for m in METRICS)
                      and r['y_pose_minus_geometry_pp'] is not None and math.isfinite(r['y_pose_minus_geometry_pp'])]
            for metric in METRICS:
                available = sum(r[metric] is not None and math.isfinite(r[metric]) for r in subset)
                value = spearman([r[metric] for r in usable], [r['y_pose_minus_geometry_pp'] for r in usable])
                value.update(n_total=len(subset), n_missing=len(subset)-len(usable))
                results.append(dict(stage=stage, block=block, metric=metric,
                    n_metric_available=available, usable_keys=[[r['stage'], r['block'], r['query']] for r in usable],
                    excluded_keys=[[r['stage'], r['block'], r['query']] for r in subset if r not in usable],
                    **value))
    return results


def verify_measurement_dir(path, source_sha, manifest_sha):
    require(path.resolve() == path and path.is_dir(), 'Invalid measurement directory')
    expected = {'rows.json', 'rows.csv', 'point_details.json', 'selection_provenance.json',
                'input_identity.json', 'frozen_manifest.json', 'source_snapshot.py', 'run_metadata.json'}
    require({p.name for p in path.iterdir()} == expected | {'measure_seal.json'}, 'Unexpected measurement artifacts')
    seal = decode(input_path(path, 'measure_seal.json').read_bytes())
    require(seal['schema'] == SCHEMA and set(seal['files']) == expected, 'Measure seal schema')
    payloads = {}
    for name in sorted(expected):
        payloads[name] = input_path(path, name).read_bytes()
        require(sha(payloads[name]) == seal['files'][name], f'Measurement artifact changed: {name}')
    metadata = decode(payloads['run_metadata.json'])
    require(metadata['status'] == 'SUCCESS' and metadata['stage'] == 'measure'
            and metadata['source_sha256'] == source_sha and metadata['manifest_sha256'] == manifest_sha
            and metadata['counters']['score_json_decoded'] == 0
            and metadata['counters']['measurement_rows'] == 24, 'Measurement not properly sealed')
    require(sha(payloads['source_snapshot.py']) == source_sha and
            sha(payloads['frozen_manifest.json']) == manifest_sha, 'Measurement frozen identity differs')
    return payloads, {name: sha(input_path(path, name).read_bytes()) for name in sorted(expected | {'measure_seal.json'})}


def run(stage, root, manifest_path, output, input_result=None):
    require(not output.exists(), 'Output exists; preserve it and choose a new directory')
    root, manifest_path = root.resolve(), manifest_path.resolve()
    output.mkdir(parents=True, exist_ok=False)
    meta = dict(schema=SCHEMA, stage=stage, status='RUNNING', started_utc=now(),
        environment=dict(python=sys.version, executable=sys.executable, numpy=np.__version__, platform=platform.platform()),
        counters=dict(input_hash_reads_before=0, input_hash_reads_after=0, measurement_csv_decoded=0,
                      measurement_json_decoded=0, score_hash_reads=0, score_json_decoded=0,
                      measurement_rows=0, point_visits=0, common_point_visits=0, pair_visits=0,
                      saved_camera_pair_uses=0,
                      joined_rows=0, correlations=0),
        scope='24 already-seen related queries; descriptive association only; no fitting, thresholds, routing, new selection, model or video')
    try:
        source_path = Path(__file__).resolve()
        source_bytes, manifest_bytes = source_path.read_bytes(), manifest_path.read_bytes()
        meta.update(source_sha256=sha(source_bytes), manifest_sha256=sha(manifest_bytes))
        manifest = decode(manifest_bytes)
        mapping = validate_manifest(manifest, sha(source_bytes))
        payloads, before = {}, {}
        for rel in sorted(mapping):
            payloads[rel] = input_path(root, rel).read_bytes()
            meta['counters']['input_hash_reads_before'] += 1
            require(sha(payloads[rel]) == mapping[rel], f'Input identity differs: {rel}')
            before[rel] = sha(payloads[rel])
        meta['all_32_inputs_verified_utc'] = now()
        artifact_before = None
        if stage == 'measure':
            require(input_result is None, 'measure cannot consume labeled or other results')
            maps = parse_maps(payloads[POINT_PATH], payloads[FRAME_PATH], meta['counters'])
            documents = {}
            for rel, data in payloads.items():
                if rel not in (POINT_PATH, FRAME_PATH):
                    documents[rel] = decode(data)
                    meta['counters']['measurement_json_decoded'] += 1
            rows, details, origins = [], [], []
            for scene in ('S7', 'S8'):
                for block in range(3):
                    for query in range(20, 24):
                        keys, g, p = selections(scene, block, query,
                            documents[prediction_path(scene, block)], documents[pose_path(scene, block, query)])
                        row, detail = measure_query(keys, maps[scene, block], g, p)
                        rows.append(row)
                        details.append(detail)
                        origins.append(dict(**keys, g=g, p=p, source_path=prediction_path(scene, block),
                                            pose_path=pose_path(scene, block, query)))
            require(len(rows) == 24, 'Expected 24 measurement rows')
            save(output/'rows.json', dict(schema=SCHEMA, columns=ROW_COLUMNS, rows=rows))
            write_csv(output/'rows.csv', ROW_COLUMNS, rows)
            save(output/'point_details.json', dict(rows=details))
            save(output/'selection_provenance.json', dict(rows=origins))
            meta['counters']['measurement_rows'] = len(rows)
            meta['counters']['point_visits'] = sum(r['n_points'] for r in rows)
            meta['counters']['common_point_visits'] = sum(r['common_points'] for r in rows)
            meta['counters']['pair_visits'] = sum(d['pair_visits'] for d in details)
            meta['counters']['saved_camera_pair_uses'] = len(rows) * 12
            meta['measurement_rows_written_utc'] = now()
        elif stage == 'associate':
            require(input_result is not None, 'associate requires a sealed measurement result')
            input_result = input_result.absolute()
            artifacts, artifact_before = verify_measurement_dir(input_result, sha(source_bytes), sha(manifest_bytes))
            meta['measurement_seal_verified_utc'] = now()
            # This is the first permitted score-file read in the executable.
            score_bytes = input_path(root, SCORE_PATH).read_bytes()
            meta['counters']['score_hash_reads'] += 1
            require(sha(score_bytes) == manifest['score_input']['sha256'], 'Score input changed')
            meta['score_first_read_utc'] = now()
            scores = decode(score_bytes)
            meta['counters']['score_json_decoded'] += 1
            rows = decode(artifacts['rows.json'])['rows']
            details = decode(artifacts['point_details.json'])['rows']
            joined = join_labels(rows, details, scores)
            correlation_rows = associations(joined)
            save(output/'joined_rows.json', dict(schema=SCHEMA, columns=ROW_COLUMNS+LABEL_COLUMNS, rows=joined))
            write_csv(output/'joined_rows.csv', ROW_COLUMNS+LABEL_COLUMNS, joined)
            save(output/'associations.json', dict(rows=correlation_rows,
                interpretation='Signed within-scene and within-block descriptive Spearman; no p-values, pooled estimate or causal/generalization claim'))
            meta['counters'].update(joined_rows=len(joined), correlations=len(correlation_rows))
            score_after = input_path(root, SCORE_PATH).read_bytes()
            meta['counters']['score_hash_reads'] += 1
            require(score_after == score_bytes, 'Score file changed during association')
            meta.update(score_sha256=sha(score_bytes), score_sha256_after=sha(score_after))
            artifact_after = {name: sha(input_path(input_result, name).read_bytes()) for name in artifact_before}
            require(artifact_before == artifact_after, 'Measurement artifacts changed during association')
            save(output/'measurement_artifact_identity.json', dict(before=artifact_before, after=artifact_after))
        else:
            raise ValueError('Unknown stage')
        after = {}
        for rel in sorted(mapping):
            after[rel] = sha(input_path(root, rel).read_bytes())
            meta['counters']['input_hash_reads_after'] += 1
        require(before == after, '32 measurement inputs changed')
        require(source_path.read_bytes() == source_bytes and manifest_path.read_bytes() == manifest_bytes,
                'Source or manifest changed')
        save(output/'input_identity.json', dict(before=before, after=after))
        (output/'source_snapshot.py').write_bytes(source_bytes)
        (output/'frozen_manifest.json').write_bytes(manifest_bytes)
        meta.update(status='SUCCESS', completed_utc=now(), before_after_identity_pass=True,
                    source_sha256_after=sha(source_bytes), manifest_sha256_after=sha(manifest_bytes),
                    output_sha256={p.name: sha(p.read_bytes()) for p in output.iterdir()})
    except Exception as error:
        meta.update(status='FAILED', completed_utc=now(), error_type=type(error).__name__, error=str(error))
        save(output/'run_metadata.json', meta)
        raise
    save(output/'run_metadata.json', meta)
    if stage == 'measure':
        save(output/'measure_seal.json', dict(schema=SCHEMA, sealed_utc=now(),
            files={p.name: sha(p.read_bytes()) for p in output.iterdir()}))
    return meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=['measure', 'associate'], required=True)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--input-result', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.stage, args.root, args.manifest, args.output, args.input_result), indent=2))


if __name__ == '__main__':
    main()
