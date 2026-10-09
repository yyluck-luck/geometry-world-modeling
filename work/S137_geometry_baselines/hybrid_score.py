#!/usr/bin/env python3
"""S137c-1 hybrid + SSIM secondary metric (CPU; reads target RGB, so run as a separate scoring process).

usage: hybrid_score.py <gen_dir> <datasets_root> <warp_dir> <out.json> [glob=*]
For every generated output whose name matches the glob (default: VMem static contexts), per target frame:
  vmem   = generated frame (score_c9 uint8 conversion)
  warp   = B2-kps nearest-filled warp at the target pose
  hybrid = warp where the splat covered the pixel, VMem elsewhere
Window-level PSNR (C9 integer metric aggregated over the 4 targets) and mean SSIM (Gaussian 11x11, sigma 1.5, luma).
"""
import io, json, math, sys
from pathlib import Path
import numpy as np
import torch
from PIL import Image

GEN, DS, WARP, OUT = map(Path, sys.argv[1:5]); PAT = sys.argv[5] if len(sys.argv) > 5 else None
REL = {'scene_13': 'heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13',
       'scene_14': 'heldout_3dmatch_scene14/extracted/rgbd-scenes-v2-scene_14'}
TGT = [60, 75, 90, 105]


def ref_grid(path):  # score_c9.future_rgb_to_model_grid
    rgb = np.asarray(Image.open(io.BytesIO(path.read_bytes())).convert('RGB'), dtype=np.uint8)
    t = torch.from_numpy(rgb.transpose(2, 0, 1).copy()).float().unsqueeze(0) / 255.0
    t = torch.nn.functional.interpolate(t, size=(576, 768), mode='area', antialias=False)[:, :, :, 96:672]
    return np.clip(t[0].permute(1, 2, 0).numpy() * 255.0, 0, 255).astype(np.uint8)


def pred_u8(frame):  # score_c9.prediction_to_uint8
    im = frame.transpose(1, 2, 0)
    if float(im.min()) < -0.1: im = (im + 1.0) / 2.0
    return np.clip(im * 255.0, 0, 255).astype(np.uint8)


_g = torch.exp(-((torch.arange(11) - 5.0) ** 2) / (2 * 1.5 ** 2)); _g = (_g / _g.sum())
_K = (_g[:, None] * _g[None, :])[None, None]


def ssim(a, b):
    def luma(x): return torch.from_numpy((x.astype(np.float64) @ np.array([0.299, 0.587, 0.114]))).float()[None, None]
    x, y = luma(a), luma(b); C1, C2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    f = lambda z: torch.nn.functional.conv2d(z, _K, padding=5)
    mx, my = f(x), f(y); sxx = f(x * x) - mx ** 2; syy = f(y * y) - my ** 2; sxy = f(x * y) - mx * my
    s = ((2 * mx * my + C1) * (2 * sxy + C2)) / ((mx ** 2 + my ** 2 + C1) * (sxx + syy + C2))
    return float(s[..., 5:-5, 5:-5].mean())


rows = []
for npy in sorted(GEN.glob('scene_1?__w????__*__s*.npy')):
    if npy.name.endswith('.tmp.npy'): continue
    key, s = npy.stem.rsplit('__s', 1); parts = key.split('__'); scene, start = parts[0], int(parts[1][1:])
    if PAT is None:  # default: static contexts only
        if parts[-1] != '-'.join(str(start + o) for o in (0, 15, 30, 45)): continue
    elif PAT not in key: continue
    seq = DS / REL[scene] / 'seq-01'; arr = np.load(npy)
    sse = {'vmem': 0.0, 'warp': 0.0, 'hybrid': 0.0}; ss = {k: [] for k in sse}; cov = []
    for i, o in enumerate(TGT):
        t = start + o; ref = ref_grid(seq / f'frame-{t:06d}.color.png')
        z = np.load(WARP / f'{scene}__w{start:04d}__t{t:06d}.npz'); valid = z['valid']; cov.append(float(valid.mean()))
        v = pred_u8(arr[i]); w = z['filled']; h = np.where(valid[..., None], w, v)
        for k, im in (('vmem', v), ('warp', w), ('hybrid', h)):
            d = im.astype(np.int64) - ref.astype(np.int64); sse[k] += float((d * d).sum()); ss[k].append(ssim(im, ref))
    n = 4 * 576 * 576 * 3
    rows.append({'ctx_key': key, 'scene': scene, 'window_start': start, 'convention': parts[2], 'seed': int(s),
                 'coverage': float(np.mean(cov)), **{f'psnr_{k}': -10 * math.log10(v / (n * 255 * 255)) for k, v in sse.items()},
                 **{f'ssim_{k}': float(np.mean(v)) for k, v in ss.items()}})
    print(f"{key} s{s} psnr vmem {rows[-1]['psnr_vmem']:.2f} warp {rows[-1]['psnr_warp']:.2f} hybrid {rows[-1]['psnr_hybrid']:.2f} "
          f"| ssim {rows[-1]['ssim_vmem']:.3f} {rows[-1]['ssim_warp']:.3f} {rows[-1]['ssim_hybrid']:.3f}", flush=True)
OUT.write_text(json.dumps({'schema': 's137c-hybrid-v1', 'rows': rows}, indent=1) + '\n')
print(len(rows), 'rows')
