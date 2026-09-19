#!/usr/bin/env python3
"""S87: six fixed derivatives; VAE only, no target reference or scorer."""
import argparse
import ast
import gc
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import random
import resource
import shutil
import signal
import socket
import sys
import time
import traceback
import types
from datetime import datetime, timezone
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ORDER = ['Gpaste_l050', 'Gterminal_l050', 'Gpaste_l075', 'Gterminal_l075',
         'Gpaste_l100', 'Gterminal_l100']
TARGETS = [20, 21, 22, 23]


def require(ok, message):
    if not bool(ok):
        raise RuntimeError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()


def write(path, value):
    data = encoded(value)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_bytes(data)
    temporary.replace(path)
    return dict(path=str(path), sha256=sha(data), bytes=len(data))


def array_info(a):
    require(a.flags.c_contiguous, 'Non-contiguous descriptor')
    return dict(shape=list(a.shape), dtype=str(a.dtype), body_bytes=a.nbytes,
                body_sha256=sha(memoryview(a).cast('B')))


def load_functions(source, names, namespace, filename):
    """Compile unchanged named AST nodes, without module imports/top-level code."""
    tree = ast.parse(source, filename)
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    require({n.name for n in nodes} == set(names), 'Requested original functions absent')
    exec(compile(ast.Module(body=nodes, type_ignores=[]), filename, 'exec'), namespace)
    return types.SimpleNamespace(**{name: namespace[name] for name in names})


def paste(raw, warp, mask, strength, torch):
    require(raw.shape == warp.shape and mask.shape == (len(raw), 1, *raw.shape[-2:]),
            'RGB mixture shape')
    require(raw.dtype == warp.dtype == torch.float32 and mask.dtype == torch.bool,
            'RGB mixture dtype')
    require(strength in (0.5, 0.75, 1.0), 'Unregistered RGB strength')
    rgb01 = torch.stack([(f + 1) / 2 if f.min() < -0.1 else f for f in raw]).clamp(0, 1)
    weight = mask.to(torch.float32) * strength
    return torch.where(weight > 0, (1 - weight) * rgb01 + weight * warp, rgb01)


def quantize(raw, np):
    """Original util.tensor_to_pil arithmetic on FP32; no Pillow round trip."""
    require(raw.ndim == 4 and raw.shape[1] == 3 and raw.dtype == np.float32
            and np.isfinite(raw).all(), 'Raw emission shape/dtype/finite')
    frames, branches = [], []
    for i, frame in enumerate(raw):
        minimum, maximum = float(frame.min()), float(frame.max())
        mapped = minimum < -0.1
        image = frame.transpose(1, 2, 0)
        if mapped:
            image = (image + 1) / 2.0
        frames.append(np.clip(image * 255, 0, 255).astype(np.uint8))
        branches.append(dict(target_id=TARGETS[i] if len(raw) == 4 else i,
                             raw_min=minimum, raw_max=maximum, maps_minus1_plus1=mapped))
    return np.stack(frames), branches


def run(contract_sha256):
    start = time.monotonic()
    out = HERE / 'execution_01'
    out.mkdir()  # Existing success or failure is never overwritten or retried.
    report = dict(schema='s87-generation-v1', status='RUNNING', started_utc=now(),
                  contract_sha256=contract_sha256, executable_sha256=sha(Path(__file__).read_bytes()),
                  order=ORDER, target_ids=TARGETS, reads=[], arms={}, arm_receipts={}, counts=dict(
                      vae_loads=0, encoder_calls=0, denoiser_calls=0, decoder_calls=0,
                      decoder_chunks=0, completed_decoder_chunks=0, paste_calls=0),
                  reference_reads=0, new_method_validated=False, unrun_arms=ORDER.copy())
    progress_path = out / 'progress.jsonl'
    progress_file = progress_path.open('x', buffering=1)
    active = None
    arm_start = None
    rng_before = None
    cfg = None
    np = torch = None

    def progress(event, **detail):
        row = dict(utc=now(), elapsed_seconds=time.monotonic() - start,
                   arm=active, arm_elapsed_seconds=None if arm_start is None else time.monotonic() - arm_start,
                   event=event, pid=os.getpid(), **detail)
        progress_file.write(json.dumps(row, allow_nan=False) + '\n')
        progress_file.flush()
        write(out / 'RECEIPT.json', report)

    def budget():
        require(time.monotonic() - start <= 600, 'Total 600s exceeded')
        if active and active.startswith('Gterminal') and arm_start is not None:
            require(time.monotonic() - arm_start <= 120, 'Terminal 120s exceeded')
        require(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss <= 16 * 1024**3,
                'Peak self RSS exceeded 16GiB (macOS bytes)')
        output_bytes = sum(p.stat().st_size for p in out.rglob('*') if p.is_file() and not p.is_symlink())
        report['output_bytes'] = output_bytes
        require(output_bytes <= 1024**3, 'New output exceeded 1GiB')

    def bound(spec, role):
        p = Path(spec['path'])
        progress('read_start', path=str(p), role=role)
        data = p.read_bytes()
        expected = spec.get('sha256', spec.get('file_sha256'))
        size = spec.get('bytes', spec.get('size'))
        entry = dict(path=str(p), role=role, utc=now(), bytes=len(data), sha256=sha(data))
        report['reads'].append(entry)
        require(entry['sha256'] == expected and (size is None or len(data) == size),
                'Input identity mismatch: ' + str(p))
        budget()
        return data

    def save_array(path, a):
        a = np.ascontiguousarray(a)
        with path.open('xb') as stream:
            np.save(stream, a, allow_pickle=False)
        item = dict(path=str(path), file_sha256=sha(path.read_bytes()), **array_info(a))
        budget()
        return item

    def load_array(spec, role):
        data = bound(spec, role)
        a = np.ascontiguousarray(np.load(io.BytesIO(data), allow_pickle=False))
        require(array_info(a) == {k: spec[k] for k in array_info(a)}, role + ' array descriptor')
        require(np.isfinite(a).all(), role + ' nonfinite')
        return torch.from_numpy(a)

    def load_npz(spec, role):
        data = bound(spec, role)
        with np.load(io.BytesIO(data), allow_pickle=False) as z:
            require(set(z.files) == set(spec['fields']), role + ' key set')
            values = {k: np.ascontiguousarray(z[k]) for k in z.files}
        for key, a in values.items():
            require(array_info(a) == spec['fields'][key] and np.isfinite(a).all(),
                    role + '/' + key + ' descriptor/finite')
        return {k: torch.from_numpy(a) for k, a in values.items()}

    def rng_capture(label):
        n = np.random.get_state()
        meta = dict(python=random.getstate(), numpy=dict(engine=n[0], keys=n[1].tolist(),
                    position=n[2], has_gauss=n[3], cached_gaussian=n[4]))
        state = torch.get_rng_state().clone().numpy()
        torch_descriptor = save_array(out / ('rng_' + label + '_torch.npy'), state)
        metadata_descriptor = write(out / ('rng_' + label + '.json'), meta)
        return dict(torch_cpu=torch_descriptor, python_numpy=metadata_descriptor,
                    state_sha256=sha(encoded(meta) + state.tobytes()))

    def stopped(signum, frame):
        raise RuntimeError('Stopped by signal ' + str(signum))

    signal.signal(signal.SIGTERM, stopped)
    signal.signal(signal.SIGINT, stopped)
    try:
        require(shutil.disk_usage(out).free >= 2 * 1024**3, 'Initial free disk below2GiB')
        raw_contract = (HERE / 'GENERATION_CONTRACT.json').read_bytes()
        require(sha(raw_contract) == contract_sha256, 'Contract SHA mismatch')
        cfg = json.loads(raw_contract)
        require(report['executable_sha256'] == cfg['runner_sha256'], 'Runner SHA mismatch')
        require(cfg['order'] == ORDER and cfg['strengths'] == [0.5, 0.75, 1.0], 'Frozen strategy grid')
        report['arms'] = {s['name']: dict(family=s['family'], strength=s['strength'],
                         status='NOT_RUN', arrays={}, terminal={}, quantizer=[]) for s in cfg['strategies']}
        report['image_mask'] = cfg['inputs']['image_mask']
        report['source_inputs'] = cfg['inputs']
        report['vae_identity'] = cfg['vae']
        report['variant'] = cfg['variant']
        report['source_bindings'] = cfg['sources']
        for name, spec in cfg['metadata'].items():
            bound(spec, 'metadata_' + name)
        sources = {name: bound(spec, 'source_' + name).decode() for name, spec in cfg['sources'].items()}
        os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', DIFFUSERS_OFFLINE='1',
                          OMP_NUM_THREADS='8', MKL_NUM_THREADS='8', TOKENIZERS_PARALLELISM='false',
                          HF_HUB_DISABLE_IMPLICIT_TOKEN='1', PYTHONDONTWRITEBYTECODE='1')
        sys.dont_write_bytecode = True
        sys.path[:0] = cfg['pythonpath']

        def offline(*args, **kwargs):
            raise RuntimeError('S87 has no network inputs')

        socket.socket.connect = socket.socket.connect_ex = socket.create_connection = offline
        import numpy as np
        import torch
        versions = {name: importlib.metadata.version(name) for name in cfg['versions']}
        require(versions == cfg['versions'], 'Runtime package version mismatch')
        report['versions'] = versions
        report['python'] = sys.version
        require(sys.version.split()[0] == cfg['python_version'] and sys.platform == 'darwin',
                'Expected frozen macOS Python version')
        torch.set_num_threads(8)
        torch.set_num_interop_threads(1)
        torch.set_default_dtype(torch.float32)
        report['runtime'] = dict(device='cpu', dtype='float32', threads=torch.get_num_threads(),
                                 interop=torch.get_num_interop_threads())
        sampling = load_functions(sources['sampling'], ['append_dims', 'to_d'],
                                  {'torch': torch}, cfg['sources']['sampling']['path'])
        hooks, fusion = {}, {}
        exec(compile(sources['hooks'], cfg['sources']['hooks']['path'], 'exec'), hooks)
        exec(compile(sources['fusion'], cfg['sources']['fusion']['path'], 'exec'), fusion)
        replay = hooks['replay_last']
        fuse = fusion['fuse_clean_prediction']
        source_last = load_npz(cfg['inputs']['last_step'], 'G0_last7')
        encoded_warp = load_npz(cfg['inputs']['encoded_warp'], 'fixed_encoded_warp')
        last = dict(source_last, **cfg['last_metadata'])
        raw_g0 = load_array(cfg['inputs']['g0_raw'], 'G0_raw')
        g0_latents = load_array(cfg['inputs']['g0_latents'], 'G0_all8_latents')
        warp = load_array(cfg['inputs']['warp_rgb'], 'warp_rgb')
        mask = load_array(cfg['inputs']['image_mask'], 'image_mask')
        W, m, history = (encoded_warp[k] for k in ('warp_latents', 'support_mask', 'history_slots'))
        same = lambda a, b: a.contiguous().numpy().tobytes() == b.contiguous().numpy().tobytes()
        require(last['mode'] == 'G0' and last['step'] == 50 and last['complete'] and last['gamma'] == 0,
                'Original last metadata')
        require((last['next_sigma'] == 0).all() and (last['sigma_hat'] > 0).all(), 'Original sigmas')
        require(same(last['raw_clean'], last['used_clean']) and same(last['output'], g0_latents),
                'Original clean/output consistency')
        require(history.tolist() == [True] * 4 + [False] * 4 and (W[:4] == 0).all()
                and (m[:4] == 0).all() and ((m >= 0) & (m <= 1)).all(), 'Warp/history identity')
        require(((warp >= 0) & (warp <= 1)).all()
                and (warp.masked_select(~mask.expand_as(warp)) == 0).all(), 'RGB warp range/holes')
        require(same(m[4:], torch.nn.functional.avg_pool2d(mask.float(), 8, 8)), 'Saved avg8 mask')
        protected = ((m == 0) | history[:, None, None, None]).expand_as(last['raw_clean'])
        budget()

        # S70's exact local ft-mse loader, restricted to the original VAE wrapper.
        import safetensors.torch
        from diffusers.models import AutoencoderKL
        wrapper = {}
        exec(compile(sources['autoencoder'], cfg['sources']['autoencoder']['path'], 'exec'), wrapper)
        local = out / 'local_vae'
        local.mkdir()
        (local / 'config.json').write_bytes(bound(cfg['vae']['config'], 'vae_config'))
        weight = cfg['vae']['weight']
        (local / 'diffusion_pytorch_model.safetensors').symlink_to(weight['path'])
        held = [bound(weight, 'vae_weight')]
        loader_calls = []
        original_load = AutoencoderKL.from_pretrained

        def tensor_load(filename, device='cpu'):
            require(Path(filename).resolve() == Path(weight['path']).resolve()
                    and str(device) == 'cpu' and len(held) == 1, 'Unexpected VAE weight consumer')
            loader_calls.append(str(filename))
            return safetensors.torch.load(held.pop())

        def local_load(repo, *args, **kwargs):
            require(repo == 'stabilityai/stable-diffusion-2-1-base' and not args and
                    kwargs == dict(subfolder='vae', force_download=False, low_cpu_mem_usage=False),
                    'Original VAE constructor changed')
            result, loading = original_load(str(local), local_files_only=True, force_download=False,
                low_cpu_mem_usage=False, use_safetensors=True, output_loading_info=True)
            report['vae_loading_info'] = loading
            require(not any(loading.get(k) for k in ('missing_keys', 'unexpected_keys',
                    'mismatched_keys', 'error_msgs')), 'Incomplete VAE weights')
            return result

        load_start = time.monotonic()
        report['counts']['vae_loads'] += 1
        progress('vae_load_start')
        with patch.object(safetensors.torch, 'load_file', tensor_load), \
             patch.object(AutoencoderKL, 'from_pretrained', local_load):
            ae = wrapper['AutoEncoder'](chunk_size=1)
        require(len(loader_calls) == 1 and not held, 'Exactly one bound weight deserialization')
        ae = ae.cpu().float().eval().requires_grad_(False)
        require('modeling.network' not in sys.modules and 'modeling.pipeline' not in sys.modules,
                'Unexpected original VMem network/pipeline import')
        report['components_loaded'] = ['VAE_only']
        require(ae.scale_factor == 0.18215 and ae.chunk_size == 1, 'VAE scale/chunk changed')
        report['vae_load_seconds'] = time.monotonic() - load_start
        report['vae_weight_consumers'] = loader_calls
        gc.collect()
        model_versions = [(name, id(t), t.data_ptr(), t._version) for name, t in ae.state_dict(keep_vars=True).items()]
        require(all(not t.requires_grad and t.device.type == 'cpu' and
                    (not t.is_floating_point() or t.dtype == torch.float32)
                    for t in ae.state_dict(keep_vars=True).values()), 'VAE freeze/CPU/FP32')
        require(all(not module.training for module in ae.modules()), 'VAE not eval')
        rng_before = rng_capture('after_load')
        report['rng_after_load'] = rng_before
        original_decode = ae._decode

        def observed_decode(z):
            require(z.shape == (1, 4, 72, 72), 'Full-eight chunk1 shape changed')
            budget()
            chunk_start = time.monotonic()
            report['counts']['decoder_chunks'] += 1
            report['arms'][active]['decoder_chunks'] += 1
            progress('decoder_chunk_start', chunk=report['arms'][active]['decoder_chunks'])
            result = original_decode(z)
            require(result.shape == (1, 3, 576, 576) and result.dtype == torch.float32
                    and torch.isfinite(result).all(), 'Decoder result shape/dtype/finite')
            report['counts']['completed_decoder_chunks'] += 1
            report['arms'][active]['completed_decoder_chunks'] += 1
            progress('decoder_chunk_end', seconds=time.monotonic() - chunk_start)
            budget()
            return result

        ae._decode = observed_decode
        progress('vae_loaded')
        with torch.inference_mode(), torch.autocast(device_type='cpu', enabled=False):
            for spec in cfg['strategies']:
                active = spec['name']
                arm_start = time.monotonic()
                arm = report['arms'][active]
                adir = out / active
                adir.mkdir()
                arm.update(status='RUNNING', started_utc=now(), decoder_calls=0,
                           decoder_chunks=0, completed_decoder_chunks=0)
                report['unrun_arms'].remove(active)
                progress('arm_start')
                budget()
                if spec['family'] == 'Gpaste':
                    report['counts']['paste_calls'] += 1
                    targets = paste(raw_g0, warp, mask, spec['strength'], torch)
                else:
                    derived = replay(sampling, last, fusion_fn=fuse, warp_latents=W,
                                     support_mask=m, history_slots=history, strength=spec['strength'])
                    require(same(derived['clean_used'][protected], last['raw_clean'][protected]),
                            'Protected clean bytes changed')
                    require(same(derived['latents'][protected], g0_latents[protected]),
                            'Protected final latent bytes changed')
                    require(all(v.dtype == torch.float32 and torch.isfinite(v).all()
                                for v in derived.values()), 'Derived nonfinite/dtype')
                    arm['protected_clean_bytes_exact'] = True
                    arm['protected_latent_bytes_exact'] = True
                    arm['terminal']['clean_used'] = save_array(adir / 'clean_used.npy', derived['clean_used'].numpy())
                    arm['terminal']['all8_latents'] = save_array(adir / 'all8_latents.npy', derived['latents'].numpy())
                    report['counts']['decoder_calls'] += 1
                    arm['decoder_calls'] += 1
                    decoded = ae.decode(derived['latents'], 1)
                    require(decoded.shape == (8, 3, 576, 576), 'Full-eight decode shape')
                    targets = decoded[4:].contiguous()
                require(targets.shape == (4, 3, 576, 576) and targets.dtype == torch.float32
                        and torch.isfinite(targets).all(), 'Target output finite/schema')
                raw = np.ascontiguousarray(targets.numpy())
                arm['arrays']['targets_fp32'] = save_array(adir / 'targets_fp32.npy', raw)
                emitted, branches = quantize(raw, np)
                arm['arrays']['targets_uint8'] = save_array(adir / 'targets_uint8.npy', emitted)
                arm['quantizer'] = branches
                budget()
                arm.update(status='COMPLETE_DERIVED', completed_utc=now(),
                           elapsed_seconds=time.monotonic() - arm_start)
                report['arm_receipts'][active] = write(adir / 'receipt.json', arm)
                progress('arm_complete', seconds=arm['elapsed_seconds'])
                del targets, raw, emitted
                if spec['family'] == 'Gterminal':
                    del decoded, derived
                active, arm_start = None, None
        report['rng_end'] = rng_capture('end')
        report['derived_rng_unchanged'] = rng_before['state_sha256'] == report['rng_end']['state_sha256']
        require(report['derived_rng_unchanged'], 'Derived phase consumed RNG')
        require(model_versions == [(name, id(t), t.data_ptr(), t._version)
                    for name, t in ae.state_dict(keep_vars=True).items()], 'VAE tensors changed')
        report['model_identity_versions_unchanged'] = True
        require(report['counts'] == dict(vae_loads=1, encoder_calls=0, denoiser_calls=0,
                    decoder_calls=3, decoder_chunks=24, completed_decoder_chunks=24, paste_calls=3),
                'Complete-call census mismatch')
        budget()
        report.update(status='COMPLETE_SIX_DERIVED_CONTROLS_PENDING_REVIEW', completed_utc=now())
        progress('complete')
        return_code = 0
    except BaseException as error:
        report.update(status='FAILED_STOPPED_NO_RETRY', failed_utc=now(),
                      error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc())
        if active is not None:
            report['arms'][active].update(status='FAILED', error=str(error), failed_utc=now(),
                                         elapsed_seconds=time.monotonic() - arm_start)
            report['arm_receipts'][active] = write(out / active / 'receipt.json', report['arms'][active])
        if rng_before is not None and 'rng_end' not in report:
            try:
                report['rng_end'] = rng_capture('end')
                report['derived_rng_unchanged'] = rng_before['state_sha256'] == report['rng_end']['state_sha256']
            except BaseException as rng_error:
                report['rng_end_error'] = str(rng_error)
        progress('failure', error=str(error))
        return_code = 1
    finally:
        report['elapsed_seconds'] = time.monotonic() - start
        report['peak_self_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        progress_file.close()
        report['progress_sha256'] = sha(progress_path.read_bytes())
        report['output_bytes_before_final_receipt'] = sum(p.stat().st_size for p in out.rglob('*')
                                                        if p.is_file() and not p.is_symlink())
        write(out / 'RECEIPT.json', report)
    return return_code


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--contract-sha256', required=True)
    args = parser.parse_args()
    sys.exit(run(args.contract_sha256))
