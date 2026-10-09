#!/usr/bin/env python3
"""S133: reproduce VMem's first surfel construction (stage 1) on CPU and instrument the scale.

Mirrors run_support_retrieval_c9.py up to the first construct_and_store_scene call:
bank frames start+{0,5,10,15,20}, VMem's rgb() crop -> tensor_to_pil, poses passed through
get_transformed_c2ws (y/z columns negated), run_inference_from_pil(niter=400, lr=0.01).
It does NOT load the diffusion model. It records, per window:
  - the similarity scale s that align_multiple_poses applies to CUT3R's MST poses,
  - the median pairwise camera distance of the MST poses (src) and the known poses (target),
  - the median optimised depth per frame vs the median dataset depth of the same frame.
Run with PYTHONPATH=work/S17C_environment/site-packages .venv-cut3r/bin/python (project CUT3R env + overlay).
Usage: repro_stage1.py [--windows scene_13:150,...] [--out results.json] [--niter 400]
"""
import argparse, io, json, os, sys, time
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / 'work/S17C_interface_preparation/isolated_vmem_source'
CUT3R = SRC / 'extern/CUT3R'
WEIGHTS = REPO / 'data/cut3r/cut3r_512_dpt_4_64.pth'
DS = REPO / 'data/S133_scale_debug/datasets'
SCENE_DIR = {'scene_13': 'heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13',
             'scene_14': 'heldout_3dmatch_scene14/extracted/rgbd-scenes-v2-scene_14'}
ALL_WINDOWS = [(s, w) for s in ('scene_13', 'scene_14') for w in (50, 100, 150, 200, 250, 300, 350)]
sys.path[:0] = [str(CUT3R), str(CUT3R / 'src')]

import torch
import torch.nn.functional as F
from PIL import Image

_torch_load = torch.load
def _load(path, *a, **k):  # same override as the S111/C9 runners for the pinned checkpoint
    if str(path) == str(WEIGHTS):
        k['weights_only'] = False
    return _torch_load(path, *a, **k)
torch.load = _load

from add_ckpt_path import add_path_to_dust3r
add_path_to_dust3r(str(WEIGHTS))
from src.dust3r.model import ARCroco3DStereo
import surfel_inference as SI
from cloud_opt.dust3r_opt import init_im_poses as IIP

PROBE = {}
PNP_FIX = False
_orig_align = IIP.align_multiple_poses
def _probe_align(src, tgt):
    s, R, T = _orig_align(src, tgt)
    from scipy.spatial.distance import pdist
    PROBE.update(
        s=float(s),
        src_med_dist=float(np.median(pdist(src[:, :3, 3].detach().cpu().numpy()))),
        tgt_med_dist=float(np.median(pdist(tgt[:, :3, 3].detach().cpu().numpy()))),
        src_centers=src[:, :3, 3].detach().cpu().numpy().tolist())
    return s, R, T
IIP.align_multiple_poses = _probe_align

_orig_pnp = IIP.fast_pnp
def _probe_pnp(pts3d, focal, msk, device, pp=None, niter_PnP=10):
    res = _orig_pnp(pts3d, focal, msk, device, pp=pp, niter_PnP=niter_PnP)
    PROBE.setdefault('pnp', []).append(dict(n_mask=int(msk.sum()), n_pix=int(msk.numel()),
                                            ok=bool(res), focal_in=None if focal is None else float(focal)))
    return res
IIP.fast_pnp = _probe_pnp
_orig_mst = IIP.minimum_spanning_tree
def _probe_mst(imshapes, edges, pred_i, pred_j, conf_i, conf_j, im_conf, min_conf_thr, *a, **k):
    PROBE['im_conf_median'] = [float(c.median()) for c in im_conf]
    PROBE['im_conf_frac_gt_thr'] = [float((c > min_conf_thr).float().mean()) for c in im_conf]
    PROBE['min_conf_thr'] = float(min_conf_thr)
    if PNP_FIX:  # S133 candidate fix: adaptive PnP mask threshold (cf. init_from_known_poses' min(thr, conf.min()-0.1))
        min_conf_thr = min(float(min_conf_thr), min(float(c.median()) for c in im_conf))
    PROBE['pnp_mask_thr'] = float(min_conf_thr)
    return _orig_mst(imshapes, edges, pred_i, pred_j, conf_i, conf_j, im_conf, min_conf_thr, *a, **k)
IIP.minimum_spanning_tree = _probe_mst


def rgb(seq, fid):  # identical to run_support_retrieval_c9.rgb
    a = np.asarray(Image.open(seq / f'frame-{fid:06d}.color.png').convert('RGB'))
    t = torch.from_numpy(a.transpose(2, 0, 1).copy()).float() / 255.
    t = F.interpolate(t.unsqueeze(0), (576, 768), mode='area')[:, :, :, 96:672]
    return (t * 2 - 1)[0]


def tensor_to_pil(t):  # identical to vmem utils.util.tensor_to_pil for a [-1,1] tensor
    im = t.permute(1, 2, 0).numpy()
    if im.min() < -0.1:
        im = (im + 1) / 2.0
    return Image.fromarray(np.clip(im * 255, 0, 255).astype(np.uint8))


def pose(seq, fid, convention):
    p = np.loadtxt(io.StringIO((seq / f'frame-{fid:06d}.pose.txt').read_text()), dtype=np.float32).reshape(4, 4)
    if convention == 'gl':
        p = p.copy(); p[:, [1, 2]] *= -1
    return p


def dataset_depth_median(seq, fid):
    d = np.asarray(Image.open(seq / f'frame-{fid:06d}.depth.png'), dtype=np.float64) / 1000.0
    d = d[:, 96 * 640 // 768:640 - 96 * 640 // 768]  # same horizontal centre crop as rgb()
    return float(np.median(d[d > 0]))


def run_window(model, scene, start, niter, convention):
    seq = DS / SCENE_DIR[scene] / 'seq-01'
    bank = [start + o for o in (0, 5, 10, 15, 20)]
    pils = [tensor_to_pil(rgb(seq, f)) for f in bank]
    c2ws = np.array([pose(seq, f, convention) for f in bank])
    c2ws_t = c2ws.copy(); c2ws_t[..., :, [1, 2]] *= -1  # VMem get_transformed_c2ws
    PROBE.clear(); t0 = time.time()
    scene_out = SI.run_inference_from_pil(pils, model, poses=c2ws_t, depths=None, lr=0.01, niter=niter, device='cpu')
    depths = [d[0].numpy() for d in scene_out['depths']]
    est = [float(np.median(d[d > 0])) for d in depths]
    gt = [dataset_depth_median(seq, f) for f in bank]
    ratio = [e / g for e, g in zip(est, gt)]
    return dict(scene=scene, window_start=start, convention=convention, pnp_fix=PNP_FIX, bank=bank, niter=niter,
                seconds=round(time.time() - t0, 1), **PROBE,
                est_depth_median=est, dataset_depth_median=gt, depth_ratio=ratio,
                depth_ratio_median=float(np.median(ratio)),
                focal=np.asarray(scene_out['camera_info']['focal']).ravel().tolist())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--windows', default='')
    ap.add_argument('--out', default=str(Path(__file__).with_name('STAGE1_REPRO.json')))
    ap.add_argument('--niter', type=int, default=400)
    ap.add_argument('--convention', default='native', choices=['native', 'gl'])
    ap.add_argument('--pnp-fix', action='store_true')
    a = ap.parse_args()
    global PNP_FIX; PNP_FIX = a.pnp_fix
    wins = [(s, int(w)) for s, w in (x.split(':') for x in a.windows.split(','))] if a.windows else ALL_WINDOWS
    torch.manual_seed(0); torch.set_num_threads(int(os.environ.get('S133_THREADS', '8')))
    model = ARCroco3DStereo.from_pretrained(str(WEIGHTS)).to('cpu').eval()
    out = Path(a.out); rows = json.loads(out.read_text())['rows'] if out.exists() else []
    for scene, start in wins:
        r = run_window(model, scene, start, a.niter, a.convention)
        rows = [x for x in rows if (x['scene'], x['window_start'], x['convention'], x.get('pnp_fix', False), x['niter']) !=
                (scene, start, a.convention, PNP_FIX, a.niter)] + [r]
        out.write_text(json.dumps({'schema': 's133-stage1-repro-v1', 'device': 'cpu', 'rows': rows}, indent=1) + '\n')
        print(f"[s133] {a.convention} fix={int(PNP_FIX)} {scene} w{start} s={r.get('s', float('nan')):.3g} src_med={r.get('src_med_dist', float('nan')):.4g} "
              f"tgt_med={r.get('tgt_med_dist', float('nan')):.4g} depth_ratio_med={r['depth_ratio_median']:.3g} ({r['seconds']}s)", flush=True)


if __name__ == '__main__':
    main()
