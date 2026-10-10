#!/usr/bin/env python3
"""S139: KPS convention detector (S135) on 7-Scenes chess: per window bank, the first 5 frames (H frames 0..200)
under gl vs native; lower minimum median reprojection error = the convention consistent with CUT3R. CPU."""
import io, json, sys
from pathlib import Path
import numpy as np
sys.argv += [] ; REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'work/S135_scale_init'))
sys.argv = [sys.argv[0]]
import repro_kps as R   # CUT3R env, model loader, rgb()/tensor_to_pil() identical to VMem
import kps
M = json.loads((REPO / 'work/S139_crossseq_revisit/WINDOW_MANIFEST.json').read_text())
ROOT = REPO / 'data/S139_chess/chess'
LOG = []; kps.install(R.IIP, log=LOG)
model = R.ARCroco3DStereo.from_pretrained(str(R.WEIGHTS)).to('cpu').eval()
def rgb(ref): s, f = ref.split('/'); return R.rgb(ROOT / s, int(f))
def pose(ref, conv):
    s, f = ref.split('/'); p = np.loadtxt(ROOT / s / f'frame-{f}.pose.txt', dtype=np.float32).reshape(4, 4)
    if conv == 'gl': p = p.copy(); p[:, [1, 2]] *= -1
    return p
rows = []
for pair in sorted({w['pair'] for w in M['windows']}):
    w = next(x for x in M['windows'] if x['pair'] == pair); refs = w['bank'][:5]
    pils = [R.tensor_to_pil(rgb(r)) for r in refs]; res = {}
    for conv in ('gl', 'native'):
        c2 = np.array([pose(r, conv) for r in refs]); c2[..., :, [1, 2]] *= -1   # VMem get_transformed_c2ws
        LOG.clear(); R.SI.run_inference_from_pil(pils, model, poses=c2, depths=None, lr=0.01, niter=0, device='cpu')
        res[conv] = {'median_reproj_px': LOG[0]['median_reproj_px'], 'sigma': LOG[0]['sigma']}
    rows.append({'pair': pair, 'frames': refs, **res, 'winner': min(res, key=lambda k: res[k]['median_reproj_px'])})
    print(pair, res, '->', rows[-1]['winner'], flush=True)
out = REPO / 'work/S139_crossseq_revisit/CONVENTION_CHECK.json'
out.write_text(json.dumps({'rows': rows, 'gl_wins': sum(r['winner'] == 'gl' for r in rows)}, indent=1) + '\n')
