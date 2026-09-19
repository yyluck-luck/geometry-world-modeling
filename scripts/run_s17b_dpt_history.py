#!/usr/bin/env python3
"""S17B fixed 512 DPT CUT3R inference; exactly two pre-exposed RGB inputs, no target query."""
from __future__ import annotations
import argparse
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
OUTPUT_SHAPES = {'pts3d_in_self_view': [1, 384, 512, 3],
                 'pts3d_in_other_view': [1, 384, 512, 3],
                 'conf_self': [1, 384, 512], 'conf': [1, 384, 512],
                 'camera_pose': [1, 7], 'rgb': [1, 384, 512, 3]}
FLAGS = {'img_mask': True, 'ray_mask': False, 'update': True, 'reset': False}
COMMIT = '8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf'
CHECKPOINT_SHA256 = '45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103'
CHECKPOINT_BYTES = 3173761006
HISTORY_SHA256 = [
    '7caa6f1b9fd1ac5b6938812682c55e3d7926a1348c7554c23e1012b47759cc39',
    '77bebdb3ac737221ef05a4404a1124676bcff536dbffdbb6e197b59bcdf811ae',
]
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg'}
EXPECTED_CONTRACT = dict(history_count=2, query_count=0, history_flags=FLAGS,
    device='cpu', cpu_threads=8, seed=0, size=[384, 512], loader_size=512, raw_image_size=[640, 480],
    head_type='dpt', patch_image_size=[512, 512], dtype='float32',
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
    require(m['schema'] == 's17b-dpt-two-frame-manifest-v1', 'Manifest schema')
    require(m['commit'] == COMMIT, 'Pinned official commit')
    for key, value in EXPECTED_CONTRACT.items():
        require(m['contract'].get(key) == value, 'Contract mismatch: ' + key)
    identities = m['identities']
    for p, digest in identities.items():
        require(Path(p).is_absolute() and p == str(Path(p).resolve()), 'Canonical identity path: ' + p)
        require(isinstance(digest, str) and len(digest) == 64 and all(c in '0123456789abcdef' for c in digest), 'SHA256 format: ' + p)
    for role in ['repo', 'python', 'runner', 'checkpoint', 'rope_check']:
        p = m[role]
        require(Path(p).is_absolute() and p == str(Path(p).absolute()), 'Absolute role: ' + role)
    for role in ['runner', 'checkpoint', 'rope_check']:
        require(m[role] in identities, 'Frozen role missing: ' + role)
    require(identities[m['checkpoint']] == CHECKPOINT_SHA256, 'Pinned checkpoint SHA')
    repo = Path(m['repo']).resolve()
    require(str(repo) == m['repo'], 'Canonical repo')
    history = m['history_images']
    require(len(history) == 2 and [x['index'] for x in history] == [0, 1], 'Ordered history indices 0/1')
    paths = [x['path'] for x in history]
    require(len(set(paths)) == 2, 'Distinct two RGB files')
    require([x['sha256'] for x in history] == HISTORY_SHA256, 'Exact S15A original RGB indices 0/1')
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
    allowed = upstream | set(paths) | set(controls) | {m['runner'], m['checkpoint'], m['rope_check'], adapter}
    require(set(identities) == allowed, 'Unpermitted identity: target images, arrays, and dataset metadata forbidden')
    for p in identities:
        require(Path(p).name not in {'groundtruth.txt', 'rgb.txt', 'depth.txt'}, 'Raw dataset metadata forbidden')
    return paths


def make_views(images, torch):
    require(len(images) == 2, 'Official loader returned two histories')
    views = []
    for i, im in enumerate(images):
        img = im['img'].float()
        require(list(img.shape) == [1, 3, 384, 512] and bool(torch.isfinite(img).all()), 'History RGB tensor')
        require(im['true_shape'].tolist() == [[384, 512]], 'History true shape')
        require(im['idx'] == i and im['instance'] == str(i), 'Official loader input order')
        views.append(dict(img=img, ray_map=torch.full((1, 384, 512, 6), torch.nan),
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
    require(len(history['pred']) == 2, 'Two prediction entries')
    require(len(snapshots) == 3 and len(snapshots[-1]) == 5, 'Two updates plus initial state')
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
    validate_array(poses, [2, 4, 4], 'float32', 'history c2w')
    require(np.array_equal(poses[:, 3, :], np.tile([0., 0., 0., 1.], (2, 1))), 'History c2w bottom row')
    rotations = poses[:, :3, :3].astype(np.float64)
    require(np.allclose(np.swapaxes(rotations, 1, 2) @ rotations, np.eye(3), rtol=0, atol=1e-4)
            and np.allclose(np.linalg.det(rotations), 1, rtol=0, atol=1e-4), 'History proper rotation')
    np.savez_compressed(out / 'history_poses.npz', history_pose_encodings=encodings.detach().cpu().numpy(), history_poses=poses)
    report['history_output_ids'] = {k: tensor_id(v) for k, v in arrays.items()}
    report['history_pose_ids'] = {k: tensor_id(v) for k, v in [('history_pose_encodings', encodings.detach().cpu().numpy()), ('history_poses', poses)]}
    report['state_final'] = {k: tensor_id(v) for k, v in state.items()}
    report['counters']['history_frames_saved'] = 2
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
    report = dict(schema='s17b-dpt-two-frame-run-v1', status='RUNNING', started_utc=utc(),
        video_generated=False, new_model_trained=False, accuracy_evaluated=False,
        python=sys.version, executable=sys.executable, device='cpu', input_reads=[],
        identity_hash_attempts=[], image_open_attempt_paths=[], image_opened_paths=[],
        counters=dict(identity_hash_attempts=0, identity_hash_successes=0, history_image_open_attempts=0,
            history_images_opened=0, history_rgb_decoded=0, target_rgb_decoded=0,
            target_depth_decoded=0, history_forward_attempts=0, history_forward_calls=0,
            history_image_encoder_calls=0, history_image_encoder_frames=0,
            history_ray_encoder_calls=0, history_frames_saved=0, query_calls=0,
            history_ray_encoder_frames=0, supplied_ray_frames=0,
            history_encoder_first_block_calls=0, history_encoder_last_block_calls=0))
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
        require(Path(m['checkpoint']).stat().st_size == CHECKPOINT_BYTES, 'Complete 512 DPT checkpoint size')
        report['checkpoint_identity'] = dict(path=m['checkpoint'], sha256=CHECKPOINT_SHA256, bytes=CHECKPOINT_BYTES)
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
        from dust3r.inference import inference
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
        phase('decode_two_history_rgb_only')
        original_open = Image.open
        decoded = []
        def tracked_open(fp, *a, **kw):
            p = str(Path(fp).resolve())
            report['counters']['history_image_open_attempts'] += 1
            report['image_open_attempt_paths'].append(p)
            require(len(decoded) < 2 and p == paths[len(decoded)], 'Image read outside ordered history allowlist: ' + p)
            image = original_open(fp, *a, **kw)
            report['counters']['history_images_opened'] += 1
            report['image_opened_paths'].append(p)
            require(list(image.size) == m['contract']['raw_image_size'] and image.mode == 'RGB', 'Frozen native Bonn RGB properties')
            image.load()
            decoded.append(p)
            report['counters']['history_rgb_decoded'] += 1
            report.setdefault('raw_image_properties', []).append(dict(index=len(decoded)-1, path=p, size=list(image.size), mode=image.mode))
            return image
        Image.open = tracked_open
        images = load_images(paths, size=512, verbose=False)
        require(decoded == paths, 'Exactly two RGB decodes in frozen order')
        views = make_views(images, torch)
        report['processed_input_shapes'] = [list(v['img'].shape) for v in views]
        report['processed_true_shapes'] = [v['true_shape'].tolist() for v in views]
        report['history_flags'] = [{k: bool(v[k].item()) for k in FLAGS} for v in views]
        report['counters']['supplied_ray_frames'] = sum(int(v['ray_mask'].sum().item()) for v in views)
        report['counters']['supplied_image_frames'] = sum(int(v['img_mask'].sum().item()) for v in views)
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
        require(model.head_type == 'dpt' and list(model.patch_embed.img_size) == [512, 512], 'Pinned 512 DPT architecture')
        require(type(model.patch_embed).__name__ == 'PatchEmbedDust3R', 'Official loader normalized image patch class')
        require(type(model.downstream_head).__name__ == 'DPTPts3dPose', 'Actual DPT six-head implementation')
        require(len(model.enc_blocks) == 24, 'Pinned image encoder depth')
        require(type(model.patch_embed_ray_map).__name__ == 'PatchEmbedDust3R', 'Pinned ray patch embedding')
        report.update(checkpoint_all_keys_matched=True, weights_only=True,
            architecture=dict(head_type=model.head_type, output_mode=model.output_mode,
                image_patch_class=type(model.patch_embed).__name__,
                ray_patch_class=type(model.patch_embed_ray_map).__name__,
                patch_image_size=list(model.patch_embed.img_size),
                downstream_head_class=type(model.downstream_head).__name__,
                encoder_blocks=len(model.enc_blocks), parameters=sum(p.numel() for p in model.parameters())),
            checkpoint_unsafe_globals=unsafe, encoder_observations=[])
        def image_hook(module, inputs, result):
            report['counters']['history_image_encoder_calls'] += 1
            report['counters']['history_image_encoder_frames'] += int(inputs[0].shape[0])
            report['encoder_observations'].append(dict(kind='image_patch', input_shape=list(inputs[0].shape), dtype=str(inputs[0].dtype), output_token_shape=list(result[0].shape)))
        def ray_hook(module, inputs, result):
            report['counters']['history_ray_encoder_calls'] += 1
            report['counters']['history_ray_encoder_frames'] += int(inputs[0].shape[0])
            report['encoder_observations'].append(dict(kind='dummy_ray_patch', input_shape=list(inputs[0].shape), dtype=str(inputs[0].dtype), all_zero=bool((inputs[0] == 0).all()), output_token_shape=list(result[0].shape)))
        def boundary_hook(kind):
            def hook(module, inputs, result):
                report['counters']['history_encoder_' + kind + '_block_calls'] += 1
                report['encoder_observations'].append(dict(kind='image_encoder_' + kind + '_block', input_shape=list(inputs[0].shape), dtype=str(inputs[0].dtype)))
            return hook
        handles = [model.patch_embed.register_forward_hook(image_hook), model.patch_embed_ray_map.register_forward_hook(ray_hook),
            model.enc_blocks[0].register_forward_hook(boundary_hook('first')), model.enc_blocks[-1].register_forward_hook(boundary_hook('last'))]
        execute_history(torch, np, inference, pose_encoding_to_camera, model, views, report, args.output, phase)
        require(report['counters']['history_forward_calls'] == 1 and report['counters']['history_image_encoder_frames'] == 2
                and report['counters']['history_image_encoder_calls'] == 1
                and report['counters']['history_ray_encoder_calls'] == 1
                and report['counters']['history_ray_encoder_frames'] == 1
                and report['counters']['history_encoder_first_block_calls'] == 1
                and report['counters']['history_encoder_last_block_calls'] == 1
                and report['counters']['supplied_ray_frames'] == 0
                and report['counters']['query_calls'] == 0, 'History-only encoder/call budget')
        obs = {o['kind']: o for o in report['encoder_observations']}
        require(obs['image_patch']['input_shape'] == [2, 3, 384, 512] and obs['image_patch']['output_token_shape'] == [2, 768, 1024], 'Actual two-image encoder input/token count')
        require(obs['dummy_ray_patch']['input_shape'] == [1, 6, 384, 512] and obs['dummy_ray_patch']['all_zero'], 'Official zero dummy ray path; no supplied rays')
        require(all(obs['image_encoder_' + kind + '_block']['input_shape'] == [2, 768, 1024] for kind in ['first', 'last']), 'Actual image backbone traversal')
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
