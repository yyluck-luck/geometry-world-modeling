#!/usr/bin/env python3
"""S143 warp-side scores (reads target RGB; separate from construction/generation). For each (window, set): Q_W = B2 warp
PSNR (C9 metric, four targets pooled) and SSIM (S140 definition, mean over targets); copy-nearest (each target gets the
pose-nearest frame of the set, VMem geodesic) PSNR; plus whole-bank copy-nearest per window.
usage: score_warps_s143.py <POOL.json> <warp_dir> <out.json>"""
import json, math, sys
from pathlib import Path
import numpy as np, torch
from PIL import Image
HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]; ROOT = REPO / 'data/S139_chess/chess'
POOL, WD, OUT = json.loads(Path(sys.argv[1]).read_text()), Path(sys.argv[2]), Path(sys.argv[3])


def grid(rgb):  # score_c9 / geometry_baselines.to_model_grid
    t = torch.from_numpy(rgb.transpose(2, 0, 1).copy()).float().unsqueeze(0) / 255.0
    t = torch.nn.functional.interpolate(t, size=(576, 768), mode='area', antialias=False)[:, :, :, 96:672]
    return np.clip(t[0].permute(1, 2, 0).numpy() * 255.0, 0, 255).astype(np.uint8)


_g = torch.exp(-((torch.arange(11) - 5.0) ** 2) / (2 * 1.5 ** 2)); _g = _g / _g.sum(); _K = (_g[:, None] * _g[None, :])[None, None]
def ssim(a, b):  # score_s140.ssim
    lum = lambda x: torch.from_numpy((x.astype(np.float64) @ np.array([0.299, 0.587, 0.114]))).float()[None, None]
    x, y = lum(a), lum(b); C1, C2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2; f = lambda z: torch.nn.functional.conv2d(z, _K, padding=5)
    mx, my = f(x), f(y); sxx = f(x * x) - mx ** 2; syy = f(y * y) - my ** 2; sxy = f(x * y) - mx * my
    return float((((2 * mx * my + C1) * (2 * sxy + C2)) / ((mx ** 2 + my ** 2 + C1) * (sxx + syy + C2)))[..., 5:-5, 5:-5].mean())


def col(ref): s, f = ref.split('/'); return np.asarray(Image.open(ROOT / s / f'frame-{f}.color.png').convert('RGB'))
def pose(ref): s, f = ref.split('/'); return np.loadtxt(ROOT / s / f'frame-{f}.pose.txt').reshape(4, 4)
def geo(a, b):
    tr = np.clip((np.trace(a[:3, :3].T @ b[:3, :3]) - 1) / 2, -1, 1); return float(np.linalg.norm(a[:3, 3] - b[:3, 3]) * 0.1 + np.arccos(tr))
def psnr4(preds, refs):
    sse = sum(float(((p.astype(np.int64) - r.astype(np.int64)) ** 2).sum()) for p, r in zip(preds, refs))
    return -10 * math.log10(sse / (len(refs) * 576 * 576 * 3 * 255 * 255))


res = {}
for w in POOL['windows']:
    wid = w['window_id']; refs = [grid(col(t)) for t in w['targets']]; tp = [pose(t) for t in w['targets']]
    bp = {r: pose(r) for r in w['bank']}
    near = lambda cands: [grid(col(min(cands, key=lambda r: geo(bp[r], T)))) for T in tp]
    out = {'copy_bank_psnr': psnr4(near(w['bank']), refs), 'sets': {}}
    for s in w['sets']:
        ws = [np.load(WD / f"{wid}__{s['set_id']}__{t.replace('/', '_')}.npz") for t in w['targets']]
        f = [z['filled'] for z in ws]
        out['sets'][s['set_id']] = {'rules': s['rules'], 'warp_psnr': psnr4(f, refs), 'warp_ssim': float(np.mean([ssim(a, b) for a, b in zip(f, refs)])),
                                    'coverage': float(np.mean([z['valid'].mean() for z in ws])), 'copy_set_psnr': psnr4(near(s['ctx_refs']), refs)}
    res[wid] = out
    print(wid, {k: round(v['warp_psnr'], 2) for k, v in out['sets'].items()}, flush=True)
OUT.write_text(json.dumps({'schema': 's143-warp-scores-v1', 'windows': res}, indent=1) + '\n')
