#!/usr/bin/env python3
"""S137a: training-free geometric baselines vs VMem static generation (CPU; the scorer is copied from C9).

Same four context frames as VMem's static arm (offsets 0,15,30,45), same four targets (60,75,90,105), same metric.
  B0 copy:  output the context frame nearest to the target in pose (VMem geodesic: angle + 0.1*translation)
  B1 warp:  forward-warp all four context frames into the target camera with their depth (z-buffer, nearest-pixel
            splat), fill holes with the nearest valid warped pixel
B1 uses history-frame depth only (dataset depth of the context frames, or a depth source passed in). It never reads
target depth; target RGB is read only by the scorer.
usage: geometry_baselines.py <datasets_root> <C9_SCORES.json> <out.json>
"""
import io, json, math, sys
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from scipy import ndimage

REL = {'scene_13': 'heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13',
       'scene_14': 'heldout_3dmatch_scene14/extracted/rgbd-scenes-v2-scene_14'}
WINDOWS = [0, 50, 100, 150, 200, 250, 300, 350]; CTX = [0, 15, 30, 45]; TGT = [60, 75, 90, 105]
import os
SPLAT = int(os.environ.get('SPLAT', '1'))


def to_model_grid(rgb_u8):  # identical transform to score_c9.future_rgb_to_model_grid
    t = torch.from_numpy(rgb_u8.transpose(2, 0, 1).copy()).float().unsqueeze(0) / 255.0
    t = torch.nn.functional.interpolate(t, size=(576, 768), mode='area', antialias=False)[:, :, :, 96:672]
    return np.clip(t[0].permute(1, 2, 0).numpy() * 255.0, 0, 255).astype(np.uint8)


def psnr(pred, ref):  # score_c9.integer_metrics psnr
    d = pred.astype(np.int64) - ref.astype(np.int64); mse = (d * d).sum() / (d.size * 255 * 255)
    return float('inf') if mse == 0 else -10.0 * math.log10(mse)


def load(seq, f, kind):
    p = seq / f'frame-{f:06d}.{kind}'
    if kind == 'color.png': return np.asarray(Image.open(p).convert('RGB'))
    if kind == 'depth.png': return np.asarray(Image.open(p), dtype=np.float64) / 1000.0
    return np.loadtxt(io.StringIO(p.read_text())).reshape(4, 4)


def geo(a, b):
    tr = np.clip((np.trace(a[:3, :3].T @ b[:3, :3]) - 1) / 2, -1, 1)
    return float(np.linalg.norm(a[:3, 3] - b[:3, 3]) * 0.1 + np.arccos(tr))


def warp(ctx, Tt, K, H=480, W=640):
    zbuf = np.full((H, W), np.inf); img = np.zeros((H, W, 3), np.uint8)
    v, u = np.mgrid[0:H, 0:W]
    Kinv = np.linalg.inv(K)
    for rgb, depth, Tc in ctx:
        m = depth > 0
        pix = np.stack([u[m], v[m], np.ones(m.sum())], 0)
        Xc = (Kinv @ pix) * depth[m]
        Xw = Tc[:3, :3] @ Xc + Tc[:3, 3:4]
        Xt = Tt[:3, :3].T @ (Xw - Tt[:3, 3:4])
        z = Xt[2]; ok = z > 1e-3
        uu = np.round(K[0, 0] * Xt[0, ok] / z[ok] + K[0, 2]).astype(int)
        vv = np.round(K[1, 1] * Xt[1, ok] / z[ok] + K[1, 2]).astype(int)
        col = rgb[m][ok]; zz = z[ok]
        inb = (uu >= 0) & (uu < W) & (vv >= 0) & (vv < H)
        uu, vv, col, zz = uu[inb], vv[inb], col[inb], zz[inb]
        order = np.argsort(-zz)                       # far first, near overwrite
        uu, vv, col, zz = uu[order], vv[order], col[order], zz[order]
        for dy in range(SPLAT):          # SPLAT=1: one pixel per point (S137a/b); SPLAT=2: 2x2 footprint (exploratory)
            for dx in range(SPLAT):
                u2 = np.clip(uu + dx, 0, W - 1); v2 = np.clip(vv + dy, 0, H - 1)
                closer = zz < zbuf[v2, u2]
                zbuf[v2[closer], u2[closer]] = zz[closer]; img[v2[closer], u2[closer]] = col[closer]
    valid = np.isfinite(zbuf)
    if valid.any() and not valid.all():
        _, (iy, ix) = ndimage.distance_transform_edt(~valid, return_indices=True)
        img = img[iy, ix]
    return img, float(valid.mean())


def warp_raw(ctx, Tt, K, H=480, W=640):
    """Same 1-pixel splat as warp(); returns (nearest-filled image, boolean coverage mask). Added for S140."""
    img, _ = warp(ctx, Tt, K, H, W)
    zb = np.full((H, W), np.inf); v, u = np.mgrid[0:H, 0:W]; Ki = np.linalg.inv(K)
    for rgb, depth, Tc in ctx:
        m = depth > 0; pix = np.stack([u[m], v[m], np.ones(m.sum())], 0)
        Xw = Tc[:3, :3] @ ((Ki @ pix) * depth[m]) + Tc[:3, 3:4]; Xt = Tt[:3, :3].T @ (Xw - Tt[:3, 3:4])
        z = Xt[2]; ok = z > 1e-3
        uu = np.round(K[0, 0] * Xt[0, ok] / z[ok] + K[0, 2]).astype(int); vv = np.round(K[1, 1] * Xt[1, ok] / z[ok] + K[1, 2]).astype(int)
        inb = (uu >= 0) & (uu < W) & (vv >= 0) & (vv < H); zb[vv[inb], uu[inb]] = np.minimum(zb[vv[inb], uu[inb]], z[ok][inb])
    return img, np.isfinite(zb)


def main():
    DS, C9, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    c9 = json.loads(C9.read_text())['arms']
    rows = []
    for scene, rel in REL.items():
        seq = DS / rel / 'seq-01'; K = np.loadtxt(DS / rel / 'camera-intrinsics.txt').reshape(3, 3)
        for w in WINDOWS:
            ctx_ids = [w + o for o in CTX]
            ctx = [(load(seq, f, 'color.png'), load(seq, f, 'depth.png'), load(seq, f, 'pose.txt')) for f in ctx_ids]
            sse = {'copy': [], 'warp': []}; cov = []
            for o in TGT:
                t = w + o; Tt = load(seq, t, 'pose.txt'); ref = to_model_grid(load(seq, t, 'color.png'))
                near = int(np.argmin([geo(Tt, c[2]) for c in ctx]))
                wimg, c = warp(ctx, Tt, K); cov.append(c)
                for name, img in (('copy', ctx[near][0]), ('warp', wimg)):
                    d = to_model_grid(img).astype(np.int64) - ref.astype(np.int64); sse[name].append(float((d * d).sum()))
            n = 4 * 576 * 576 * 3
            agg = {k: -10 * math.log10(sum(v) / (n * 255 * 255)) for k, v in sse.items()}
            vm = {conv: float(np.mean([c9[f'{scene}__w{w:04d}__static__{conv}__s{s}']['aggregate']['psnr_db'] for s in (42, 7)]))
                  for conv in ('native', 'gl')}
            rows.append({'scene': scene, 'window_start': w, 'copy_psnr': agg['copy'], 'warp_psnr': agg['warp'],
                         'warp_coverage': float(np.mean(cov)), 'vmem_static_native': vm['native'], 'vmem_static_gl': vm['gl']})
            print(f"{scene[-2:]} w{w:<4d} copy {agg['copy']:6.2f}  warp {agg['warp']:6.2f} (cov {np.mean(cov):.2f})  "
                  f"VMem static native {vm['native']:6.2f} gl {vm['gl']:6.2f}", flush=True)
    summ = {k: float(np.mean([r[k] for r in rows])) for k in ('copy_psnr', 'warp_psnr', 'vmem_static_native', 'vmem_static_gl')}
    summ['warp_beats_vmem_native'] = sum(r['warp_psnr'] > r['vmem_static_native'] for r in rows)
    summ['copy_beats_vmem_native'] = sum(r['copy_psnr'] > r['vmem_static_native'] for r in rows)
    summ['n'] = len(rows)
    OUT.write_text(json.dumps({'schema': 's137a-geometry-baselines-v1', 'summary': summ, 'windows': rows}, indent=1) + '\n')
    print(json.dumps(summ, indent=1))


if __name__ == '__main__':
    main()
