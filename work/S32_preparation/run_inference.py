"""S32 stage A only: four frozen fresh-PIL CUT3R windows, no GA or GT access."""
from __future__ import annotations
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import random
import sys
import time
import traceback
from datetime import datetime, timezone


def utc(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def require(ok, message):
    if not ok: raise RuntimeError(message)
def write(p, value):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    temporary = p.with_suffix(p.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    temporary.replace(p)
def module(p, name):
    spec = importlib.util.spec_from_file_location(name, p)
    obj = importlib.util.module_from_spec(spec); sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj


def contract(path, expected):
    require(sha(path) == expected, 'Exact frozen S32 A contract SHA required')
    c = read(path)
    require(c['schema'] == 's32-original-consumer-fresh4-inference-v1' and c['status'] == 'FROZEN', 'A candidate cannot execute')
    require(c['phase'] == 'A_inference_only' and c['total_frames'] == 16, 'Only four fresh4 windows')
    require(c['limits'] == dict(threads=8, seconds_per_window=180, rss_bytes_per_window=16*1024**3), 'Fixed A budget')
    require(c['inference_entry'] == 'src.dust3r.inference.inference' and c['training'] is False, 'Original VMem inference and eval mode')
    for p, h in c['identities'].items(): require(sha(p) == h, 'Changed source/selection identity: ' + p)
    require(sha(c['selection']) == c['selection_sha256'], 'Original metadata selection changed')
    selection = read(c['selection'])['windows']
    require(len(selection) == len(c['windows']) == 4, 'All four preselected windows retained')
    for original, window in zip(selection, c['windows']):
        for key in ('id', 'scene', 'j', 'start_index', 'total_original_RGB'):
            require(original[key] == window[key], 'Selection identity: ' + key)
        require(len(window['frames']) == 4, 'Four consecutive RGB entries')
        for index, (old, new) in enumerate(zip(original['frames'], window['frames'])):
            for key in ('index', 'source_rgb_index', 'path', 'rgb_time'):
                require(old[key] == new[key], 'Frame selection identity: ' + key)
            require(new['index'] == index and new['source_rgb_index'] == window['start_index'] + index, 'Local/global RGB order')
            require(isinstance(new['sha256'], str) and len(new['sha256']) == 64, 'Root must seal RGB bytes before A')
    checkpoint = Path(c['checkpoint'])
    require(checkpoint.is_file() and [checkpoint.stat().st_size, checkpoint.stat().st_mtime_ns] == c['checkpoint_stat'], 'Previously sealed local checkpoint stat changed')
    c['_sha'] = expected
    return c


def worker(c, window_id):
    found = [w for w in c['windows'] if w['id'] == window_id]
    require(len(found) == 1, 'Exactly one predefined window')
    window = found[0]; out = Path(c['output_root']) / window_id
    require(not out.exists(), 'Never overwrite or automatically repeat a window')
    out.mkdir(parents=True)
    receipt = dict(status='RUNNING', phase='A_inference_only', started_utc=utc(), contract_sha256=c['_sha'], window=window_id,
                   sensor_depth_bytes_read=0, GT_pose_file_bytes_read=0, GA_calls=0, backward_calls=0, Adam_steps=0,
                   evidence_scope='New original CUT3R inference on fixed RGB windows only; no accuracy or consumer optimization claim')
    write(out / 'receipt.json', receipt)
    try:
        for frame in window['frames']: require(sha(frame['path']) == frame['sha256'], 'Selected RGB bytes changed')
        a = module(c['adapter'], 's32_saved_head_adapter')
        ns, source_proof = a.configure_original_geometry(c['binding'])
        import numpy as np
        import torch
        from typing import Any
        from collections import defaultdict
        from omegaconf import DictConfig
        from omegaconf.base import ContainerMetadata, Metadata
        from omegaconf.nodes import AnyNode
        from dust3r.model import ARCroco3DStereo
        from src.dust3r.inference import inference
        from models.pos_embed import RoPE2D
        from models.rope_cpu import RoPE2DPyTorch
        torch.set_num_threads(8); torch.manual_seed(0); np.random.seed(0); random.seed(0)
        require(not torch.is_autocast_enabled('cpu') and not torch.is_autocast_enabled('cuda'), 'No outer autocast')
        views = a.load_original_views(ns, window['frames'])
        require(len(views) == 4, 'Exactly four original PIL views')
        view_arrays = {}
        for index, view in enumerate(views):
            require(view['idx'] == index and view['instance'] == str(index), 'PIL local frame identities')
            require(tuple(view['img'].shape) == (1, 3, 384, 512) and view['img'].dtype == torch.float32, 'PIL shape/dtype')
            require(bool(view['img_mask']) and not bool(view['ray_mask']) and bool(view['update']) and not bool(view['reset']), 'Original image-only recurrence flags')
            require(torch.equal(view['camera_pose'], torch.eye(4, dtype=torch.float32)[None]), 'A uses original identity input camera, no GT pose')
            require(bool(torch.isnan(view['ray_map']).all()), 'Original unused raymap remains NaN')
            view_arrays[f'img_{index}'] = view['img'].numpy().copy()
            view_arrays[f'shape_{index}'] = view['true_shape'].numpy().copy()
        np.savez_compressed(out / 'preprocessing.npz', **view_arrays)
        write(out / 'inputs_seal.json', dict(contract_sha256=c['_sha'], window=window_id, frames=window['frames'],
              selection_sha256=c['selection_sha256'], preprocessing_sha256=sha(out/'preprocessing.npz'),
              camera_input='original identity per view, no GT camera/ray input', source_proof=source_proof))
        allowed = [DictConfig, ContainerMetadata, Any, dict, defaultdict, AnyNode, Metadata]
        unsafe = torch.serialization.get_unsafe_globals_in_checkpoint(c['checkpoint'])
        require(set(unsafe) <= {f'{x.__module__}.{x.__qualname__}' for x in allowed}, 'Checkpoint serialization allowlist')
        load_log = io.StringIO(); started = time.perf_counter()
        with contextlib.redirect_stdout(load_log), torch.serialization.safe_globals(allowed):
            model = ARCroco3DStereo.from_pretrained(c['checkpoint']).float().to('cpu')
        (out / 'checkpoint_load.txt').write_text(load_log.getvalue())
        require('All keys matched successfully' in load_log.getvalue(), 'Complete checkpoint key match')
        model.eval()  # Exact original VMem pipeline.py mode, not inherited S21 mode.
        require(not any(m.training for m in model.modules()), 'All modules in original eval mode')
        require(all(p.dtype == torch.float32 and p.device.type == 'cpu' for p in model.parameters()), 'CPU FP32 model')
        for name, child in model.named_modules():
            if isinstance(child, RoPE2D):
                require(child.F0 == child.cpu_impl.F0 == 1.0 and child.base == child.cpu_impl.base == 100.0 and isinstance(child.cpu_impl, RoPE2DPyTorch), 'Frozen CPU RoPE runtime class/constants: ' + name)
        receipt.update(model_load_seconds=time.perf_counter()-started, training_flag=model.training,
                       model_class=type(model).__module__+'.'+type(model).__qualname__, weights_only=True,
                       torch_version=torch.__version__, numpy_version=np.__version__)
        counters = dict(model_calls=0, state_initializations=0, downstream_head_calls=0)
        cpu_rope_calls = 0
        def rope_done(_module, _inputs, _output):
            nonlocal cpu_rope_calls
            cpu_rope_calls += 1
        saved, captured = [], []
        original_init = model._init_state
        def observed_init(*args, **kwargs):
            counters['state_initializations'] += 1
            require(counters['state_initializations'] == 1, 'Single new recurrent state initialization')
            return original_init(*args, **kwargs)
        def model_done(*args): counters['model_calls'] += 1
        def head_done(_module, _inputs, prediction):
            index = counters['downstream_head_calls']; require(index < 4, 'No extra frame forward')
            require(set(prediction) == set(a.SHAPES), 'Exactly six original heads')
            arrays = {}
            for name, shape in a.SHAPES.items():
                value = prediction[name].detach().cpu().numpy().copy()
                require(value.shape == shape and value.dtype == np.float32 and np.isfinite(value).all(), 'Complete finite FP32 head: ' + name)
                if name in ('conf', 'conf_self'): require((value > 0).all(), 'Positive original confidence')
                arrays[name] = value
            path = out / f'frame_{index:04d}.npz'
            np.savez_compressed(path, **arrays)
            captured.append(arrays); saved.append(dict(index=index, path=str(path), sha256=sha(path), source_rgb_sha256=window['frames'][index]['sha256'], anchor_local_index=0))
            counters['downstream_head_calls'] += 1
            receipt.update(frames_completed=len(saved), counts=dict(counters), last_frame_utc=utc())
            write(out / 'receipt.json', receipt)
        model._init_state = observed_init
        mh = model.register_forward_hook(model_done); hh = model.downstream_head.register_forward_hook(head_done)
        rh = [child.register_forward_hook(rope_done) for child in model.modules() if isinstance(child, RoPE2DPyTorch)]
        require(len(rh) > 0, 'Bound CPU RoPE modules must exist')
        started = time.perf_counter()
        try:
            outputs, state_args = inference(views, model, 'cpu', verbose=False)
        finally:
            mh.remove(); hh.remove(); model._init_state = original_init
            for handle in rh: handle.remove()
        require(counters == dict(model_calls=1, state_initializations=1, downstream_head_calls=4), 'Exactly one fresh4 model call')
        require(cpu_rope_calls > 0, 'Actual frozen CPU RoPE path used')
        require(len(outputs['views']) == len(outputs['pred']) == 4 and len(state_args) == 5, 'Full original state/return length')
        for index, prediction in enumerate(outputs['pred']):
            require(set(prediction) == set(a.SHAPES), 'Return six-head set')
            for name in a.SHAPES:
                value = prediction[name].detach().cpu().numpy()
                require(value.dtype == captured[index][name].dtype and value.shape == captured[index][name].shape and value.tobytes() == captured[index][name].tobytes(), 'Saved vs returned head bytes')
        star = a.assemble_saved_output(ns, outputs['views'], outputs['pred'])
        for edge, index in enumerate((1, 2, 3)):
            for side, name, source_index in [('pred1', 'pts3d_in_self_view', 0), ('pred1', 'conf_self', 0), ('pred2', 'pts3d_in_other_view', index), ('pred2', 'conf', index)]:
                actual = star[side][name][edge:edge+1].detach().cpu().numpy()
                require(actual.tobytes() == captured[source_index][name].tobytes(), 'Actual star head identity')
        loaded = {}; embedded = Path(c['binding']['embedded_root']).resolve()
        for name, obj in list(sys.modules.items()):
            if name.startswith(('dust3r.', 'src.dust3r.', 'models.', 'croco.', 'cloud_opt.')):
                origin = getattr(obj, '__file__', None)
                if origin:
                    p = Path(origin).resolve()
                    require(p.is_relative_to(embedded) and c['binding']['source_identities'].get(str(p)) == sha(p), 'Loaded geometry namespace/source mismatch: ' + name)
                    loaded[name] = str(p)
        for p, identity in c['identities'].items(): require(sha(p) == identity, 'Source/selection changed during inference')
        for frame in window['frames']: require(sha(frame['path']) == frame['sha256'], 'RGB changed during inference')
        checkpoint = Path(c['checkpoint'])
        require([checkpoint.stat().st_size, checkpoint.stat().st_mtime_ns] == c['checkpoint_stat'], 'Checkpoint stat changed during inference')
        write(out / 'head_archive_records.json', saved)
        receipt.update(status='PASS_INFERENCE_SEALED', completed_utc=utc(), counts=counters, frames_completed=4,
                       inference_with_archival_seconds=time.perf_counter()-started, state_history_entries=5,
                       cpu_rope_calls=cpu_rope_calls, cpu_rope_source=c['cpu_rope_source'],
                       full_saved_return_head_comparisons=24, actual_star_edges=[[0,1],[0,2],[0,3]], actual_star_tensor_comparisons=12,
                       loaded_geometry_modules=loaded, preprocessing_input_identity_passed=True,
                       outputs={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='receipt.json'})
        write(out / 'receipt.json', receipt)
        print(json.dumps(dict(window=window_id, status=receipt['status'], counts=counters)), flush=True)
    except BaseException as error:
        receipt.update(status='FAILED', failed_utc=utc(), error=repr(error))
        write(out / 'receipt.json', receipt); (out / 'traceback.txt').write_text(traceback.format_exc()); raise


def dispatch(c, path):
    b = module(c['supervisor_source'], 's32_existing_supervisor')
    b.WORK = Path(c['execution_root']); b.WORK.mkdir(parents=True, exist_ok=True)
    target = b.WORK / 'dispatch_receipt.json'; require(not target.exists(), 'No automatic repeated A dispatch')
    receipt = dict(status='RUNNING', phase='A_inference_only', started_utc=utc(), contract_sha256=c['_sha'], completed_windows=[])
    write(target, receipt)
    try:
        for window in c['windows']:
            command = [sys.executable, str(Path(__file__).resolve()), 'worker', '--window', window['id'], '--contract', str(path), '--sha256', c['_sha']]
            b.supervised(command, window['id'], 180, 16*1024**3)
            produced = read(Path(c['output_root']) / window['id'] / 'receipt.json')
            require(produced['status'] == 'PASS_INFERENCE_SEALED' and produced['contract_sha256'] == c['_sha'], 'Sealed window producer')
            receipt['completed_windows'].append(window['id']); write(target, receipt)
        receipt.update(status='PASS_A_INFERENCE_ONLY', completed_utc=utc(), frames=16, model_calls=4, GA_calls=0, GT_reads=0,
                       next_stage='B is a separate unimplemented/unfrozen stage; no optimization or accuracy conclusion')
        write(target, receipt)
    except BaseException as error:
        receipt.update(status='FAILED', failed_utc=utc(), error=repr(error)); write(target, receipt); raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['dispatch', 'worker']); parser.add_argument('--window')
    parser.add_argument('--contract', required=True); parser.add_argument('--sha256', required=True)
    args = parser.parse_args(); frozen = contract(args.contract, args.sha256)
    if args.command == 'worker': worker(frozen, args.window)
    else: dispatch(frozen, args.contract)
