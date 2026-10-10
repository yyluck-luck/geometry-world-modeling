#!/usr/bin/env python3
"""S139 CPU baselines (as S137): B0 copy the pose-nearest bank frame per target; B2 CUT3R + KPS forward warp of a
4-frame context set into each target camera (nearest fill). gl poses as VMem; no dataset depth. C9 scorer metric.
usage: baselines_s139.py <arm static_recent|mem_vmem|mem_pose|copy_bank> <plan.json|NONE> <out.json>
"""
import io, json, math, sys, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
ARM, OUT = sys.argv[1], Path(sys.argv[3]); PLAN = json.loads(Path(sys.argv[2]).read_text()) if sys.argv[2] != 'NONE' else None
SAVE = Path(sys.argv[4]) if len(sys.argv) > 4 else None   # S140: save model-grid warps (filled, valid)
_ARGV = list(sys.argv); sys.argv = [sys.argv[0]]
sys.path.insert(0, str(REPO / 'work/S135_scale_init')); sys.path.insert(0, str(REPO / 'work/S137_geometry_baselines'))
from geometry_baselines import to_model_grid, warp, geo          # noqa: E402 (S137 warp, scorer transform, VMem geodesic)
ROOT = REPO / 'data/S139_chess/chess'
K = np.loadtxt(ROOT / 'camera-intrinsics.txt').reshape(3, 3)
M = json.loads((HERE / 'WINDOW_MANIFEST.json').read_text()); MW = {w['window_id']: w for w in M['windows']}
from PIL import Image


def load(ref, kind):
    s, f = ref.split('/'); p = ROOT / s / f'frame-{f}.{kind}'
    return np.asarray(Image.open(p).convert('RGB')) if kind == 'color.png' else np.loadtxt(p).reshape(4, 4)


def psnr4(preds, refs):
    sse = sum(float(((to_model_grid(p).astype(np.int64) - to_model_grid(load(r, 'color.png')).astype(np.int64)) ** 2).sum())
              for p, r in zip(preds, refs))
    return -10 * math.log10(sse / (len(refs) * 576 * 576 * 3 * 255 * 255))


rows = []
if ARM == 'copy_bank':
    for w in M['windows']:
        bank = w['bank']; bp = [load(r, 'pose.txt') for r in bank]; preds = []
        for t in w['targets']:
            Tt = load(t, 'pose.txt'); preds.append(load(bank[int(np.argmin([geo(Tt, p) for p in bp]))], 'color.png'))
        rows.append({'window_id': w['window_id'], 'psnr': psnr4(preds, w['targets'])})
        print(f"[b0] {w['window_id']} {rows[-1]['psnr']:.2f}", flush=True)
else:
    import repro_kps as R, kps                                    # CUT3R env + VMem rgb()/tensor_to_pil()
    LOG = []; kps.install(R.IIP, log=LOG)
    model = R.ARCroco3DStereo.from_pretrained(str(R.WEIGHTS)).to('cpu').eval()
    def depth640(d):                                              # corrected pixel-centre map (S137 Amendment 2)
        v0, u0 = np.mgrid[0:480, 0:640]
        x = np.round(((u0 + 0.5) * 1.2 - 96) * 512 / 576 - 0.5).astype(int); y = np.round((v0 + 0.5) * 1.2 * 512 / 576 - 64 - 0.5).astype(int)
        ok = (x >= 0) & (x < 512) & (y >= 0) & (y < 384); out = np.zeros((480, 640)); out[ok] = d[y[ok], x[ok]]; return out
    ctxs = ([{'window_id': w['window_id'], 'ctx_refs': w['static_recent'], 'target_refs': w['targets']} for w in M['windows']]
            if ARM == 'static_recent' else [c for c in PLAN['contexts'] if ARM in c['arms']])
    for c in ctxs:
        refs = c['ctx_refs']; t0 = time.time(); LOG.clear()
        seen = []; [seen.append(r) for r in refs if r not in seen]      # duplicates add nothing to a warp
        c2w = np.array([load(r, 'pose.txt') for r in seen], dtype=np.float32)
        vm = c2w.copy()                                                # gl -> VMem transform = identity on OpenCV poses
        pils = [R.tensor_to_pil(R.rgb(ROOT / r.split('/')[0], int(r.split('/')[1]))) for r in seen]
        if len(seen) == 1: rows.append({'window_id': c['window_id'], 'psnr': None, 'note': 'single frame'}); continue
        out = R.SI.run_inference_from_pil(pils, model, poses=vm, depths=None, lr=0.01, niter=0, device='cpu')
        ctx = [(load(r, 'color.png'), depth640(d[0].numpy()), load(r, 'pose.txt')) for r, d in zip(seen, out['depths'])]
        preds = [warp(ctx, load(t, 'pose.txt'), K)[0] for t in c['target_refs']]
        if SAVE is not None:
            from geometry_baselines import warp_raw   # same splat, returns coverage
            SAVE.mkdir(parents=True, exist_ok=True)
            for t, p_img in zip(c['target_refs'], preds):
                _, valid = warp_raw(ctx, load(t, 'pose.txt'), K)
                vm = to_model_grid(np.repeat(valid[..., None].astype(np.uint8) * 255, 3, 2))[..., 0] > 127
                np.savez_compressed(SAVE / f"{c['window_id']}__{ARM}__{t.replace('/', '_')}.npz", filled=to_model_grid(p_img), valid=vm)
        rows.append({'window_id': c['window_id'], 'ctx_refs': refs, 'psnr': psnr4(preds, c['target_refs']),
                     'kps': list(LOG), 'seconds': round(time.time() - t0, 1)})
        print(f"[b2] {ARM} {c['window_id']} {rows[-1]['psnr']:.2f}", flush=True)
OUT.write_text(json.dumps({'schema': 's139-baselines-v1', 'arm': ARM, 'rows': rows}, indent=1) + '\n')
v = [r['psnr'] for r in rows if r['psnr'] is not None]; print('mean', np.mean(v), 'n', len(v))
