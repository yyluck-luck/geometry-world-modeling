#!/usr/bin/env python3
"""S70: three fixed contexts through original VMem sampling; no retrieval or reference RGB."""
import ast
import gc
import hashlib
import importlib.metadata
import io
import json
import math
import os
from pathlib import Path
import random
import resource
import shutil
import socket
import sys
import time
import traceback
import types
from datetime import datetime, timezone
from unittest.mock import patch

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
HERE = ROOT / 'work/S70_fixed_context_generation'
ORIGINAL = ROOT / 'work/S20_environment/isolated_vmem_source'
INPUT_SHA = '2a5551e348f1f389ef44ca6fac7d47e8853b44772884cbd38cecb0064a6e80e7'
FIELDS = ('crossattn', 'replace', 'concat', 'dense_vector')


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def write_json(path, value):
    data = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False).encode() + b'\n'
    with Path(path).open('xb') as stream:
        stream.write(data)
    return {'path': str(path), 'sha256': sha(data), 'size_bytes': len(data)}


def read_bound(path, digest, reads, kind, size=None):
    data = Path(path).read_bytes()
    actual = sha(data)
    reads.append(dict(path=str(path), kind=kind, bytes=len(data), sha256=actual))
    require(actual == digest and (size is None or len(data) == size), f'Input identity: {path}')
    return data


def load_code(manifest, reads):
    """Only original module definitions, no modeling.__init__, pipeline or model construction."""
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                      HF_HUB_DISABLE_IMPLICIT_TOKEN='1', PYTHONDONTWRITEBYTECODE='1',
                      OMP_NUM_THREADS='8', MKL_NUM_THREADS='8', MPLBACKEND='Agg')
    sys.dont_write_bytecode = True
    sys.path[:0] = manifest['pythonpath']

    def offline(*args, **kwargs):
        raise RuntimeError('This worker has no network inputs')
    socket.socket.connect = offline
    socket.socket.connect_ex = offline
    socket.create_connection = offline
    import numpy as np
    import torch
    from PIL import Image
    versions = {k: importlib.metadata.version(k) for k in manifest['versions']}
    require(versions == manifest['versions'], 'Runtime versions differ')
    require(sys.version_info[:2] == (3, 12) and sys.platform == 'darwin', 'Expected macOS Python3.12')
    sources = {p: read_bound(p, h, reads, 'original_source')
               for p, h in manifest['source_sha256'].items()}
    for name in ('modeling', 'modeling.modules'):
        require(name not in sys.modules, f'Unexpected preloaded namespace: {name}')
        module = types.ModuleType(name)
        module.__path__ = []
        module.__package__ = name
        sys.modules[name] = module
        if '.' in name:
            setattr(sys.modules['modeling'], 'modules', module)
    modules = {}
    for name, relative in [('modeling.modules.transformer', 'modeling/modules/transformer.py'),
                           ('modeling.modules.layers', 'modeling/modules/layers.py'),
                           ('modeling.network', 'modeling/network.py'),
                           ('modeling.sampling', 'modeling/sampling.py'),
                           ('modeling.modules.autoencoder', 'modeling/modules/autoencoder.py')]:
        path = ORIGINAL / relative
        module = types.ModuleType(name)
        module.__file__ = str(path)
        module.__package__ = name.rpartition('.')[0]
        sys.modules[name] = module  # dataclass resolution requires registration before exec.
        setattr(sys.modules[module.__package__], name.rpartition('.')[2], module)
        exec(compile(sources[str(path)], str(path), 'exec'), module.__dict__)
        modules[name] = module
    path = ORIGINAL / 'utils/util.py'
    tree = ast.parse(sources[str(path)], filename=str(path))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef)
             and n.name in {'do_sample', 'tensor_to_pil'}]
    require({n.name for n in nodes} == {'do_sample', 'tensor_to_pil'}, 'Original helper closure missing')
    env = dict(torch=torch, np=np, Image=Image, math=math)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), env)
    require('modeling.pipeline' not in sys.modules and 'open_clip' not in sys.modules,
            'Unexpected full pipeline or CLIP import')
    return np, torch, modules, env, versions


def load_models(manifest, reads, modules, torch, out, report, progress):
    import safetensors.torch
    from diffusers.models import AutoencoderKL
    network = modules['modeling.network']
    component = manifest['components']['vmem']
    progress('load', detail='vmem verified bytes and original constructor')
    blob = read_bound(component['path'], component['sha256'], reads, 'vmem_weight', component['size'])
    state = torch.load(io.BytesIO(blob), map_location='cpu', weights_only=True)
    state = {k.replace('module.', '') if 'module.' in k else k: v for k, v in state.items()}
    raw = network.VMemModel(network.VMemModelParams())
    info = raw.load_state_dict(state, strict=True)
    require(not info.missing_keys and not info.unexpected_keys, 'VMem incomplete weights')
    model = network.VMemWrapper(raw).cpu().float().eval().requires_grad_(False)
    report['vmem_loading_info'] = {'missing_keys': list(info.missing_keys),
                                  'unexpected_keys': list(info.unexpected_keys)}
    del blob, state
    gc.collect()
    progress('load', detail='declared ft-mse VAE verified bytes and original constructor')
    config = manifest['components']['vae_config']
    local = out / 'local_vae'
    local.mkdir()
    config_data = read_bound(config['path'], config['sha256'], reads, 'vae_config', config['size'])
    (local / 'config.json').write_bytes(config_data)
    weight = manifest['components']['vae_weight']
    (local / 'diffusion_pytorch_model.safetensors').symlink_to(weight['path'])
    held = [read_bound(weight['path'], weight['sha256'], reads, 'vae_weight', weight['size'])]
    original_load = AutoencoderKL.from_pretrained
    calls = []

    def tensor_load(filename, device='cpu'):
        require(Path(filename).resolve() == Path(weight['path']).resolve() and str(device) == 'cpu'
                and len(held) == 1, 'Unexpected VAE weight consumer')
        calls.append(str(filename))
        return safetensors.torch.load(held.pop())

    def local_load(repo, *args, **kwargs):
        require(repo == 'stabilityai/stable-diffusion-2-1-base' and not args and
                kwargs == dict(subfolder='vae', force_download=False, low_cpu_mem_usage=False),
                'Original VAE constructor call differs')
        result, loading = original_load(str(local), local_files_only=True,
            force_download=False, low_cpu_mem_usage=False, use_safetensors=True, output_loading_info=True)
        report['vae_loading_info'] = loading
        require(not any(loading.get(k) for k in
                        ('missing_keys', 'unexpected_keys', 'mismatched_keys', 'error_msgs')),
                'Incomplete declared VAE weights')
        return result

    with patch.object(safetensors.torch, 'load_file', tensor_load), \
         patch.object(AutoencoderKL, 'from_pretrained', local_load):
        ae = modules['modeling.modules.autoencoder'].AutoEncoder(chunk_size=1)
    require(len(calls) == 1 and not held, 'VAE did not consume exactly the bound bytes')
    ae = ae.cpu().float().eval().requires_grad_(False)
    report['vae_weight_decoder_calls'] = calls
    gc.collect()
    return model, ae


def array_info(array):
    require(array.flags.c_contiguous, 'Array descriptor needs C-contiguous bytes')
    return dict(shape=list(array.shape), dtype=str(array.dtype), body_bytes=array.nbytes,
                body_sha256=sha(memoryview(array).cast('B')))


def save_array(path, array, np):
    array = np.ascontiguousarray(array)
    with path.open('xb') as stream:
        np.save(stream, array, allow_pickle=False)
    return dict(path=str(path), file_sha256=sha(path.read_bytes()), **array_info(array))


def read_conditions(manifest, reads, np):
    results = {}
    for name, item in manifest['conditions'].items():
        data = read_bound(item['path'], item['sha256'], reads, 'saved_S69_conditions', item['size_bytes'])
        with np.load(io.BytesIO(data), allow_pickle=False) as archive:
            require(set(archive.files) == set(item['fields']), 'Condition field set changed')
            arrays = {k: np.ascontiguousarray(archive[k]) for k in archive.files}
        for key, value in arrays.items():
            require(array_info(value) == item['fields'][key] and np.isfinite(value).all(),
                    f'Condition descriptor/finite: {name}/{key}')
        require(arrays['ordered_ids'].tolist() == manifest['ordered_history_ids'][name] + [20,21,22,23],
                'Saved slot/source mapping differs')
        require(arrays['input_masks'].tolist() == [True]*4 + [False]*4, 'Target mask differs')
        results[name] = arrays
    return results


def model_snapshot(models, torch):
    values, identity, modes = [], [], []
    for label, model in models.items():
        for kind, iterator in [('parameter', model.named_parameters()), ('buffer', model.named_buffers())]:
            for name, value in iterator:
                require(value.device.type == 'cpu' and not value.requires_grad, 'Unfrozen/non-CPU model')
                require(not value.is_floating_point() or value.dtype == torch.float32, 'Model precision differs')
                array = value.detach().contiguous().numpy()
                values.append(dict(model=label, kind=kind, name=name, **array_info(array)))
                identity.append([label, kind, name, id(value), value.data_ptr(), value._version,
                                 value.requires_grad])
        for name, module in model.named_modules():
            modes.append([label, name, module.training])
            require(not module.training, 'Model entered training mode')
    return dict(value_sha256=sha(encoded(values)), identity_sha256=sha(encoded(identity)),
                modes_sha256=sha(encoded(modes)), values=values, identity=identity, modes=modes)


def rng_capture(np, torch):
    return random.getstate(), np.random.get_state(), torch.get_rng_state().clone()


def rng_json(state):
    py, num, tor = state
    return dict(python=py, numpy=dict(engine=num[0], keys=num[1].tolist(), position=num[2],
                                     has_gauss=num[3], cached_gaussian=num[4]), torch_cpu=tor.tolist())


def rng_sha(np, torch):
    return sha(encoded(rng_json(rng_capture(np, torch))))


def run():
    out = HERE / 'execution_01'
    out.mkdir()  # One create-only attempt. Existing failure/result is never overwritten.
    began = time.monotonic()
    reads, arms = [], {}
    report = dict(schema='s70-fixed-generation-receipt-v1', started_utc=utc(), status='RUNNING',
                  input_sha256=INPUT_SHA, executable_sha256=sha(Path(__file__).read_bytes()),
                  reads=reads, arms=arms, exact_replay_pass=False)
    progress_file = (out / 'progress.jsonl').open('x', buffering=1)
    arm_name, arm_start = None, None

    def progress(phase, step=None, **detail):
        row = dict(phase=phase, utc=utc(), elapsed_seconds=time.monotonic()-began,
                   arm=arm_name, step=step, pid=os.getpid(),
                   arm_elapsed_seconds=None if arm_start is None else time.monotonic()-arm_start, **detail)
        progress_file.write(json.dumps(row, allow_nan=False) + '\n')
        progress_file.flush()

    def budget():
        require(time.monotonic()-began <= 5520, 'Total 5520s budget exceeded')
        require(arm_start is None or time.monotonic()-arm_start <= 1800, 'Arm 1800s budget exceeded')
        require(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss <= 45*1024**3, 'Peak RSS exceeds45GiB')
        require(shutil.disk_usage(out).free >= 10*1024**3, 'Disk free below10GiB')

    try:
        progress('start')
        manifest = json.loads(read_bound(HERE/'INPUTS.json', INPUT_SHA, reads, 'input_metadata'))
        report.update(variant=manifest['variant'], controls=manifest['controls'],
                      claim_boundary=manifest['claim_boundary'], target_ids=manifest['target_ids'])
        for path, digest in manifest['metadata_sha256'].items():
            read_bound(path, digest, reads, 'accepted_metadata')
        np, torch, modules, util, versions = load_code(manifest, reads)
        report['versions'] = versions
        report['python_version'] = sys.version
        torch.set_num_threads(8)
        torch.set_num_interop_threads(1)
        torch.set_default_dtype(torch.float32)
        budget()
        conditions = read_conditions(manifest, reads, np)
        model, ae = load_models(manifest, reads, modules, torch, out, report, progress)
        budget()
        baseline = model_snapshot({'vmem': model, 'vae': ae}, torch)
        report['model_baseline'] = write_json(out/'model_baseline.json', baseline)
        baseline_checks = {k: baseline[k] for k in ('value_sha256','identity_sha256','modes_sha256')}
        del baseline
        random.seed(44)
        np.random.seed(44)
        torch.manual_seed(44)
        common = rng_capture(np, torch)
        common_hash = sha(encoded(rng_json(common)))
        report['common_rng'] = write_json(out/'common_rng.json', rng_json(common))
        report['common_rng_state_sha256'] = common_hash
        sampling = modules['modeling.sampling']
        for arm_name, key in manifest['arm_order']:
            arm_start = time.monotonic()
            arm_dir = out/arm_name
            arm_dir.mkdir()
            result = dict(schema='s70-arm-receipt-v1', arm=arm_name, condition=key, status='RUNNING',
                          started_utc=utc(), condition_npz_sha256=manifest['conditions'][key]['sha256'],
                          ordered_history_ids=manifest['ordered_history_ids'][key], target_ids=[20,21,22,23],
                          steps=[], arrays={})
            arms[arm_name] = result
            progress('arm_start', step=0)
            steps_file = (arm_dir/'steps.jsonl').open('x', buffering=1)
            state_changed = False
            try:
                budget()
                before = model_snapshot({'vmem': model, 'vae': ae}, torch)
                result['model_before'] = {k: before[k] for k in baseline_checks}
                require(result['model_before'] == baseline_checks, 'Model changed before arm')
                del before
                data = {k: torch.from_numpy(v.copy()) for k, v in conditions[key].items()}
                c = {f: data['c__'+f] for f in FIELDS}
                uc = {f: data['uc__'+f] for f in FIELDS}
                discretization = sampling.DDPMDiscretization()
                denoiser = sampling.DiscreteDenoiser(discretization, num_idx=1000, device='cpu')
                sampler = sampling.create_samplers(guider_types=1, discretization=discretization,
                    num_frames=8, num_steps=50, cfg_min=1.2, device='cpu')[0]
                require(type(sampler.guider).__name__ == 'MultiviewCFG', 'Wrong original guider')
                original_step = sampler.sampler_step

                def observed_step(*args, **kwargs):
                    budget()
                    step = len(result['steps']) + 1
                    entry = dict(step=step, started_utc=utc(), rng_before=rng_sha(np, torch))
                    try:
                        value = original_step(*args, **kwargs)
                    except Exception as error:
                        entry.update(failed_utc=utc(), rng_after=rng_sha(np, torch),
                                     error_type=type(error).__name__, error=str(error))
                        steps_file.write(json.dumps(entry) + '\n')
                        raise
                    entry.update(completed_utc=utc(), rng_after=rng_sha(np, torch),
                                 finite=bool(torch.isfinite(value).all()), shape=list(value.shape),
                                 dtype=str(value.dtype))
                    result['steps'].append(entry)
                    steps_file.write(json.dumps(entry) + '\n')
                    progress('step', step=step)
                    require(entry['finite'] and step <= 50, 'Invalid sampler step output/count')
                    budget()
                    return value

                sampler.sampler_step = observed_step
                sampler_calls = []

                def observed_sampler(denoiser_call, noise, **kwargs):
                    require(not sampler_calls, 'Original sampler called more than once')
                    sampler_calls.append(1)
                    result['noise'] = save_array(arm_dir/'noise.npy', noise.detach().cpu().numpy().copy(), np)
                    result['sampler_entry_rng'] = write_json(arm_dir/'sampler_entry_rng.json',
                                                             rng_json(rng_capture(np, torch)))
                    result['sampler_entry_rng_state_sha256'] = rng_sha(np, torch)
                    value = sampler(denoiser_call, noise, **kwargs)
                    result['arrays']['all8_latents'] = save_array(arm_dir/'all8_latents.npy',
                                                                  value.detach().cpu().numpy(), np)
                    return value

                random.setstate(common[0])
                np.random.set_state(common[1])
                torch.set_rng_state(common[2].clone())
                result['restored_rng_state_sha256'] = rng_sha(np, torch)
                require(result['restored_rng_state_sha256'] == common_hash, 'Actual RNG restore differs')
                samples, latents = util['do_sample'](model, ae, denoiser, observed_sampler,
                    c, uc, data['post_cond_optical_c2ws'], data['K_pixels_576'], data['input_masks'],
                    H=576, W=576, C=4, F=8, T=8, cfg=2.0, decoding_t=1,
                    verbose=True, global_pbar=None, return_latents=True, device='cpu')
                target = samples[~data['input_masks']]
                result['arrays']['targets_fp32'] = save_array(arm_dir/'targets_fp32.npy',
                                                                target.detach().cpu().numpy(), np)
                require(list(samples.shape) == [8,3,576,576] and samples.dtype == torch.float32
                        and bool(torch.isfinite(samples).all()), 'Full8 decode shape/precision/finite')
                require(list(latents.shape) == [8,4,72,72] and latents.dtype == torch.float32
                        and bool(torch.isfinite(latents).all()), 'Full8 latent shape/precision/finite')
                quantized = np.stack([np.array(util['tensor_to_pil'](frame)) for frame in target])
                result['arrays']['targets_uint8'] = save_array(arm_dir/'targets_uint8.npy', quantized, np)
                result['quantizer'] = [dict(target_id=i, raw_min=float(frame.min()),
                    maps_minus1_plus1=bool(frame.min() < -.1)) for i, frame in zip([20,21,22,23], target)]
                require(len(result['steps']) == 50 and len(sampler_calls) == 1, 'Incomplete50-step sampling')
                result.update(status='COMPLETE_ARM', full_decoded_shape=list(samples.shape),
                              full_decoded_dtype=str(samples.dtype), completed_steps=50, sampler_calls=1)
            except Exception as error:
                result.update(status='FAILED_ARM', error_type=type(error).__name__, error=str(error),
                              traceback=traceback.format_exc())
                progress('failure', step=len(result['steps']), error=str(error))
            finally:
                steps_file.close()
                result['terminal_rng'] = write_json(arm_dir/'terminal_rng.json', rng_json(rng_capture(np, torch)))
                result['terminal_rng_state_sha256'] = rng_sha(np, torch)
                try:
                    after = model_snapshot({'vmem': model, 'vae': ae}, torch)
                    result['model_after'] = {k: after[k] for k in baseline_checks}
                    state_changed = result['model_after'] != baseline_checks
                    del after
                except Exception as error:
                    state_changed = True
                    result['model_check_error'] = str(error)
                result['model_unchanged'] = not state_changed
                if state_changed:
                    result['status'] = 'FAILED_ARM_MODEL_CHANGED'
                result['completed_utc'] = utc()
                result['elapsed_seconds'] = time.monotonic()-arm_start
                result['outputs'] = write_json(arm_dir/'outputs.json', dict(schema='s70-arm-outputs-v1',
                    status=result['status'], arm=arm_name, target_ids=[20,21,22,23],
                    arrays=result['arrays'], quantizer=result.get('quantizer')))
                result['receipt'] = write_json(arm_dir/'receipt.json', result.copy())
                progress('arm_complete', step=len(result['steps']), status=result['status'])
            require(not state_changed, 'Mutable model state prevents remaining fixed arms')
            budget()
            # Release previous returned tensors/closure references before the next fixed arm.
            if result['status'] == 'COMPLETE_ARM':
                del samples, latents, target, quantized
            gc.collect()
        arm_name, arm_start = None, None
        complete = all(arms[n]['status'] == 'COMPLETE_ARM' for n in ('A0','A1','B'))
        if complete:
            signatures = {n: dict(noise=arms[n]['noise']['body_sha256'],
                entry_rng=arms[n]['sampler_entry_rng_state_sha256'],
                step_rng=[[s['rng_before'],s['rng_after']] for s in arms[n]['steps']],
                terminal_rng=arms[n]['terminal_rng_state_sha256']) for n in arms}
            report['shared_actual_random_stream_pass'] = signatures['A0'] == signatures['A1'] == signatures['B']
            report['exact_replay_fields'] = {k: arms['A0']['arrays'][k]['body_sha256'] ==
                arms['A1']['arrays'][k]['body_sha256'] for k in ('all8_latents','targets_fp32','targets_uint8')}
            report['exact_replay_pass'] = all(report['exact_replay_fields'].values())
            report['attributable_fixed_bundle_comparison'] = (
                report['shared_actual_random_stream_pass'] and report['exact_replay_pass'])
            require(report['shared_actual_random_stream_pass'], 'Actual shared noise/RNG differs')
            report['status'] = 'COMPLETE_THREE_FIXED_GENERATION_ARMS'
        else:
            report['status'] = 'FAILED_FIXED_GENERATION'
        budget()
    except Exception as error:
        report.update(status='FAILED_FIXED_GENERATION', error_type=type(error).__name__, error=str(error),
                      traceback=traceback.format_exc())
        progress('failure', error=str(error))
    finally:
        report.update(completed_utc=utc(), elapsed_seconds=time.monotonic()-began,
                      peak_self_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                      unrun_arms=[n for n in ('A0','A1','B') if n not in arms],
                      reference_rgb_body_bytes=0, reference_depth_body_bytes=0,
                      generated_rgb_viewed=False)
        report['readlist'] = write_json(out/'readlist.json', reads)
        progress('complete', status=report['status'])
        progress_file.close()
        report['progress_sha256'] = sha((out/'progress.jsonl').read_bytes())
        write_json(out/'receipt.json', report)
        for path in out.rglob('*'):
            if path.is_file() and not path.is_symlink():
                path.chmod(0o444)
    print(json.dumps({'status':report['status'], 'receipt':str(out/'receipt.json')}), flush=True)
    return 0 if report['status'] == 'COMPLETE_THREE_FIXED_GENERATION_ARMS' else 1


if __name__ == '__main__':
    if sys.argv[1:] == ['--check-imports']:
        checked_reads = []
        inputs = json.loads(read_bound(HERE/'INPUTS.json', INPUT_SHA, checked_reads, 'input_metadata'))
        _np, _torch, _modules, _util, _versions = load_code(inputs, checked_reads)
        print(json.dumps(dict(status='PASS_INERT_IMPORTS_ONLY', versions=_versions, reads=checked_reads,
                              model_instances=0, weight_bytes=0, condition_npz_bytes=0, rgb_bytes=0)))
    else:
        require(not sys.argv[1:], 'Only formal default or inert --check-imports is supported')
        raise SystemExit(run())
