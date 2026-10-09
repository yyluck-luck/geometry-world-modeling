#!/usr/bin/env python3
"""S135b: is VMem's surfel retrieval a pose-distance heuristic in disguise? (CPU, receipts only)

VMem get_context_info (surfel mode): render surfels at the averaged target pose, count visible surfels per bank
frame (process_retrieved_spatial_information), turn the counts into a candidate multiset (get_frame_distribution,
n = min(context_num_frames + 10, #frames)), then sort candidates by pose geodesic distance (rotation angle +
0.1 x translation) and select 4 with pose-distance NMS. This script re-implements the post-render steps exactly
and compares:
  (a) RECON: candidates rebuilt from the saved render maps + surfel_to_timestep. Must reproduce VMem 14/14.
  (b) POSE_ONLY: every bank frame is a candidate (count 1). No 3D map at all.
  (c) POSE_ONLY_MEMSET: candidates = the bank frames that own any surfel (VMem's stage 2 only adds surfels for the
      last target_num_frames frames, so offsets 25/30/35 are never in memory), count 1 each. No rendering.
usage: pose_only_retrieval.py <retrieval_job_dir> <datasets_root> <out.json>
"""
import io, json, sys
from pathlib import Path
import numpy as np

JOB, DS, OUT = map(Path, sys.argv[1:4])
SCENE_DIR = {'scene_13': 'heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13',
             'scene_14': 'heldout_3dmatch_scene14/extracted/rgbd-scenes-v2-scene_14'}
W_T, CTX = 0.1, 4  # translation_distance_weight, context_num_frames (inference.yaml)


def pose(seq, f):
    return np.loadtxt(io.StringIO((seq / f'frame-{f:06d}.pose.txt').read_text()), dtype=np.float32).reshape(4, 4)


import torch
def geo(a, b):  # VMem geodesic_distance, verbatim, torch float32 (CPU; VMem ran it on CUDA)
    a = torch.from_numpy(np.asarray(a, dtype=np.float32)); b = torch.from_numpy(np.asarray(b, dtype=np.float32))
    t = torch.norm(a[:3, 3] - b[:3, 3])
    tr = torch.clamp(torch.trace(torch.matmul(a[:3, :3].T, b[:3, :3])), -1.0, 3.0)
    return float(t * W_T + torch.acos((tr - 1) / 2))


def frame_distribution(n, ratios):  # get_frame_distribution, verbatim logic
    k = len(ratios)
    if k > n:
        res = [0] * k
        for i in np.argsort(ratios)[::-1][:n]: res[i] = 1
        return res
    res = [1] * k; left = n - k
    if left == 0: return res
    prods = [r * left for r in ratios]; fl = [int(p // 1) for p in prods]
    left2 = left - sum(fl)
    for i in range(k): res[i] += fl[i]
    rem = sorted([(p - f, i) for i, (p, f) in enumerate(zip(prods, fl))], key=lambda x: x[0], reverse=True)
    for j in range(left2): res[rem[j][1]] = 1   # (sic) VMem sets to 1, not += 1
    return res


def counts_from_render(maps, s2t):
    idx, cos, dep = maps['surfel_index_map'], maps['cos_value_map'], maps['depth']
    m = idx >= 0; tc = {}
    for si, c, d in zip(idx[m], cos[m], dep[m]):
        if c < 0: continue
        for ts in s2t[int(si)]:
            if ts not in tc: tc[ts] = c / (1 + d)
            tc[ts] += c / (1 + d)
    vals = np.array(list(tc.values())); ratios = vals / vals.sum()
    n = min(CTX + 10, len(ratios)); fc = frame_distribution(n, list(ratios))
    return sorted(zip(tc.keys(), fc), key=lambda x: x[0])


def select(frame_count, c2ws, target, thr):
    cands = []
    for f, c in frame_count: cands.extend([f] * int(c))
    d = [geo(target, c2ws[f]) for f in cands]
    order = [cands[i] for i in np.argsort(np.array(d), kind='stable')]
    max_frames = min(CTX, len(cands), len(c2ws))
    sel = [order[0]]; cur = thr
    while len(sel) < max_frames and cur >= 1e-5:
        for i in order[1:]:
            if len(sel) >= max_frames: break
            if all(geo(c2ws[i], c2ws[j]) >= cur for j in sel): sel.append(i)
        if len(sel) < max_frames: cur /= 1.2
        else: break
    if len(sel) < max_frames:
        sel.extend([i for i in order if i not in sel][:max_frames - len(sel)])
    return sel


rows = []
for wdir in sorted(JOB.glob('scene_1?_w????')):
    rec = json.loads((wdir / 'WINDOW_RECEIPT.json').read_text())
    scene, start, bank = rec['scene'], int(rec['window_start']), rec['vmem_bank_timestep_to_frame']
    seq = DS / SCENE_DIR[scene] / 'seq-01'
    c2ws = [pose(seq, f) for f in bank]
    pw = sorted(geo(c2ws[i], c2ws[j]) for i in range(5) for j in range(i + 1, 5))
    thr = pw[int(len(pw) * 0.5)]                       # initial_threshold set at the 5-frame call
    tgt = pose(seq, int(rec['averaged_render_target']))
    from scipy.spatial.transform import Rotation as _R   # average_camera_pose of one pose = quaternion round trip
    tgt = tgt.copy(); tgt[:3, :3] = _R.from_quat(_R.from_matrix(tgt[:3, :3]).as_quat()).as_matrix()
    z = np.load(wdir / 'surfel_to_timestep.npz')
    s2t, off = {}, 0
    for k, n in zip(z['keys'], z['lengths']): s2t[int(k)] = list(z['flat'][off:off + n]); off += n
    maps = dict(np.load(wdir / f"t{int(rec['averaged_render_target']):06d}" / 'retrieval_maps.npz'))
    fc = counts_from_render(maps, s2t)
    recon = [bank[i] for i in select(fc, c2ws, tgt, thr)]
    pose_only = [bank[i] for i in select([(i, 1) for i in range(len(bank))], c2ws, tgt, thr)]
    memset = sorted({int(t) for v in s2t.values() for t in v})
    pose_memset = [bank[i] for i in select([(i, 1) for i in memset], c2ws, tgt, thr)]
    vmem = [int(x) for x in rec['raw_contexts']['memory_nms_on_clean']]
    rows.append({'scene': scene, 'window_start': start, 'vmem': vmem, 'recon': recon, 'pose_only': pose_only,
                 'pose_memset': pose_memset, 'memset_frames': [bank[i] for i in memset],
                 'pose_memset_exact': pose_memset == vmem, 'pose_memset_overlap': len(set(pose_memset) & set(vmem)),
                 'n_candidate_frames': len(fc), 'candidate_multiset': [[bank[f], int(c)] for f, c in fc],
                 'recon_exact': recon == vmem, 'pose_only_exact': pose_only == vmem,
                 'pose_only_same_set': sorted(pose_only) == sorted(vmem),
                 'pose_only_overlap': len(set(pose_only) & set(vmem))})
summary = {k: sum(r[k] for r in rows) for k in ('recon_exact', 'pose_only_exact', 'pose_only_same_set', 'pose_memset_exact')}
summary['mean_memset_overlap_of_4'] = float(np.mean([r['pose_memset_overlap'] for r in rows]))
summary['n'] = len(rows); summary['mean_overlap_of_4'] = float(np.mean([r['pose_only_overlap'] for r in rows]))
OUT.write_text(json.dumps({'schema': 's135b-pose-only-v1', 'job': str(JOB), 'summary': summary, 'windows': rows}, indent=1) + '\n')
print(json.dumps(summary))
for r in rows:
    print(r['scene'][-2:], r['window_start'], 'vmem', r['vmem'], 'recon', 'OK' if r['recon_exact'] else r['recon'],
          'pose_memset', 'OK' if r['pose_memset_exact'] else r['pose_memset'], 'cands', r['n_candidate_frames'])
