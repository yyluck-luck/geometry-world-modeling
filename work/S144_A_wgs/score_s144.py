#!/usr/bin/env python3
"""S144 scorer for every arm and control (R263 §3.4), one frozen conversion path.
usage: score_s144.py <F_dir> <A_dir> <data_root> <gen plan (F)> <warp_dir> <seeds e.g. 3,4> <alpha.json|FIT> <out.json>
Arms per (context, seed): F_C, F_R, A_C, A_R, [A_none if present], B2, V=D(E(B2)), P_V, P_FC, P_AC (covered from G, holes from
B2, original pixel masks), REV_AC (covered B2, holes A_C), BL_V/BL_FC/BL_AC = alpha*G + (1-alpha)*B2 (float, clip, truncate
to uint8 once). With FIT, blends are scored for every alpha in {0, 0.05, ..., 1} (PSNR only) for development fitting.
PSNR: SSE pooled over the four targets (integer RGB); SSIM: S140 definition, frame mean; regions on original masks."""
import io, json, math, sys
from pathlib import Path
import numpy as np, torch
from PIL import Image
FD, AD, DS, PL, WD = [Path(a) for a in sys.argv[1:6]]; SEEDS = [int(x) for x in sys.argv[6].split(',')]
ALPHA = None if sys.argv[7] == 'FIT' else json.loads(Path(sys.argv[7]).read_text())['alpha']; OUT = Path(sys.argv[8])
GRID = [round(0.05 * i, 2) for i in range(21)]
ctxs = [c for c in json.loads(PL.read_text())['contexts'] if c['mode'] == 'W2CR']


def ref_grid(p):  # score_s140.ref_grid
    rgb = np.asarray(Image.open(io.BytesIO(p.read_bytes())).convert('RGB'), dtype=np.uint8)
    t = torch.from_numpy(rgb.transpose(2, 0, 1).copy()).float().unsqueeze(0) / 255.0
    t = torch.nn.functional.interpolate(t, size=(576, 768), mode='area', antialias=False)[:, :, :, 96:672]
    return np.clip(t[0].permute(1, 2, 0).numpy() * 255.0, 0, 255).astype(np.uint8)
def pred_u8(fr):  # score_s140.pred_u8 (frozen range heuristic)
    im = fr.transpose(1, 2, 0)
    if float(im.min()) < -0.1: im = (im + 1.0) / 2.0
    return np.clip(im * 255.0, 0, 255).astype(np.uint8)
_g = torch.exp(-((torch.arange(11) - 5.0) ** 2) / (2 * 1.5 ** 2)); _g = _g / _g.sum(); _K = (_g[:, None] * _g[None, :])[None, None]
def ssim(a, b):  # score_s140.ssim
    lum = lambda x: torch.from_numpy((x.astype(np.float64) @ np.array([0.299, 0.587, 0.114]))).float()[None, None]
    x, y = lum(a), lum(b); C1, C2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2; f = lambda z: torch.nn.functional.conv2d(z, _K, padding=5)
    mx, my = f(x), f(y); sxx = f(x * x) - mx ** 2; syy = f(y * y) - my ** 2; sxy = f(x * y) - mx * my
    return float((((2 * mx * my + C1) * (2 * sxy + C2)) / ((mx ** 2 + my ** 2 + C1) * (sxx + syy + C2)))[..., 5:-5, 5:-5].mean())
def metrics(ims, refs, masks, with_ssim=True):
    n = len(refs) * 576 * 576 * 3; sse = cov_sse = hole_sse = 0.0; cov_n = hole_n = 0
    for p, r, m in zip(ims, refs, masks):
        e = ((p.astype(np.int64) - r.astype(np.int64)) ** 2).sum(-1); sse += float(e.sum())
        cov_sse += float(e[m].sum()); hole_sse += float(e[~m].sum()); cov_n += int(m.sum()) * 3; hole_n += int((~m).sum()) * 3
    ps = lambda s, k: (-10 * math.log10(max(s, 1e-12) / (k * 255 * 255))) if k > 0 else None
    out = {'psnr_db': ps(sse, n), 'psnr_covered': ps(cov_sse, cov_n), 'psnr_holes': ps(hole_sse, hole_n)}
    if with_ssim: out['ssim'] = float(np.mean([ssim(p, r) for p, r in zip(ims, refs)]))
    return out
def blend(G, W, a): return [np.clip(a * g.astype(np.float64) + (1 - a) * w.astype(np.float64), 0, 255).astype(np.uint8) for g, w in zip(G, W)]
def paste(cov_src, hole_src, masks): return [np.where(m[..., None], c, h) for c, h, m in zip(cov_src, hole_src, masks)]


runs = {}
for c in ctxs:
    root = DS / c['scene_dir']
    refs = [ref_grid(root / r.split('/')[0] / f"frame-{r.split('/')[1]}.color.png") for r in c['target_refs']]
    ws = [np.load(WD / f) for f in c['warp_files']]; B2 = [z['filled'] for z in ws]; M = [z['valid'].astype(bool) for z in ws]
    V = [pred_u8(f) for f in np.load(FD / f"{c['ctx_key']}__V__s0.npy")]
    for s in SEEDS:
        arm = {'B2': B2, 'V': V}
        for tag, d in (('F', FD), ('A', AD)):
            for e in ('C', 'R'):
                arm[f'{tag}_{e}'] = [pred_u8(f) for f in np.load(d / f"{c['ctx_key']}__{e}__s{s}.npy")]
        an = AD / f"{c['ctx_key']}__s{s}.npy"
        if an.exists(): arm['A_none'] = [pred_u8(f) for f in np.load(an)]
        arm['P_V'] = paste(V, B2, M); arm['P_FC'] = paste(arm['F_C'], B2, M); arm['P_AC'] = paste(arm['A_C'], B2, M)
        arm['REV_AC'] = paste(B2, arm['A_C'], M)
        rec = {'window_id': c['window_id'], 'seed': s, 'seq': c.get('seq'), 'kind': c.get('kind')}
        for k, ims in arm.items(): rec[k] = metrics(ims, refs, M)
        for gname, G in (('V', V), ('FC', arm['F_C']), ('AC', arm['A_C'])):
            if ALPHA is None:
                rec[f'BLgrid_{gname}'] = {str(a): metrics(blend(G, B2, a), refs, M, with_ssim=False)['psnr_db'] for a in GRID}
            else:
                rec[f'BL_{gname}'] = metrics(blend(G, B2, ALPHA[gname]), refs, M)
        runs[f"{c['ctx_key']}__s{s}"] = rec
    print(c['ctx_key'], {k: round(v['psnr_db'], 2) for k, v in rec.items() if isinstance(v, dict) and 'psnr_db' in v}, flush=True)
OUT.write_text(json.dumps({'schema': 's144-scores-v1', 'alpha': ALPHA, 'seeds': SEEDS, 'runs': runs}, indent=1) + '\n')
print('scored', len(runs))
