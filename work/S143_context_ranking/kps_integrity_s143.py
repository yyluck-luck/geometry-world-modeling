#!/usr/bin/env python3
"""Integrity check (post hoc, CPU): original KPS (S139, 71528da4) + observer logging (S146 kps_orig_obs) on every S143 package
(bank order) and every S140 chess warp context (mem_vmem, original order): is the KPS objective finite, how many views are
finite at the chosen scale, positive-depth fraction. Same CUT3R call as the warp pipeline (niter 0, CPU). No targets read.
usage: kps_integrity_s143.py <out.json>   (PYTHONPATH=work/S17C_environment/site-packages .venv-cut3r/bin/python)"""
import json, sys, importlib.util
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
_argv = list(sys.argv); sys.argv = [sys.argv[0]]
sys.path.insert(0, str(REPO / 'work/S135_scale_init')); import repro_kps as R
sys.argv = _argv
spec = importlib.util.spec_from_file_location('kps_obs', str(REPO / 'work/S146_fresh12/kps_orig_obs.py')); K = importlib.util.module_from_spec(spec); spec.loader.exec_module(K)
LOG = []; K.install(R.IIP, log=LOG)
model = R.ARCroco3DStereo.from_pretrained(str(R.WEIGHTS)).to('cpu').eval()
ROOT = REPO / 'data/S139_chess/chess'
def load_pose(ref): s, f = ref.split('/'); return np.loadtxt(ROOT / s / f'frame-{f}.pose.txt').reshape(4, 4)
jobs = []
P = json.loads((HERE / 'POOL.json').read_text())
for w in P['windows']:
    for s in w['sets']: jobs.append(('S143', w['window_id'], s['set_id'], s['ctx_refs']))
for c in json.loads((REPO / 'work/S140_warp_guided/plan_confirm.json').read_text())['contexts']:
    jobs.append(('S140', c['window_id'], 'mem_vmem_orig', c['ctx_refs']))
rows = []
for src, wid, sid, refs in jobs:
    pils = [R.tensor_to_pil(R.rgb(ROOT / r.split('/')[0], int(r.split('/')[1]))) for r in refs]
    c2w = np.array([load_pose(r) for r in refs], dtype=np.float32); LOG.clear()
    R.SI.run_inference_from_pil(pils, model, poses=c2w, depths=None, lr=0.01, niter=0, device='cpu')
    l = LOG[0]
    rows.append({'source': src, 'window_id': wid, 'set_id': sid, 'err': l['median_reproj_px'], 'finite': bool(np.isfinite(l['median_reproj_px'])),
                 'n_finite_at_best': sum(l['finite_at_best']), 'n_views': len(l['finite_at_best']), 'min_positive_depth_frac': min(l['positive_depth_frac'])})
    print(src, wid, sid, rows[-1]['finite'], rows[-1]['n_finite_at_best'], round(rows[-1]['min_positive_depth_frac'], 3), flush=True)
summ = {src: {'n': sum(r['source'] == src for r in rows), 'non_finite': sum(r['source'] == src and not r['finite'] for r in rows),
              'min_positive_depth_frac': min(r['min_positive_depth_frac'] for r in rows if r['source'] == src)} for src in ('S143', 'S140')}
Path(sys.argv[1]).write_text(json.dumps({'summary': summ, 'rows': rows}, indent=1, default=float) + '\n'); print(json.dumps(summ))
