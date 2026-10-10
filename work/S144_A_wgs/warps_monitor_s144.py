#!/usr/bin/env python3
"""S144 development warps: the B2 pipeline on CPU (CUT3R + KPS niter 0, corrected depth mapping, 1-px z-buffer splat,
nearest fill) for the 32 S141 monitor clips, saved per target in the S140 format (filled uint8 576x576x3, valid bool on the
model grid) as <clip_id>__t<j>.npz. Context frames and target POSES only. Same math as warps_s141.py with device=cpu.
usage: warps_monitor_s144.py <data7_root> <clips_s141.json> <out_dir>   (env RUN_ROOT, WEIGHTS; OMP threads)"""
import json, os, sys, time
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s141_common as C
import torch
from PIL import Image
from scipy import ndimage
import modeling.pipeline as PM
from cloud_opt.dust3r_opt import init_im_poses as IIP
from utils import tensor_to_pil
import kps

D, CL, OUT = Path(sys.argv[1]), [c for c in json.loads(Path(sys.argv[2]).read_text())['clips'] if c['split'] == 'val'], Path(sys.argv[3])
assert len(CL) == 32
OUT.mkdir(parents=True, exist_ok=True)
LOG = []; kps.install(IIP, log=LOG)
ck = str(C.WEIGHTS / 'cut3r_512_dpt_4_64.pth'); PM.add_path_to_dust3r(ck)
cut3r = PM.ARCroco3DStereo.from_pretrained(ck).to('cpu').eval()
K = C.K7.astype(np.float64)


def to_model_grid(rgb_u8):
    t = torch.from_numpy(rgb_u8.transpose(2, 0, 1).copy()).float().unsqueeze(0) / 255.0
    t = torch.nn.functional.interpolate(t, size=(576, 768), mode='area', antialias=False)[:, :, :, 96:672]
    return np.clip(t[0].permute(1, 2, 0).numpy() * 255.0, 0, 255).astype(np.uint8)


def depth640(d):
    v0, u0 = np.mgrid[0:480, 0:640]
    x = np.round(((u0 + 0.5) * 1.2 - 96) * 512 / 576 - 0.5).astype(int); y = np.round((v0 + 0.5) * 1.2 * 512 / 576 - 64 - 0.5).astype(int)
    ok = (x >= 0) & (x < 512) & (y >= 0) & (y < 384); out = np.zeros((480, 640)); out[ok] = d[y[ok], x[ok]]; return out


def warp_both(ctx, Tt, H=480, W=640):  # geometry_baselines.warp (SPLAT=1) + pre-fill coverage
    zbuf = np.full((H, W), np.inf); img = np.zeros((H, W, 3), np.uint8)
    v, u = np.mgrid[0:H, 0:W]; Kinv = np.linalg.inv(K)
    for rgb, depth, Tc in ctx:
        m = depth > 0
        pix = np.stack([u[m], v[m], np.ones(m.sum())], 0)
        Xw = Tc[:3, :3] @ ((Kinv @ pix) * depth[m]) + Tc[:3, 3:4]
        Xt = Tt[:3, :3].T @ (Xw - Tt[:3, 3:4])
        z = Xt[2]; ok = z > 1e-3
        uu = np.round(K[0, 0] * Xt[0, ok] / z[ok] + K[0, 2]).astype(int); vv = np.round(K[1, 1] * Xt[1, ok] / z[ok] + K[1, 2]).astype(int)
        col = rgb[m][ok]; zz = z[ok]
        inb = (uu >= 0) & (uu < W) & (vv >= 0) & (vv < H)
        uu, vv, col, zz = uu[inb], vv[inb], col[inb], zz[inb]
        order = np.argsort(-zz); uu, vv, col, zz = uu[order], vv[order], col[order], zz[order]
        closer = zz < zbuf[vv, uu]
        zbuf[vv[closer], uu[closer]] = zz[closer]; img[vv[closer], uu[closer]] = col[closer]
    valid = np.isfinite(zbuf)
    if valid.any() and not valid.all():
        _, (iy, ix) = ndimage.distance_transform_edt(~valid, return_indices=True); img = img[iy, ix]
    return img, valid


def path(ref, kind):
    sc, q, f = ref.split('/'); return D / sc / q / f'frame-{f}.{kind}'


t0 = time.time(); logf = OUT / 'WARP_LOG_monitor_cpu.jsonl'
for c in CL:
    names = [OUT / f"{c['id']}__t{j}.npz" for j in range(4)]
    if all(n.exists() for n in names): continue
    LOG.clear(); seen = []; [seen.append(r) for r in c['ctx'] if r not in seen]
    poses = np.array([C.load_pose_path(path(r, 'pose.txt')) for r in seen], dtype=np.float32)
    pils = [tensor_to_pil(C.load_rgb_path(path(r, 'color.png'))) for r in seen]
    with torch.no_grad():
        out = PM.run_inference_from_pil(pils, cut3r, poses=poses, depths=None, lr=0.01, niter=0, device='cpu')
    ctx = [(np.asarray(Image.open(path(r, 'color.png')).convert('RGB')), depth640(d[0].detach().float().cpu().numpy()), p.astype(np.float64))
           for r, d, p in zip(seen, out['depths'], poses)]
    for j, (t, n) in enumerate(zip(c['tgt'], names)):
        img, val = warp_both(ctx, C.load_pose_path(path(t, 'pose.txt')).astype(np.float64))
        vm = to_model_grid(np.repeat(val[..., None].astype(np.uint8) * 255, 3, 2))[..., 0] > 127
        np.savez_compressed(n, filled=to_model_grid(img), valid=vm)
    kl = [dict(l) for l in LOG]
    with logf.open('a') as fh: fh.write(json.dumps({'id': c['id'], 'kps': kl, 'seconds': round(time.time() - t0, 1)}, default=float) + '\n')
    print(f"[warp-cpu] {c['id']} kps {[l.get('kps') for l in kl]} {time.time() - t0:.0f}s", flush=True)
print('[warp-cpu] done', len(CL))
