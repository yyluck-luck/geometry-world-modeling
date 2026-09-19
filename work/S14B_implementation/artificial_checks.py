"""Artificial software checks only; never load real measurement inputs."""
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT/'scripts/measure_s14b_observation_disagreement.py'
spec = importlib.util.spec_from_file_location('s14b_measurement', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
started = datetime.now(timezone.utc).isoformat()
records = []


def fixture():
    # Birth 0 in frame 0; three observations {1, 3, 5} in frame 1.
    # Then no observations in frames 2..19. m=2, n_obs=4, radius=2.
    obs = dict(points=np.array([[0., 0., 0.], [1., 0., 0.], [3., 0., 0.], [5., 0., 0.]]),
               ids=np.array([[0, 0, 0], [1, 0, 0], [1, 8, 0], [1, 16, 0]], dtype=np.int64),
               radii=np.array([2., 2., 2., 2.]),
               offsets=np.array([0, 1, 4]+[4]*18, dtype=np.int64))
    mem = dict(points=np.array([[0., 0., 0.]]), radii=np.array([2.]), counts=np.array([2]))
    events = [dict(frame=0, old_n=0, targets=[0], matches=[-1], new_n=1, threshold=1.),
              dict(frame=1, old_n=1, targets=[0, 0, 0], matches=[0, 0, 0], new_n=1, threshold=1.)]
    events += [dict(frame=f, old_n=1, targets=[], matches=[], new_n=1, threshold=1.) for f in range(2, 20)]
    return obs, mem, events, {'0': [0, 1]}


def run(data):
    with np.errstate(over='raise', invalid='raise', divide='raise'):
        return mod.measure_block(*data, 'ARTIFICIAL', 0)


def check(name, callback):
    callback()
    records.append(dict(name=name, status='PASS'))


def truth(condition):
    if not condition:
        raise AssertionError('Artificial expected value mismatch')


def rejects(name, mutation):
    data = fixture()
    mutation(data)
    try:
        run(data)
    except (ValueError, FloatingPointError, OverflowError) as exc:
        records.append(dict(name=name, status='PASS', rejected_type=type(exc).__name__, reason=str(exc)))
        return
    raise AssertionError('Should reject: '+name)


points, frames, associations, summary = run(fixture())
r = points[0]
check('unequal_pixels_frame_equal_W_4_over_3', lambda: truth(np.isclose(r['W'], 4/3, atol=1e-15, rtol=0)))
check('unequal_pixels_frame_equal_B_A_2_25_D_4_5', lambda: truth([r[x] for x in ['B', 'A', 'D']] == [2.25, 2.25, 4.5]))
check('not_pixel_equal_centroid_2_25', lambda: truth(r['A'] != 2.25**2))
check('all_four_metrics_divide_radius_square', lambda: truth(all(r[k+'_over_radius2'] == r[k]/4 for k in ['W','B','A','D'])))
check('association_exactly_all_four_observations', lambda: truth(associations == [dict(point_id=0, frame=0, flat_indices=[0]), dict(point_id=0, frame=1, flat_indices=[1,2,3])]))
check('two_source_four_obs_counts', lambda: truth(r['m'] == 2 and r['n_obs'] == 4 and r['single_source'] == 0))
check('frame_centroid_and_within', lambda: truth(frames[1]['c_x'] == 3 and frames[1]['within_variance'] == 8/3))
check('direct_D_equals_B_plus_A', lambda: truth(r['D'] == r['B']+r['A']))
check('exact_m_summary_linear_named', lambda: truth(summary['by_m'][0]['m'] == 2 and summary['by_m'][0]['metrics']['D'] == dict(mean=4.5, median=4.5, p90=4.5)))

data = fixture()
data[0]['points'][:] = 0
zero = run(data)[0][0]
check('all_zero_dispersion', lambda: truth(all(zero[k] == 0 for k in mod.METRICS)))

data = fixture()
data[0]['points'][1:, 0] = 3
between = run(data)[0][0]
check('pure_between_no_within', lambda: truth(between['W'] == 0 and between['B'] == 2.25))

data = fixture()
for key in ['points','ids','radii']:
    data[0][key] = data[0][key][:1]
data[0]['offsets'] = np.array([0]+[1]*20)
data[1]['counts'][0] = 1
data[2][1]['targets'] = []
data[2][1]['matches'] = []
data[3]['0'] = [0]
single = run(data)[0][0]
check('single_source_birth_all_metrics_zero', lambda: truth(single['single_source'] == 1 and all(single[k] == 0 for k in mod.METRICS)))

rejects('zero_map_radius', lambda d: d[1]['radii'].__setitem__(0, 0))
rejects('negative_observation_radius', lambda d: d[0]['radii'].__setitem__(1, -2))
rejects('nonfinite_points', lambda d: d[0]['points'].__setitem__((1,0), np.nan))
rejects('mismatched_birth_position', lambda d: d[1]['points'].__setitem__((0,0), 1))
rejects('mismatched_birth_radius', lambda d: d[1]['radii'].__setitem__(0, 3))
rejects('bad_source_frames', lambda d: d[3].__setitem__('0', [0, 2]))
rejects('bad_source_counts', lambda d: d[1]['counts'].__setitem__(0, 3))
rejects('noninteger_counts', lambda d: d[1].__setitem__('counts', np.array([2.0])))
rejects('boolean_event_integer', lambda d: d[2][0].__setitem__('old_n', False))
rejects('match_minus_two', lambda d: d[2][0]['matches'].__setitem__(0, -2))
rejects('target_does_not_yet_exist', lambda d: d[2][0]['matches'].__setitem__(0, 0))
rejects('bad_birth_order', lambda d: d[2][0]['targets'].__setitem__(0, 1))
rejects('wrong_frame_identity', lambda d: d[0]['ids'].__setitem__((1,0), 2))
rejects('duplicate_pixel_identity', lambda d: d[0]['ids'].__setitem__((2,1), 0))
rejects('non_raster_pixel_identity', lambda d: d[0]['ids'].__setitem__((1,1), 24))
rejects('off_grid_pixel', lambda d: d[0]['ids'].__setitem__((1,1), 1))
rejects('out_of_image_pixel', lambda d: d[0]['ids'].__setitem__((1,1), 224))
rejects('wrong_offsets_total', lambda d: d[0]['offsets'].__setitem__(-1, 3))
rejects('missing_observation_target', lambda d: d[2][1]['targets'].pop())
rejects('illegal_single_source_duplicates', lambda d: d[3].__setitem__('0', [0,0,1]))
rejects('nonfinite_threshold', lambda d: d[2][1].__setitem__('threshold', float('inf')))

for name, raw in [('duplicate_json_key', b'{"a": 1, "a": 2}'), ('nonfinite_json', b'{"a": NaN}')]:
    try:
        mod.strict_json(raw)
    except ValueError:
        records.append(dict(name=name, status='PASS'))
    else:
        raise AssertionError(name)

receipt = dict(schema='s14b-artificial-checks-v1', started_utc=started,
               completed_utc=datetime.now(timezone.utc).isoformat(),
               scope='Artificial software tests; not research effects or real-data execution',
               source_sha256=hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),
               check_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               python=sys.version, numpy=np.__version__, checks=records, n_checks=len(records),
               real_npz_decodes=0, gt_query_score_feature_reads=0)
output = Path(sys.argv[1])
with output.open('x') as f:
    json.dump(receipt, f, indent=2)
    f.write('\n')
print(json.dumps(dict(status='PASS', checks=len(records), receipt=str(output))))
