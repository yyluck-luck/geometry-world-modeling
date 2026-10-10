#!/usr/bin/env python3
"""PSNR (C9 metric) + SSIM (S137 definition) for every output of a plan with cross-sequence refs; no warps needed.
usage: score_ssim_plan.py <gen_dir> <data_root containing scene_dir> <plan.json> <out.json>"""
import json, sys, math
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib.util
spec = importlib.util.spec_from_file_location('s140score', str(Path(__file__).resolve().parent / 'score_s140.py'))
RUN, DS, PLAN, OUT = Path(sys.argv[1]), Path(sys.argv[2]), json.loads(Path(sys.argv[3]).read_text()), Path(sys.argv[4])
src = open(Path(__file__).resolve().parent / 'score_s140.py').read().split('ctx = {c')[0]   # helpers only
ns = {'__name__': 'helpers'}; sys.argv = sys.argv[:1] + ['.', '.', str(sys.argv[3]), '.']; exec(compile(src, 'score_s140_helpers', 'exec'), ns)
ref_grid, pred_u8, ssim = ns['ref_grid'], ns['pred_u8'], ns['ssim']
scene = PLAN.get('scene_dir', 'chess'); ctx = {c['ctx_key']: c for c in PLAN['contexts']}; out = {}
for npy in sorted(RUN.glob('*__s*.npy')):
    if npy.name.endswith('.tmp.npy'): continue
    key, s = npy.stem.rsplit('__s', 1); c = ctx.get(key)
    if c is None: continue
    arr = np.load(npy); sse = 0.0; ss = []
    for i, r in enumerate(c['target_refs']):
        sq, f = r.split('/'); ref = ref_grid(DS / c.get('scene_dir', scene) / sq / f'frame-{f}.color.png'); p = pred_u8(arr[i])
        d = p.astype(np.int64) - ref.astype(np.int64); sse += float((d * d).sum()); ss.append(ssim(p, ref))
    out[npy.stem] = {'ctx_key': key, 'window_id': c['window_id'], 'arms': c.get('arms'), 'seed': int(s),
                     'psnr_db': -10 * math.log10(sse / (len(c['target_refs']) * 576 * 576 * 3 * 255 * 255)), 'ssim': float(np.mean(ss))}
OUT.write_text(json.dumps({'schema': 'ssim-plan-v1', 'runs': out}, indent=1) + '\n'); print('scored', len(out))
