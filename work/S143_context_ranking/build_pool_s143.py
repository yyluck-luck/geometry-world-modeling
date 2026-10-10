#!/usr/bin/env python3
"""S143 context pool (poses + context-only geometry; target RGB/depth never read).
usage: build_pool_s143.py <out POOL.json> [--no-coverage]
Rules per window (S139 manifest/plan): 1 static_recent, 2 mem_pose, 3 mem_vmem (S139 plan), 4 nearest-4 by mean VMem pose
distance (angle + 0.1 * translation, fp64) to the four target cameras, 5 coverage-greedy over bank frames using
CUT3R + KPS depth of all 32 bank frames (one star-rooted call per window, known poses, niter 0, CPU), 6 random
(default_rng(259), sequential over windows in manifest order). Each set is sorted by bank index; identical sets merge.
Run with the project CUT3R env: PYTHONPATH=work/S17C_environment/site-packages .venv-cut3r/bin/python ..."""
import json, sys, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
S139 = REPO / 'work/S139_crossseq_revisit'; ROOT = REPO / 'data/S139_chess/chess'
OUT = Path(sys.argv[1]); NOCOV = '--no-coverage' in sys.argv
M = json.loads((S139 / 'WINDOW_MANIFEST.json').read_text()); P = json.loads((S139 / 'plan.json').read_text())
K = np.loadtxt(ROOT / 'camera-intrinsics.txt').reshape(3, 3)


def pose(ref):
    s, f = ref.split('/'); return np.loadtxt(ROOT / s / f'frame-{f}.pose.txt').reshape(4, 4)


def geo(a, b):  # VMem geodesic (angle + 0.1 * translation), fp64
    tr = np.clip((np.trace(a[:3, :3].T @ b[:3, :3]) - 1) / 2, -1, 1)
    return float(np.linalg.norm(a[:3, 3] - b[:3, 3]) * 0.1 + np.arccos(tr))


arm = {}
for c in P['contexts']:
    for a in c['arms']:
        arm[(c['window_id'], a)] = c['ctx_refs']

if not NOCOV:
    _argv = list(sys.argv); sys.argv = [sys.argv[0]]
    sys.path.insert(0, str(REPO / 'work/S135_scale_init')); sys.path.insert(0, str(S139))
    import repro_kps as R, kps
    sys.argv = _argv
    LOG = []; kps.install(R.IIP, log=LOG)
    model = R.ARCroco3DStereo.from_pretrained(str(R.WEIGHTS)).to('cpu').eval()

    def depth640(d):  # baselines_s139.depth640 (S137 Amendment 2 mapping)
        v0, u0 = np.mgrid[0:480, 0:640]
        x = np.round(((u0 + 0.5) * 1.2 - 96) * 512 / 576 - 0.5).astype(int); y = np.round((v0 + 0.5) * 1.2 * 512 / 576 - 64 - 0.5).astype(int)
        ok = (x >= 0) & (x < 512) & (y >= 0) & (y < 384); out = np.zeros((480, 640)); out[ok] = d[y[ok], x[ok]]; return out

    def cover(depth, Tc, Tt, step=4):  # validity of a forward splat of one frame into target (1/4-res grid, no fill)
        H, W = 480, 640; v, u = np.mgrid[0:H:step, 0:W:step]; d = depth[::step, ::step]; m = d > 0
        pix = np.stack([u[m], v[m], np.ones(m.sum())], 0)
        Xw = Tc[:3, :3] @ ((np.linalg.inv(K) @ pix) * d[m]) + Tc[:3, 3:4]; Xt = Tt[:3, :3].T @ (Xw - Tt[:3, 3:4])
        z = Xt[2]; ok = z > 1e-3
        uu = np.floor((K[0, 0] * Xt[0, ok] / z[ok] + K[0, 2]) / step).astype(int); vv = np.floor((K[1, 1] * Xt[1, ok] / z[ok] + K[1, 2]) / step).astype(int)
        inb = (uu >= 0) & (uu < W // step) & (vv >= 0) & (vv < H // step)
        c = np.zeros((H // step, W // step), bool); c[vv[inb], uu[inb]] = True; return c

rng = np.random.default_rng(259); rows = []; t0 = time.time()
for w in M['windows']:
    wid, bank, tg = w['window_id'], w['bank'], w['targets']
    bp = [pose(r) for r in bank]; tp = [pose(r) for r in tg]
    sets = {1: arm[(wid, 'static_recent')], 2: arm[(wid, 'mem_pose')], 3: arm[(wid, 'mem_vmem')]}
    dist = [np.mean([geo(b, t) for t in tp]) for b in bp]
    sets[4] = [bank[i] for i in sorted(np.argsort(np.array(dist), kind='stable')[:4])]
    info = {}
    if not NOCOV:
        LOG.clear(); pils = [R.tensor_to_pil(R.rgb(ROOT / r.split('/')[0], int(r.split('/')[1]))) for r in bank]
        out = R.SI.run_inference_from_pil(pils, model, poses=np.array(bp, dtype=np.float32), depths=None, lr=0.01, niter=0, device='cpu')
        cov = [[cover(depth640(d[0].numpy()), bp[i], tp[j]) for j in range(4)] for i, d in enumerate(out['depths'])]
        sel = []; gains = []; union = [np.zeros_like(cov[0][0]) for _ in range(4)]
        for _ in range(4):
            gain = [(-1 if i in sel else sum(int((union[j] | cov[i][j]).sum()) for j in range(4))) for i in range(len(bank))]
            best = int(np.argmax(gain)); sel.append(best); union = [union[j] | cov[best][j] for j in range(4)]; gains.append(int(gain[best]))
        sets[5] = [bank[i] for i in sorted(sel)]
        kl = [dict(l) for l in LOG]
        finite = (len(kl) == 1 and kl[0].get('kps') == 'OK' and np.isfinite(kl[0].get('sigma', np.nan)) and np.isfinite(kl[0].get('median_reproj_px', np.nan))
                  and all(f is not None and np.isfinite(f) for f in kl[0].get('focals', [None])))
        assert finite, ('rule-5 geometry invalid', wid, kl)   # R260: no silent KPS fallback; invalid geometry stops the build
        info = {'kps_log': kl, 'greedy_union_pixels': gains, 'union_coverage': float(np.mean([u.mean() for u in union])),
                'per_frame_coverage': [float(np.mean([cov[i][j].mean() for j in range(4)])) for i in range(len(bank))]}
    sets[6] = [bank[i] for i in sorted(rng.choice(len(bank), 4, replace=False))]
    order = {r: i for i, r in enumerate(bank)}
    uniq = {}
    for rule, s in sets.items():
        key = tuple(sorted(s, key=lambda r: order[r]))
        assert len(set(key)) == 4 and all(r in order for r in key), (wid, rule, key)
        uniq.setdefault(key, []).append(rule)
    rows.append({'window_id': wid, 'pair': w['pair'], 'targets': tg, 'bank': bank, 'rules': {str(k): v for k, v in sets.items()},
                 'sets': [{'set_id': 's' + '-'.join(map(str, labels)), 'rules': labels, 'ctx_refs': list(key)} for key, labels in uniq.items()],
                 'mean_pose_distance': dist, **info})
    print(f"{wid} unique sets {len(uniq)} {[s for s in uniq.values()]} cov {info.get('union_coverage', 'n/a')} {time.time() - t0:.0f}s", flush=True)
OUT.write_text(json.dumps({'schema': 's143-pool-v1', 'coverage_rule': not NOCOV, 'windows': rows}, indent=1) + '\n')
print('total unique sets', sum(len(r['sets']) for r in rows))
