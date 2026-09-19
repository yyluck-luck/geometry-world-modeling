"""Fixed five-source TUM appearance bridge. No pipeline, geometry or query pixels."""
from __future__ import annotations

import ast
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
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
from typing import Optional, Tuple, Union
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ORIGINAL = ROOT / 'work/S20_environment/isolated_vmem_source'
INPUT_SHA = 'f14621d1988566f0fb09d314e02e0736e352fbe0a49c1055249c0011a34454bc'
IDS = [12, 13, 14, 18, 19]
HELPERS = {'get_wh_with_fixed_shortest_side', 'get_resizing_factor',
           'load_img_and_K', 'transform_img_and_K', 'encode_image', 'encode_vae_image'}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')


def extract(data, path, names, env):
    nodes = [n for n in ast.parse(data, filename=str(path)).body
             if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names]
    require({n.name for n in nodes} == names, 'Missing exact original definitions')
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), env)


def main():
    if sys.argv[1:] == ['--compile-only']:
        compile(Path(__file__).read_bytes(), str(Path(__file__)), 'exec')
        print('COMPILE_ONLY_NO_COMPONENT_OR_SCIENTIFIC_READ')
        return 0
    require(not sys.argv[1:], 'No mutable data, IDs or runtime options')
    out = HERE / 'execution_01'
    out.mkdir(exist_ok=False)
    started = time.monotonic()
    report = {'schema': 's68-five-history-appearance-result-v1', 'started_utc': utc(),
              'status': 'RUNNING', 'evidence_kind': 'recorded_component_execution',
              'rows': [], 'reads': [], 'weight_decoder_calls': [], 'state_dict_loads': [],
              'query_rgb_bytes_read': 0, 'depth_bytes_read': 0,
              'pipeline_calls': 0, 'geometry_calls': 0, 'get_cond_calls': 0,
              'generation_calls': 0, 'images_viewed': 0,
              'complete_twenty_frame_cache': False, 'new_method_validated': False}
    manifest = None

    def read_bound(path, expected, kind, size=None):
        path = Path(path)
        with path.open('rb') as f:
            before = os.fstat(f.fileno())
            data = f.read()
            after = os.fstat(f.fileno())
        item = {'path': str(path), 'kind': kind, 'bytes_read': len(data),
                'sha256': sha(data), 'expected_sha256': expected}
        report['reads'].append(item)
        require(before.st_ino == after.st_ino and before.st_size == after.st_size
                and before.st_mtime_ns == after.st_mtime_ns, 'Input changed during read')
        require(item['sha256'] == expected and (size is None or len(data) == size),
                'Input SHA or length mismatch: ' + str(path))
        return data

    def budget():
        require(time.monotonic() - started <= 900, 'Internal 900 second stop budget')
        require(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss <= 20 * 1024**3,
                '20 GiB process peak RSS exceeded (macOS bytes)')

    def denied_network(*args, **kwargs):
        raise RuntimeError('Offline component bridge forbids network')

    try:
        require(sys.platform == 'darwin', 'RSS units fixed to macOS')
        manifest = json.loads(read_bound(HERE / 'INPUTS.json', INPUT_SHA, 'input_metadata'))
        require(manifest['body_history_ids'] == IDS, 'Five-source body whitelist changed')
        require([r['history_id'] for r in manifest['history_metadata']] == list(range(20)),
                'Original twenty-history metadata order changed')
        report.update(input_sha256=INPUT_SHA, executable_sha256=sha(Path(__file__).read_bytes()),
                      variant=manifest['variant'], body_history_ids=IDS,
                      source_id_to_storage_row=manifest['source_id_to_storage_row'],
                      conditional_old_selection_sets=manifest['conditional_old_selection_sets'],
                      selection_scope=manifest['selection_scope'])
        source = {p: read_bound(p, h, 'source') for p, h in manifest['source_sha256'].items()}
        for p, h in manifest['provenance_sha256'].items():
            read_bound(p, h, 'existing_text_or_metadata')
        require(shutil.disk_usage(out).free >= 10 * 1024**3, 'Less than 10 GiB free disk')
        os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                          HF_HUB_DISABLE_IMPLICIT_TOKEN='1', KORNIA_CHECK_VERSION='0',
                          PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='8',
                          MKL_NUM_THREADS='8', MPLBACKEND='Agg')
        sys.dont_write_bytecode = True
        sys.path[:0] = manifest['runtime_pythonpath']
        socket.socket.connect = denied_network
        socket.socket.connect_ex = denied_network
        socket.create_connection = denied_network
        import importlib.metadata
        import numpy as np
        import torch
        import torch.nn.functional as F
        import torchvision.transforms.functional as TF
        from PIL import Image
        import kornia
        import open_clip
        import safetensors.torch
        from diffusers.models import AutoencoderKL
        versions = {k: importlib.metadata.version(k.replace('_', '-'))
                    for k in manifest['versions']}
        require(versions == manifest['versions'], 'Scientific package version differs')
        report['versions'] = versions
        torch.set_num_threads(8)
        torch.set_num_interop_threads(1)
        random.seed(44)
        np.random.seed(44)
        torch.manual_seed(44)
        env = dict(torch=torch, nn=torch.nn, np=np, F=F, TF=TF, Image=Image, math=math,
                   Union=Union, Tuple=Tuple, Optional=Optional, kornia=kornia,
                   open_clip=open_clip, AutoencoderKL=AutoencoderKL)
        util = ORIGINAL / 'utils/util.py'
        extract(source[str(util)], util, HELPERS, env)
        for name, filename in [('AutoEncoder', 'autoencoder.py'),
                               ('CLIPConditioner', 'conditioner.py')]:
            path = ORIGINAL / 'modeling/modules' / filename
            extract(source[str(path)], path, {name}, env)
        budget()

        # Same original constructors; only route their named assets to verified local bytes.
        components = manifest['components']
        config = read_bound(components['vae_config']['path'], components['vae_config']['sha256'],
                            'vae_config', components['vae_config']['size'])
        local_vae_dir = out / 'local_vae'
        local_vae_dir.mkdir()
        (local_vae_dir / 'config.json').write_bytes(config)
        (local_vae_dir / 'diffusion_pytorch_model.safetensors').symlink_to(
            components['vae_weight']['path'])
        weight_bytes = {}
        original_vae_load = AutoencoderKL.from_pretrained
        original_clip_load = open_clip.create_model_and_transforms
        original_state_load = torch.nn.Module.load_state_dict
        raw_safetensor_load = safetensors.torch.load

        def load_verified_tensor_bytes(filename, device='cpu'):
            key = str(Path(filename).resolve())
            require(str(device) == 'cpu' and key in weight_bytes, 'Unbound tensor weight load')
            report['weight_decoder_calls'].append(key)
            return raw_safetensor_load(weight_bytes.pop(key))

        def state_load(module, *args, **kwargs):
            result = original_state_load(module, *args, **kwargs)
            report['state_dict_loads'].append({'class': type(module).__name__,
                'missing_keys': list(result.missing_keys),
                'unexpected_keys': list(result.unexpected_keys)})
            require(not result.missing_keys and not result.unexpected_keys, 'Incomplete model weights')
            return result

        def local_vae(repo, *args, **kwargs):
            require(repo == 'stabilityai/stable-diffusion-2-1-base' and not args
                    and kwargs == dict(subfolder='vae', force_download=False,
                                       low_cpu_mem_usage=False), 'Changed original VAE call')
            module, info = original_vae_load(str(local_vae_dir), local_files_only=True,
                force_download=False, low_cpu_mem_usage=False, use_safetensors=True,
                output_loading_info=True)
            report['vae_loading_info'] = info
            require(not any(info.get(k) for k in
                ['missing_keys', 'unexpected_keys', 'mismatched_keys', 'error_msgs']),
                'Incomplete declared ft-mse VAE load')
            return module

        def local_clip(name, *args, **kwargs):
            require(name == 'ViT-H-14' and not args
                    and kwargs == {'pretrained': 'laion2b_s32b_b79k'}, 'Changed original CLIP call')
            return original_clip_load(name, pretrained=components['clip']['path'])

        with ExitStack() as stack:
            stack.enter_context(patch.object(safetensors.torch, 'load_file', load_verified_tensor_bytes))
            stack.enter_context(patch.object(torch.nn.Module, 'load_state_dict', state_load))
            stack.enter_context(patch.object(AutoencoderKL, 'from_pretrained', local_vae))
            stack.enter_context(patch.object(open_clip, 'create_model_and_transforms', local_clip))
            models = {}
            for key, cls, arguments in [('vae_weight', 'AutoEncoder', {'chunk_size': 1}),
                                         ('clip', 'CLIPConditioner', {})]:
                item = components[key]
                weight_bytes[str(Path(item['path']).resolve())] = read_bound(
                    item['path'], item['sha256'], 'model_weight', item['size'])
                models[key] = env[cls](**arguments).to('cpu', torch.float32).eval()
                require(not weight_bytes, 'Original loader did not consume the verified weight bytes')
                budget()
        vae, clip = models['vae_weight'], models['clip']
        require(len(report['weight_decoder_calls']) == 2, 'Expected one decode per component')
        require(not vae.module.use_tiling and not vae.module.use_slicing
                and vae.chunk_size == 1 and vae.scale_factor == .18215 and vae.downsample == 8,
                'Declared original VAE execution settings changed')
        for model in [vae, clip]:
            require(all(not m.training for m in model.modules()), 'Model not in eval mode')
            require(all(p.device.type == 'cpu' and p.dtype == torch.float32
                        and not p.requires_grad for p in model.parameters()), 'Expected frozen CPU FP32')
        report['loaded_utc'] = utc()
        original_K = torch.tensor(manifest['controls']['input_K_pixels_640_480'], dtype=torch.float32)
        for storage_row, history_id in enumerate(IDS):
            budget()
            item = manifest['history_metadata'][history_id]
            require(item['history_id'] == history_id and item['body_allowed'], 'Non-whitelisted image')
            png = read_bound(item['path'], item['sha256'], 'historical_rgb_png', item['size_bytes'])
            with Image.open(io.BytesIO(png)) as image:
                require(image.size == (640, 480) and image.mode == 'RGB', 'Expected original 640x480 RGB PNG')
            with torch.inference_mode():
                image, _ = env['load_img_and_K'](io.BytesIO(png), None, K=None, device='cpu')
                image, K = env['transform_img_and_K'](image, (576, 576), mode='crop',
                                                     K=original_K.unsqueeze(0))
                require(tuple(image.shape) == (1, 3, 576, 576)
                        and image.dtype == torch.float32 and torch.isfinite(image).all()
                        and image.min() >= -1 and image.max() <= 1, 'Invalid original preprocessing')
                z = env['encode_vae_image'](image, vae, 'cpu', torch.float32)[0].cpu().numpy()
                e = env['encode_image'](image, clip, 'cpu', torch.float32)[0].cpu().numpy()
            require(z.shape == (4, 72, 72) and e.shape == (1024,)
                    and z.dtype == np.float32 and e.dtype == np.float32
                    and np.isfinite(z).all() and np.isfinite(e).all(), 'Invalid appearance output')
            kp = K[0].numpy().copy()
            kn = kp.copy()
            # Original get_plucker_coordinates line 146 normalization; no ray function called.
            kn[:2] /= np.float32(576)
            require(np.isfinite(kp).all() and np.isfinite(kn).all(), 'Nonfinite derived K')
            arrays = dict(latent=np.ascontiguousarray(z), embedding=np.ascontiguousarray(e),
                          K_pixels_576=kp, K_normalized_576=kn)
            destination = out / f'history_{history_id:02d}.npz'
            with destination.open('xb') as f:
                np.savez(f, **arrays)
            descriptors = {key: {'shape': list(a.shape), 'dtype': str(a.dtype),
                                 'body_bytes': a.nbytes, 'body_sha256': sha(a.tobytes(order='C'))}
                           for key, a in arrays.items()}
            row = dict(history_id=history_id, storage_row=storage_row,
                       input_rgb=item, npz_path=str(destination),
                       npz_sha256=sha(destination.read_bytes()), tensors=descriptors,
                       image_tensor_sha256=sha(image.cpu().numpy().tobytes(order='C')),
                       completed_utc=utc())
            save_json(out / f'history_{history_id:02d}.json', row)
            report['rows'].append(row)
            budget()
        require([r['history_id'] for r in report['rows']] == IDS, 'Incomplete five-source cache')
        require(not any(n == 'modeling.pipeline' or n.startswith('extern.CUT3R')
                        for n in sys.modules), 'Forbidden full pipeline or geometry import')
        report['status'] = 'COMPLETE_FIVE_REAL_HISTORY_APPEARANCE_CACHE_ONLY'
        report['camera_pose_status'] = 'NOT_PROVIDED_NOT_INFERRED'
        return_code = 0
    except BaseException as error:
        report.update(status='FAILED_COMPONENT_BRIDGE', error_type=type(error).__name__,
                      error=str(error), traceback=traceback.format_exc())
        return_code = 2
    finally:
        report.update(completed_utc=utc(), elapsed_seconds=time.monotonic() - started,
                      peak_self_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        report['historical_rgb_file_bytes_read'] = sum(r['bytes_read'] for r in report['reads']
                                                       if r['kind'] == 'historical_rgb_png')
        report['model_weight_file_bytes_read'] = sum(r['bytes_read'] for r in report['reads']
                                                     if r['kind'] == 'model_weight')
        save_json(out / 'receipt.json', report)
        for path in out.rglob('*'):
            if path.is_file() and not path.is_symlink():
                path.chmod(0o444)
    print(json.dumps({'status': report['status'], 'completed_sources': len(report['rows']),
                      'receipt': str(out / 'receipt.json')}))
    return return_code


if __name__ == '__main__':
    raise SystemExit(main())
