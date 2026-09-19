#!/usr/bin/env python3
"""S14E prediction-only runner: restored S14D state, exact parity, four sealed cameras.

No image decoder is used. This program does not align cameras or score outputs.
The four known-camera conditions are authorized inputs, not target image/depth labels.
"""
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
OUTPUT_SHAPES = {'pts3d_in_self_view': [1, 224, 224, 3],
                 'pts3d_in_other_view': [1, 224, 224, 3],
                 'conf_self': [1, 224, 224], 'conf': [1, 224, 224],
                 'camera_pose': [1, 7], 'rgb': [1, 224, 224, 3]}
FLAGS = {'img_mask': False, 'ray_mask': True, 'update': False, 'reset': False}
INPUT_ROLES = ['prior_run_metadata', 'state_npz', 'parity_inputs_npz',
               'parity_output_npz', 'condition_npz', 'condition_seal']


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


def validate_contract(manifest):
    require(manifest['schema'] == 's14e-state-reuse-manifest-v1', 'Manifest schema')
    c = manifest['contract']
    expected = dict(target_count=4, query_count=5, dummy_values=['zero'] * 5,
                    query_flags=FLAGS, device='cpu', cpu_threads=8, seed=0,
                    size=[224, 224], dtype='float32', wall_seconds=600,
                    monitored_rss_bytes=34359738368)
    for k, v in expected.items():
        require(c.get(k) == v, 'Contract mismatch: ' + k)
    require(c.get('history_rgb_allowed') is False and c.get('target_rgb_allowed') is False
            and c.get('target_depth_allowed') is False, 'Data boundary contract')
    identities = manifest['identities']
    for role in INPUT_ROLES + ['checkpoint', 'rope_check', 'runner']:
        p = manifest[role]
        require(Path(p).is_absolute() and p == str(Path(p).resolve()), 'Canonical absolute path: ' + role)
        require(p in identities, 'Input missing from identity freeze: ' + role)
    require(len({manifest[k] for k in INPUT_ROLES}) == len(INPUT_ROLES), 'Distinct input roles required')
    allowed_npz = {manifest[k] for k in ['state_npz', 'parity_inputs_npz', 'parity_output_npz', 'condition_npz']}
    for p in identities:
        suffix = Path(p).suffix.lower()
        require(suffix not in ['.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.exr', '.npy'],
                'Image/depth array must not be hashed by predictor: ' + p)
        require(suffix != '.npz' or p in allowed_npz, 'Unpermitted NPZ identity: ' + p)
        require(Path(p).name not in ['groundtruth.txt', 'rgb.txt', 'depth.txt'], 'Raw dataset metadata forbidden: ' + p)
    return expected


def validate_state(state, previous_ids):
    require(set(state) == set(FIELDS) and set(previous_ids) == set(FIELDS), 'State fields')
    for k in FIELDS:
        validate_array(state[k], *STATE_SCHEMA[k], k)
        require(tensor_id(state[k]) == previous_ids[k], 'Restored state differs from S14D: ' + k)


def validate_outputs(arrays):
    require(set(arrays) == set(OUTPUT_SHAPES), 'Exactly six output tensors required')
    for k, shape in OUTPUT_SHAPES.items():
        validate_array(arrays[k], shape, 'float32', k)


def compare_exact(actual, reference):
    import numpy as np
    validate_outputs(actual)
    validate_outputs(reference)
    for k in OUTPUT_SHAPES:
        require(tensor_id(actual[k]) == tensor_id(reference[k]) and
                np.array_equal(actual[k], reference[k]), 'Exact parity failed: ' + k)
    return {k: tensor_id(actual[k]) for k in OUTPUT_SHAPES}


def validate_conditions(values):
    import numpy as np
    require(set(values) == {'target_poses', 'K', 'ray_maps'}, 'Sealed condition key domain')
    validate_array(values['target_poses'], [4, 4, 4], 'float64', 'target_poses')
    validate_array(values['K'], [4, 3, 3], 'float64', 'K')
    validate_array(values['ray_maps'], [4, 224, 224, 6], 'float32', 'ray_maps')
    require(np.array_equal(values['target_poses'][:, 3, :], np.tile([0., 0., 0., 1.], (4, 1))), 'c2w bottom row')
    require(np.array_equal(values['K'][:, 2, :], np.tile([0., 0., 1.], (4, 1))), 'K bottom row')
    require((values['K'][:, [0, 1], [0, 1]] > 0).all(), 'Positive focal lengths')
    # Coordinate/alignment/ray correctness belongs to the independently sealed prepare stage.


def execute_queries(torch, np, inference_step, model, anchor, before_ids, parity, conditions,
                    reference, report, out, phase):
    """Small injectable orchestration boundary for artificial control-flow tests."""
    outputs = {}
    query_specs = [('parity', 0)] + [('condition', i) for i in range(4)]
    for call, (kind, target) in enumerate(query_specs):
        require(call == 0 or report.get('parity_all_six_outputs_exact') is True,
                'New query attempted before parity success')
        arrays = parity if kind == 'parity' else conditions
        # Q0 parity matches the exact previous zero-dummy call, including its metadata.
        view = dict(img=torch.zeros((1, 3, 224, 224), dtype=torch.float32),
                    ray_map=torch.from_numpy(arrays['ray_maps'][target][None].copy()),
                    true_shape=torch.tensor([[224, 224]], dtype=torch.int64), idx=20+target,
                    instance=f'ray_target_{target}' if kind == 'parity' else f's14e_target_{target}',
                    camera_pose=torch.from_numpy(arrays['target_poses'][target][None].astype(np.float32)),
                    **{k: torch.tensor([v]) for k, v in FLAGS.items()})
        run = dict(call=call, kind=kind, target_index=target, dummy='zero', status='STARTED',
                   started_utc=utc(), output_path=f'query_call_{call}.npz',
                   input_shapes={k: list(view[k].shape) for k in ['img', 'ray_map', 'true_shape', 'camera_pose']},
                   input_dtypes={k: str(view[k].dtype) for k in ['img', 'ray_map', 'true_shape', 'camera_pose']},
                   flags={k: view[k].tolist() for k in FLAGS}, target_camera_pose=view['camera_pose'].tolist())
        report['query_runs'].append(run)
        report['counters']['query_call_attempts'] += 1
        phase(f'query_call_{call}_started')
        started = time.perf_counter()
        with torch.inference_mode():
            pred = inference_step(view, anchor, model, 'cpu', verbose=False)['pred']
        report['counters']['query_calls'] += 1
        run.update(status='RETURNED', returned_utc=utc(), seconds=time.perf_counter()-started)
        current = {k: v.detach().cpu().numpy().copy() for k, v in pred.items() if torch.is_tensor(v)}
        np.savez_compressed(out / run['output_path'], **current)
        run.update(output_saved=True, output_sha256=sha(out / run['output_path']))
        phase(f'query_call_{call}_saved_before_gates')
        validate_outputs(current)
        ids = {k: tensor_id(t.detach().cpu().numpy()) for k, t in zip(FIELDS, anchor)}
        require(ids == before_ids, 'Query modified the restored latent state')
        run['state_ids_after'] = ids
        require(report['counters']['query_image_encoder_batches'] == 0 and
                report['counters']['query_ray_encoder_calls'] == call + 1, 'Unexpected query encoder use')
        if call == 0:
            report['parity_output_ids'] = compare_exact(current, reference)
            report['parity_all_six_outputs_exact'] = True
        outputs.update({f'call{call}_{k}': a for k, a in current.items()})
        run.update(status='PASS', completed_utc=utc(), output_ids={k: tensor_id(v) for k, v in current.items()})
        phase(f'query_call_{call}_complete')
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'Preserve prior output: choose a fresh directory')
    args.output.mkdir(parents=True)
    report = dict(schema='s14e-state-reuse-queries-v1', status='RUNNING', started_utc=utc(),
                  video_generated=False, new_model_trained=False, accuracy_evaluated=False,
                  known_camera_conditions_are_authorized_inputs=True,
                  python=sys.version, executable=sys.executable, device='cpu', query_runs=[],
                  input_reads=[], identity_hash_attempts=[],
                  counters=dict(identity_hash_attempts=0, identity_hash_successes=0,
                                npz_open_attempts=0, npz_opened=0, npz_array_decode_attempts=0,
                                npz_arrays_decoded=0, json_decode_attempts=0, json_decoded=0,
                                history_rgb_decoded=0, target_rgb_decoded=0, target_depth_decoded=0,
                                image_open_attempts=0, history_forward_calls=0,
                                query_call_attempts=0, query_calls=0, query_image_encoder_batches=0,
                                query_ray_encoder_calls=0))
    def phase(name):
        report.update(phase=name, updated_utc=utc())
        write(args.output / 'run_metadata.json', report)
        print(json.dumps(dict(utc=utc(), phase=name)), flush=True)
    def load_json(path, role):
        entry = dict(path=str(path), role=role, format='json', attempted_utc=utc(), completed=False)
        report['input_reads'].append(entry)
        report['counters']['json_decode_attempts'] += 1
        value = json.loads(Path(path).read_text())
        report['counters']['json_decoded'] += 1
        entry.update(completed=True, completed_utc=utc())
        return value
    def identities_check(identities):
        for p, digest in identities.items():
            report['counters']['identity_hash_attempts'] += 1
            report['identity_hash_attempts'].append(dict(path=p, utc=utc()))
            require(sha(p) == digest, 'Frozen input/source changed: ' + p)
            report['counters']['identity_hash_successes'] += 1
    handles = []
    restore_image_open = None
    try:
        phase('read_manifest')
        manifest = load_json(args.manifest, 'manifest')
        validate_contract(manifest)
        require(str(Path(__file__).resolve()) == manifest['runner'], 'Runner path')
        require(os.path.realpath(sys.executable) == os.path.realpath(manifest['python']), 'Python executable')
        report['manifest_sha256'] = sha(args.manifest)
        identities = manifest['identities']
        phase('pre_run_identity')
        identities_check(identities)
        require(sha(__file__) == identities[str(Path(__file__).resolve())], 'Runner source identity')
        repo = Path(manifest['repo'])
        require(str(repo / 'viser_utils.py') in identities and
                str(Path(__file__).parent / 'cut3r_rope_compat.py') in identities, 'Required pinned source missing')
        upstream = [p for p in identities if Path(p).is_relative_to(repo) and Path(p).suffix == '.py']
        require(len(upstream) == 99, 'Expected 99 pinned upstream Python files')
        commit = subprocess.check_output(['/usr/bin/git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
        dirty = subprocess.check_output(['/usr/bin/git', '-C', str(repo), 'status', '--porcelain', '--untracked-files=no'], text=True).strip()
        require(commit == manifest['commit'] and not dirty, 'Official checkout identity')
        require(str(os.environ.get('TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD', '')).lower() not in ['1', 'y', 'yes', 'true'], 'Unsafe loader override')
        prior = load_json(manifest['prior_run_metadata'], 'S14D provenance, no image arrays')
        require(prior['schema'] == 's14d-ray-only-probe-v1' and prior['status'] == 'SUCCESS', 'Successful S14D provenance required')
        for role in ['state_npz', 'parity_inputs_npz', 'parity_output_npz']:
            path = manifest[role]
            require(prior['output_sha256'][Path(path).name] == identities[path], 'Prior output binding: ' + role)
        require(Path(manifest['parity_output_npz']).name == 'query_call_1.npz', 'Use prior Q0 zero call')
        seal = load_json(manifest['condition_seal'], 'new condition seal')
        require(seal['schema'] == 's14e-condition-seal-v1' and
                seal['condition_npz_sha256'] == identities[manifest['condition_npz']], 'Condition seal binding')
        require(datetime.fromisoformat(seal['sealed_utc']) <= datetime.fromisoformat(report['started_utc']), 'Condition sealed before predictor')
        shutil.copy2(args.manifest, args.output / 'frozen_manifest.json')
        shutil.copy2(__file__, args.output / 'source_snapshot.py')
        import numpy as np
        import torch
        require(np.__version__ == prior['numpy_version'] and torch.__version__ == prior['torch_version'], 'Runtime differs from parity reference')
        def load_npz(path, role, keys, complete_keys=None):
            entry = dict(path=path, role=role, format='npz', attempted_utc=utc(), completed=False, array_reads=[])
            report['input_reads'].append(entry)
            report['counters']['npz_open_attempts'] += 1
            with np.load(path, allow_pickle=False) as source:
                report['counters']['npz_opened'] += 1
                if complete_keys is not None:
                    require(set(source.files) == set(complete_keys), 'NPZ key domain: ' + role)
                values = {}
                for k in keys:
                    report['counters']['npz_array_decode_attempts'] += 1
                    entry['array_reads'].append(dict(key=k, completed=False))
                    values[k] = source[k].copy()
                    report['counters']['npz_arrays_decoded'] += 1
                    entry['array_reads'][-1]['completed'] = True
                entry.update(completed=True, completed_utc=utc())
                return values
        phase('restore_sealed_prediction_inputs')
        state = load_npz(manifest['state_npz'], 'saved history latent', FIELDS, FIELDS)
        validate_state(state, prior['state_before'])
        parity = load_npz(manifest['parity_inputs_npz'], 'old Q0 parity camera only', ['target_poses', 'K', 'ray_maps'],
                          ['history_pose_encodings', 'history_poses', 'target_poses', 'K', 'ray_maps'])
        validate_array(parity['target_poses'], [4, 4, 4], 'float64', 'old target poses')
        validate_array(parity['K'], [3, 3], 'float32', 'old K')
        validate_array(parity['ray_maps'], [4, 224, 224, 6], 'float32', 'old rays')
        reference = load_npz(manifest['parity_output_npz'], 'old Q0 zero output parity only', list(OUTPUT_SHAPES), OUTPUT_SHAPES)
        validate_outputs(reference)
        conditions = load_npz(manifest['condition_npz'], 'four sealed given-camera conditions', ['target_poses', 'K', 'ray_maps'], ['target_poses', 'K', 'ray_maps'])
        validate_conditions(conditions)
        report['state_before'] = {k: tensor_id(v) for k, v in state.items()}
        report['new_condition_input_ids'] = {k: tensor_id(v) for k, v in conditions.items()}
        phase('load_existing_checkpoint')
        sys.path[:0] = [str(repo / 'src'), str(repo / 'src' / 'croco')]
        from PIL import Image
        restore_image_open = Image.open
        def reject_image_open(fp, *a, **kw):
            report['counters']['image_open_attempts'] += 1
            report.setdefault('forbidden_image_attempts', []).append(str(fp))
            raise ValueError('No image reads permitted in S14E predictor')
        Image.open = reject_image_open
        from dust3r.model import ARCroco3DStereo
        from dust3r.inference import inference_step
        from models.pos_embed import RoPE2D
        import cut3r_rope_compat
        check = load_json(manifest['rope_check'], 'existing signed RoPE check')
        require(check['ok'] and check['commit'] == commit and check['adapter_sha256'] == sha(cut3r_rope_compat.__file__), 'Signed RoPE identity')
        cut3r_rope_compat.install(RoPE2D)
        torch.set_num_threads(8)
        torch.manual_seed(0)
        np.random.seed(0)
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
        report.update(torch_version=torch.__version__, numpy_version=np.__version__, commit=commit,
                      cpu_threads=8, seed=0, precision='FP32 model; official internal RoPE casts preserved',
                      checkpoint_all_keys_matched=True, weights_only=True,
                      runtime_adapter='Existing signed RoPE only; no new shape/ray adapter')
        anchor = tuple(torch.from_numpy(state[k].copy()) for k in FIELDS)
        def image_hook(module, inputs, result):
            report['counters']['query_image_encoder_batches'] += int(inputs[0].shape[0])
        def ray_hook(module, inputs, result):
            report['counters']['query_ray_encoder_calls'] += 1
        handles = [model.patch_embed.register_forward_hook(image_hook), model.patch_embed_ray_map.register_forward_hook(ray_hook)]
        phase('parity_then_four_new_camera_queries')
        outputs = execute_queries(torch, np, inference_step, model, anchor, report['state_before'],
                                  parity, conditions, reference, report, args.output, phase)
        for h in handles:
            h.remove()
        handles = []
        np.savez_compressed(args.output / 'query_outputs.npz', **outputs)
        np.savez_compressed(args.output / 'state_after.npz', **{k: t.detach().cpu().numpy() for k, t in zip(FIELDS, anchor)})
        require(report['counters']['query_calls'] == 5 and report['counters']['query_image_encoder_batches'] == 0
                and report['counters']['query_ray_encoder_calls'] == 5, 'Final call/encoder budget')
        loaded = {}
        for name, module in list(sys.modules.items()):
            path = getattr(module, '__file__', None)
            if path:
                p = Path(path).resolve()
                if p.is_relative_to(repo) and p.suffix == '.py':
                    require(str(p) in identities, 'Imported source missing from freeze: ' + str(p))
                    loaded[name] = dict(path=str(p), sha256=sha(p))
        report['loaded_upstream_modules'] = loaded
        phase('post_run_identity')
        identities_check(identities)
        require(sha(args.manifest) == report['manifest_sha256'], 'Manifest changed')
        report['before_after_identity_pass'] = True
        report['output_sha256'] = {p.name: sha(p) for p in sorted(args.output.iterdir()) if p.is_file() and p.name != 'run_metadata.json'}
        report['peak_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if platform.system() == 'Darwin' else 1024)
        report.update(status='SUCCESS', completed_utc=utc(), phase='complete')
        write(args.output / 'run_metadata.json', report)
        print(json.dumps(dict(status='SUCCESS', query_calls=5, parity_exact=True)), flush=True)
    except BaseException as error:
        report.update(status='FAILED', completed_utc=utc(), error=repr(error), traceback=traceback.format_exc())
        write(args.output / 'run_metadata.json', report)
        print(report['traceback'], file=sys.stderr)
        return 1
    finally:
        for h in handles:
            h.remove()
        if restore_image_open is not None:
            from PIL import Image
            Image.open = restore_image_open
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
