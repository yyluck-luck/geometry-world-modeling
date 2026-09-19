"""S75: decode previously accepted history latents once; no encoder or video sampler."""
from __future__ import annotations
import ast
from datetime import datetime, timezone
import gc
import hashlib
import io
import json
import math
import os
from pathlib import Path
import resource
import shutil
import socket
import sys
import time
import traceback
from typing import Optional, Tuple, Union
from unittest.mock import patch

D = Path(__file__).resolve().parent
IDS = [12, 13, 14, 18, 19]
HELPERS = {'get_wh_with_fixed_shortest_side', 'get_resizing_factor',
           'load_img_and_K', 'transform_img_and_K'}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def need(ok, msg):
    if not ok:
        raise RuntimeError(msg)


def save_json(p, x):
    with p.open('x') as f:
        json.dump(x, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')
    p.chmod(0o444)


def extract(b, path, names, env):
    nodes = [n for n in ast.parse(b, filename=path).body
             if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names]
    need({n.name for n in nodes} == names, 'Missing original definitions')
    exec(compile(ast.Module(body=nodes, type_ignores=[]), path, 'exec'), env)


def main():
    if sys.argv[1:] == ['--compile-only']:
        compile(Path(__file__).read_bytes(), str(Path(__file__)), 'exec')
        print('COMPILE_ONLY_NO_SCIENTIFIC_READ')
        return 0
    cb = (D / 'CONTRACT.json').read_bytes()
    need(len(sys.argv) == 2 and sha(cb) == sys.argv[1], 'Exact frozen contract SHA required')
    c = json.loads(cb)
    out = D / 'execution_01'
    out.mkdir(exist_ok=False)
    started = time.monotonic()
    r = dict(schema='s75-five-history-vae-decode-v1', started_utc=utc(), status='RUNNING',
             contract_sha256=sha(cb), source_sha256=sha(Path(__file__).read_bytes()),
             rows=[], reads=[], decode_calls=[], vae_weight_decoder_calls=[],
             new_encode_calls=0, clip_calls=0, vmem_calls=0, sampling_calls=0,
             new_method_validated=False)
    rc = 1
    save_json(out / 'started.json', dict(started_utc=r['started_utc'],
        contract_sha256=r['contract_sha256'], source_sha256=r['source_sha256'], pid=os.getpid()))

    def progress(event, **extra):
        with (out / 'progress.jsonl').open('a') as f:
            f.write(json.dumps(dict(utc=utc(), event=event, **extra), allow_nan=False) + '\n')
            f.flush()

    def read(item, kind):
        p = Path(item['path'])
        with p.open('rb') as f:
            pre = os.fstat(f.fileno()); b = f.read(); post = os.fstat(f.fileno())
        h = sha(b)
        r['reads'].append(dict(path=str(p), kind=kind, bytes=len(b), sha256=h))
        need((pre.st_ino, pre.st_size, pre.st_mtime_ns) ==
             (post.st_ino, post.st_size, post.st_mtime_ns), 'Input changed during read')
        need(h == item['sha256'] and ('size' not in item or len(b) == item['size']),
             'Input SHA/size mismatch: ' + str(p))
        return b

    def budget():
        need(time.monotonic() - started <= c['limits']['worker_seconds'], 'Worker time budget exceeded')
        need(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss <= c['limits']['rss_bytes'],
             'macOS peak RSS budget exceeded')

    def deny_network(*a, **kw):
        raise RuntimeError('S75 offline: network denied')

    def deny_encoder(*a, **kw):
        raise RuntimeError('S75 forbids new encoder calls')

    try:
        need(sys.platform == 'darwin', 'Resource units require macOS')
        need(c['history_ids'] == IDS, 'Fixed five historical sources changed')
        need(sys.version.split()[0] == c['python_version'], 'Python version changed')
        accepted = json.loads(read(c['s68_acceptance'], 'accepted_S68_metadata'))
        old = json.loads(read(c['s68_receipt'], 'accepted_S68_result_metadata'))
        need(accepted['status'] == 'ACCEPTED_FIVE_REAL_HISTORY_APPEARANCE_CACHE_ONLY', 'S68 not accepted')
        need(accepted['review_identity']['execution_01/receipt.json'] == c['s68_receipt']['sha256'],
             'S68 accepted receipt binding differs')
        need(old['status'] == 'COMPLETE_FIVE_REAL_HISTORY_APPEARANCE_CACHE_ONLY', 'S68 incomplete')
        need([x['history_id'] for x in old['rows']] == IDS, 'S68 source order changed')
        metadata = []
        for item, original in zip(c['histories'], old['rows']):
            m = json.loads(read(item['metadata'], 'history_metadata'))
            need(m == original and m['history_id'] == item['history_id'], 'History receipt differs')
            need(item['npz'] == dict(path=m['npz_path'], sha256=m['npz_sha256']), 'NPZ binding differs')
            need(item['png'] == dict(path=m['input_rgb']['path'], sha256=m['input_rgb']['sha256'],
                                     size=m['input_rgb']['size_bytes']), 'Historical PNG binding differs')
            metadata.append(m)
        sources = {key: read(item, 'original_source') for key, item in c['sources'].items()}
        need(shutil.disk_usage(out).free >= c['limits']['minimum_free_bytes'], 'Insufficient free disk')
        os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_IMPLICIT_TOKEN='1',
                          PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='8', MKL_NUM_THREADS='8')
        sys.dont_write_bytecode = True
        sys.path[:0] = c['pythonpath']
        socket.socket.connect = deny_network
        socket.socket.connect_ex = deny_network
        socket.create_connection = deny_network
        from importlib.metadata import version
        import numpy as np
        import torch
        import torch.nn.functional as F
        import torchvision.transforms.functional as TF
        from PIL import Image
        import cv2
        import safetensors.torch
        from diffusers.models import AutoencoderKL
        actual = {k: version(k) for k in c['versions']}
        need(actual == c['versions'], 'Scientific package version changed')
        r['versions'] = actual
        torch.set_num_threads(8); torch.set_num_interop_threads(1)
        torch.manual_seed(c['seed']); np.random.seed(c['seed'])
        cv2.setNumThreads(1); cv2.setRNGSeed(c['seed'])
        env = dict(torch=torch, nn=torch.nn, np=np, F=F, TF=TF, Image=Image, math=math,
                   Union=Union, Tuple=Tuple, Optional=Optional, AutoencoderKL=AutoencoderKL)
        extract(sources['util'], c['sources']['util']['path'], HELPERS, env)
        extract(sources['autoencoder'], c['sources']['autoencoder']['path'], {'AutoEncoder'}, env)
        budget()
        local = out / 'local_vae'; local.mkdir()
        (local / 'config.json').write_bytes(read(c['components']['vae_config'], 'vae_config'))
        weight = c['components']['vae_weight']
        (local / 'diffusion_pytorch_model.safetensors').symlink_to(weight['path'])
        held = [read(weight, 'vae_weight')]
        original_load = AutoencoderKL.from_pretrained

        def tensor_load(filename, device='cpu'):
            need(Path(filename).resolve() == Path(weight['path']).resolve() and str(device) == 'cpu'
                 and len(held) == 1, 'Unexpected VAE weight consumer')
            r['vae_weight_decoder_calls'].append(str(filename))
            return safetensors.torch.load(held.pop())

        def local_load(repo, *a, **kw):
            need(repo == 'stabilityai/stable-diffusion-2-1-base' and not a and
                 kw == dict(subfolder='vae', force_download=False, low_cpu_mem_usage=False),
                 'Original VAE constructor differs')
            result, info = original_load(str(local), local_files_only=True, force_download=False,
                low_cpu_mem_usage=False, use_safetensors=True, output_loading_info=True)
            r['vae_loading_info'] = info
            need(not any(info.get(k) for k in ['missing_keys','unexpected_keys','mismatched_keys','error_msgs']),
                 'Incomplete VAE weights')
            return result

        with patch.object(safetensors.torch, 'load_file', tensor_load), \
             patch.object(AutoencoderKL, 'from_pretrained', local_load):
            ae = env['AutoEncoder'](chunk_size=1).cpu().float().eval().requires_grad_(False)
        need(len(r['vae_weight_decoder_calls']) == 1 and not held, 'VAE bound-byte consumption differs')
        need(ae.scale_factor == .18215 and ae.downsample == 8 and ae.chunk_size == 1
             and not ae.module.use_slicing and not ae.module.use_tiling, 'VAE execution settings differ')
        need(all(not x.training for x in ae.modules()) and
             all(p.dtype == torch.float32 and p.device.type == 'cpu' and not p.requires_grad for p in ae.parameters()),
             'Expected frozen CPU FP32 eval')
        gc.collect(); budget()
        r['loaded_utc'] = utc()
        progress('vae_loaded')
        sift = cv2.SIFT_create(**c['sift'])
        bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)

        def array_save(path, a):
            a = np.ascontiguousarray(a)
            with path.open('xb') as f:
                np.save(f, a, allow_pickle=False)
            path.chmod(0o444)
            return dict(path=str(path), shape=list(a.shape), dtype=str(a.dtype),
                        body_bytes=a.nbytes, body_sha256=sha(a.tobytes()), file_sha256=sha(path.read_bytes()))

        def png_save(path, a):
            # Both inputs have declared [-1,1] scale. No data-dependent range branch.
            rgb = np.floor((np.clip(a, -1, 1).transpose(1, 2, 0).astype(np.float64) + 1) * 127.5 + .5).astype(np.uint8)
            with path.open('xb') as f:
                Image.fromarray(rgb, mode='RGB').save(f, format='PNG')
            path.chmod(0o444)
            return rgb, dict(path=str(path), file_sha256=sha(path.read_bytes()),
                             pixel_sha256=sha(rgb.tobytes()), shape=list(rgb.shape))

        def ratios(a, b):
            if a is None or b is None or len(b) < 2:
                return {}
            return {m.queryIdx: m.trainIdx for row in bf.knnMatch(a, b, k=2) if len(row) == 2
                    for m, n in [row] if m.distance < c['ratio'] * n.distance}

        def coverage(x):
            if not len(x):
                return dict(span_xy_fraction=None, occupied_4x4_cells=0)
            cells = np.clip(np.floor(x / 144), 0, 3).astype(int)
            return dict(span_xy_fraction=(np.ptp(x, axis=0)/575).tolist(),
                        occupied_4x4_cells=len(set(map(tuple, cells.tolist()))))

        K0 = torch.tensor(c['input_K_pixels_640_480'], dtype=torch.float32)
        with patch.object(ae, 'encode', deny_encoder), patch.object(ae.module, 'encode', deny_encoder):
            for item, meta in zip(c['histories'], metadata):
                budget()
                hid = item['history_id']; rowdir = out / f'history_{hid:02d}'; rowdir.mkdir()
                row = dict(history_id=hid, started_utc=utc(), status='RUNNING')
                r['rows'].append(row)
                blob = read(item['npz'], 'S68_cached_npz_latent_only_decoded')
                with np.load(io.BytesIO(blob), allow_pickle=False) as archive:
                    need(set(archive.files) == {'latent','embedding','K_pixels_576','K_normalized_576'}, 'Unexpected cache fields')
                    z = archive['latent']
                need(z.shape == (4,72,72) and z.dtype == np.float32 and np.isfinite(z).all(), 'Invalid cached latent')
                desc = meta['tensors']['latent']
                need(desc == dict(shape=list(z.shape), dtype=str(z.dtype), body_bytes=z.nbytes,
                                  body_sha256=sha(np.ascontiguousarray(z).tobytes())), 'Cached latent body differs')
                png = read(item['png'], 'historical_RGB_png')
                with Image.open(io.BytesIO(png)) as im:
                    need(im.mode == 'RGB' and im.size == (640,480), 'Original historical image shape/mode differs')
                with torch.inference_mode():
                    x, _ = env['load_img_and_K'](io.BytesIO(png), None, K=None, device='cpu')
                    x, _ = env['transform_img_and_K'](x, (576,576), mode='crop', K=K0.unsqueeze(0))
                    need(x.shape == (1,3,576,576) and x.dtype == torch.float32 and torch.isfinite(x).all()
                         and float(x.min()) >= -1 and float(x.max()) <= 1, 'Preprocessed image differs')
                    need(sha(x.numpy().tobytes()) == meta['image_tensor_sha256'], 'S68 preprocessing tensor SHA differs')
                    row['reference_tensor_sha256'] = sha(x.numpy().tobytes())
                    call = dict(history_id=hid, started_utc=utc(), scale_factor=ae.scale_factor,
                                input_latent_body_sha256=desc['body_sha256'])
                    r['decode_calls'].append(call)
                    progress('decode_start', history_id=hid)
                    y = ae.decode(torch.from_numpy(z.copy()).unsqueeze(0), chunk_size=1)
                    call['completed_utc'] = utc()
                    progress('decode_return', history_id=hid)
                need(y.shape == (1,3,576,576) and y.dtype == torch.float32 and y.device.type == 'cpu'
                     and torch.isfinite(y).all(), 'Invalid reconstruction')
                ref = np.ascontiguousarray(x.numpy()[0]); rec = np.ascontiguousarray(y.numpy()[0])
                row['arrays'] = dict(reference_fp32=array_save(rowdir/'reference_fp32.npy', ref),
                                     reconstruction_raw_fp32=array_save(rowdir/'reconstruction_raw_fp32.npy', rec))
                ref8, refinfo = png_save(rowdir/'reference.png', ref)
                rec8, recinfo = png_save(rowdir/'reconstruction.png', rec)
                row['pngs'] = dict(reference=refinfo, reconstruction=recinfo)
                diff = rec.astype(np.float64) - ref.astype(np.float64)
                row['raw_error_minus1_plus1'] = dict(mse=float(np.mean(diff*diff)), mae=float(np.mean(np.abs(diff))),
                    pixel_channel_count=int(diff.size), reconstruction_min=float(rec.min()), reconstruction_max=float(rec.max()),
                    below_minus1_count=int(np.sum(rec < -1)), above_plus1_count=int(np.sum(rec > 1)))
                kp, dp = sift.detectAndCompute(cv2.cvtColor(ref8, cv2.COLOR_RGB2GRAY), None)
                kq, dq = sift.detectAndCompute(cv2.cvtColor(rec8, cv2.COLOR_RGB2GRAY), None)
                fwd, rev = ratios(dp,dq), ratios(dq,dp)
                pairs = [(i,j) for i,j in sorted(fwd.items()) if rev.get(j) == i]
                sx = np.array([kp[i].pt for i,j in pairs], dtype=np.float64).reshape(-1,2)
                tx = np.array([kq[j].pt for i,j in pairs], dtype=np.float64).reshape(-1,2)
                dist = np.linalg.norm(tx-sx, axis=1)
                N = len(kp); M = len(pairs)
                row['matching'] = dict(source_feature_count=N, reconstruction_feature_count=len(kq), match_count=M,
                    unmatched_count=N-M, match_fraction=M/N if N else None, unmatched_fraction=(N-M)/N if N else None,
                    status='MATCHES_AVAILABLE' if M else 'NO_ACCEPTED_MATCHES',
                    match_keypoint_ids=pairs, source_xy=sx.tolist(), reconstruction_xy=tx.tolist(),
                    displacements_px=dist.tolist(), quantiles_px=np.quantile(dist,c['quantiles']).tolist() if M else None,
                    maximum_px=float(dist.max()) if M else None, source_coverage=coverage(sx),
                    reconstruction_coverage=coverage(tx),
                    cutoff_counts={str(t):int(np.sum(dist <= t)) for t in c['cutoffs_px']},
                    cutoff_fraction_of_source={str(t):float(np.sum(dist <= t))/N if N else None for t in c['cutoffs_px']},
                    cutoff_fraction_of_matches={str(t):float(np.sum(dist <= t))/M if M else None for t in c['cutoffs_px']})
                row.update(status='COMPLETE_HISTORY_ROUNDTRIP', completed_utc=utc())
                save_json(rowdir/'receipt.json',row)
                progress('history_completed', history_id=hid)
                del x,y,ref,rec,z,blob,png,diff
                budget()
        need([x['history_id'] for x in r['rows']] == IDS and
             all(x['status'] == 'COMPLETE_HISTORY_ROUNDTRIP' for x in r['rows']), 'Incomplete five-history run')
        need(len(r['decode_calls']) == 5, 'Expected one decode per source')
        need(not any(n == 'modeling.pipeline' or n == 'open_clip' or n.startswith('extern.CUT3R')
                     for n in sys.modules), 'Forbidden unrelated pipeline import')
        r['status'] = 'COMPLETE_FIVE_HISTORY_VAE_ROUNDTRIP'; rc = 0
    except Exception as e:
        r.update(status='FAILED',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc())
        for row in r['rows']:
            if row['status'] == 'RUNNING':
                row.update(status='FAILED_HISTORY', error_type=type(e).__name__, error=str(e))
    finally:
        r.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-started,
                 peak_self_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                 unrun_history_ids=[hid for hid in IDS if hid not in [x['history_id'] for x in r['rows']]])
        save_json(out/'receipt.json',r)
    print(json.dumps(dict(status=r['status'],completed_histories=sum(x['status']=='COMPLETE_HISTORY_ROUNDTRIP' for x in r['rows']),
                         elapsed_seconds=r['elapsed_seconds'],output=str(out))))
    return rc


if __name__ == '__main__':
    raise SystemExit(main())
