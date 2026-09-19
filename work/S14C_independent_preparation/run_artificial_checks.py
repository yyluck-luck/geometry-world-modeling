"""Artificial-only S14C verifier tests. Reads its source and synthetic local artifacts only."""
import copy
import csv
import importlib.util
import io
import itertools
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(__file__).resolve().parent
SOURCE = ROOT / 'scripts/verify_s14c_selection_disagreement_independent.py'
spec = importlib.util.spec_from_file_location('independent_s14c', SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
a, checks = m.Audit(), []


def ok(name, actual, expected, close=False):
    (a.close if close else a.exact)(actual, expected, name)
    checks.append({'name': name, 'status': 'PASS'})


def rejects(name, operation):
    try:
        operation()
    except (ValueError, KeyError, TypeError, AssertionError):
        checks.append({'name': name, 'status': 'EXPECTED_REJECTION'})
    else:
        raise AssertionError(name + ': expected rejection')


def data_csv(fields, rows):
    f = io.StringIO()
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return f.getvalue().encode()


def trace(selected, multiplier):
    steps = []
    for i, f in enumerate(selected[1:], 1):
        steps.append({'frame': f, 'accepted': True,
                      'comparisons': [[p, float(multiplier * (i + j + 1))] for j, p in enumerate(selected[:i])]})
    return {'selected': selected, 'nms': True, 'expanded_candidates': list(range(14)),
            'distances_float32': [float(i) for i in range(14)], 'sorted_frames': list(range(14)), 'steps': steps}


cache, point_rows, frame_rows = {}, [], []
for stage in ['S7', 'S8']:
    for block in range(3):
        split = 'development' if stage == 'S7' and block == 0 else 'test'
        source = {'block': block, 'stride': 8, 'split': split, 'queries': []}
        for query in range(20, 24):
            gsel, psel = [0, 1, 2, 3], ([0, 1, 2, 3] if query == 20 else [0, 1, 4, 5])
            gt, pt = trace(gsel, 1), trace(psel, 2)
            source['queries'].append({'frame': query, 'maps': {'A0P0': {
                'readouts': {'official': gt}, 'official_trace': {'selected': gsel, 'candidates': list(range(14)),
                'candidate_counts': [[i, int(i < 14)] for i in range(20)]}}}})
            pose = {'stage': stage, 'block': block, 'query': query, 'split': split, 'trace': pt,
                    'pose14_ranked_candidates': list(range(14)), 'full20_frame_order': list(range(20)),
                    'full20_distances_float32': [float(i) for i in range(20)], 'full20_sorted_frames': list(range(20))}
            cache[m.pose_path(stage, block, query)] = __import__('json').dumps(pose).encode()
        cache[m.prediction_path(stage, block)] = __import__('json').dumps(source).encode()
        for point, frames, radius in [(0, list(range(6)), 2.), (1, [0, 1], 1.), (2, [19], 1.)]:
            point_rows.append(dict(phase=stage, block=block, stride=8, point_id=point, m=len(frames), radius=radius, W='NOT_NUMERIC_NOT_READ'))
            for f in frames:
                frame_rows.append(dict(phase=stage, block=block, stride=8, point_id=point, frame=f,
                                       n_obs=f+1, c_x=float(f), c_y=0., c_z=0., within_variance='NOT_NUMERIC_NOT_READ'))
cache[m.POINT_PATH] = data_csv(list(point_rows[0]), point_rows)
cache[m.CENTROID_PATH] = data_csv(list(frame_rows[0]), frame_rows)
ok('exact artificial predicted input count', len(cache), 32)
rows, details, provenance = m.build_measurement(cache)
ok('all 24 query rows reconstructed', len(rows), 24)
ok('all metadata IDs in prescribed order', [(r['stage'], r['block'], r['query']) for r in rows], m.KEYS)
ok('same selected set has exact zero x', rows[0]['disagreement_g_minus_p'], 0.)
ok('known opposite selected source mean', rows[1]['disagreement_g_minus_p'], -1., True)
ok('25 coverage cells', len(details[0]['source_count_grid']), 25)
ok('coverage complete', sum(c['n_points'] for c in details[0]['source_count_grid']), 3)
ok('all common IDs', [d['point_id'] for d in details[0]['points']], [0, 1])
ok('camera baseline fixed sign P minus G', rows[1]['camera_pair_p_minus_g'] > 0, True)
ok('query baseline fixed sign G minus P', rows[1]['query_distance_g_minus_p'], -1.)
ok('k2 single pair squared distance', m.dispersion([[0., 0., 0.], [2., 0., 0.]], 1.), 4.)
triangle = [[0., 0., 0.], [2., 0., 0.], [1., math.sqrt(3.), 0.]]
ok('different k equal pair-average', m.dispersion(triangle, 1.), 4., True)
ok('source permutation invariance', m.dispersion(list(reversed(triangle)), 1.), 4., True)
ok('translation-stable variance', m.dispersion([[1e12, 0., 0.], [1e12+2., 0., 0.]], 1.), 4.)
changed = copy.deepcopy(frame_rows)
for item in changed:
    item['n_obs'] *= 100
changed_cache = dict(cache, **{m.CENTROID_PATH: data_csv(list(changed[0]), changed)})
ok('fixed-centroid repeated pixel counts ignored', m.build_measurement(changed_cache)[0], rows)
points = {0: {'radius': 1., 'centroids': {2: [0., 0., 0.], 3: [1., 0., 0.]}},
          1: {'radius': 1., 'centroids': {4: [0., 0., 0.], 5: [1., 0., 0.]}}}
action = {'G': [0, 1, 2, 3], 'P': [4, 5, 6, 7], 'G_candidates': list(range(14)),
          'P_candidates': list(range(14)), 'P_ranked_candidates': list(range(14)),
          'G_pairs': m.trace_pairs(trace([0, 1, 2, 3], 1)), 'P_pairs': m.trace_pairs(trace([4, 5, 6, 7], 2)),
          'distances': [float(i) for i in range(20)]}
empty, empty_detail, _ = m.query_measure(points, action, m.identity('S7', 0, 20))
ok('empty common domain is null', empty['disagreement_g_minus_p'], None)
ok('empty source baseline is null', empty['source_count_p_minus_g'], None)
ok('empty common domain status', empty['status'], 'NO_COMMON_MULTISOURCE_POINTS')
ok('empty common keeps camera baseline', math.isfinite(empty['camera_pair_p_minus_g']), True)
ok('double average ranks', m.rank_twice([2., 1., 1., 4.]), [6, 3, 3, 8])
ok('signed Spearman with ties', m.spearman([1., 1., 2., 3.], [3., 3., 2., 1.])[0], -1.)
ok('constant rank null', m.spearman([1., 1., 1.], [1., 2., 3.]), (None, 'CONSTANT_X'))
ok('constant label null', m.spearman([1., 2., 3.], [1., 1., 1.]), (None, 'CONSTANT_Y'))
ok('fewer than three null', m.spearman([1., 2.], [1., 2.]), (None, 'N_LT_3'))
ok('floating near values not merged', m.rank_twice([1., 1.+1e-14, 2.]), [2, 4, 6])
for radius in [0., -1., float('nan'), float('inf'), 1e200, 1e-200]:
    rejects('invalid radius ' + repr(radius), lambda r=radius: m.dispersion([[0., 0., 0.], [1., 0., 0.]], r))
bad_cache = dict(cache, **{m.CENTROID_PATH: data_csv(list(frame_rows[0]), frame_rows + [frame_rows[0]])})
rejects('duplicate point-frame rejected', lambda: m.build_measurement(bad_cache))
bad_cache2 = dict(cache, **{m.CENTROID_PATH: data_csv(list(frame_rows[0]), [dict(frame_rows[0], frame=20)] + frame_rows[1:])})
rejects('out of domain frame rejected', lambda: m.build_measurement(bad_cache2))
rejects('score cannot open before verified seal', lambda: m.load_score_after_seal({'path': m.LABEL_PATH}, False, True, {}))
rejects('score cannot open without association', lambda: m.load_score_after_seal({'path': m.LABEL_PATH}, True, False, {}))

records = []
for r, d in zip(rows, details):
    gn, pn, den = 5, r['query'] - 12, 16
    for stride in [8, 12]:
        for arm in ['A0P0', 'A0P1', 'A1P0', 'A1P1']:
            record = dict(r, stride=stride, arm=arm, main_comparison=(stride == 8 and arm == 'A0P0'),
                          old_readouts={'official': {'selected': d['g_selected'], 'supported_pixels': gn, 'valid_pixels': den, 'support': gn/den}},
                          pose14={'selected': d['p_selected'], 'supported_pixels': pn, 'valid_pixels': den, 'support': pn/den},
                          geometry14_candidates=d['g_candidates'], pose14_ranked_candidates=d['p_ranked_candidates'],
                          geometry14_minus_pose14_pp=100 * (gn/den - pn/den))
            records.append(record)
joined = m.join_labels(records, rows, details, a)
ok('exact saved label reused', joined[0]['y_pose_minus_geometry_pp'], 18.75)
ok('32 signed descriptions only', len(m.association_rows(joined)), 32)
ok('only 8 scene/block groups', len({(x['stage'], x['block']) for x in m.association_rows(joined)}), 8)
missing = copy.deepcopy(joined)
for key in m.METRICS[:2]:
    missing[0][key] = None
associations = m.association_rows(missing)
ok('same valid domain for all four metrics', [r['n_usable'] for r in associations[:4]], [11] * 4)
ok('camera available retained but same comparison set', associations[2]['n_metric_available'], 12)
bad_labels = copy.deepcopy(records)
bad_labels[0]['pose14']['valid_pixels'] = 17
rejects('different label denominators', lambda: m.join_labels(bad_labels, rows, details, m.Audit()))
bad_labels = copy.deepcopy(records)
bad_labels[0]['query'] = 23
rejects('misaligned duplicate label IDs', lambda: m.join_labels(bad_labels, rows, details, m.Audit()))
bad_labels = copy.deepcopy(records)
bad_labels[0]['old_readouts']['official']['selected'] = [0, 1, 2, 4]
rejects('wrong label selected IDs', lambda: m.join_labels(bad_labels, rows, details, m.Audit()))
bad_source = __import__('json').loads(cache[m.prediction_path('S7', 0)])
bad_source['queries'].pop()
rejects('missing query', lambda: m.load_actions('S7', 0, 20, bad_source, __import__('json').loads(cache[m.pose_path('S7', 0, 20)])))
rejects('input byte change detected', lambda: m.require(m.digest(b'changed') == m.digest(b'original'), 'SHA mismatch'))
rejects('code byte change detected', lambda: m.require(m.digest(SOURCE.read_bytes()+b'changed') == m.sha(SOURCE), 'code SHA mismatch'))
m.dump(WORK / 'artificial_checks_final_source.json', {'completed_utc': m.now(), 'source_sha256': m.sha(SOURCE),
       'status': 'PASS', 'checks': checks, 'check_count': len(checks), 'exact_comparisons': a.exact_checks,
       'float_comparisons': a.float_checks, 'real_input_files_decoded': 0, 'real_label_files_read': 0,
       'synthetic_prediction_file_count': len(cache), 'synthetic_rows': len(rows), 'synthetic_labels': len(records),
       'actual_count_note': 'Synthetic values and file contents exist only in memory; no real prediction/label data used.'})
print({'status': 'PASS', 'checks': len(checks), 'source_sha256': m.sha(SOURCE)})
