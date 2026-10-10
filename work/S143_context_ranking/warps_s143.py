#!/usr/bin/env python3
"""S143 warps: the S139/S140 B2 pipeline (CUT3R + KPS depth of the 4 context frames in the given order, gl/OpenCV poses,
corrected depth mapping, 1-pixel z-buffer splat, nearest fill; CPU) for every unique set of POOL.json, saved like the S140
warp files (filled, valid on the 576x576 model grid). Context frames and target POSES only; no target RGB.
usage: warps_s143.py <POOL.json> <out_dir> [shard i/N]
Run: PYTHONPATH=work/S17C_environment/site-packages .venv-cut3r/bin/python ..."""
import json, sys, time
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
POOL, OUTD = json.loads(Path(sys.argv[1]).read_text()), Path(sys.argv[2])
SI, SN = map(int, (sys.argv[3] if len(sys.argv) > 3 else '0/1').split('/'))
_argv = list(sys.argv); sys.argv = [sys.argv[0]]
sys.path.insert(0, str(REPO / 'work/S135_scale_init')); sys.path.insert(0, str(REPO / 'work/S139_crossseq_revisit'))
sys.path.insert(0, str(REPO / 'work/S137_geometry_baselines'))
import repro_kps as R, kps
from geometry_baselines import to_model_grid, warp, warp_raw
sys.argv = _argv
from PIL import Image
ROOT = REPO / 'data/S139_chess/chess'; K = np.loadtxt(ROOT / 'camera-intrinsics.txt').reshape(3, 3)
LOG = []; kps.install(R.IIP, log=LOG)
model = R.ARCroco3DStereo.from_pretrained(str(R.WEIGHTS)).to('cpu').eval()


def load(ref, kind):
    s, f = ref.split('/'); p = ROOT / s / f'frame-{f}.{kind}'
    return np.asarray(Image.open(p).convert('RGB')) if kind == 'color.png' else np.loadtxt(p).reshape(4, 4)


def depth640(d):
    v0, u0 = np.mgrid[0:480, 0:640]
    x = np.round(((u0 + 0.5) * 1.2 - 96) * 512 / 576 - 0.5).astype(int); y = np.round((v0 + 0.5) * 1.2 * 512 / 576 - 64 - 0.5).astype(int)
    ok = (x >= 0) & (x < 512) & (y >= 0) & (y < 384); out = np.zeros((480, 640)); out[ok] = d[y[ok], x[ok]]; return out


OUTD.mkdir(parents=True, exist_ok=True)
jobs = [(w, s) for w in POOL['windows'] for s in w['sets']]
jobs = [j for k, j in enumerate(jobs) if k % SN == SI]
log = OUTD / f'WARP_LOG_{SI}of{SN}.jsonl'; t0 = time.time()
for w, s in jobs:
    names = [f"{w['window_id']}__{s['set_id']}__{t.replace('/', '_')}.npz" for t in w['targets']]
    if all((OUTD / n).exists() for n in names): continue
    LOG.clear(); refs = s['ctx_refs']
    pils = [R.tensor_to_pil(R.rgb(ROOT / r.split('/')[0], int(r.split('/')[1]))) for r in refs]
    c2w = np.array([load(r, 'pose.txt') for r in refs], dtype=np.float32)
    out = R.SI.run_inference_from_pil(pils, model, poses=c2w, depths=None, lr=0.01, niter=0, device='cpu')
    ctx = [(load(r, 'color.png'), depth640(d[0].numpy()), load(r, 'pose.txt')) for r, d in zip(refs, out['depths'])]
    for t, n in zip(w['targets'], names):
        Tt = load(t, 'pose.txt'); img, _ = warp(ctx, Tt, K); _, valid = warp_raw(ctx, Tt, K)
        vm = to_model_grid(np.repeat(valid[..., None].astype(np.uint8) * 255, 3, 2))[..., 0] > 127
        np.savez_compressed(OUTD / n, filled=to_model_grid(img), valid=vm)
    with log.open('a') as fh:
        fh.write(json.dumps({'window_id': w['window_id'], 'set_id': s['set_id'], 'kps': [l.get('kps') for l in LOG],
                             'seconds': round(time.time() - t0, 1)}) + '\n')
    print(f"[warp] {w['window_id']} {s['set_id']} kps {[l.get('kps') for l in LOG]} {time.time() - t0:.0f}s", flush=True)
print('[warp] done', len(jobs))
