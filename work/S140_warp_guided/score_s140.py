#!/usr/bin/env python3
"""S140 scorer: C9 PSNR metric (score_c9.py functions) + SSIM (S137 hybrid_score.ssim) per output, plus the same metrics
for the warp itself. Separate CPU process; reads target RGB. usage: score_s140.py <gen_dir> <data_root> <plan.json> <warp_dir> [<out.json>]"""
import io, json, math, sys
from pathlib import Path
import numpy as np, torch
from PIL import Image
RUN, DS, PLAN, WARP = Path(sys.argv[1]), Path(sys.argv[2]), json.loads(Path(sys.argv[3]).read_text()), Path(sys.argv[4])
OUTF = Path(sys.argv[5]) if len(sys.argv) > 5 else RUN / 'S140_SCORES.json'   # optional output path
def ref_grid(p):
    rgb = np.asarray(Image.open(io.BytesIO(p.read_bytes())).convert('RGB'), dtype=np.uint8)
    t = torch.from_numpy(rgb.transpose(2, 0, 1).copy()).float().unsqueeze(0) / 255.0
    t = torch.nn.functional.interpolate(t, size=(576, 768), mode='area', antialias=False)[:, :, :, 96:672]
    return np.clip(t[0].permute(1, 2, 0).numpy() * 255.0, 0, 255).astype(np.uint8)
def pred_u8(fr):
    im = fr.transpose(1, 2, 0)
    if float(im.min()) < -0.1: im = (im + 1.0) / 2.0
    return np.clip(im * 255.0, 0, 255).astype(np.uint8)
_g = torch.exp(-((torch.arange(11) - 5.0) ** 2) / (2 * 1.5 ** 2)); _g = _g / _g.sum(); _K = (_g[:, None] * _g[None, :])[None, None]
def ssim(a, b):
    lum = lambda x: torch.from_numpy((x.astype(np.float64) @ np.array([0.299, 0.587, 0.114]))).float()[None, None]
    x, y = lum(a), lum(b); C1, C2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2; f = lambda z: torch.nn.functional.conv2d(z, _K, padding=5)
    mx, my = f(x), f(y); sxx = f(x * x) - mx ** 2; syy = f(y * y) - my ** 2; sxy = f(x * y) - mx * my
    return float((((2 * mx * my + C1) * (2 * sxy + C2)) / ((mx ** 2 + my ** 2 + C1) * (sxx + syy + C2)))[..., 5:-5, 5:-5].mean())
ctx = {c['ctx_key']: c for c in PLAN['contexts']}; out = {}; warp_scores = {}
for npy in sorted(RUN.glob('*__s*.npy')):
    if npy.name.endswith('.tmp.npy'): continue
    key, s = npy.stem.rsplit('__s', 1); c = ctx.get(key)
    if c is None: continue
    arr = np.load(npy); root = DS / c['scene_dir']; sse = sw = 0.0; ss = []; sws = []
    reg = {'cov_sse': 0.0, 'cov_n': 0, 'hole_sse': 0.0, 'hole_n': 0, 'wcov_sse': 0.0, 'whole_sse': 0.0}   # region split by warp coverage
    for i, r in enumerate(c['target_refs']):
        sq, f = r.split('/'); ref = ref_grid(root / sq / f'frame-{f}.color.png'); p = pred_u8(arr[i])
        d = p.astype(np.int64) - ref.astype(np.int64); sse += float((d * d).sum()); ss.append(ssim(p, ref))
        zz = np.load(WARP / c['warp_files'][i]); val = zz['valid']; dw2 = zz['filled'].astype(np.int64) - ref.astype(np.int64)
        e = (d * d).sum(-1); ew = (dw2 * dw2).sum(-1)
        reg['cov_sse'] += float(e[val].sum()); reg['hole_sse'] += float(e[~val].sum()); reg['cov_n'] += int(val.sum()) * 3; reg['hole_n'] += int((~val).sum()) * 3
        reg['wcov_sse'] += float(ew[val].sum()); reg['whole_sse'] += float(ew[~val].sum())
        if c['window_id'] not in warp_scores:
            w = np.load(WARP / c['warp_files'][i])['filled']; dw = w.astype(np.int64) - ref.astype(np.int64); sw += float((dw * dw).sum()); sws.append(ssim(w, ref))
    n = len(c['target_refs']) * 576 * 576 * 3
    if c['window_id'] not in warp_scores:
        warp_scores[c['window_id']] = {'psnr': -10 * math.log10(sw / (n * 255 * 255)), 'ssim': float(np.mean(sws))}
    out[npy.stem] = {'ctx_key': key, 'window_id': c['window_id'], 'mode': c['mode'], 'strength': c['strength'], 'seed': int(s),
                     'psnr_db': -10 * math.log10(sse / (n * 255 * 255)), 'ssim': float(np.mean(ss)),
                     'psnr_covered': -10 * math.log10(max(reg['cov_sse'], 1) / (max(reg['cov_n'], 1) * 255 * 255)),
                     'psnr_holes': -10 * math.log10(max(reg['hole_sse'], 1) / (max(reg['hole_n'], 1) * 255 * 255)),
                     'warp_psnr_covered': -10 * math.log10(max(reg['wcov_sse'], 1) / (max(reg['cov_n'], 1) * 255 * 255)),
                     'warp_psnr_holes': -10 * math.log10(max(reg['whole_sse'], 1) / (max(reg['hole_n'], 1) * 255 * 255)),
                     'hole_fraction': reg['hole_n'] / max(reg['hole_n'] + reg['cov_n'], 1)}
OUTF.write_text(json.dumps({'schema': 's140-scores-v1', 'runs': out, 'warps': warp_scores}, indent=1) + '\n')
print('scored', len(out), 'warps', len(warp_scores))
