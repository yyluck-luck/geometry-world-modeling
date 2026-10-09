#!/usr/bin/env python3
"""S134 map certification (CPU; the only S134 process that reads target depth).

usage: eval_map_s134.py <retrieval_out_dir> <datasets_root> <out.json>
Per window and target frame:
  ratio = median(rendered surfel depth > 0) / median(dataset target depth > 0, model-visible columns)
          (scale only, convention-agnostic: no pixel correspondence needed)
  corr  = C8 own-render depth correlation via retrieval_hits (copied from compute_support_masks.py);
          reported, not gated (it depends on the camera convention).
Gate (PROTOCOL.md): window ratio (median over targets) in [0.5, 2] for >= 12/14 windows and none > 10 or < 0.1.
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

JOB, DS, OUT = map(Path, sys.argv[1:4])
SCENE_DIR = {'scene_13': 'heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13',
             'scene_14': 'heldout_3dmatch_scene14/extracted/rgbd-scenes-v2-scene_14'}
STRIDE, X0, X1 = 2, 80, 560
TOL = lambda z: np.maximum(0.05, 0.05 * z)


def load_depth(seq, f):
    return np.asarray(Image.open(seq / f'frame-{f:06d}.depth.png'), dtype=np.float64) / 1000.0


def retrieval_hits(p_cam, maps, f_r, size):  # copied from work/S130_C8_diagnostics/compute_support_masks.py
    W, H = size; fx, fy = (f_r[0], f_r[1]) if len(f_r) > 1 else (f_r[0], f_r[0])
    z = p_cam[:, 2]; ok = z > 0.1
    sx = np.where(ok, fx * p_cam[:, 0] / np.where(ok, z, 1) + W / 2, -99)
    sy = np.where(ok, fy * p_cam[:, 1] / np.where(ok, z, 1) + H / 2, -99)
    u, v = np.round(sx).astype(int), np.round(sy).astype(int)
    ok &= (np.hypot(sx - u, sy - v) <= 1.5) & (u >= 0) & (u < W) & (v >= 0) & (v < H)
    idx = np.full(len(z), -1); rd = np.full(len(z), np.nan)
    idx[ok] = maps['surfel_index_map'][v[ok], u[ok]]
    rd[ok] = maps['depth'][v[ok], u[ok]]
    ray = ok & (idx >= 0) & np.isfinite(rd)
    return ray, rd, z


rows = []
for wdir in sorted(JOB.glob('scene_1?_w????')):
    rec = json.loads((wdir / 'WINDOW_RECEIPT.json').read_text())
    scene, start = rec['scene'], int(rec['window_start'])
    seq = DS / SCENE_DIR[scene] / 'seq-01'
    K = np.loadtxt(DS / SCENE_DIR[scene] / 'camera-intrinsics.txt').reshape(3, 3)
    f_r = np.atleast_1d(np.asarray(rec['retrieval_focal'], dtype=float)).ravel(); size = rec['retrieval_size']
    per_t = []
    for r in rec['renders']:
        t = int(r['target_frame'])
        maps = dict(np.load(wdir / f't{t:06d}' / 'retrieval_maps.npz'))
        rdm = maps['depth']; D = load_depth(seq, t)
        gt = D[:, X0:X1]; gt = gt[gt > 0]
        ratio = float(np.median(rdm[rdm > 0]) / np.median(gt)) if (rdm > 0).any() else None
        vv, uu = np.mgrid[0:D.shape[0]:STRIDE, X0:X1:STRIDE]; d = D[vv, uu]; m = d > 0
        uu, vv, d = uu[m], vv[m], d[m]
        p = np.stack([(uu - K[0, 2]) * d / K[0, 0], (vv - K[1, 2]) * d / K[1, 1], d], 1)
        ray, rd, z = retrieval_hits(p, maps, f_r, size)
        corr = float(np.corrcoef(rd[ray], z[ray])[0, 1]) if ray.sum() > 10 else None
        per_t.append({'target': t, 'scale_ratio': ratio, 'render_coverage': float((rdm > 0).mean()),
                      'own_render_corr': corr, 'own_render_ray_frac': float(ray.mean())})
    ratios = [x['scale_ratio'] for x in per_t if x['scale_ratio'] is not None]
    corrs = [x['own_render_corr'] for x in per_t if x['own_render_corr'] is not None]
    rows.append({'scene': scene, 'window_start': start, 'pnp_fix': rec.get('pnp_fix'), 'convention': rec.get('convention'),
                 'window_scale_ratio': float(np.median(ratios)) if ratios else None,
                 'window_own_render_corr': float(np.median(corrs)) if corrs else None,
                 'n_surfels': rec['n_surfels'], 'construct_probes': rec.get('construct_probes'), 'targets': per_t})
wr = [r['window_scale_ratio'] for r in rows if r['window_scale_ratio'] is not None]
gate = {'n_windows': len(rows), 'n_in_0p5_2': sum(0.5 <= x <= 2 for x in wr),
        'n_gt_10': sum(x > 10 for x in wr), 'n_lt_0p1': sum(x < 0.1 for x in wr),
        'median_corr': float(np.median([r['window_own_render_corr'] for r in rows if r['window_own_render_corr'] is not None]))}
gate['PASS'] = gate['n_in_0p5_2'] >= 12 and gate['n_gt_10'] == 0 and gate['n_lt_0p1'] == 0 and len(rows) == 14
OUT.write_text(json.dumps({'schema': 's134-map-eval-v1', 'gate': gate, 'windows': rows}, indent=1) + '\n')
print(json.dumps(gate))
for r in rows:
    print(r['scene'], r['window_start'], 'ratio', None if r['window_scale_ratio'] is None else round(r['window_scale_ratio'], 3),
          'corr', None if r['window_own_render_corr'] is None else round(r['window_own_render_corr'], 3))
