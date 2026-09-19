#!/usr/bin/env python3
"""Independent S14C reconstruction. Does not import production or S14A/S14B code.

Selected-centroid dispersion uses centered sum-of-squares, not pairwise distances.
Spearman uses doubled integer average ranks and integer Pearson cross-products.
All calculated floats: abs(actual-reference) <= 1e-12 + 1e-10*abs(reference).
"""
import argparse
import csv
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import platform
import sys
import traceback
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
ATOL, RTOL = 1e-12, 1e-10
VARIABLES = ['x', 'b_source_count', 'b_query_distance', 'b_camera_diversity']
SCHEMA = 's14c-selection-disagreement-v1'
METRICS = ['disagreement_g_minus_p', 'source_count_p_minus_g', 'camera_pair_p_minus_g', 'query_distance_g_minus_p']
COLUMNS = ('stage block query split arm stride n_points eligible_g eligible_p common_points '
           'common_fraction common_fraction_of_g common_fraction_of_p same_selected_set status '
           'disagreement_g disagreement_p disagreement_g_minus_p source_count_g source_count_p '
           'source_count_p_minus_g camera_pair_g camera_pair_p camera_pair_p_minus_g '
           'query_distance_g query_distance_p query_distance_g_minus_p').split()
LABEL_COLUMNS = 'g_supported_pixels p_supported_pixels valid_pixels g_support p_support y_pose_minus_geometry_pp'.split()
MEASURE_FILES = ['rows.json', 'rows.csv', 'point_details.json', 'selection_provenance.json',
                 'input_identity.json', 'frozen_manifest.json', 'source_snapshot.py', 'run_metadata.json']
GROUP_CONTRACT = {'scene_groups': ['S7', 'S8'],
                  'block_groups': [['S7', 0], ['S7', 1], ['S7', 2], ['S8', 0], ['S8', 1], ['S8', 2]],
                  'metrics': METRICS, 'pooled': 'rows_and_counts_only_no_rho', 'minimum_valid_rows': 3,
                  'tie_rule': 'exact_sealed_float_equality_average_ranks', 'valid_domain': 'all_four_metrics_finite'}
INTERPRETATION = 'Signed within-scene and within-block descriptive Spearman; no p-values, pooled estimate or causal/generalization claim'
POINT_PATH = 'results/S14B_observation_disagreement/points.csv'
CENTROID_PATH = 'results/S14B_observation_disagreement/frame_centroids.csv'
LABEL_PATH = 'results/S12_matched_budget/records.json'
KEYS = [(s, b, q) for s in ['S7', 'S8'] for b in range(3) for q in range(20, 24)]


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    return digest(Path(path).read_bytes())


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False, default=repr) + '\n')


def decode(data):
    def unique(pairs):
        result = {}
        for key, val in pairs:
            if key in result:
                raise ValueError('duplicate JSON key: ' + key)
            result[key] = val
        return result
    return json.loads(data, object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def require(condition, label):
    if not condition:
        raise ValueError(label)


def finite(value, label, nonnegative=False):
    require(type(value) in (int, float), label + ': numeric')
    require(math.isfinite(value) and (not nonnegative or value >= 0), label + ': finite/domain')
    return float(value)


def integer(value, label):
    require(type(value) is int, label + ': integer')
    return value


def ids(value, count, label):
    require(type(value) is list and len(value) == count, label + ': count')
    require(all(type(x) is int and 0 <= x < 20 for x in value), label + ': frame range')
    require(len(set(value)) == len(value), label + ': uniqueness')
    return value


def prediction_path(stage, block):
    folder = 'S7_event_replay' if stage == 'S7' else 'S8_event_replay_v2'
    return f'results/{folder}/block{block}_stride8/prediction_only_selection.json'


def pose_path(stage, block, query):
    return f'results/S12_matched_budget/selections/{stage}_block{block}_query{query}.json'


def allowed_inputs():
    return {POINT_PATH, CENTROID_PATH} | {prediction_path(s, b) for s, b, _ in KEYS} | {pose_path(*k) for k in KEYS}


def get_csv(data):
    reader = csv.DictReader(io.StringIO(data.decode('utf-8')))
    require(reader.fieldnames is not None and len(reader.fieldnames) == len(set(reader.fieldnames)), 'CSV unique headers')
    rows = list(reader)
    require(all(None not in row and all(x is not None for x in row.values()) for row in rows), 'CSV complete fields')
    return reader.fieldnames, rows


def csv_int(text):
    value = int(text)
    require(str(value) == text, 'canonical CSV integer')
    return value


def load_points(point_data, centroid_data):
    ph, prows = get_csv(point_data)
    fh, frows = get_csv(centroid_data)
    require(set('phase block stride point_id m radius'.split()) <= set(ph), 'point whitelist fields')
    require(set('phase block stride point_id frame n_obs c_x c_y c_z'.split()) <= set(fh), 'centroid whitelist fields')
    maps = {(s, b): {} for s in ['S7', 'S8'] for b in range(3)}
    for row in prows:
        key = (row['phase'], csv_int(row['block']))
        require(key in maps and csv_int(row['stride']) == 8, 'point block/stride')
        point = csv_int(row['point_id'])
        require(point >= 0 and point not in maps[key], 'unique nonnegative point_id')
        m = csv_int(row['m'])
        require(1 <= m <= 20, 'point source count')
        r = finite(float(row['radius']), 'radius')
        require(r > 0 and math.isfinite(r * r) and r * r > 0, 'positive finite radius squared')
        maps[key][point] = {'m': m, 'radius': r, 'centroids': {}, 'n_obs': {}}
    for row in frows:
        key = (row['phase'], csv_int(row['block']))
        point, frame = csv_int(row['point_id']), csv_int(row['frame'])
        require(key in maps and point in maps[key] and csv_int(row['stride']) == 8, 'centroid point/stride')
        require(0 <= frame < 20 and frame not in maps[key][point]['centroids'], 'unique valid point-frame')
        count = csv_int(row['n_obs'])
        require(count > 0, 'positive frame pixel count')
        c = [finite(float(row['c_' + a]), 'centroid coordinate') for a in ['x', 'y', 'z']]
        maps[key][point]['centroids'][frame] = c
        maps[key][point]['n_obs'][frame] = count
    for key, points in maps.items():
        require(points and sorted(points) == list(range(len(points))), 'complete map point IDs')
        for point in points.values():
            require(len(point['centroids']) == point['m'], 'source count/centroid groups')
    return maps


def dispersion(centroids, radius):
    k = len(centroids)
    require(2 <= k <= 4, 'selected source count 2..4')
    require(math.isfinite(radius) and radius > 0 and math.isfinite(radius * radius) and radius * radius > 0,
            'positive finite radius squared')
    require(all(len(c) == 3 and all(math.isfinite(v) for v in c) for c in centroids), 'centroid shape/finite')
    ref = centroids[0]
    centered = [[c[d] - ref[d] for d in range(3)] for c in centroids]
    mean = [math.fsum(c[d] for c in centered) / k for d in range(3)]
    ss = math.fsum((c[d] - mean[d]) ** 2 for c in centered for d in range(3))
    result = (2.0 / (k - 1)) * ss / (radius * radius)
    require(math.isfinite(result) and result >= 0, 'finite nonnegative dispersion')
    return result


def trace_pairs(trace):
    selected = ids(trace['selected'], 4, 'trace selected')
    require(trace['nms'] is True, 'NMS true')
    accepted = []
    for index, step in enumerate(trace['steps']):
        if 'fallback_added' in step:
            require(not step['fallback_added'], 'no unproven fallback')
        if 'frame' not in step:
            continue
        ids([step['frame']], 1, 'step frame')
        require(type(step['accepted']) is bool, 'accepted flag')
        for comp in step['comparisons']:
            require(type(comp) is list and len(comp) == 2, 'comparison shape')
            ids([comp[0]], 1, 'comparison frame')
            finite(comp[1], 'saved comparison distance', True)
        if step['accepted']:
            accepted.append((index, step))
    require([s['frame'] for _, s in accepted] == selected[1:], 'accepted selected order')
    provenance = []
    for ordinal, (index, step) in enumerate(accepted, start=1):
        require([c[0] for c in step['comparisons']] == selected[:ordinal], 'complete prior accepted comparisons')
        for ci, (other, distance) in enumerate(step['comparisons']):
            provenance.append({'pair': sorted([step['frame'], other]), 'step_index': index,
                               'comparison_index': ci, 'saved_distance': float(distance)})
    require(len(provenance) == 6, 'six camera pairs')
    require({tuple(p['pair']) for p in provenance} == {tuple(sorted(p)) for p in itertools.combinations(selected, 2)},
            'camera pair identity')
    return provenance


def load_actions(stage, block, query, source, pose):
    split = 'development' if stage == 'S7' and block == 0 else 'test'
    require((source['block'], source['stride'], source['split']) == (block, 8, split), 'source identity')
    require([q['frame'] for q in source['queries']] == list(range(20, 24)), 'source query IDs')
    require((pose['stage'], pose['block'], pose['query'], pose['split']) == (stage, block, query, split), 'pose identity')
    choice = source['queries'][query - 20]['maps']['A0P0']
    gtrace, ptrace, official = choice['readouts']['official'], pose['trace'], choice['official_trace']
    gsel, psel = ids(gtrace['selected'], 4, 'G'), ids(ptrace['selected'], 4, 'P')
    require(official['selected'] == gsel, 'official G selected identity')
    gcandidates = ids(official['candidates'], 14, 'G candidates')
    pcandidates = ids(pose['pose14_ranked_candidates'], 14, 'P candidates')
    require(gcandidates == gtrace['expanded_candidates'], 'G candidate order')
    allocations = official['candidate_counts']
    require(type(allocations) is list and all(type(a) is list and len(a) == 2 for a in allocations), 'candidate allocation shape')
    require(ids([p[0] for p in allocations], 20, 'allocation IDs') == list(range(20)), 'allocation order')
    require(all(type(p[1]) is int and p[1] in (0, 1) for p in allocations), 'binary allocation')
    require([i for i, n in allocations if n] == gcandidates, 'allocation candidate identity')
    require(ids(pose['full20_frame_order'], 20, 'full20 order') == list(range(20)), 'full20 exact order')
    require(len(pose['full20_distances_float32']) == 20, 'full20 distance count')
    distances = [finite(v, 'query distance', True) for v in pose['full20_distances_float32']]
    ranked = ids(pose['full20_sorted_frames'], 20, 'full20 ranked')
    require([distances[f] for f in ranked] == sorted(distances), 'full20 distance ranking')
    require(len(set(distances)) == 20, 'frozen full20 no ties')
    require(pcandidates == ranked[:14], 'P candidates full20 prefix')
    for trace, candidates in [(gtrace, gcandidates), (ptrace, pcandidates)]:
        expanded = ids(trace['expanded_candidates'], 14, 'expanded candidates')
        require(set(expanded) == set(candidates), 'candidate set')
        require(set(ids(trace['selected'], 4, 'selected')) <= set(candidates), 'selected subset')
        rank = ids(trace['sorted_frames'], 14, 'trace rank')
        require(set(rank) == set(candidates), 'rank candidate set')
        require(len(trace['distances_float32']) == 14, 'trace distance count')
        require(trace['distances_float32'] == [distances[f] for f in expanded], 'shared query distance identity')
        require([distances[f] for f in rank] == sorted(distances[f] for f in candidates), 'trace ranked distance order')
    gpairs, ppairs = trace_pairs(gtrace), trace_pairs(ptrace)
    return {'G': gsel, 'P': psel, 'G_candidates': gcandidates, 'P_candidates': list(ptrace['expanded_candidates']),
            'P_ranked_candidates': pcandidates,
            'G_pairs': gpairs, 'P_pairs': ppairs, 'distances': distances}


def rank_twice(values):
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [None] * len(values)
    start = 0
    while start < len(values):
        stop = start + 1
        while stop < len(values) and values[order[stop]] == values[order[start]]:
            stop += 1
        for index in order[start:stop]:
            ranks[index] = start + 1 + stop
        start = stop
    return ranks


def spearman(x, y):
    require(len(x) == len(y), 'rank data length')
    if len(x) < 3:
        return None, 'N_LT_3'
    rx, ry = rank_twice(x), rank_twice(y)
    n = len(rx)
    ax, ay = n * sum(a * a for a in rx) - sum(rx) ** 2, n * sum(b * b for b in ry) - sum(ry) ** 2
    if ax == 0:
        return None, 'CONSTANT_X'
    if ay == 0:
        return None, 'CONSTANT_Y'
    covariance = n * sum(a * b for a, b in zip(rx, ry)) - sum(rx) * sum(ry)
    return covariance / math.sqrt(ax * ay), None


class Audit:
    def __init__(self):
        self.exact_checks = 0
        self.float_checks = 0
        self.max_abs_difference = 0.0
        self.errors = []

    def exact(self, actual, expected, label):
        self.exact_checks += 1
        if actual != expected:
            self.errors.append({'label': label, 'actual': actual, 'expected': expected, 'type': 'exact'})
            raise ValueError('Exact mismatch: ' + label)

    def close(self, actual, expected, label):
        self.float_checks += 1
        require(type(actual) in (int, float) and math.isfinite(actual) and math.isfinite(expected), label + ': finite float')
        difference, bound = abs(actual - expected), ATOL + RTOL * abs(expected)
        self.max_abs_difference = max(self.max_abs_difference, difference)
        if difference > bound:
            self.errors.append({'label': label, 'actual': actual, 'expected': expected,
                                'difference': difference, 'bound': bound, 'type': 'float'})
            raise ValueError('Floating mismatch: ' + label)

    def tree(self, actual, expected, label='', exact_floats=False):
        if type(expected) is dict:
            self.exact(type(actual), dict, label + ':type')
            self.exact(set(actual), set(expected), label + ':keys')
            for k, val in expected.items():
                self.tree(actual[k], val, label + '/' + str(k), exact_floats)
        elif type(expected) is list:
            self.exact(type(actual), list, label + ':type')
            self.exact(len(actual), len(expected), label + ':length')
            for i, val in enumerate(expected):
                self.tree(actual[i], val, label + '/' + str(i), exact_floats)
        elif type(expected) is float and not exact_floats:
            self.close(actual, expected, label)
        else:
            self.exact(type(actual), type(expected), label + ':type')
            self.exact(actual, expected, label)


def avg(values):
    require(bool(values), 'nonempty mean')
    return math.fsum(values) / len(values)


def ratio(num, den):
    return num / den if den else None


def identity(stage, block, query):
    return {'stage': stage, 'block': block, 'query': query,
            'split': 'development' if stage == 'S7' and block == 0 else 'test', 'arm': 'A0P0', 'stride': 8}


def query_measure(points, action, metadata):
    grid = {(kg, kp): 0 for kg in range(5) for kp in range(5)}
    details = []
    for point_id, point in sorted(points.items()):
        cf = point['centroids']
        gf, pf = sorted(set(action['G']) & cf.keys()), sorted(set(action['P']) & cf.keys())
        kg, kp = len(gf), len(pf)
        grid[kg, kp] += 1
        if kg < 2 or kp < 2:
            continue
        r = point['radius']
        eg, ep = dispersion([cf[f] for f in gf], r), dispersion([cf[f] for f in pf], r)
        def pair_details(frames):
            return [{'frames': [a, b], 'normalized_squared_distance': dispersion([cf[a], cf[b]], r)}
                    for a, b in itertools.combinations(frames, 2)]
        details.append({'point_id': point_id, 'g_frames': gf, 'p_frames': pf, 'k_g': kg, 'k_p': kp,
                        'disagreement_g': eg, 'disagreement_p': ep, 'g_pairs': pair_details(gf), 'p_pairs': pair_details(pf)})
    ng = sum(v for (kg, kp), v in grid.items() if kg >= 2)
    np_ = sum(v for (kg, kp), v in grid.items() if kp >= 2)
    nj = len(details)
    eg = avg([d['disagreement_g'] for d in details]) if nj else None
    ep = avg([d['disagreement_p'] for d in details]) if nj else None
    sg = avg([d['k_g'] for d in details]) if nj else None
    sp = avg([d['k_p'] for d in details]) if nj else None
    cg, cp = avg([p['saved_distance'] for p in action['G_pairs']]), avg([p['saved_distance'] for p in action['P_pairs']])
    qg, qp = avg([action['distances'][f] for f in action['G']]), avg([action['distances'][f] for f in action['P']])
    row = dict(metadata, n_points=len(points), eligible_g=ng, eligible_p=np_, common_points=nj,
               common_fraction=ratio(nj, len(points)), common_fraction_of_g=ratio(nj, ng),
               common_fraction_of_p=ratio(nj, np_), same_selected_set=set(action['G']) == set(action['P']),
               status='OK' if nj else 'NO_COMMON_MULTISOURCE_POINTS', disagreement_g=eg, disagreement_p=ep,
               disagreement_g_minus_p=(eg - ep if nj else None), source_count_g=sg, source_count_p=sp,
               source_count_p_minus_g=(sp - sg if nj else None), camera_pair_g=cg, camera_pair_p=cp,
               camera_pair_p_minus_g=cp - cg, query_distance_g=qg, query_distance_p=qp,
               query_distance_g_minus_p=qg - qp)
    detail = dict(metadata, g_selected=action['G'], p_selected=action['P'], g_candidates=action['G_candidates'],
                  p_candidates=action['P_candidates'], p_ranked_candidates=action['P_ranked_candidates'],
                  pair_visits=sum(len(p['g_pairs']) + len(p['p_pairs']) for p in details),
                  source_count_grid=[{'k_g': kg, 'k_p': kp, 'n_points': grid[kg, kp]} for kg in range(5) for kp in range(5)],
                  points=details)
    def provenance(side, camera, query):
        result = {'selected': action[side], 'candidates': action[side + '_candidates'],
                  'pairs': action[side + '_pairs'], 'camera_pair': camera, 'query_distance': query}
        if side == 'P':
            result['ranked_candidates'] = action['P_ranked_candidates']
        return result
    prov = dict(metadata, g=provenance('G', cg, qg), p=provenance('P', cp, qp),
                source_path=prediction_path(metadata['stage'], metadata['block']),
                pose_path=pose_path(metadata['stage'], metadata['block'], metadata['query']))
    return row, detail, prov


def build_measurement(cache):
    maps = load_points(cache[POINT_PATH], cache[CENTROID_PATH])
    documents = {p: decode(data) for p, data in cache.items() if p.endswith('.json')}
    rows, details, provenances = [], [], []
    for stage, block, query in KEYS:
        action = load_actions(stage, block, query, documents[prediction_path(stage, block)],
                              documents[pose_path(stage, block, query)])
        row, detail, prov = query_measure(maps[stage, block], action, identity(stage, block, query))
        rows.append(row)
        details.append(detail)
        provenances.append(prov)
    return rows, details, provenances


def compare_csv(data, columns, expected, audit):
    fields, rows = get_csv(data)
    audit.exact(fields, columns, 'CSV columns')
    audit.exact(len(rows), len(expected), 'CSV row count')
    for i, (row, ref) in enumerate(zip(rows, expected)):
        for key in columns:
            text, val = row[key], ref[key]
            label = f'CSV/{i}/{key}'
            if type(val) is float:
                # JSON is the sealed primary value; CSV must round-trip that exact value.
                audit.exact(float(text), val, label)
            else:
                audit.exact(text, '' if val is None else str(val), label)


def join_labels(records, rows, details, audit):
    require(type(records) is list and len(records) == 192, 'S12 records exactly 192 saved conditions')
    selected = {}
    for record in records:
        require(type(record['main_comparison']) is bool, 'saved main flag type')
        main = record['arm'] == 'A0P0' and record['stride'] == 8
        require(record['main_comparison'] == main, 'saved main flag semantics')
        if not main:
            continue
        key = (record['stage'], integer(record['block'], 'label block'), integer(record['query'], 'label query'))
        require(key in KEYS and key not in selected, 'unique allowed main label identity')
        selected[key] = record
    audit.exact(set(selected), set(KEYS), '24 label identities')
    joined = []
    for row, detail in zip(rows, details):
        key = (row['stage'], row['block'], row['query'])
        rec = selected[key]
        g, p = rec['old_readouts']['official'], rec['pose14']
        for field in ['stage', 'block', 'query', 'split', 'arm', 'stride']:
            audit.exact(rec[field], row[field], 'label metadata/' + field)
        audit.tree(g['selected'], detail['g_selected'], 'label G selected', True)
        audit.tree(p['selected'], detail['p_selected'], 'label P selected', True)
        audit.tree(rec['geometry14_candidates'], detail['g_candidates'], 'label G candidates', True)
        audit.tree(rec['pose14_ranked_candidates'], detail['p_ranked_candidates'], 'label P candidates', True)
        den = integer(g['valid_pixels'], 'G denominator')
        require(den > 0, 'positive denominator')
        audit.exact(integer(p['valid_pixels'], 'P denominator'), den, 'shared denominator')
        gn, pn = integer(g['supported_pixels'], 'G numerator'), integer(p['supported_pixels'], 'P numerator')
        require(0 <= gn <= den and 0 <= pn <= den, 'support numerator domain')
        gs, ps = finite(g['support'], 'G support'), finite(p['support'], 'P support')
        audit.exact(gs, gn / den, 'saved exact G support')
        audit.exact(ps, pn / den, 'saved exact P support')
        gap = finite(rec['geometry14_minus_pose14_pp'], 'saved signed gap')
        audit.exact(gap, 100 * (gs - ps), 'saved gap writer expression')
        y = -gap
        audit.exact(y, 100 * (ps - gs), 'saved label sign')
        joined.append(dict(row, g_supported_pixels=gn, p_supported_pixels=pn, valid_pixels=den,
                           g_support=gs, p_support=ps, y_pose_minus_geometry_pp=y))
    return joined


def association_rows(rows):
    groups = []
    for stage in ['S7', 'S8']:
        for block in [None, 0, 1, 2]:
            subset = [r for r in rows if r['stage'] == stage and (block is None or r['block'] == block)]
            usable = [r for r in subset if all(type(r[m]) in (int, float) and math.isfinite(r[m]) for m in METRICS)]
            keys = [[r['stage'], r['block'], r['query']] for r in usable]
            excluded = [[r['stage'], r['block'], r['query']] for r in subset if r not in usable]
            for metric in METRICS:
                rho, reason = spearman([r[metric] for r in usable], [r['y_pose_minus_geometry_pp'] for r in usable])
                reason = {'N_LT_3': 'fewer_than_three_usable', 'CONSTANT_X': 'constant_x_or_y',
                          'CONSTANT_Y': 'constant_x_or_y', None: None}[reason]
                groups.append({'stage': stage, 'block': block, 'metric': metric,
                               'n_metric_available': sum(type(r[metric]) in (int, float) and math.isfinite(r[metric]) for r in subset),
                               'usable_keys': keys, 'excluded_keys': excluded, 'n_total': len(subset),
                               'n_usable': len(usable), 'n_missing': len(subset) - len(usable), 'rho': rho, 'reason': reason})
    return groups


def verify_seal(measure, manifest_data, audit):
    require(measure.is_dir(), 'measurement directory exists')
    seal_data = (measure / 'measure_seal.json').read_bytes()
    seal = decode(seal_data)
    audit.exact(seal['schema'], SCHEMA, 'measure seal schema')
    audit.exact(set(seal['files']), set(MEASURE_FILES), 'measure seal exact file domain')
    cache = {name: (measure / name).read_bytes() for name in MEASURE_FILES}
    for name, data in cache.items():
        audit.exact(digest(data), seal['files'][name], 'sealed file/' + name)
    audit.exact(cache['frozen_manifest.json'], manifest_data, 'sealed original manifest bytes')
    return seal, cache, dict({name: digest(data) for name, data in cache.items()},
                            **{'measure_seal.json': digest(seal_data)})


def load_score_after_seal(score_entry, seal_verified, association_exists, receipt):
    require(seal_verified and association_exists, 'score forbidden before verified measurement seal and association existence')
    require(score_entry['path'] == LABEL_PATH, 'unique allowed score path')
    path = ROOT / LABEL_PATH
    require(path.resolve() == path and path.is_file(), 'score path is canonical file')
    receipt['score_first_read_utc'] = now()
    data = path.read_bytes()
    receipt['score_hash_before'] = digest(data)
    require(digest(data) == score_entry['sha256'], 'score SHA before decode')
    receipt['score_json_decoded'] = 1
    return decode(data)


def run(manifest_path, measure, associate, output):
    output.mkdir(parents=True, exist_ok=False)
    a = Audit()
    started = now()
    source_data, manifest_data = Path(__file__).read_bytes(), manifest_path.read_bytes()
    source_sha = digest(source_data)
    (output / 'verifier_source_snapshot.py').write_bytes(source_data)
    receipt = {'schema': 's14c-independent-verification-v1', 'status': 'RUNNING', 'started_utc': started,
               'python': sys.version, 'platform': platform.platform(), 'source_sha256': source_sha,
               'manifest_sha256': digest(manifest_data), 'score_json_decoded': 0,
               'atol': ATOL, 'rtol': RTOL, 'comparison': 'abs(actual-reference)<=atol+rtol*abs(reference)',
               'input_hashes_before': {}, 'input_hashes_after': {}, 'score_first_read_utc': None,
               'measurement_seal_verified_utc': None}
    dump(output / 'verification.json', receipt)
    try:
        manifest = decode(manifest_data)
        a.exact(manifest['schema'], SCHEMA, 'manifest schema')
        a.exact(manifest['independent_verifier_sha256'], source_sha, 'frozen independent source')
        a.tree(manifest['group_contract'], GROUP_CONTRACT, 'group contract', True)
        a.exact(len(manifest['inputs']), 32, 'manifest 32 inputs')
        a.exact({p['path'] for p in manifest['inputs']}, allowed_inputs(), 'fixed predicted input set')
        a.exact(manifest['score_input']['path'], LABEL_PATH, 'frozen label domain')
        require(associate.is_dir(), 'corresponding association directory must already exist')
        require((associate / 'associations.json').is_file(), 'corresponding association result must already exist')
        # No score file, joined rows, or association values are opened until the measure has been independently verified.
        seal, artifacts, measure_hashes = verify_seal(measure, manifest_data, a)
        receipt['measurement_hashes_before'] = measure_hashes
        a.exact(digest(artifacts['source_snapshot.py']), manifest['source_sha256'], 'frozen production source')
        cache = {}
        for entry in manifest['inputs']:
            path = ROOT / entry['path']
            require(path.resolve() == path and path.is_file(), 'canonical predicted input path')
            data = path.read_bytes()
            value = digest(data)
            a.exact(value, entry['sha256'], 'input SHA before/' + entry['path'])
            receipt['input_hashes_before'][entry['path']] = value
            cache[entry['path']] = data
        receipt['all_32_inputs_verified_utc'] = now()
        # Decoding starts only here, from the already verified cache.
        expected_rows, expected_details, expected_provenance = build_measurement(cache)
        actual_doc = decode(artifacts['rows.json'])
        a.exact(actual_doc['schema'], SCHEMA, 'rows schema')
        a.exact(actual_doc['columns'], COLUMNS, 'rows column contract')
        a.exact(set(actual_doc), {'schema', 'columns', 'rows'}, 'rows top-level keys')
        a.tree(actual_doc['rows'], expected_rows, 'prediction rows')
        compare_csv(artifacts['rows.csv'], COLUMNS, actual_doc['rows'], a)
        a.tree(decode(artifacts['point_details.json']), {'rows': expected_details}, 'point details')
        a.tree(decode(artifacts['selection_provenance.json']), {'rows': expected_provenance}, 'selection provenance')
        # Saved camera distances are identities, not recomputed estimates: enforce exactness.
        actual_prov = decode(artifacts['selection_provenance.json'])['rows']
        for actual, ref in zip(actual_prov, expected_provenance):
            for side in ['g', 'p']:
                a.tree(actual[side]['pairs'], ref[side]['pairs'], 'saved camera pair provenance', True)
        a.tree(decode(artifacts['input_identity.json']),
               {'before': receipt['input_hashes_before'], 'after': receipt['input_hashes_before']}, 'production input identity', True)
        metadata = decode(artifacts['run_metadata.json'])
        a.exact(metadata['status'], 'SUCCESS', 'measure success')
        a.exact(metadata['schema'], SCHEMA, 'measure metadata schema')
        for field in ['source_sha256', 'source_sha256_after']:
            a.exact(metadata[field], manifest['source_sha256'], 'measure/' + field)
        for field in ['manifest_sha256', 'manifest_sha256_after']:
            a.exact(metadata[field], digest(manifest_data), 'measure/' + field)
        counters = metadata['counters']
        for name, value in {'input_hash_reads_before': 32, 'input_hash_reads_after': 32,
                            'measurement_csv_decoded': 2, 'measurement_json_decoded': 30,
                            'score_hash_reads': 0, 'score_json_decoded': 0, 'measurement_rows': 24,
                            'saved_camera_pair_uses': 288, 'joined_rows': 0, 'correlations': 0}.items():
            a.exact(counters[name], value, 'measure counter/' + name)
        a.exact(counters['point_visits'], sum(r['n_points'] for r in expected_rows), 'all map point visits')
        a.exact(counters['common_point_visits'], sum(r['common_points'] for r in expected_rows), 'common point visits')
        a.exact(counters['pair_visits'], sum(d['pair_visits'] for d in expected_details), 'pair visits')
        times = [metadata[k] for k in ['started_utc', 'all_32_inputs_verified_utc', 'measurement_rows_written_utc', 'completed_utc']] + [seal['sealed_utc']]
        parsed = [datetime.fromisoformat(t) for t in times]
        require(all(x <= y for x, y in zip(parsed, parsed[1:])), 'measurement temporal order before seal')
        for name, value in metadata['output_sha256'].items():
            require(name in artifacts and name != 'run_metadata.json', 'measure declared output hash domain')
            a.exact(digest(artifacts[name]), value, 'measure output hash/' + name)
        receipt['measurement_seal_verified_utc'] = now()
        dump(output / 'independent_prediction_rows.json', {'columns': COLUMNS, 'rows': expected_rows})
        receipt['independent_prediction_rows_sha256'] = sha(output / 'independent_prediction_rows.json')
        receipt['prediction_reconstruction_completed_utc'] = now()
        dump(output / 'verification.json', receipt)
        # Read association metadata (no labels) to establish same frozen run and claimed label boundary.
        assoc_meta_data = (associate / 'run_metadata.json').read_bytes()
        assoc_meta = decode(assoc_meta_data)
        a.exact(assoc_meta['status'], 'SUCCESS', 'association success')
        a.exact(assoc_meta['schema'], SCHEMA, 'association schema')
        for field in ['source_sha256', 'source_sha256_after']:
            a.exact(assoc_meta[field], manifest['source_sha256'], 'association/' + field)
        for field in ['manifest_sha256', 'manifest_sha256_after']:
            a.exact(assoc_meta[field], digest(manifest_data), 'association/' + field)
        require(datetime.fromisoformat(assoc_meta['measurement_seal_verified_utc']) < datetime.fromisoformat(assoc_meta['score_first_read_utc']),
                'production seal verified before first label read')
        require(datetime.fromisoformat(seal['sealed_utc']) <= datetime.fromisoformat(assoc_meta['measurement_seal_verified_utc']),
                'production measurement seal precedes association verification')
        for name, expected in {'score_hash_reads': 2, 'score_json_decoded': 1,
                               'measurement_csv_decoded': 0, 'measurement_json_decoded': 0,
                               'joined_rows': 24, 'correlations': 32, 'input_hash_reads_before': 32,
                               'input_hash_reads_after': 32, 'measurement_rows': 0, 'point_visits': 0,
                               'common_point_visits': 0, 'pair_visits': 0, 'saved_camera_pair_uses': 0}.items():
            a.exact(assoc_meta['counters'][name], expected, 'associate counter/' + name)
        records = load_score_after_seal(manifest['score_input'], True, True, receipt)
        joined = join_labels(records, actual_doc['rows'], expected_details, a)
        # Rank the exact stored scalar values, after independent numeric validation.
        # Floating equality defines ties; independent sum rounding must not invent a different tie set.
        expected_associations = association_rows(joined)
        assoc_files = ['joined_rows.json', 'joined_rows.csv', 'associations.json', 'measurement_artifact_identity.json',
                       'input_identity.json', 'frozen_manifest.json', 'source_snapshot.py', 'run_metadata.json']
        assoc_cache = {name: (associate / name).read_bytes() for name in assoc_files}
        receipt['association_hashes_before'] = {name: digest(data) for name, data in assoc_cache.items()}
        a.exact(assoc_cache['run_metadata.json'], assoc_meta_data, 'association metadata unchanged during join')
        a.exact(assoc_cache['frozen_manifest.json'], manifest_data, 'association frozen manifest bytes')
        a.exact(digest(assoc_cache['source_snapshot.py']), manifest['source_sha256'], 'association source snapshot')
        joined_doc = decode(assoc_cache['joined_rows.json'])
        a.exact(joined_doc['schema'], SCHEMA, 'joined schema')
        a.exact(joined_doc['columns'], COLUMNS + LABEL_COLUMNS, 'joined column contract')
        a.exact(set(joined_doc), {'schema', 'columns', 'rows'}, 'joined top-level fields')
        a.tree(joined_doc['rows'], joined, 'joined original values', True)
        compare_csv(assoc_cache['joined_rows.csv'], COLUMNS + LABEL_COLUMNS, joined_doc['rows'], a)
        a.tree(decode(assoc_cache['associations.json']), {'rows': expected_associations, 'interpretation': INTERPRETATION}, 'signed associations')
        a.tree(decode(assoc_cache['measurement_artifact_identity.json']),
               {'before': measure_hashes, 'after': measure_hashes}, 'sealed measure untouched', True)
        a.tree(decode(assoc_cache['input_identity.json']),
               {'before': receipt['input_hashes_before'], 'after': receipt['input_hashes_before']}, 'association prediction input identity', True)
        for field in ['score_sha256', 'score_sha256_after']:
            a.exact(assoc_meta[field], manifest['score_input']['sha256'], 'association/' + field)
        for name, value in assoc_meta['output_sha256'].items():
            require(name in assoc_cache and name != 'run_metadata.json', 'associate declared output hash domain')
            a.exact(digest(assoc_cache[name]), value, 'associate declared output SHA/' + name)
        for name, value in measure_hashes.items():
            a.exact(sha(measure / name), value, 'measure SHA after/' + name)
        for name, value in receipt['association_hashes_before'].items():
            a.exact(sha(associate / name), value, 'association SHA after/' + name)
        for path, value in receipt['input_hashes_before'].items():
            receipt['input_hashes_after'][path] = sha(ROOT / path)
            a.exact(receipt['input_hashes_after'][path], value, 'prediction SHA after/' + path)
        receipt['score_hash_after'] = sha(ROOT / LABEL_PATH)
        a.exact(receipt['score_hash_after'], receipt['score_hash_before'], 'score unchanged after')
        a.exact(sha(manifest_path), digest(manifest_data), 'manifest unchanged after')
        a.exact(sha(__file__), source_sha, 'independent source unchanged after')
        dump(output / 'independent_associations.json', {'rows': expected_associations})
        receipt.update(status='PASS', prediction_rows=24, association_rows=32, group_count=8,
                       pooled_rho_computed=False, common_point_visits=sum(r['common_points'] for r in expected_rows),
                       total_pair_visits=sum(d['pair_visits'] for d in expected_details),
                       score_json_decoded=1)
    except BaseException as exc:
        receipt.update(status='FAIL', exception=repr(exc), traceback=traceback.format_exc())
        raise
    finally:
        receipt.update(completed_utc=now(), source_sha256_after=sha(__file__),
                       exact_checks=a.exact_checks, float_checks=a.float_checks,
                       max_abs_difference=a.max_abs_difference, errors=a.errors)
        dump(output / 'verification.json', receipt)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--measure', type=Path, required=True)
    parser.add_argument('--associate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.manifest.resolve(), args.measure.resolve(), args.associate.resolve(), args.output.resolve())
