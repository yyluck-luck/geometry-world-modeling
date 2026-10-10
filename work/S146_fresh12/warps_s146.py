#!/usr/bin/env python3
"""S146 warps (adapter of S143 warps_s143.py / the S139 B2 pipeline): per package, CUT3R + KPS (niter 0, CPU) on exactly its
four ordered frames with geometry poses (gl winner: P; native: P.F), corrected depth lookup, 1-px z-buffer splat with
this room's staged K, nearest fill; saved per target (filled, valid on the model grid). Finite-KPS gate per call.
Context frames and target poses only. usage: warps_s146.py <stage12> <POOL.json|POOL_phase1.json> <out_dir> [shard i/N]"""
import json, sys, time
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import s141_common as C
import torch
from PIL import Image
from scipy import ndimage
import modeling.pipeline as PM
from cloud_opt.dust3r_opt import init_im_poses as IIP
from utils import tensor_to_pil
import kps
STAGE, POOL, OUTD = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text()), Path(sys.argv[3])
SI, SN = map(int, (sys.argv[4] if len(sys.argv) > 4 else '0/1').split('/'))
LOG = []; kps.install(IIP, log=LOG)
ck = str(C.WEIGHTS / 'cut3r_512_dpt_4_64.pth'); PM.add_path_to_dust3r(ck)
model = PM.ARCroco3DStereo.from_pretrained(ck).to('cpu').eval()
F = np.diag([1.0, -1.0, -1.0, 1.0])
def to_model_grid(rgb_u8):
    t = torch.from_numpy(rgb_u8.transpose(2, 0, 1).copy()).float().unsqueeze(0) / 255.0
    t = torch.nn.functional.interpolate(t, size=(576, 768), mode='area', antialias=False)[:, :, :, 96:672]
    return np.clip(t[0].permute(1, 2, 0).numpy() * 255.0, 0, 255).astype(np.uint8)
def depth640(d):
    v0, u0 = np.mgrid[0:480, 0:640]
    x = np.round(((u0 + 0.5) * 1.2 - 96) * 512 / 576 - 0.5).astype(int); y = np.round((v0 + 0.5) * 1.2 * 512 / 576 - 64 - 0.5).astype(int)
    ok = (x >= 0) & (x < 512) & (y >= 0) & (y < 384); out = np.zeros((480, 640)); out[ok] = d[y[ok], x[ok]]; return out
def warp_both(ctx, Tt, K, H=480, W=640):  # geometry_baselines.warp (SPLAT=1) + pre-fill coverage
    zbuf = np.full((H, W), np.inf); img = np.zeros((H, W, 3), np.uint8); v, u = np.mgrid[0:H, 0:W]; Kinv = np.linalg.inv(K)
    for rgb, depth, Tc in ctx:
        m = depth > 0; pix = np.stack([u[m], v[m], np.ones(m.sum())], 0)
        Xw = Tc[:3, :3] @ ((Kinv @ pix) * depth[m]) + Tc[:3, 3:4]; Xt = Tt[:3, :3].T @ (Xw - Tt[:3, 3:4]); z = Xt[2]; ok = z > 1e-3
        uu = np.round(K[0, 0] * Xt[0, ok] / z[ok] + K[0, 2]).astype(int); vv = np.round(K[1, 1] * Xt[1, ok] / z[ok] + K[1, 2]).astype(int)
        col = rgb[m][ok]; zz = z[ok]; inb = (uu >= 0) & (uu < W) & (vv >= 0) & (vv < H)
        uu, vv, col, zz = uu[inb], vv[inb], col[inb], zz[inb]; order = np.argsort(-zz); uu, vv, col, zz = uu[order], vv[order], col[order], zz[order]
        closer = zz < zbuf[vv, uu]; zbuf[vv[closer], uu[closer]] = zz[closer]; img[vv[closer], uu[closer]] = col[closer]
    valid = np.isfinite(zbuf)
    if valid.any() and not valid.all():
        _, (iy, ix) = ndimage.distance_transform_edt(~valid, return_indices=True); img = img[iy, ix]
    return img, valid
OUTD.mkdir(parents=True, exist_ok=True)
jobs = []
for w in POOL['windows']:
    packs = w['sets'] if 'sets' in w else [{'set_id': 'p1r' + k, 'ctx_refs': sorted(v, key=lambda x: w['bank'].index(x))} for k, v in w['rules_phase1'].items()]
    jobs += [(w, s) for s in packs]
jobs = [j for k, j in enumerate(jobs) if k % SN == SI]; logf = OUTD / f'WARP_LOG_{SI}of{SN}.jsonl'; t0 = time.time()
for w, s in jobs:
    room = w['room']; root = STAGE / room; K = np.loadtxt(root / 'camera-intrinsics.txt').reshape(3, 3)
    tag = '-'.join(r.replace('/', '_') for r in s['ctx_refs'])          # warps keyed by the ordered tuple itself
    names = [OUTD / f"{w['window_id']}__{tag}__{t.replace('/', '_')}.npz" for t in w['targets']]
    if all(n.exists() for n in names): continue
    P = lambda ref: np.loadtxt(root / ref.split('/')[0] / f"frame-{ref.split('/')[1]}.pose.txt").reshape(4, 4)
    G = (lambda ref: P(ref)) if w['convention'] == 'gl' else (lambda ref: P(ref) @ F)
    LOG.clear(); refs = s['ctx_refs']
    pils = [tensor_to_pil(C.load_rgb_path(root / r.split('/')[0] / f"frame-{r.split('/')[1]}.color.png")) for r in refs]
    gp = np.array([G(r) for r in refs], dtype=np.float32)
    with torch.no_grad():
        out = PM.run_inference_from_pil(pils, model, poses=gp, depths=None, lr=0.01, niter=0, device='cpu')
    kl = [dict(l) for l in LOG]
    assert len(kl) == 1 and kl[0].get('kps') == 'OK' and np.isfinite(kl[0]['sigma']) and np.isfinite(kl[0]['median_reproj_px']), (w['window_id'], tag, kl)
    ctx = [(np.asarray(Image.open(root / r.split('/')[0] / f"frame-{r.split('/')[1]}.color.png").convert('RGB')), depth640(d[0].detach().float().numpy()),
            gp[i].astype(np.float64)) for i, (r, d) in enumerate(zip(refs, out['depths']))]
    for t, n in zip(w['targets'], names):
        img, val = warp_both(ctx, G(t), K)
        np.savez_compressed(n, filled=to_model_grid(img), valid=to_model_grid(np.repeat(val[..., None].astype(np.uint8) * 255, 3, 2))[..., 0] > 127)
    with logf.open('a') as fh: fh.write(json.dumps({'window_id': w['window_id'], 'tag': tag, 'kps': kl, 'seconds': round(time.time() - t0, 1)}, default=float) + '\n')
    print(f"[warp] {w['window_id']} {s['set_id']} {time.time() - t0:.0f}s", flush=True)
print('[warp] done', len(jobs))
