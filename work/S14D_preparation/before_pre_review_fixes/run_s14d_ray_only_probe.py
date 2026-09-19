#!/usr/bin/env python3
"""Actual CUT3R direct ray-query interface probe; no target image or GT.

Uses the pinned official inference/inference_step and AST-extracted official
viewer ray convention, including its translation term. Not video or quality.
"""
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
REQUIRED = ['pts3d_in_self_view', 'pts3d_in_other_view', 'conf_self', 'conf', 'camera_pose']


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


def extract_ray_factory(path, np):
    tree = ast.parse(Path(path).read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'PointCloudViewer')
    names = ['generate_pseudo_intrinsics', 'get_ray_map']
    methods = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in names]
    require([n.name for n in methods] == names, 'Official ray methods not found in order')
    pure = ast.Module(body=[ast.ClassDef(name='OfficialRayFactory', bases=[], keywords=[],
                                       body=methods, decorator_list=[])], type_ignores=[])
    pure = ast.fix_missing_locations(pure)
    namespace = {'np': np}
    exec(compile(pure, str(path), 'exec'), namespace)
    return namespace['OfficialRayFactory'](), ast.unparse(pure) + '\n'


def target_poses_from_history(history, np):
    distances = np.linalg.norm(history[:, :3, 3].astype(np.float64) - history[0, :3, 3], axis=1)
    positive = distances[distances > 1e-6]
    require(positive.size > 0, 'No nondegenerate history translation scale')
    d = 0.05 * float(np.median(positive))
    anchor = history[-1].astype(np.float64)
    poses = np.repeat(anchor[None], 4, axis=0)
    offsets = np.array([[0, 0, 0], [d, 0, 0], [-d, 0, 0], [0, 0, d]], dtype=np.float64)
    poses[:, :3, 3] += (anchor[:3, :3] @ offsets.T).T
    return poses, d, distances


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'Preserve prior output: use a fresh directory')
    args.output.mkdir(parents=True)
    manifest = json.loads(args.manifest.read_text())
    report = dict(schema='s14d-ray-only-probe-v1', status='RUNNING', started_utc=utc(),
                  manifest_sha256=sha(args.manifest), video_generated=False,
                  new_model_trained=False, accuracy_evaluated=False, device='cpu',
                  python=sys.version, executable=sys.executable,
                  counters=dict(history_rgb_decoded=0, query_rgb_decoded=0,
                                gt_files_decoded=0, query_calls=0,
                                query_image_encoder_batches=0, query_ray_encoder_calls=0),
                  query_runs=[])
    def phase(name):
        report['phase'] = name
        report['updated_utc'] = utc()
        write(args.output / 'run_metadata.json', report)
        print(json.dumps(dict(utc=utc(), phase=name)), flush=True)
    try:
        import numpy as np
        import torch
        identities = manifest['identities']
        require(manifest['schema'] == 's14d-ray-only-manifest-v1', 'Manifest schema')
        require(sha(__file__) == identities[str(Path(__file__).resolve())], 'Runner identity')
        for path, digest in identities.items():
            require(sha(path) == digest, 'Frozen input/source changed: ' + path)
        require(len(manifest['history_images']) == 20, 'Exactly 20 history inputs required')
        require(manifest['contract']['call_target_indices'] == [0, 0, 1, 2, 3], 'Call order')
        require(manifest['contract']['query_dummy_values'] == ['nan', 'zero', 'nan', 'nan', 'nan'], 'Dummy order')
        require(manifest['contract']['response_threshold'] == 1e-6, 'Response rule')
        repo = Path(manifest['repo'])
        commit = subprocess.check_output(['/usr/bin/git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
        dirty = subprocess.check_output(['/usr/bin/git', '-C', str(repo), 'status', '--porcelain', '--untracked-files=no'], text=True).strip()
        require(commit == manifest['commit'] and not dirty, 'Official checkout identity')
        require(not str(os.environ.get('TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD', '')).lower() in ['1', 'y', 'yes', 'true'], 'Unsafe loader override')
        shutil.copy2(args.manifest, args.output / 'frozen_manifest.json')
        shutil.copy2(__file__, args.output / 'source_snapshot.py')
        sys.path[:0] = [str(repo / 'src'), str(repo / 'src' / 'croco')]
        from dust3r.model import ARCroco3DStereo
        from dust3r.inference import inference, inference_step
        from dust3r.utils.image import load_images
        from dust3r.utils.camera import pose_encoding_to_camera
        from models.pos_embed import RoPE2D
        import cut3r_rope_compat
        check = json.loads(Path(manifest['rope_check']).read_text())
        require(check['ok'] and check['commit'] == commit and
                check['adapter_sha256'] == sha(cut3r_rope_compat.__file__), 'Signed RoPE identity')
        cut3r_rope_compat.install(RoPE2D)
        torch.set_num_threads(8)
        torch.manual_seed(0)
        np.random.seed(0)
        report.update(torch_version=torch.__version__, numpy_version=np.__version__, commit=commit,
                      cpu_threads=8, seed=0, precision='FP32 model; official internal RoPE casts preserved',
                      runtime_adapter='Existing signed RoPE only; no new shape or ray formula adapter')
        phase('load_history_rgb_only')
        from PIL import Image
        original_open = Image.open
        permitted = {str(Path(p['path']).resolve()) for p in manifest['history_images']}
        decoded_paths = []
        def tracked_open(fp, *a, **kw):
            path = str(Path(fp).resolve())
            require(path in permitted, 'Unexpected image read: ' + path)
            decoded_paths.append(path)
            return original_open(fp, *a, **kw)
        Image.open = tracked_open
        try:
            images = load_images([p['path'] for p in manifest['history_images']], size=224, verbose=False)
        finally:
            Image.open = original_open
        require(decoded_paths == [p['path'] for p in manifest['history_images']], 'History read order')
        report['counters']['history_rgb_decoded'] = len(decoded_paths)
        report['decoded_image_paths'] = decoded_paths
        views = []
        for i, im in enumerate(images):
            img = im['img'].float()
            require(list(img.shape) == [1, 3, 224, 224], 'History image tensor size')
            views.append(dict(img=img, ray_map=torch.full((1, 6, 224, 224), torch.nan),
                              true_shape=torch.from_numpy(im['true_shape']), idx=i, instance=str(i),
                              camera_pose=torch.eye(4).unsqueeze(0), img_mask=torch.tensor([True]),
                              ray_mask=torch.tensor([False]), update=torch.tensor([True]), reset=torch.tensor([False])))
        phase('load_existing_checkpoint')
        from omegaconf import DictConfig
        from omegaconf.base import ContainerMetadata, Metadata
        from omegaconf.nodes import AnyNode
        allowed = [DictConfig, ContainerMetadata, Any, dict, defaultdict, AnyNode, Metadata]
        names = {f'{v.__module__}.{v.__qualname__}' for v in allowed}
        unsafe = torch.serialization.get_unsafe_globals_in_checkpoint(manifest['checkpoint'])
        require(not set(unsafe) - names, 'Unexpected checkpoint globals')
        stream = io.StringIO()
        try:
            with contextlib.redirect_stdout(stream), torch.serialization.safe_globals(allowed):
                model = ARCroco3DStereo.from_pretrained(manifest['checkpoint']).float().to('cpu').eval()
        finally:
            (args.output / 'checkpoint_load.txt').write_text(stream.getvalue())
        require('All keys matched successfully' in stream.getvalue(), 'Checkpoint key mismatch')
        require(model.head_type == 'linear' and list(model.patch_embed.img_size) == [224, 224], 'Architecture')
        require(type(model.patch_embed_ray_map).__name__ == 'PatchEmbedDust3R', 'Unreviewed ray patch embed')
        report['ray_patch_embed'] = type(model.patch_embed_ray_map).__name__
        report['checkpoint_all_keys_matched'] = True
        report['weights_only'] = True
        query_phase = [False]
        def image_hook(module, inputs, result):
            if query_phase[0]: report['counters']['query_image_encoder_batches'] += int(inputs[0].shape[0])
        def ray_hook(module, inputs, result):
            if query_phase[0]: report['counters']['query_ray_encoder_calls'] += 1
        handles = [model.patch_embed.register_forward_hook(image_hook), model.patch_embed_ray_map.register_forward_hook(ray_hook)]
        def stage(view):
            for key, value in list(view.items()):
                if torch.is_tensor(value):
                    old = value.detach().cpu().numpy().copy()
                    view[key] = value.to('cpu', non_blocking=False)
                    require(np.array_equal(old, view[key].numpy(), equal_nan=True), 'Staging corruption')
        for view in views: stage(view)
        phase('history_forward_for_new_latent_state')
        t = time.perf_counter()
        with torch.inference_mode():
            history, snapshots = inference(views, model, 'cpu', verbose=False)
        report['history_forward_seconds'] = time.perf_counter() - t
        require(len(snapshots) == 21 and len(snapshots[-1]) == 5, 'History latent schema')
        encodings = torch.cat([p['camera_pose'] for p in history['pred']], 0)
        history_poses = pose_encoding_to_camera(encodings).numpy()
        require(np.isfinite(history_poses).all(), 'History pose finite gate')
        poses, distance, distances = target_poses_from_history(history_poses, np)
        factory, ray_source = extract_ray_factory(repo / 'viser_utils.py', np)
        (args.output / 'extracted_ray_factory.py').write_text(ray_source)
        K = factory.generate_pseudo_intrinsics(224, 224)
        rays = np.array([factory.get_ray_map(p, 224, 224, K) for p in poses], dtype=np.float32)
        require(np.isfinite(rays).all(), 'Ray input finite gate')
        require(all(not np.array_equal(rays[0], v) for v in rays[1:]), 'Distinct target rays required')
        np.savez_compressed(args.output / 'probe_inputs.npz', history_pose_encodings=encodings.numpy(),
                            history_poses=history_poses, target_poses=poses, K=K, ray_maps=rays)
        report['target_step'] = distance
        report['history_distances'] = distances.tolist()
        anchor = snapshots[-1]
        before = {name: value.detach().cpu().numpy().copy() for name, value in zip(FIELDS, anchor)}
        require(all(np.isfinite(v).all() for v in before.values()), 'State finite gate')
        np.savez_compressed(args.output / 'state_before.npz', **before)
        def tensor_id(a):
            a = np.ascontiguousarray(a)
            return dict(shape=list(a.shape), dtype=str(a.dtype), sha256=hashlib.sha256(a.tobytes()).hexdigest())
        report['state_before'] = {k: tensor_id(v) for k, v in before.items()}
        output_arrays = {}
        phase('direct_ray_only_queries')
        query_phase[0] = True
        for i, target in enumerate([0, 0, 1, 2, 3]):
            dummy = 'zero' if i == 1 else 'nan'
            view = dict(img=torch.full((1, 3, 224, 224), 0.0 if dummy == 'zero' else torch.nan),
                        ray_map=torch.from_numpy(rays[target][None].copy()), true_shape=torch.tensor([[224, 224]]),
                        idx=20+target, instance=f'ray_target_{target}', camera_pose=torch.from_numpy(poses[target][None].astype(np.float32)),
                        img_mask=torch.tensor([False]), ray_mask=torch.tensor([True]), update=torch.tensor([False]), reset=torch.tensor([False]))
            stage(view)
            started = utc(); t = time.perf_counter()
            with torch.inference_mode(): pred = inference_step(view, anchor, model, 'cpu', verbose=False)['pred']
            require(all(k in pred for k in REQUIRED), 'Missing geometry output')
            keys = []
            for key, value in pred.items():
                if not torch.is_tensor(value): continue
                a = value.detach().cpu().numpy()
                output_arrays[f'call{i}_{key}'] = a
                require(np.isfinite(a).all(), 'Nonfinite query output: ' + key)
                keys.append(key)
            hashes = {}
            for name, value in zip(FIELDS, anchor):
                a = value.detach().cpu().numpy()
                require(np.array_equal(a, before[name]), 'Query mutated latent state: ' + name)
                hashes[name] = tensor_id(a)['sha256']
            report['query_runs'].append(dict(call=i, target_index=target, dummy=dummy, started_utc=started,
                completed_utc=utc(), seconds=time.perf_counter()-t, state_hashes=hashes, output_keys=keys,
                flags={k: view[k].tolist() for k in ['img_mask', 'ray_mask', 'update', 'reset']}))
            report['counters']['query_calls'] += 1
            phase('query_call_' + str(i) + '_complete')
        for h in handles: h.remove()
        np.savez_compressed(args.output / 'query_outputs.npz', **output_arrays)
        after = {k: t.detach().cpu().numpy() for k, t in zip(FIELDS, anchor)}
        np.savez_compressed(args.output / 'state_after.npz', **after)
        keys = report['query_runs'][0]['output_keys']
        require(all(np.array_equal(output_arrays['call0_'+k], output_arrays['call1_'+k]) for k in keys), 'Dummy image invariance failed')
        require(report['counters']['query_image_encoder_batches'] == 0 and
                report['counters']['query_ray_encoder_calls'] == 5, 'Unexpected query encoder usage')
        report['dummy_all_outputs_exact'] = True
        report['response_diagnostics'] = []
        for i in [2, 3, 4]:
            difference = max(float(np.max(np.abs(output_arrays[f'call{i}_'+k].astype(np.float64) -
                                        output_arrays['call0_'+k].astype(np.float64))))
                             for k in ['pts3d_in_self_view', 'pts3d_in_other_view'])
            report['response_diagnostics'].append(dict(call=i, target_index=i-1, max_abs_geometry_difference=difference,
                response_detected=difference > 1e-6, threshold=1e-6, quality_evidence=False))
        loaded = {}
        for name, module in list(sys.modules.items()):
            path = getattr(module, '__file__', None)
            if not path: continue
            p = Path(path).resolve()
            if p.is_relative_to(repo) and p.suffix == '.py':
                require(str(p) in identities, 'Imported source missing from freeze: '+str(p))
                loaded[name] = dict(path=str(p), sha256=sha(p))
        report['loaded_upstream_modules'] = loaded
        phase('post_run_identity')
        for path, digest in identities.items(): require(sha(path) == digest, 'Post-run identity: ' + path)
        require(sha(args.manifest) == report['manifest_sha256'], 'Manifest changed')
        report['before_after_identity_pass'] = True
        report['output_sha256'] = {p.name: sha(p) for p in sorted(args.output.iterdir()) if p.is_file() and p.name != 'run_metadata.json'}
        report['peak_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if platform.system() == 'Darwin' else 1024)
        report.update(status='SUCCESS', completed_utc=utc(), phase='complete')
        write(args.output / 'run_metadata.json', report)
        print(json.dumps(dict(status='SUCCESS', responses=report['response_diagnostics'])), flush=True)
    except BaseException as error:
        report.update(status='FAILED', completed_utc=utc(), error=repr(error), traceback=traceback.format_exc())
        write(args.output / 'run_metadata.json', report)
        print(report['traceback'], file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
