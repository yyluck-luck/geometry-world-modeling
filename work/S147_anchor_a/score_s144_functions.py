"""Verbatim helper block of work/S144_A_wgs/score_s144.py (ref_grid .. blend), imported by score_s147.py."""
import io, math
from pathlib import Path
import numpy as np, torch
from PIL import Image
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
