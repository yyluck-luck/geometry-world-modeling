#!/usr/bin/env python3
"""S15B twelve-RGB prefix and fixed source-camera proposals; no witnesses or depth labels."""
from __future__ import annotations
import argparse
import ast
from collections import defaultdict
import contextlib
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import resource
import shutil
import subprocess
import sys
import time
import traceback
from typing import Any

FIELDS = ['state_feat', 'state_pos', 'init_state_feat', 'mem', 'init_mem']
STATE_SCHEMA = {'state_feat': ([1, 768, 768], 'float32'),
                'state_pos': ([1, 768, 2], 'int64'),
                'init_state_feat': ([1, 768, 768], 'float32'),
                'mem': ([1, 256, 1536], 'float32'), 'init_mem': ([1, 256, 1536], 'float32')}
OUTPUT_SHAPES = {'pts3d_in_self_view': [1, 224, 224, 3],
                 'pts3d_in_other_view': [1, 224, 224, 3],
                 'conf_self': [1, 224, 224], 'conf': [1, 224, 224],
                 'camera_pose': [1, 7], 'rgb': [1, 224, 224, 3]}
FLAGS = {'img_mask': True, 'ray_mask': False, 'update': True, 'reset': False}
COMMIT = '8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf'
CHECKPOINT_SHA256 = '7a7d83e47f822e040980c8f5aff4c15aa94366d469d3ceae51fa30cc2f62327d'
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg'}
SOURCE_INDICES = [0, 3, 6, 9]
QUERY_SOURCE_ORDER = [0, 0, 3, 6, 9]
QUERY_FLAGS = {'img_mask': False, 'ray_mask': True, 'update': False, 'reset': False}
K_FIXED = [[245.2734375, 0., 112.], [0., 245., 111.5], [0., 0., 1.]]
EXPECTED_CONTRACT = dict(history_count=12, query_count=5, history_flags=FLAGS,
    source_indices=SOURCE_INDICES, query_source_order=QUERY_SOURCE_ORDER, query_flags=QUERY_FLAGS,
    K=K_FIXED, camera_pose_time='rgb', minimum_alignment_D_metric_squared=1e-12,
    rotation_atol=1e-5, roundtrip_atol=1e-5, roundtrip_rtol=1e-5,
    witness_rgb_allowed=False, sensor_depth_allowed=False,
    source_geometry_camera='aligned_given_optical_c2w',
    network_ray_convention='ro=t; rd=normalize(R K^-1 p + t)',
    device='cpu', cpu_threads=8, seed=0, size=[224, 224], dtype='float32',
    wall_seconds=600, monitored_rss_bytes=34359738368, external_monitor_required=True,
    history_rgb_allowed=True, target_rgb_allowed=False, target_depth_allowed=False)


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def tensor_id(a):
    import numpy as np
    a = np.ascontiguousarray(a)
    return dict(shape=list(a.shape), dtype=str(a.dtype), sha256=hashlib.sha256(a.tobytes()).hexdigest())


def validate_array(a, shape, dtype, label):
    import numpy as np
    require(list(a.shape) == shape and str(a.dtype) == dtype, 'Array schema: ' + label)
    require(np.isfinite(a).all(), 'Array finite gate: ' + label)


def validate_contract(m):
    require(m['schema'] == 's15b-prefix-proposals-manifest-v1', 'Manifest schema')
    require(m['commit'] == COMMIT, 'Pinned official commit')
    for key, value in EXPECTED_CONTRACT.items():
        require(m['contract'].get(key) == value, 'Contract mismatch: ' + key)
    identities = m['identities']
    for p, digest in identities.items():
        require(Path(p).is_absolute() and p == str(Path(p).resolve()), 'Canonical identity path: ' + p)
        require(isinstance(digest, str) and len(digest) == 64 and all(c in '0123456789abcdef' for c in digest), 'SHA256 format: ' + p)
    for role in ['repo', 'python', 'runner', 'checkpoint', 'rope_check', 'camera_inputs']:
        p = m[role]
        require(Path(p).is_absolute() and p == str(Path(p).absolute()), 'Absolute role: ' + role)
    for role in ['runner', 'checkpoint', 'rope_check', 'camera_inputs']:
        require(m[role] in identities, 'Frozen role missing: ' + role)
    require(Path(m['camera_inputs']).suffix == '.json', 'Camera input must be JSON')
    require(identities[m['checkpoint']] == CHECKPOINT_SHA256, 'Pinned checkpoint SHA')
    repo = Path(m['repo']).resolve()
    require(str(repo) == m['repo'], 'Canonical repo')
    history = m['history_images']
    require(len(history) == 12 and [x['index'] for x in history] == list(range(12)), 'Ordered history indices 0..11')
    paths = [x['path'] for x in history]
    require(len(set(paths)) == 12, 'Distinct twelve RGB files')
    for item in history:
        p = item['path']
        require(Path(p).suffix.lower() in IMAGE_EXTENSIONS, 'Official RGB extension')
        require(identities.get(p) == item['sha256'], 'History identity binding: ' + p)
    upstream = {p for p in identities if Path(p).is_relative_to(repo) and Path(p).suffix == '.py'}
    require(len(upstream) == 99, 'Exactly 99 frozen upstream Python files')
    adapter = str(Path(m['runner']).parent / 'cut3r_rope_compat.py')
    require(adapter in identities, 'Frozen signed RoPE adapter')
    controls = m.get('control_files', [])
    require(len(controls) == len(set(controls)), 'Distinct control paths')
    for p in controls:
        require(p in identities and Path(p).suffix in {'.md', '.json', '.py'}, 'Control type/identity: ' + p)
    allowed = upstream | set(paths) | set(controls) | {m['runner'], m['checkpoint'], m['rope_check'], m['camera_inputs'], adapter}
    require(set(identities) == allowed, 'Unpermitted identity: target images, arrays, and dataset metadata forbidden')
    for p in identities:
        require(Path(p).name not in {'groundtruth.txt', 'rgb.txt', 'depth.txt'}, 'Raw dataset metadata forbidden')
    return paths


def validate_poses(poses, label):
    import numpy as np
    require(poses.ndim == 3 and poses.shape[1:] == (4, 4) and np.isfinite(poses).all(), label + ' shape/finite')
    require(np.array_equal(poses[:, 3, :], np.tile([0., 0., 0., 1.], (len(poses), 1))), label + ' exact bottom row')
    rotations = poses[:, :3, :3].astype(np.float64)
    require(np.allclose(rotations @ rotations.transpose(0, 2, 1), np.eye(3), atol=1e-5, rtol=0), label + ' orthogonality')
    require(np.allclose(np.linalg.det(rotations), 1, atol=1e-5, rtol=0), label + ' proper rotation')


def validate_cameras(cameras, m):
    import numpy as np
    require(cameras['schema'] == 's15b-prefix-cameras-v1', 'Camera metadata schema')
    for key, value in [('source_indices', SOURCE_INDICES), ('pose_time', 'rgb'),
                       ('coordinate_frame', 'TUM optical camera-to-world'), ('units', 'meter'), ('K', K_FIXED)]:
        require(cameras[key] == value, 'Camera contract: ' + key)
    require(cameras['history_rgb_paths'] == [x['path'] for x in m['history_images']], 'Camera RGB path binding')
    require(cameras['history_rgb_sha256'] == [x['sha256'] for x in m['history_images']], 'Camera RGB SHA binding')
    timestamps = np.asarray(cameras['history_timestamps'], dtype=np.float64)
    require(timestamps.shape == (12,) and np.isfinite(timestamps).all() and (np.diff(timestamps) > 0).all(), 'Twelve increasing RGB timestamps')
    gt = np.asarray(cameras['gt_c2w'], dtype=np.float64)
    require(gt.shape == (12, 4, 4), 'Exactly twelve permitted camera poses')
    validate_poses(gt, 'Given history c2w')
    return gt, np.asarray(cameras['K'], dtype=np.float64), timestamps


def align_prefix(gt, pred):
    """Forward model-per-meter OLS; same formula as frozen S14E, only prefix 0..11."""
    import numpy as np
    validate_poses(gt, 'GT alignment'); validate_poses(pred, 'Predicted alignment')
    require(len(gt) == len(pred) == 12, 'Twelve-pose alignment only')
    gt = gt.astype(np.float64); pred = pred.astype(np.float64)
    A = pred[0, :3, :3] @ gt[0, :3, :3].T
    u = (gt[:, :3, 3] - gt[0, :3, 3]) @ A.T
    v = pred[:, :3, 3] - pred[0, :3, 3]
    D = float(np.sum(u * u)); N = float(np.sum(u * v))
    require(np.isfinite(D) and D > 1e-12, 'Degenerate metric displacement D')
    s = N / D
    require(np.isfinite(s) and s > 0, 'Nonpositive/nonfinite model-per-meter scale')
    c = pred[0, :3, 3] - s * (A @ gt[0, :3, 3])
    mapped = np.tile(np.eye(4), (12, 1, 1))
    mapped[:, :3, :3] = A[None] @ gt[:, :3, :3]
    mapped[:, :3, 3] = s * (gt[:, :3, 3] @ A.T) + c
    validate_poses(mapped, 'Mapped history c2w')
    back = ((mapped[:, :3, 3] - c) / s) @ A
    require(np.allclose(back, gt[:, :3, 3], atol=1e-5, rtol=1e-5), 'Similarity translation roundtrip')
    require(np.allclose(A.T[None] @ mapped[:, :3, :3], gt[:, :3, :3], atol=1e-5, rtol=1e-5), 'Similarity rotation roundtrip')
    residual = pred[:, :3, 3] - mapped[:, :3, 3]
    norms = np.linalg.norm(residual, axis=1)
    rms = float(np.sqrt(np.mean(np.sum(residual ** 2, axis=1))))
    displacement_rms = float(np.sqrt(np.mean(np.sum(v * v, axis=1))))
    relative = pred[:, :3, :3].transpose(0, 2, 1) @ mapped[:, :3, :3]
    angles = np.degrees(np.arccos(np.clip((np.trace(relative, axis1=1, axis2=2)-1)/2, -1, 1)))
    alignment = dict(schema='s15b-prefix-alignment-v1', s_model_per_metric=s, A=A.tolist(), c=c.tolist(),
        D_metric_squared=D, N_model_metric=N, history_count=12, source_indices=SOURCE_INDICES,
        fit_includes_witnesses=False, fit_includes_targets=False,
        residual_vectors_model=residual.tolist(), residual_norms_model=norms.tolist(),
        rms_model=rms, max_residual_model=float(norms.max()), predicted_displacement_rms_model=displacement_rms,
        normalized_rms=None if displacement_rms == 0 else rms/displacement_rms,
        orientation_residual_degrees=angles.tolist(),
        A_orthogonality_max_error=float(np.max(np.abs(A @ A.T-np.eye(3)))),
        translation_roundtrip_max_error_m=float(np.max(np.abs(back-gt[:, :3, 3]))))
    return alignment, mapped


def extract_ray_factory(path):
    """Evaluate only the pinned official pure NumPy viewer ray methods."""
    import numpy as np
    tree = ast.parse(Path(path).read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'PointCloudViewer')
    names = ['generate_pseudo_intrinsics', 'get_ray_map']
    methods = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in names]
    require([n.name for n in methods] == names, 'Official ray method domain/order')
    pure = ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='OfficialRayFactory', bases=[], keywords=[], body=methods, decorator_list=[])], type_ignores=[]))
    namespace = {'np': np}
    exec(compile(pure, str(path), 'exec'), namespace)
    return namespace['OfficialRayFactory'](), ast.unparse(pure) + '\n'


def prepare_conditions(np, gt, predicted_poses, K, arrays, repo, out, report):
    alignment, mapped = align_prefix(gt, predicted_poses)
    write(out / 'alignment.json', alignment)
    source_poses = mapped[SOURCE_INDICES].copy()
    factory, source = extract_ray_factory(repo / 'viser_utils.py')
    (out / 'official_ray_methods.py').write_text(source)
    rays = np.asarray([factory.get_ray_map(p, 224, 224, K) for p in source_poses], dtype=np.float32)
    validate_array(rays, [4, 224, 224, 6], 'float32', 'source ray conditions')
    s = alignment['s_model_per_metric']
    old_z = np.asarray([arrays[f'frame{i}_pts3d_in_self_view'][0, :, :, 2] for i in SOURCE_INDICES], dtype=np.float32)
    payload = dict(source_indices=np.asarray(SOURCE_INDICES, dtype=np.int64),
        source_poses=source_poses, K=np.repeat(K[None], 4, axis=0), ray_maps=rays,
        old_self_z_model=old_z, old_self_z_m=old_z.astype(np.float64)/s,
        old_conf_self=np.asarray([arrays[f'frame{i}_conf_self'][0] for i in SOURCE_INDICES], dtype=np.float32),
        gt_history_poses=gt, aligned_history_poses=mapped, s_model_per_metric=np.asarray(s, dtype=np.float64))
    np.savez_compressed(out / 'proposal_inputs.npz', **payload)
    report['alignment'] = alignment
    report['proposal_input_ids'] = {k: tensor_id(v) for k, v in payload.items()}
    return payload


def validate_outputs(arrays):
    require(set(arrays) == set(OUTPUT_SHAPES), 'Exactly six official query outputs')
    for key, shape in OUTPUT_SHAPES.items():
        validate_array(arrays[key], shape, 'float32', key)


def execute_queries(torch, np, inference_step, model, state, conditions, report, out, phase):
    """All queries use the exact frozen prefix state; first two calls repeat source 0."""
    anchor = tuple(torch.from_numpy(state[k].copy()) for k in FIELDS)
    before_ids = {k: tensor_id(state[k]) for k in FIELDS}
    report['state_before_queries'] = before_ids
    outputs = {}; reference = None; new_z = []; new_conf = []
    for call, source in enumerate(QUERY_SOURCE_ORDER):
        require(call < 2 or report.get('parity_all_six_outputs_exact') is True, 'Unverified parity before new source query')
        position = SOURCE_INDICES.index(source)
        view = dict(img=torch.zeros((1, 3, 224, 224), dtype=torch.float32),
            ray_map=torch.from_numpy(conditions['ray_maps'][position][None].copy()),
            true_shape=torch.tensor([[224, 224]], dtype=torch.int64), idx=source,
            instance=f's15b_source_{source}',
            camera_pose=torch.from_numpy(conditions['source_poses'][position][None].astype(np.float32)),
            **{k: torch.tensor([v]) for k, v in QUERY_FLAGS.items()})
        run = dict(call=call, source_index=source, kind='repeat_parity' if call == 1 else 'proposal',
            status='STARTED', started_utc=utc(), output_path=f'query_call_{call}.npz',
            flags={k: view[k].tolist() for k in QUERY_FLAGS}, dummy='zero',
            input_ids={k: tensor_id(view[k].numpy()) for k in ['img', 'ray_map', 'true_shape', 'camera_pose']})
        report['query_runs'].append(run)
        report['counters']['query_call_attempts'] += 1
        phase(f'query_call_{call}_started'); started = time.perf_counter()
        with torch.inference_mode():
            pred = inference_step(view, anchor, model, 'cpu', verbose=False)['pred']
        report['counters']['query_calls'] += 1
        run.update(status='RETURNED', returned_utc=utc(), seconds=time.perf_counter()-started)
        current = {k: v.detach().cpu().numpy().copy() for k, v in pred.items() if torch.is_tensor(v)}
        np.savez_compressed(out / run['output_path'], **current)
        run.update(output_saved=True, output_sha256=sha(out / run['output_path']))
        phase(f'query_call_{call}_saved_before_gates')
        validate_outputs(current)
        after_ids = {k: tensor_id(t.detach().cpu().numpy()) for k, t in zip(FIELDS, anchor)}
        require(after_ids == before_ids, 'Query modified frozen prefix latent state')
        run['state_ids_after'] = after_ids
        require(report['counters']['query_image_encoder_calls'] == 0 and report['counters']['query_ray_encoder_calls'] == call + 1, 'Query encoder budget')
        if call == 0:
            reference = current
        elif call == 1:
            for key in OUTPUT_SHAPES:
                require(tensor_id(current[key]) == tensor_id(reference[key]) and np.array_equal(current[key], reference[key]), 'Repeated first-query byte parity failed: ' + key)
            report['parity_all_six_outputs_exact'] = True
        if call != 1:
            new_z.append(current['pts3d_in_self_view'][0, :, :, 2]); new_conf.append(current['conf_self'][0])
        outputs.update({f'call{call}_{k}': v for k, v in current.items()})
        run.update(status='PASS', completed_utc=utc(), output_ids={k: tensor_id(v) for k, v in current.items()})
        phase(f'query_call_{call}_complete')
    proposals = {k: conditions[k] for k in ['source_indices', 'source_poses', 'K', 'old_self_z_model', 'old_self_z_m', 'old_conf_self', 's_model_per_metric']}
    proposals.update(new_self_z_model=np.asarray(new_z, dtype=np.float32),
        new_self_z_m=np.asarray(new_z, dtype=np.float64)/float(conditions['s_model_per_metric']),
        new_conf_self=np.asarray(new_conf, dtype=np.float32))
    for candidate in ['old', 'new']:
        proposals[candidate + '_positive_mask'] = proposals[candidate + '_self_z_model'] > 0
    np.savez_compressed(out / 'proposals.npz', **proposals)
    np.savez_compressed(out / 'query_outputs.npz', **outputs)
    np.savez_compressed(out / 'state_after_queries.npz', **{k: t.detach().cpu().numpy() for k, t in zip(FIELDS, anchor)})
    report['proposal_output_ids'] = {k: tensor_id(v) for k, v in proposals.items()}
    report['query_output_ids'] = {k: tensor_id(v) for k, v in outputs.items()}
    report['state_after_queries'] = after_ids
    report['nonpositive_source_counts'] = {candidate: np.sum(~proposals[candidate + '_positive_mask'], axis=(1, 2)).tolist() for candidate in ['old', 'new']}
    return outputs


def make_views(images, torch):
    require(len(images) == 12, 'Official loader returned twelve histories')
    views = []
    for i, im in enumerate(images):
        img = im['img'].float()
        require(list(img.shape) == [1, 3, 224, 224] and bool(torch.isfinite(img).all()), 'History RGB tensor')
        require(im['true_shape'].tolist() == [[224, 224]], 'History true shape')
        require(im['idx'] == i and im['instance'] == str(i), 'Official loader input order')
        views.append(dict(img=img, ray_map=torch.full((1, 224, 224, 6), torch.nan),
            true_shape=torch.from_numpy(im['true_shape']), idx=i, instance=str(i),
            camera_pose=torch.eye(4).unsqueeze(0), **{k: torch.tensor([v]) for k, v in FLAGS.items()}))
    return views


def execute_history(torch, np, inference, pose_decoder, model, views, report, out, phase):
    """Injectable numerical boundary; artificial tests do not instantiate CUT3R."""
    report['counters']['history_forward_attempts'] += 1
    phase('history_forward_started')
    started = time.perf_counter()
    with torch.inference_mode():
        history, snapshots = inference(views, model, 'cpu', verbose=False)
    report['counters']['history_forward_calls'] += 1
    report['history_forward_seconds'] = time.perf_counter() - started
    phase('history_forward_returned')
    require(isinstance(history, dict) and 'pred' in history, 'History prediction return')
    require(len(history['pred']) == 12, 'Twelve prediction entries')
    require(len(snapshots) == 13 and len(snapshots[-1]) == 5, 'Twelve updates plus initial state')
    # Persist all returned numerical model evidence before finite/semantic gates.
    arrays = {}
    for i, pred in enumerate(history['pred']):
        current = {k: t.detach().cpu().numpy().copy() for k, t in pred.items() if torch.is_tensor(t)}
        arrays.update({f'frame{i}_{k}': v for k, v in current.items()})
    np.savez_compressed(out / 'predictions.npz', **arrays)
    state = {k: t.detach().cpu().numpy().copy() for k, t in zip(FIELDS, snapshots[-1])}
    np.savez_compressed(out / 'state.npz', **state)
    report['raw_predictions_saved_before_gates'] = True
    phase('raw_history_outputs_saved')
    for i, pred in enumerate(history['pred']):
        require({k for k, t in pred.items() if torch.is_tensor(t)} == set(OUTPUT_SHAPES), 'Exactly six official tensors per frame')
        for k, shape in OUTPUT_SHAPES.items():
            validate_array(arrays[f'frame{i}_{k}'], shape, 'float32', f'frame{i}_{k}')
    for k in FIELDS:
        validate_array(state[k], *STATE_SCHEMA[k], k)
    encodings = torch.cat([p['camera_pose'] for p in history['pred']], dim=0)
    with torch.inference_mode():
        poses = pose_decoder(encodings).detach().cpu().numpy().copy()
    validate_array(poses, [12, 4, 4], 'float32', 'history c2w')
    require(np.array_equal(poses[:, 3, :], np.tile([0., 0., 0., 1.], (12, 1))), 'History c2w bottom row')
    rotations = poses[:, :3, :3].astype(np.float64)
    require(np.allclose(np.swapaxes(rotations, 1, 2) @ rotations, np.eye(3), rtol=0, atol=1e-5)
            and np.allclose(np.linalg.det(rotations), 1, rtol=0, atol=1e-5), 'History proper rotation')
    np.savez_compressed(out / 'history_poses.npz', history_pose_encodings=encodings.detach().cpu().numpy(), history_poses=poses)
    report['history_output_ids'] = {k: tensor_id(v) for k, v in arrays.items()}
    report['history_pose_ids'] = {k: tensor_id(v) for k, v in [('history_pose_encodings', encodings.detach().cpu().numpy()), ('history_poses', poses)]}
    report['state_final'] = {k: tensor_id(v) for k, v in state.items()}
    report['counters']['history_frames_saved'] = 12
    phase('history_outputs_validated')
    return arrays, poses, state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'Preserve earlier output; choose a fresh directory')
    args.output.mkdir(parents=True)
    started_monotonic = time.perf_counter()
    report = dict(schema='s15b-prefix-proposals-run-v1', status='RUNNING', started_utc=utc(),
        video_generated=False, new_model_trained=False, accuracy_evaluated=False,
        python=sys.version, executable=sys.executable, device='cpu', input_reads=[], query_runs=[],
        identity_hash_attempts=[], image_open_attempt_paths=[], image_opened_paths=[],
        counters=dict(identity_hash_attempts=0, identity_hash_successes=0, history_image_open_attempts=0,
            history_images_opened=0, history_rgb_decoded=0, target_rgb_decoded=0,
            target_depth_decoded=0, history_forward_attempts=0, history_forward_calls=0,
            history_image_encoder_calls=0, history_image_encoder_frames=0,
            history_ray_encoder_calls=0, history_frames_saved=0, query_calls=0,
            camera_json_reads=0, witness_rgb_decoded=0, query_call_attempts=0,
            query_image_encoder_calls=0, query_image_encoder_frames=0, query_ray_encoder_calls=0))
    def phase(name):
        report.update(phase=name, updated_utc=utc(), elapsed_seconds=time.perf_counter()-started_monotonic)
        report['peak_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if platform.system() == 'Darwin' else 1024)
        write(args.output / 'run_metadata.json', report)
        print(json.dumps(dict(utc=utc(), phase=name)), flush=True)
    def check_identities(identities):
        for p, digest in identities.items():
            report['counters']['identity_hash_attempts'] += 1
            report['identity_hash_attempts'].append(dict(path=p, utc=utc()))
            require(sha(p) == digest, 'Frozen source/input changed: ' + p)
            report['counters']['identity_hash_successes'] += 1
    handles = []
    original_open = None
    try:
        phase('read_manifest')
        m = json.loads(args.manifest.read_text())
        report['input_reads'].append(dict(role='manifest', path=str(args.manifest.resolve()), utc=utc()))
        paths = validate_contract(m)
        require(str(Path(__file__).resolve()) == m['runner'], 'Runner path')
        require(os.path.realpath(sys.executable) == os.path.realpath(m['python']), 'Python executable')
        report['manifest_sha256'] = sha(args.manifest)
        identities = m['identities']
        phase('pre_run_identity')
        check_identities(identities)
        repo = Path(m['repo'])
        commit = subprocess.check_output(['/usr/bin/git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
        dirty = subprocess.check_output(['/usr/bin/git', '-C', str(repo), 'status', '--porcelain', '--untracked-files=no'], text=True).strip()
        require(commit == m['commit'] and not dirty, 'Official checkout identity')
        require(str(os.environ.get('TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD', '')).lower() not in {'1', 'y', 'yes', 'true'}, 'Unsafe loader override')
        shutil.copy2(args.manifest, args.output / 'frozen_manifest.json')
        shutil.copy2(__file__, args.output / 'source_snapshot.py')
        import numpy as np
        import torch
        from PIL import Image
        sys.path[:0] = [str(repo / 'src'), str(repo / 'src' / 'croco')]
        from dust3r.model import ARCroco3DStereo
        from dust3r.inference import inference, inference_step
        from dust3r.utils.image import load_images
        from dust3r.utils.camera import pose_encoding_to_camera
        from models.pos_embed import RoPE2D
        import cut3r_rope_compat
        check = json.loads(Path(m['rope_check']).read_text())
        report['input_reads'].append(dict(role='rope_check', path=m['rope_check'], utc=utc()))
        require(check['ok'] and check['commit'] == commit and check['adapter_sha256'] == sha(cut3r_rope_compat.__file__), 'Signed RoPE check')
        cut3r_rope_compat.install(RoPE2D)
        torch.set_num_threads(8)
        torch.manual_seed(0)
        np.random.seed(0)
        report.update(torch_version=torch.__version__, numpy_version=np.__version__, pillow_version=Image.__version__,
            commit=commit, cpu_threads=8, seed=0, precision='FP32; existing official RoPE internal casts',
            runtime_adapter='Existing signed RoPE only', history_images=m['history_images'])
        phase('read_allowed_twelve_camera_json')
        camera_metadata = json.loads(Path(m['camera_inputs']).read_text())
        report['counters']['camera_json_reads'] += 1
        report['input_reads'].append(dict(role='twelve_given_prefix_cameras', path=m['camera_inputs'], utc=utc()))
        gt, K, timestamps = validate_cameras(camera_metadata, m)
        report['history_rgb_timestamps'] = timestamps.tolist()
        report['given_camera_array_ids'] = {'gt_c2w': tensor_id(gt), 'K': tensor_id(K), 'rgb_timestamps': tensor_id(timestamps)}
        phase('decode_twelve_history_rgb_only')
        original_open = Image.open
        decoded = []
        def tracked_open(fp, *a, **kw):
            p = str(Path(fp).resolve())
            report['counters']['history_image_open_attempts'] += 1
            report['image_open_attempt_paths'].append(p)
            require(len(decoded) < 12 and p == paths[len(decoded)], 'Image read outside ordered history allowlist: ' + p)
            image = original_open(fp, *a, **kw)
            report['counters']['history_images_opened'] += 1
            report['image_opened_paths'].append(p)
            image.load()
            decoded.append(p)
            report['counters']['history_rgb_decoded'] += 1
            report.setdefault('raw_image_properties', []).append(dict(index=len(decoded)-1, path=p, size=list(image.size), mode=image.mode))
            require(image.size == (640, 480) and image.mode == 'RGB', 'Frozen TUM native RGB dimensions/mode')
            return image
        Image.open = tracked_open
        images = load_images(paths, size=224, verbose=False)
        require(decoded == paths, 'Exactly twelve RGB decodes in frozen order')
        views = make_views(images, torch)
        phase('load_existing_checkpoint')
        from omegaconf import DictConfig
        from omegaconf.base import ContainerMetadata, Metadata
        from omegaconf.nodes import AnyNode
        allowed = [DictConfig, ContainerMetadata, Any, dict, defaultdict, AnyNode, Metadata]
        names = {f'{v.__module__}.{v.__qualname__}' for v in allowed}
        unsafe = torch.serialization.get_unsafe_globals_in_checkpoint(m['checkpoint'])
        require(not set(unsafe) - names, 'Unexpected checkpoint globals')
        stream = io.StringIO()
        try:
            with contextlib.redirect_stdout(stream), torch.serialization.safe_globals(allowed):
                model = ARCroco3DStereo.from_pretrained(m['checkpoint']).float().to('cpu').eval()
        finally:
            (args.output / 'checkpoint_load.txt').write_text(stream.getvalue())
        require('All keys matched successfully' in stream.getvalue(), 'Checkpoint key mismatch')
        require(model.head_type == 'linear' and list(model.patch_embed.img_size) == [224, 224], 'Pinned architecture')
        require(type(model.patch_embed_ray_map).__name__ == 'PatchEmbedDust3R', 'Pinned ray patch embedding')
        report.update(checkpoint_all_keys_matched=True, weights_only=True)
        def image_hook(module, inputs, result):
            report['counters']['history_image_encoder_calls'] += 1
            report['counters']['history_image_encoder_frames'] += int(inputs[0].shape[0])
        def ray_hook(module, inputs, result):
            report['counters']['history_ray_encoder_calls'] += 1
        handles = [model.patch_embed.register_forward_hook(image_hook), model.patch_embed_ray_map.register_forward_hook(ray_hook)]
        arrays, poses, state = execute_history(torch, np, inference, pose_encoding_to_camera, model, views, report, args.output, phase)
        require(report['counters']['history_forward_calls'] == 1 and report['counters']['history_image_encoder_frames'] == 12
                and report['counters']['history_image_encoder_calls'] == 1
                and report['counters']['history_ray_encoder_calls'] == 1 and report['counters']['query_calls'] == 0, 'History-only encoder/call budget')
        for handle in handles:
            handle.remove()
        handles = []
        phase('align_twelve_prefix_cameras_and_freeze_source_conditions')
        conditions = prepare_conditions(np, gt, poses, K, arrays, repo, args.output, report)
        phase('source_conditions_saved')
        def query_image_hook(module, inputs, result):
            report['counters']['query_image_encoder_calls'] += 1
            report['counters']['query_image_encoder_frames'] += int(inputs[0].shape[0])
        def query_ray_hook(module, inputs, result):
            report['counters']['query_ray_encoder_calls'] += 1
        handles = [model.patch_embed.register_forward_hook(query_image_hook), model.patch_embed_ray_map.register_forward_hook(query_ray_hook)]
        execute_queries(torch, np, inference_step, model, state, conditions, report, args.output, phase)
        require(report['counters']['query_calls'] == 5 and report['counters']['query_image_encoder_calls'] == 0
                and report['counters']['query_image_encoder_frames'] == 0
                and report['counters']['query_ray_encoder_calls'] == 5, 'Final query encoder/call budget')
        require(report['state_final'] == report['state_before_queries'] == report['state_after_queries'], 'Frozen prefix state identity across stages')
        loaded = {}
        for name, module in list(sys.modules.items()):
            path = getattr(module, '__file__', None)
            if path:
                p = Path(path).resolve()
                if p.is_relative_to(repo) and p.suffix == '.py':
                    require(str(p) in identities, 'Imported source not frozen: ' + str(p))
                    loaded[name] = dict(path=str(p), sha256=sha(p))
        report['loaded_upstream_modules'] = loaded
        phase('post_run_identity')
        check_identities(identities)
        require(sha(args.manifest) == report['manifest_sha256'], 'Manifest changed')
        report['before_after_identity_pass'] = True
        phase('identities_verified')
        require(report['elapsed_seconds'] < m['contract']['wall_seconds'] and report['peak_rss_bytes'] < m['contract']['monitored_rss_bytes'], 'Completed-run resource gate')
        report['output_sha256'] = {p.name: sha(p) for p in sorted(args.output.iterdir()) if p.is_file() and p.name != 'run_metadata.json'}
        report.update(status='SUCCESS', completed_utc=utc())
        phase('complete')
    except BaseException as error:
        report.update(status='FAILED', completed_utc=utc(), error=repr(error), traceback=traceback.format_exc())
        phase('failed')
        print(report['traceback'], file=sys.stderr)
        return 1
    finally:
        for h in handles:
            h.remove()
        if original_open is not None:
            from PIL import Image
            Image.open = original_open
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
