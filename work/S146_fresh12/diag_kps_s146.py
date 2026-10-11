#!/usr/bin/env python3
"""S146 diagnostic (bank-only, no targets, no generation): for every window and step A's construction sizes (5, 20, 32 bank
frames, star rooted at bank[0], gl/geometry poses), original KPS with per-view logging: residual valid at any grid scale,
finite at the chosen scale, fraction of positive finite depth. usage: diag_kps_s146.py <stage12> <manifest_dir> <out.json> [shard i/N]"""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import s141_common as C
import torch
import modeling.pipeline as PM
from cloud_opt.dust3r_opt import init_im_poses as IIP
from utils import tensor_to_pil
import kps_diag as kps
STAGE, MD, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); SI, SN = map(int, (sys.argv[4] if len(sys.argv) > 4 else '0/1').split('/'))
LOG = []; kps.install(IIP, log=LOG)
ck = str(C.WEIGHTS / 'cut3r_512_dpt_4_64.pth'); PM.add_path_to_dust3r(ck)
model = PM.ARCroco3DStereo.from_pretrained(ck).to('cpu').eval()
jobs = []
for mf in sorted(MD.glob('WINDOW_MANIFEST_*_*.json')):
    M = json.loads(mf.read_text())
    for w in M['windows']: jobs.append((M['scene_dir'], w))
jobs = [j for k, j in enumerate(jobs) if k % SN == SI]; rows = []
for room, w in jobs:
    root = STAGE / room; bank = w['bank']; res = {}
    for n in (5, 20, 32):
        refs = bank[:n]
        pils = [tensor_to_pil(C.load_rgb_path(root / r.split('/')[0] / f"frame-{r.split('/')[1]}.color.png")) for r in refs]
        gp = np.array([C.load_pose_path(root / r.split('/')[0] / f"frame-{r.split('/')[1]}.pose.txt") for r in refs], dtype=np.float32)
        LOG.clear()
        with torch.no_grad():
            PM.run_inference_from_pil(pils, model, poses=gp, depths=None, lr=0.01, niter=0, device='cpu')
        l = LOG[0]
        res[n] = {'err': l['median_reproj_px'], 'sigma': l['sigma'], 'n_views': len(l['grid_valid_any']), 'n_grid_valid': sum(l['grid_valid_any']),
                  'n_finite_at_best': sum(l['finite_at_best']), 'views_not_finite_at_best': [i + 1 for i, v in enumerate(l['finite_at_best']) if not v],
                  'positive_depth_frac': l['positive_depth_frac']}
    rows.append({'room': room, 'window_id': w['window_id'], 'constructions': res})
    print(w['window_id'], {n: (round(r['err'], 1) if np.isfinite(r['err']) else 'inf', r['n_finite_at_best'], r['n_views'], round(min(r['positive_depth_frac']), 3)) for n, r in res.items()}, flush=True)
OUT.write_text(json.dumps({'rows': rows}, indent=1, default=float) + '\n')
