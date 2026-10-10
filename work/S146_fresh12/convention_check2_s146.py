#!/usr/bin/env python3
"""S146 Amendment 1 second convention check: same detector as convention_check_s146.py on a different fixed frame set per
room: the first window's recent C bank frames C[s0, s0+5, ..., s0+20]. usage: convention_check2_s146.py <stage12> <manifest dir> <out.json>"""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import s141_common as C
import torch
import modeling.pipeline as PM
from cloud_opt.dust3r_opt import init_im_poses as IIP
from utils import tensor_to_pil
import kps
STAGE, MD, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
LOG = []; kps.install(IIP, log=LOG)
ck = str(C.WEIGHTS / 'cut3r_512_dpt_4_64.pth'); PM.add_path_to_dust3r(ck)
model = PM.ARCroco3DStereo.from_pretrained(ck).to('cpu').eval()
rows = []
for mf in sorted(MD.glob('WINDOW_MANIFEST_*_*.json')):
    M = json.loads(mf.read_text()); root = STAGE / M['scene_dir']; refs = M['windows'][0]['bank'][20:25]
    assert all(r.startswith('seq-01/') for r in refs) and not set(refs) & set(t for w in M['windows'] for t in w['targets'])
    pils = [tensor_to_pil(C.load_rgb_path(root / r.split('/')[0] / f"frame-{r.split('/')[1]}.color.png")) for r in refs]
    res = {}
    for conv in ('gl', 'native'):
        c2 = []
        for r in refs:
            p = C.load_pose_path(root / r.split('/')[0] / f"frame-{r.split('/')[1]}.pose.txt").copy()
            if conv == 'gl': p[:, [1, 2]] *= -1
            c2.append(p)
        c2 = np.array(c2, dtype=np.float32); c2[..., :, [1, 2]] *= -1
        LOG.clear()
        with torch.no_grad():
            PM.run_inference_from_pil(pils, model, poses=c2, depths=None, lr=0.01, niter=0, device='cpu')
        res[conv] = {'median_reproj_px': float(LOG[0]['median_reproj_px']), 'sigma': float(LOG[0]['sigma'])}
    win = min(res, key=lambda k: res[k]['median_reproj_px'])
    rows.append({'room': M['scene_dir'], 'frames': refs, **res, 'winner': win}); print(M['scene_dir'], res, '->', win, flush=True)
OUT.write_text(json.dumps({'rows': rows}, indent=1) + '\n')
