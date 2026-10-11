#!/usr/bin/env python3
"""S146 operational generation-only scorer (Amendment 3): S140 conversion and metrics (per-output PSNR from SSE pooled over the
four targets, mean target SSIM); per-context scene_dir; no warp reads. Strict: every plan context x seed present, finite.
usage: score_gen_s146.py <gen_dir> <stage12> <plan.json> <seeds e.g. 42,7,1,2> <out.json>"""
import io, json, math, sys
from pathlib import Path
import numpy as np, torch
from PIL import Image
GD, DS, PLAN, OUT = Path(sys.argv[1]), Path(sys.argv[2]), json.loads(Path(sys.argv[3]).read_text()), Path(sys.argv[5]); SEEDS = [int(x) for x in sys.argv[4].split(',')]
def ref_grid(p):  # score_s140.ref_grid
    rgb = np.asarray(Image.open(io.BytesIO(p.read_bytes())).convert('RGB'), dtype=np.uint8)
    t = torch.from_numpy(rgb.transpose(2, 0, 1).copy()).float().unsqueeze(0) / 255.0
    t = torch.nn.functional.interpolate(t, size=(576, 768), mode='area', antialias=False)[:, :, :, 96:672]
    return np.clip(t[0].permute(1, 2, 0).numpy() * 255.0, 0, 255).astype(np.uint8)
def pred_u8(fr):  # score_s140.pred_u8
    im = fr.transpose(1, 2, 0)
    if float(im.min()) < -0.1: im = (im + 1.0) / 2.0
    return np.clip(im * 255.0, 0, 255).astype(np.uint8)
_g = torch.exp(-((torch.arange(11) - 5.0) ** 2) / (2 * 1.5 ** 2)); _g = _g / _g.sum(); _K = (_g[:, None] * _g[None, :])[None, None]
def ssim(a, b):  # score_s140.ssim
    lum = lambda x: torch.from_numpy((x.astype(np.float64) @ np.array([0.299, 0.587, 0.114]))).float()[None, None]
    x, y = lum(a), lum(b); C1, C2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2; f = lambda z: torch.nn.functional.conv2d(z, _K, padding=5)
    mx, my = f(x), f(y); sxx = f(x * x) - mx ** 2; syy = f(y * y) - my ** 2; sxy = f(x * y) - mx * my
    return float((((2 * mx * my + C1) * (2 * sxy + C2)) / ((mx ** 2 + my ** 2 + C1) * (sxx + syy + C2)))[..., 5:-5, 5:-5].mean())
out = {}
for c in PLAN['contexts']:
    root = DS / c['scene_dir']; refs = [ref_grid(root / r.split('/')[0] / f"frame-{r.split('/')[1]}.color.png") for r in c['target_refs']]
    for s in SEEDS:
        a = np.load(GD / f"{c['ctx_key']}__s{s}.npy"); assert a.shape == (4, 3, 576, 576) and np.isfinite(a).all(), (c['ctx_key'], s)
        ps = [pred_u8(f) for f in a]; sse = sum(float(((p.astype(np.int64) - r.astype(np.int64)) ** 2).sum()) for p, r in zip(ps, refs))
        psnr = -10 * math.log10(sse / (4 * 576 * 576 * 3 * 255 * 255)); ss = float(np.mean([ssim(p, r) for p, r in zip(ps, refs)]))
        assert math.isfinite(psnr) and math.isfinite(ss)
        out[f"{c['ctx_key']}__s{s}"] = {'ctx_key': c['ctx_key'], 'window_id': c['window_id'], 'room': c['room'], 'mode': c['mode'], 'seed': s, 'psnr_db': psnr, 'ssim': ss}
OUT.write_text(json.dumps({'schema': 's146-op-scores-v1', 'runs': out}, indent=1) + '\n'); print('scored', len(out))
