#!/usr/bin/env python3
"""C8 Experiment 2 CPU evaluator: B / C / J support masks. The ONLY process that reads target depth.

usage: compute_support_masks.py <support_job_dir> <datasets_root> <LEAK_REGIME_CENSUS.json> <S113_SCORES.json> <out.json>

Definitions follow DESIGN_AND_PREREGISTRATION.md (Masks, Amendments 2-3). Dataset poses are used as
camera-to-world with OpenCV camera axes (x right, y down, z forward); depth PNG is millimetres.
"""
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image

JOB, DS, CENSUS, SCORES, OUT = map(Path, sys.argv[1:6])
SCENE_DIR = {'scene_13': 'heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13',
             'scene_14': 'heldout_3dmatch_scene14/extracted/rgbd-scenes-v2-scene_14'}
STRIDE, X0, X1 = 2, 80, 560          # model-visible columns of the 640x480 frame
TOL = lambda z: np.maximum(0.05, 0.05 * z)
ARM_SEALED = {'memory_nms_on_clean': 'memory_nms_on_clean', 'memory_nms_on_leaked': 'memory_nms_on',
              'memory_nms_off': 'memory_nms_off', 'static': 'static'}
CENSUS_KEY = {'memory_nms_on_clean': 'clean_nms_on', 'memory_nms_on_leaked': 'leaked_nms_on_same_build',
              'memory_nms_off': 'recency_nms_off'}

def load_pose(seq, f): return np.loadtxt(seq / f'frame-{f:06d}.pose.txt').reshape(4, 4)
def load_depth(seq, f): return np.asarray(Image.open(seq / f'frame-{f:06d}.depth.png'), dtype=np.float64) / 1000.0

def observed_in(Xw, seq, K, frames):
    """Boolean per point: visible and depth-consistent in at least one of `frames`."""
    hit = np.zeros(len(Xw), bool)
    for f in frames:
        T = load_pose(seq, f); D = load_depth(seq, f)
        p = (Xw - T[:3, 3]) @ T[:3, :3]                    # world -> camera (R^T (X - t))
        z = p[:, 2]; ok = z > 1e-6
        u = np.full(len(z), -1); v = np.full(len(z), -1)
        u[ok] = np.round(K[0, 0] * p[ok, 0] / z[ok] + K[0, 2]).astype(int)
        v[ok] = np.round(K[1, 1] * p[ok, 1] / z[ok] + K[1, 2]).astype(int)
        ok &= (u >= 0) & (u < D.shape[1]) & (v >= 0) & (v < D.shape[0])
        ds = np.zeros(len(z)); ds[ok] = D[v[ok], u[ok]]
        ok &= ds > 0
        ok &= np.abs(ds - z) <= TOL(z)
        hit |= ok
    return hit

def retrieval_hits(p_cam, maps, f_r, size):
    """Project camera-frame points into a retrieval render (standard pinhole, principal point at centre)."""
    W, H = size; fx, fy = (f_r[0], f_r[1]) if len(f_r) > 1 else (f_r[0], f_r[0])
    z = p_cam[:, 2]; ok = z > 0.1
    sx = np.where(ok, fx * p_cam[:, 0] / np.where(ok, z, 1) + W / 2, -99)
    sy = np.where(ok, fy * p_cam[:, 1] / np.where(ok, z, 1) + H / 2, -99)
    u, v = np.round(sx).astype(int), np.round(sy).astype(int)
    ok &= (np.hypot(sx - u, sy - v) <= 1.5) & (u >= 0) & (u < W) & (v >= 0) & (v < H)
    idx = np.full(len(z), -1); rd = np.full(len(z), np.nan); cs = np.full(len(z), np.nan)
    idx[ok] = maps['surfel_index_map'][v[ok], u[ok]]
    rd[ok] = maps['depth'][v[ok], u[ok]]; cs[ok] = maps['cos_value_map'][v[ok], u[ok]]
    ray = ok & (idx >= 0) & np.isfinite(rd)
    tol = np.zeros(len(z), bool); tol[ray] = np.abs(rd[ray] - z[ray]) <= TOL(z[ray])
    return {'J_ray': ray, 'J': tol, 'J_cos': tol & (np.nan_to_num(cs, nan=-1) >= 0), 'rd': rd, 'z': z}

census = {(w['scene'], int(w['window_start'])): w for w in json.loads(CENSUS.read_text())['windows'] if w.get('status') == 'OK'}
psnr = {}
for r in json.loads(SCORES.read_text())['rows']:
    w = int(r['tag'].split('__w')[1][:4]); psnr.setdefault((r['scene'], w, r['arm']), []).append(r['psnr_db'])

windows = []
for wdir in sorted(JOB.glob('scene_1?_w????')):
    rec = json.loads((wdir / 'WINDOW_RECEIPT.json').read_text())
    scene, start = rec['scene'], int(rec['window_start'])
    seq = DS / SCENE_DIR[scene] / 'seq-01'
    K = np.loadtxt(DS / SCENE_DIR[scene] / 'camera-intrinsics.txt').reshape(3, 3)
    bank, targets = rec['bank_frame_ids'], rec['target_frame_ids']
    # ---- harness gate: recomputed contexts must equal the sealed census lists ----
    cw = census.get((scene, start)); gate = {}
    for arm, ck in CENSUS_KEY.items():
        gate[arm] = bool(cw) and [int(x) for x in rec['raw_contexts'][arm]] == [int(x) for x in cw[ck]['retrieved_frame_ids']]
    gate_ok = all(gate.values())
    f_r = np.atleast_1d(np.asarray(rec['retrieval_focal'], dtype=float)).ravel(); size = rec['retrieval_size']
    renders = {int(r['target_frame']): r for r in rec['renders']}
    avg_t = int(rec['averaged_render_target'])
    maps = {t: dict(np.load(wdir / f't{t:06d}' / 'retrieval_maps.npz')) for t in targets}
    contexts = dict(rec['consumer_contexts']); contexts['static'] = [start + o for o in (0, 15, 30, 45)]
    per_target = []
    for t in targets:
        Tt = load_pose(seq, t); D = load_depth(seq, t)
        vv, uu = np.mgrid[0:D.shape[0]:STRIDE, X0:X1:STRIDE]; d = D[vv, uu]; m = d > 0
        uu, vv, d = uu[m], vv[m], d[m]
        p = np.stack([(uu - K[0, 2]) * d / K[0, 0], (vv - K[1, 2]) * d / K[1, 1], d], 1)   # target camera
        Xw = p @ Tt[:3, :3].T + Tt[:3, 3]
        B = observed_in(Xw, seq, K, bank)
        C = {arm: observed_in(Xw, seq, K, sorted(set(ids))) for arm, ids in contexts.items()}
        own = retrieval_hits(p, maps[t], f_r, size)
        Ta = load_pose(seq, avg_t); pa = (Xw - Ta[:3, 3]) @ Ta[:3, :3]
        avg = retrieval_hits(pa, maps[avg_t], f_r, size)
        rr = own['rd'][own['J_ray']] / own['z'][own['J_ray']]
        corr = float(np.corrcoef(own['rd'][own['J_ray']], own['z'][own['J_ray']])[0, 1]) if own['J_ray'].sum() > 10 else None
        per_target.append({'target': t, 'n_eval_pixels': int(len(d)), 'B': float(B.mean()),
                           'C': {a: float(c.mean()) for a, c in C.items()},
                           'J': float(avg['J'].mean()), 'J_cos': float(avg['J_cos'].mean()), 'J_ray': float(avg['J_ray'].mean()),
                           'J_own': float(own['J'].mean()), 'J_own_ray': float(own['J_ray'].mean()),
                           'own_render_depth_ratio_median': float(np.median(rr)) if len(rr) else None,
                           'own_render_depth_corr': corr})
    mean = lambda k: float(np.mean([pt[k] for pt in per_target]))
    arms = {}
    for arm in contexts:
        ps = psnr.get((scene, start, ARM_SEALED[arm]), [])
        arms[arm] = {'C': float(np.mean([pt['C'][arm] for pt in per_target])),
                     'psnr_db_mean_over_seeds': float(np.mean(ps)) if ps else None, 'n_psnr': len(ps)}
    windows.append({'scene': scene, 'window_start': start, 'harness_gate': gate, 'harness_gate_ok': gate_ok,
                    'B': mean('B'), 'J': mean('J'), 'J_cos': mean('J_cos'), 'J_ray': mean('J_ray'),
                    'J_own': mean('J_own'), 'J_own_ray': mean('J_own_ray'), 'arms': arms, 'per_target': per_target})
OUT.write_text(json.dumps({'schema': 'c8-support-masks-v1', 'windows': windows,
                           'new_method_validated': False, 'novelty_authorization': 'NONE'}, indent=2) + '\n')
print(f'windows: {len(windows)}  gate_ok: {sum(w["harness_gate_ok"] for w in windows)}')
for w in windows:
    pt = w['per_target']
    print(f"{w['scene']} w{w['window_start']:3d} gate={'OK ' if w['harness_gate_ok'] else 'BAD'} B={w['B']:.3f} J={w['J']:.3f} "
          f"J_ray={w['J_ray']:.3f} J_own_ray={w['J_own_ray']:.3f} depth_ratio={[round(x['own_render_depth_ratio_median'],2) if x['own_render_depth_ratio_median'] else None for x in pt]} "
          f"corr={[round(x['own_render_depth_corr'],2) if x['own_render_depth_corr'] is not None else None for x in pt]}")
