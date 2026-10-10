#!/usr/bin/env python3
"""S139 pose-only quantities (poses only, no images): mem_pose contexts and the history-favourable stratum.

usage: pose_arms_s139.py <WINDOW_MANIFEST.json> <data_root (contains chess/seq-XX)> <out.json>
mem_pose: VMem's pose-distance ranking + NMS (get_context_info post-render logic, S135 pose_only_retrieval.select)
over all 32 bank frames, threshold = 50th-percentile pairwise geodesic among the first 5 bank frames (VMem's 5-frame
state). Geodesic computed in torch fp32 like VMem (angle + 0.1 * translation); gl/native flips leave it unchanged.
stratum: history_favourable if min geodesic(last target, H frames) < min geodesic(last target, recent C frames).
"""
import io, json, sys
from pathlib import Path
import numpy as np
import torch
from scipy.spatial.transform import Rotation as Rot

M, ROOT, OUT = json.loads(Path(sys.argv[1]).read_text()), Path(sys.argv[2]) / 'chess', Path(sys.argv[3])
W_T, CTX = 0.1, 4


def pose(ref):
    s, f = ref.split('/')
    return np.loadtxt(io.StringIO((ROOT / s / f'frame-{f}.pose.txt').read_text()), dtype=np.float32).reshape(4, 4)


def geo(a, b):
    a = torch.from_numpy(np.asarray(a, np.float32)); b = torch.from_numpy(np.asarray(b, np.float32))
    tr = torch.clamp(torch.trace(a[:3, :3].T @ b[:3, :3]), -1.0, 3.0)
    return float(torch.norm(a[:3, 3] - b[:3, 3]) * W_T + torch.acos((tr - 1) / 2))


def select(cands, c2ws, target, thr):  # S135 pose_only_retrieval.select, verbatim logic
    d = [geo(target, c2ws[f]) for f in cands]
    order = [cands[i] for i in np.argsort(np.array(d), kind='stable')]
    max_frames = min(CTX, len(cands), len(c2ws)); sel = [order[0]]; cur = thr
    while len(sel) < max_frames and cur >= 1e-5:
        for i in order[1:]:
            if len(sel) >= max_frames: break
            if all(geo(c2ws[i], c2ws[j]) >= cur for j in sel): sel.append(i)
        if len(sel) < max_frames: cur /= 1.2
        else: break
    if len(sel) < max_frames: sel.extend([i for i in order if i not in sel][:max_frames - len(sel)])
    return sel


rows = []
for w in M['windows']:
    bank = w['bank']; c2ws = [pose(r) for r in bank]
    pw = sorted(geo(c2ws[i], c2ws[j]) for i in range(5) for j in range(i + 1, 5)); thr = pw[int(len(pw) * 0.5)]
    tgt = pose(w['targets'][-1]).copy()
    tgt[:3, :3] = Rot.from_quat(Rot.from_matrix(tgt[:3, :3]).as_quat()).as_matrix()   # average_camera_pose of one pose
    sel = [bank[i] for i in select(list(range(len(bank))), c2ws, tgt, thr)]
    hist = [i for i, r in enumerate(bank) if r.startswith(w['history_seq'])]
    cur = [i for i, r in enumerate(bank) if r.startswith(w['current_seq'])]
    dh = min(geo(tgt, c2ws[i]) for i in hist); dc = min(geo(tgt, c2ws[i]) for i in cur)
    rows.append({'window_id': w['window_id'], 'pair': w['pair'], 'mem_pose': sel,
                 'mem_pose_hist_frac': sum(r.startswith(w['history_seq']) for r in sel) / 4,
                 'min_geo_hist': dh, 'min_geo_recent': dc, 'history_favourable': dh < dc, 'nms_threshold': thr})
    print(f"{w['window_id']} mem_pose={sel} hist_frac={rows[-1]['mem_pose_hist_frac']} dH={dh:.3f} dC={dc:.3f} "
          f"{'HIST' if dh < dc else 'recent'}")
OUT.write_text(json.dumps({'schema': 's139-pose-arms-v1', 'rows': rows,
                           'n_history_favourable': sum(r['history_favourable'] for r in rows)}, indent=1) + '\n')
print('history-favourable windows:', sum(r['history_favourable'] for r in rows), '/', len(rows))
