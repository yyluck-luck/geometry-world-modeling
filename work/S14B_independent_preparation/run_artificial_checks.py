"""Synthetic data only; never opens real research NPZ or production implementation."""
from pathlib import Path
import importlib.util
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'scripts/verify_s14b_disagreement_independent.py'
spec = importlib.util.spec_from_file_location('independent', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
work = Path(__file__).resolve().parent
fixture = work / 'artificial_input'
fixture.mkdir(exist_ok=False)
ids, points, offsets, events = [], [], [0], []
for f in range(20):
    if f == 0:
        targets, matches, xs, old, new = [0, 1], [-1, -1], [0., 10.], 0, 2
    elif f == 1:
        targets, matches, xs, old, new = [0, 0, 1], [0, 0, 1], [2., 4., 10.], 2, 2
    elif f == 19:
        targets, matches, xs, old, new = [1, 2], [1, -1], [10., 30.], 2, 3
    else:
        targets, matches, xs, old, new = [1], [1], [10.], 2, 2
    ids.extend([[f, i * 8, 0] for i in range(len(xs))])
    points.extend([[x, 0., 0.] for x in xs])
    offsets.append(len(ids))
    events.append(dict(frame=f, old_n=old, new_n=new, targets=targets, matches=matches, threshold=.1))
np.savez(fixture / 'observations.npz', ids=np.array(ids), points=np.array(points),
         radii=np.ones(len(ids)), offsets=np.array(offsets))
np.savez(fixture / 'A0P0.npz', points=np.array([[0., 0., 0.], [10., 0., 0.], [30., 0., 0.]]),
         radii=np.ones(3), counts=np.array([2, 20, 1]))
m.write_json(fixture / 'A0_events.json', events)
m.write_json(fixture / 'A0P0_sources.json', {'0': [0, 1], '1': list(range(20)), '2': [19]})
a = m.Audit()
prows, frows, assoc, summary = m.reconstruct(fixture, 'ARTIFICIAL', 0, a)
for key, expected in {'W': .5, 'B': 2.25, 'A': 2.25, 'D': 4.5}.items():
    a.close(prows[0][key], expected, 'artificial_point0:' + key)
for key in ['W', 'B', 'A', 'D']:
    a.exact(prows[2][key], 0., 'legal_single_source:' + key)
a.exact(prows[0]['m'], 2, 'unbalanced:frame_count')
a.exact(prows[0]['n_obs'], 3, 'unbalanced:pixel_count')
a.exact(prows[2]['m'], 1, 'single_source:frame_count')
a.exact(prows[2]['n_obs'], 1, 'single_source:pixel_count')
a.exact(summary['n_observations'], 24, 'coverage')
a.exact(summary['n_frame_groups'], 23, 'groups')
m.write_json(work / 'connection_checks.json', {'completed_utc': m.now(), 'source_sha256': m.sha(SCRIPT),
             'status': 'PASS', 'fixture': 'artificial_input', 'real_npz_arrays_decoded': 0,
             'artificial_arrays_decoded': 7, 'exact_checks': a.checks, 'float_checks': a.float_checks,
             'points': prows, 'summary': summary})
original = m.read_json(work / 'synthetic_checks.json')
for case in original['cases']:
    if case['case'] == 'linear_quantile':
        a.close(m.quantile(case['values'], case['probability']), case['expected'], 'quantile')
for radius in [0., -1., float('nan'), float('inf'), 1e-200, 1e200]:
    try:
        m.measure([[[0., 0., 0.]]], [0., 0., 0.], radius)
    except ValueError:
        pass
    else:
        raise AssertionError('invalid radius accepted')
vals, _ = m.measure([[[0., 0., 0.], [2., 0., 0.]], [[7., 0., 0.]]], [0., 0., 0.], 2.)
for key, expected in original['cases'][0]['expected'].items():
    a.close(vals[key], expected, 'unequal_frame_pixel_counts:' + key)
m.write_json(work / 'synthetic_checks_v2.json', {'completed_utc': m.now(), 'source_sha256': m.sha(SCRIPT),
             'status': 'PASS', 'kind': 'final source recheck plus artificial connection',
             'exact_checks': a.checks, 'float_checks': a.float_checks,
             'real_npz_arrays_decoded': 0, 'gt_query_scores_reads': 0})
print(json.dumps({'status': 'PASS', 'exact_checks': a.checks, 'float_checks': a.float_checks,
                  'source_sha256': m.sha(SCRIPT)}))
