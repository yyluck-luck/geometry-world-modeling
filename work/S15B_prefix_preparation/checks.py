"""Artificial-only checks. No real image, trajectory, NPZ or checkpoint is opened."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import traceback
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / 'round2'
OUT.mkdir(exist_ok=False)
sys.path.insert(0, str(ROOT / 'scripts'))
import run_s15b_prefix_proposals as runner
torch.set_num_threads(8)
started = datetime.now(timezone.utc).isoformat()
checks = []


def record(name, fn):
    fn()
    checks.append(dict(name=name, status='PASS'))


def reject(name, fn, text):
    try:
        fn()
    except (ValueError, KeyError) as e:
        assert text in str(e), (name, repr(e))
        checks.append(dict(name=name, status='PASS', expected_error=str(e)))
    else:
        raise AssertionError('Did not reject: ' + name)


def eq(a, b):
    assert a == b, (a, b)


def near(a, b):
    np.testing.assert_allclose(a, b, atol=1e-12, rtol=1e-12)


base = OUT / 'synthetic_paths'
repo = base / 'repo'
runner_path = base / 'scripts/run_s15b_prefix_proposals.py'
paths = [str(base / f'history/rgb_{i}.png') for i in range(12)]
ids = {str(repo / f'source{i}.py'): '0'*64 for i in range(99)}
ids.update({p: '0'*64 for p in paths})
for p in [runner_path, base/'checkpoint.pth', base/'rope_check.json', runner_path.parent/'cut3r_rope_compat.py', base/'camera_inputs.json']:
    ids[str(p)] = '0'*64
ids[str(base/'checkpoint.pth')] = runner.CHECKPOINT_SHA256
m = dict(schema='s15b-prefix-proposals-manifest-v1', repo=str(repo), commit=runner.COMMIT,
    python=sys.executable, runner=str(runner_path), checkpoint=str(base/'checkpoint.pth'),
    rope_check=str(base/'rope_check.json'), camera_inputs=str(base/'camera_inputs.json'),
    identities=ids, history_images=[dict(index=i, path=p, sha256='0'*64) for i, p in enumerate(paths)],
    contract=deepcopy(runner.EXPECTED_CONTRACT), control_files=[])
gt = np.tile(np.eye(4), (12, 1, 1)); gt[:, 0, 3] = np.arange(12)*.05; gt[:, 1, 3] = np.arange(12)**2*.003
cameras = dict(schema='s15b-prefix-cameras-v1', history_rgb_paths=paths,
    history_rgb_sha256=['0'*64]*12, history_timestamps=(100+np.arange(12)*.4).tolist(),
    gt_c2w=gt.tolist(), K=runner.K_FIXED, source_indices=runner.SOURCE_INDICES,
    pose_time='rgb', coordinate_frame='TUM optical camera-to-world', units='meter')

record('valid exact manifest', lambda: eq(runner.validate_contract(m), paths))
for label, mutation, error in [
    ('extra witness identity', lambda x: x['identities'].update({str(base/'witness.png'): '0'*64}), 'Unpermitted identity'),
    ('extra arbitrary NPZ identity', lambda x: x['identities'].update({str(base/'labels.npz'): '0'*64}), 'Unpermitted identity'),
    ('13 history entries', lambda x: x['history_images'].append(x['history_images'][-1]), 'Ordered history'),
    ('duplicate source RGB path', lambda x: x['history_images'].__setitem__(11, dict(x['history_images'][0], index=11)), 'Distinct twelve'),
    ('reordered source indices', lambda x: x['contract'].__setitem__('source_indices', [0, 6, 3, 9]), 'Contract mismatch'),
    ('four queries omits parity budget', lambda x: x['contract'].__setitem__('query_count', 4), 'Contract mismatch'),
    ('unfrozen weight', lambda x: x['identities'].__setitem__(x['checkpoint'], '0'*64), 'Pinned checkpoint'),
    ('changed RGB SHA', lambda x: x['history_images'][0].__setitem__('sha256', '1'*64), 'History identity'),
]:
    bad = deepcopy(m); mutation(bad)
    reject(label, lambda bad=bad: runner.validate_contract(bad), error)
record('twelve allowed camera records', lambda: near(runner.validate_cameras(cameras, m)[0], gt))
for label, mutation, error in [
    ('camera path mismatch', lambda c: c['history_rgb_paths'].__setitem__(1, 'other'), 'Camera RGB path binding'),
    ('camera SHA mismatch', lambda c: c['history_rgb_sha256'].__setitem__(1, 'a'*64), 'Camera RGB SHA binding'),
    ('timestamp duplicate', lambda c: c['history_timestamps'].__setitem__(1, c['history_timestamps'][0]), 'increasing'),
    ('13 camera records', lambda c: c['gt_c2w'].append(c['gt_c2w'][0]), 'Exactly twelve'),
    ('depth-time metadata', lambda c: c.__setitem__('pose_time', 'depth'), 'Camera contract'),
    ('reflected optical rotation', lambda c: c['gt_c2w'][0][0].__setitem__(0, -1), 'proper rotation'),
    ('NaN camera position', lambda c: c['gt_c2w'][0][0].__setitem__(3, float('nan')), 'shape/finite'),
    ('changed K', lambda c: c['K'][0].__setitem__(0, 500.), 'Camera contract'),
]:
    bad = deepcopy(cameras); mutation(bad)
    reject(label, lambda bad=bad: runner.validate_cameras(bad, m), error)

angle = .37; A = np.array([[np.cos(angle), -np.sin(angle), 0], [np.sin(angle), np.cos(angle), 0], [0, 0, 1]])
pred = gt.copy(); pred[:, :3, :3] = A; pred[:, :3, 3] = 2.5*(gt[:, :3, 3] @ A.T)+[.1, -.2, .3]
alignment, mapped = runner.align_prefix(gt, pred)
record('forward OLS recovers model per meter scale', lambda: near(alignment['s_model_per_metric'], 2.5))
record('forward OLS mapped cameras', lambda: near(mapped, pred))
record('forward OLS residual zero', lambda: near(alignment['rms_model'], 0.))
record('OLS no reciprocal error', lambda: eq(alignment['s_model_per_metric'] > 1, True))
bad = np.tile(np.eye(4), (12, 1, 1)); reject('degenerate no-motion camera fit', lambda: runner.align_prefix(bad, pred), 'Degenerate')
bad = gt.copy(); bad[:, :3, 3] *= -1; reject('negative fitted scale', lambda: runner.align_prefix(gt, bad), 'Nonpositive')

images = [dict(img=torch.zeros((1, 3, 224, 224)), true_shape=np.array([[224, 224]], dtype=np.int32), idx=i, instance=str(i)) for i in range(12)]
record('twelve official-shaped history views', lambda: eq(len(runner.make_views(images, torch)), 12))
reject('eleven history views', lambda: runner.make_views(images[:11], torch), 'twelve')
bad = deepcopy(images); bad[1]['idx'] = 2; reject('loader order mismatch', lambda: runner.make_views(bad, torch), 'input order')

state = {k: np.zeros(shape, dtype=dtype) for k, (shape, dtype) in runner.STATE_SCHEMA.items()}
conditions = dict(source_indices=np.array(runner.SOURCE_INDICES, np.int64), source_poses=pred[runner.SOURCE_INDICES],
    K=np.repeat(np.array(runner.K_FIXED)[None], 4, axis=0), ray_maps=np.zeros((4, 224, 224, 6), np.float32),
    old_self_z_model=np.ones((4, 224, 224), np.float32), old_self_z_m=np.ones((4, 224, 224), np.float64)/2.5,
    old_conf_self=np.ones((4, 224, 224), np.float32), s_model_per_metric=np.array(2.5, np.float64))


def query_trial(name, mode='valid'):
    out = OUT / name; out.mkdir()
    report = dict(query_runs=[], counters=dict(query_call_attempts=0, query_calls=0, query_image_encoder_calls=0, query_ray_encoder_calls=0))
    call = [0]
    def fake(view, anchor, model, device, verbose=False):
        assert device == 'cpu'
        i = call[0]; call[0] += 1
        assert view['idx'] == runner.QUERY_SOURCE_ORDER[i]
        assert all(view[k].tolist() == [v] for k, v in runner.QUERY_FLAGS.items())
        assert torch.count_nonzero(view['img']) == 0
        report['counters']['query_ray_encoder_calls'] += 1
        p = {k: torch.ones(shape, dtype=torch.float32) for k, shape in runner.OUTPUT_SHAPES.items()}
        if mode == 'parity' and i == 1: p['conf_self'][0, 0, 0] = 2
        if mode == 'mutate': anchor[0][0, 0, 0] = 1
        if mode == 'nan': p['pts3d_in_self_view'][0, 0, 0, 0] = float('nan')
        if mode == 'image': report['counters']['query_image_encoder_calls'] += 1
        return dict(pred=p)
    runner.execute_queries(torch, np, fake, None, state, conditions, report, out, lambda x: None)
    return report, out

report, out = query_trial('synthetic_success')
record('five query budget includes repeat', lambda: eq(report['counters']['query_calls'], 5))
record('all six repeated heads exactly equal', lambda: eq(report['parity_all_six_outputs_exact'], True))
record('five latent fields immutable', lambda: eq(report['state_before_queries'], report['state_after_queries']))
record('all thirty query heads saved', lambda: eq(len(report['query_output_ids']), 30))
with np.load(out/'proposals.npz') as q:
    record('metric new depths use same fixed scale', lambda: near(q['new_self_z_m'], .4))
    record('both old and new confidences saved', lambda: eq((q['old_conf_self'].shape, q['new_conf_self'].shape), ((4,224,224), (4,224,224))))
for name, mode, error in [('parity_changed','parity','byte parity failed'), ('state_changed','mutate','modified frozen'),
                         ('nonfinite_return','nan','finite gate'), ('query_image_encoding','image','Query encoder')]:
    reject(name, lambda name=name, mode=mode: query_trial('synthetic_'+name, mode), error)
    record(name+' preserves returned arrays before rejection', lambda name=name: eq((OUT/('synthetic_'+name)/'query_call_0.npz').exists(), True))

source = Path(runner.__file__).read_text()
record('no NPZ input loading in runner', lambda: eq('np.load(' in source, False))
record('ordered image decoder guard present', lambda: eq("len(decoded) < 12 and p == paths[len(decoded)]" in source, True))
record('post-model complete identity recheck present', lambda: eq("check_identities(identities)" in source, True))

# Only upstream source text is read here; no dataset or model arrays are opened.
official = Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/cut3r-local/viser_utils.py')
factory, _ = runner.extract_ray_factory(official)
ray = factory.get_ray_map(pred[3], 224, 224, np.array(runner.K_FIXED))
grid_y, grid_x = np.indices((224, 224))
vectors = np.stack([(grid_x-112)/245.2734375, (grid_y-111.5)/245, np.ones((224,224))], -1)
direction = vectors @ pred[3,:3,:3].T + pred[3,:3,3]
direction /= np.linalg.norm(direction, axis=-1, keepdims=True)
record('official ray directions agree with separate component formula', lambda: near(ray[:,:,3:], direction))
record('official ray origins match camera center', lambda: near(ray[:,:,:3], np.broadcast_to(pred[3,:3,3], (224,224,3))))

history_dir = OUT/'synthetic_history'; history_dir.mkdir()
history_report = dict(counters=dict(history_forward_attempts=0, history_forward_calls=0, history_frames_saved=0))
fake_heads = [{k: torch.ones(shape, dtype=torch.float32) for k, shape in runner.OUTPUT_SHAPES.items()} for i in range(12)]
fake_state = tuple(torch.from_numpy(state[k]) for k in runner.FIELDS)
def history_fake(views, model, device, verbose=False):
    return dict(pred=fake_heads), [fake_state]*13
def pose_fake(encodings):
    return torch.from_numpy(pred.astype(np.float32))
history_arrays, history_poses, history_state = runner.execute_history(torch, np, history_fake, pose_fake, None,
    runner.make_views(images, torch), history_report, history_dir, lambda name: None)
record('twelve history frames and all 72 heads retained', lambda: eq(len(history_arrays), 72))
record('history final five state fields retained', lambda: eq(set(history_state), set(runner.FIELDS)))
record('one logical 12-frame history call counted', lambda: eq(history_report['counters']['history_forward_calls'], 1))
record('raw history evidence saved before semantic gates', lambda: eq(history_report['raw_predictions_saved_before_gates'], True))
receipt = dict(schema='s15b-prefix-artificial-checks-v1', status='PASS', started_utc=started,
    completed_utc=datetime.now(timezone.utc).isoformat(), checks=checks, check_count=len(checks),
    runner_sha256=hashlib.sha256(Path(runner.__file__).read_bytes()).hexdigest(),
    evidence_type='Artificial software checks only', model_instantiations=0, actual_inference_calls=0,
    actual_image_decodes=0, actual_numpy_archives_read=0, actual_trajectory_reads=0, actual_weight_reads=0,
    numpy_version=np.__version__, torch_version=torch.__version__, python=sys.executable)
(OUT/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps({k: receipt[k] for k in ['status', 'check_count', 'runner_sha256', 'completed_utc']}))
