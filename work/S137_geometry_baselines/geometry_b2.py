#!/usr/bin/env python3
"""S137b B2: RGB + pose-only geometric predictor = CUT3R depth (VMem's alignment, chosen INIT) + forward warp.

usage: geometry_b2.py <init orig|fix|kps> <out.json> [<save_dir>]   (project CUT3R env + S17C overlay on PYTHONPATH)
If save_dir is given, the model-grid (576x576) warps (nearest-filled and raw with coverage mask) are saved per window.
Context = VMem static offsets 0,15,30,45; targets 60,75,90,105; poses converted to gl and then VMem-transformed,
exactly as VMem's construct_and_store_scene would pass them to CUT3R. No dataset depth is read.
"""
import io, json, math, sys, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(REPO / 'work/S135_scale_init'))
INIT, OUT = sys.argv[1], Path(sys.argv[2]); SAVE = Path(sys.argv[3]) if len(sys.argv) > 3 else None
SRC = REPO / 'work/S17C_interface_preparation/isolated_vmem_source'; CUT3R = SRC / 'extern/CUT3R'
WEIGHTS = REPO / 'data/cut3r/cut3r_512_dpt_4_64.pth'; DS = REPO / 'data/S134_tacc/datasets'
sys.path[:0] = [str(CUT3R), str(CUT3R / 'src')]
import torch
import torch.nn.functional as F
from PIL import Image
_tl = torch.load
torch.load = lambda p, *a, **k: _tl(p, *a, **{**k, 'weights_only': False}) if str(p) == str(WEIGHTS) else _tl(p, *a, **k)
from add_ckpt_path import add_path_to_dust3r
add_path_to_dust3r(str(WEIGHTS))
from src.dust3r.model import ARCroco3DStereo
import surfel_inference as SI
from cloud_opt.dust3r_opt import init_im_poses as IIP
from geometry_baselines import to_model_grid, load, warp, REL, WINDOWS, CTX, TGT  # noqa: E402  (scorer/warp from S137a)
from scipy import ndimage


def warp_raw(ctx, Tt, K):  # same splat as geometry_baselines.warp, without hole filling; returns image and coverage
    img, _ = warp(ctx, Tt, K)                       # filled image
    H, W = 480, 640; zb = np.full((H, W), np.inf); v, u = np.mgrid[0:H, 0:W]; Ki = np.linalg.inv(K)
    for rgb, depth, Tc in ctx:
        m = depth > 0; pix = np.stack([u[m], v[m], np.ones(m.sum())], 0)
        Xw = Tc[:3, :3] @ ((Ki @ pix) * depth[m]) + Tc[:3, 3:4]; Xt = Tt[:3, :3].T @ (Xw - Tt[:3, 3:4])
        z = Xt[2]; ok = z > 1e-3
        uu = np.round(K[0, 0] * Xt[0, ok] / z[ok] + K[0, 2]).astype(int); vv = np.round(K[1, 1] * Xt[1, ok] / z[ok] + K[1, 2]).astype(int)
        inb = (uu >= 0) & (uu < W) & (vv >= 0) & (vv < H); zb[vv[inb], uu[inb]] = np.minimum(zb[vv[inb], uu[inb]], z[ok][inb])
    return img, np.isfinite(zb)

LOG = []
if INIT == 'fix':
    _om = IIP.minimum_spanning_tree
    def _mst(imshapes, edges, pi, pj, ci, cj, im_conf, thr, *a, **k):
        return _om(imshapes, edges, pi, pj, ci, cj, im_conf, min(float(thr), min(float(c.median()) for c in im_conf)), *a, **k)
    IIP.minimum_spanning_tree = _mst
elif INIT == 'kps':
    import kps; kps.install(IIP, log=LOG)
elif INIT != 'orig':
    raise SystemExit(f'bad INIT {INIT}')
import os
if os.environ.get('OPTFIX') == '1':
    sys.path.insert(0, str(REPO / 'work/S138_depth_opt')); import optfix; optfix.install()


def rgb576(seq, f):  # VMem rgb() -> tensor_to_pil
    a = load(seq, f, 'color.png'); t = torch.from_numpy(a.transpose(2, 0, 1).copy()).float() / 255.
    t = F.interpolate(t.unsqueeze(0), (576, 768), mode='area')[:, :, :, 96:672][0]
    return Image.fromarray(np.clip(t.permute(1, 2, 0).numpy() * 255, 0, 255).astype(np.uint8))


def cut3r_depth_to_640(d):  # CUT3R 384x512 grid -> original 640x480 (nearest), NaN outside the crop
    v0, u0 = np.mgrid[0:480, 0:640]
    # pixel centres (codex R250): source centre u+0.5 -> CUT3R continuous coord c -> index round(c - 0.5)
    x = np.round(((u0 + 0.5) * 1.2 - 96) * 512 / 576 - 0.5).astype(int); y = np.round((v0 + 0.5) * 1.2 * 512 / 576 - 64 - 0.5).astype(int)
    ok = (x >= 0) & (x < 512) & (y >= 0) & (y < 384)
    out = np.zeros((480, 640)); out[ok] = d[y[ok], x[ok]]
    return out


torch.manual_seed(0); torch.set_num_threads(8)
model = ARCroco3DStereo.from_pretrained(str(WEIGHTS)).to('cpu').eval()
rows = []
for scene, rel in REL.items():
    seq = DS / rel / 'seq-01'; K = np.loadtxt(DS / rel / 'camera-intrinsics.txt').reshape(3, 3)
    for w in WINDOWS:
        ids = [w + o for o in CTX]; t0 = time.time(); LOG.clear()
        c2w = np.array([load(seq, f, 'pose.txt') for f in ids], dtype=np.float32)
        gl = c2w.copy(); gl[..., :, [1, 2]] *= -1        # dataset OpenCV -> gl (VMem input convention)
        vm = gl.copy(); vm[..., :, [1, 2]] *= -1         # VMem get_transformed_c2ws (back to OpenCV for CUT3R)
        out = SI.run_inference_from_pil([rgb576(seq, f) for f in ids], model, poses=vm, depths=None, lr=0.01, niter=400, device='cpu')
        depths = [cut3r_depth_to_640(d[0].numpy()) for d in out['depths']]
        ctx = [(load(seq, f, 'color.png'), dep, load(seq, f, 'pose.txt')) for f, dep in zip(ids, depths)]
        sse, cov = 0.0, []
        for o in TGT:
            t = w + o; Tt = load(seq, t, 'pose.txt'); ref = to_model_grid(load(seq, t, 'color.png'))
            img, c = warp(ctx, Tt, K); cov.append(c)
            if SAVE is not None:
                _, valid = warp_raw(ctx, Tt, K)
                vm = to_model_grid(np.repeat(valid[..., None].astype(np.uint8) * 255, 3, 2))[..., 0] > 127
                SAVE.mkdir(parents=True, exist_ok=True)
                np.savez_compressed(SAVE / f'{scene}__w{w:04d}__t{t:06d}.npz', filled=to_model_grid(img), valid=vm,
                                    target_c2w=Tt.astype(np.float32))
            d = to_model_grid(img).astype(np.int64) - ref.astype(np.int64); sse += float((d * d).sum())
        p = -10 * math.log10(sse / (4 * 576 * 576 * 3 * 255 * 255))
        rows.append({'scene': scene, 'window_start': w, 'init': INIT, 'optfix': os.environ.get('OPTFIX') == '1', 'b2_psnr': p, 'coverage': float(np.mean(cov)),
                     'depth_median': [float(np.median(x[x > 0])) for x in depths], 'kps': list(LOG),
                     'seconds': round(time.time() - t0, 1)})
        print(f'[b2] {INIT} {scene[-2:]} w{w} psnr {p:.2f} cov {np.mean(cov):.2f} ({rows[-1]["seconds"]}s)', flush=True)
OUT.write_text(json.dumps({'schema': 's137b-b2-v1', 'init': INIT, 'rows': rows,
                           'mean_psnr': float(np.mean([r['b2_psnr'] for r in rows]))}, indent=1) + '\n')
print('mean', np.mean([r['b2_psnr'] for r in rows]))
