#!/usr/bin/env python3
"""S141 fixed clip list (seed 0), poses only. usage: build_clips_s141.py <data7_root> <out.json> [n_train=2000] [n_val=32]
Clip: current sequence C, start s on the 5-frame grid with s+105 < len(C); targets C s+60,75,90,105. Contexts: p=0.5
'static' (C s,+15,+30,+45), else 'memory' = VMem pose-only NMS (S139 pose_arms_s139.select, verbatim) over a bank of
20 evenly spaced frames of another sequence H of the same scene + 12 recent C frames (s..s+55), threshold from the first
5 bank frames, query = last target. The last sequence of office and redkitchen is a monitor-only split (val C)."""
import io, json, sys
from pathlib import Path
import numpy as np
import torch
from scipy.spatial.transform import Rotation as Rot

D7, OUT = Path(sys.argv[1]), Path(sys.argv[2])
N_TRAIN = int(sys.argv[3]) if len(sys.argv) > 3 else 2000; N_VAL = int(sys.argv[4]) if len(sys.argv) > 4 else 32
SCENES = ['fire', 'heads', 'office', 'pumpkin', 'redkitchen', 'stairs']
W_T, CTX = 0.1, 4
seqs = {sc: sorted(p.name for p in (D7 / sc).glob('seq-*') if p.is_dir()) for sc in SCENES}
VAL_SEQS = {('office', seqs['office'][-1]), ('redkitchen', seqs['redkitchen'][-1])}
nfr = {(sc, q): len(list((D7 / sc / q).glob('frame-*.color.png'))) for sc in SCENES for q in seqs[sc]}
_pc = {}
def pose(sc, q, f):
    k = (sc, q, f)
    if k not in _pc:
        _pc[k] = np.loadtxt(io.StringIO((D7 / sc / q / f'frame-{f:06d}.pose.txt').read_text()), dtype=np.float32).reshape(4, 4)
    return _pc[k]
def geo(a, b):  # pose_arms_s139.geo
    a = torch.from_numpy(np.asarray(a, np.float32)); b = torch.from_numpy(np.asarray(b, np.float32))
    tr = torch.clamp(torch.trace(a[:3, :3].T @ b[:3, :3]), -1.0, 3.0)
    return float(torch.norm(a[:3, 3] - b[:3, 3]) * W_T + torch.acos((tr - 1) / 2))
def select(cands, c2ws, target, thr):  # pose_arms_s139.select, verbatim logic
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

rng = np.random.default_rng(0)
train_C = [(sc, q) for sc in SCENES for q in seqs[sc] if (sc, q) not in VAL_SEQS]
val_C = sorted(VAL_SEQS)
clips = []
for i in range(N_TRAIN + N_VAL):
    split = 'train' if i < N_TRAIN else 'val'
    pool = train_C if split == 'train' else val_C
    sc, q = pool[int(rng.integers(len(pool)))]
    n = nfr[(sc, q)]; s = 5 * int(rng.integers(0, (n - 110) // 5 + 1))
    assert s + 105 < n
    tgt = [(q, s + o) for o in (60, 75, 90, 105)]
    kind = 'static' if rng.random() < 0.5 else 'memory'
    H = None; ctx = [(q, s + o) for o in (0, 15, 30, 45)]; info = {}
    if kind == 'memory':
        others = [h for h in seqs[sc] if h != q and (split == 'val' or (sc, h) not in VAL_SEQS)]
        H = others[int(rng.integers(len(others)))]; nH = nfr[(sc, H)]; step = nH // 20
        bank = [(H, f) for f in range(0, step * 20, step)] + [(q, s + o) for o in range(0, 60, 5)]
        c2ws = [pose(sc, *b) for b in bank]
        pw = sorted(geo(c2ws[a], c2ws[b]) for a in range(5) for b in range(a + 1, 5)); thr = pw[int(len(pw) * 0.5)]
        tq = pose(sc, *tgt[-1]).copy(); tq[:3, :3] = Rot.from_quat(Rot.from_matrix(tq[:3, :3]).as_quat()).as_matrix()
        ctx = [bank[j] for j in select(list(range(len(bank))), c2ws, tq, thr)]
        info = {'hist_frac': sum(c[0] == H for c in ctx) / 4, 'nms_threshold': thr}
    ref = lambda t: f'{sc}/{t[0]}/{t[1]:06d}'
    clips.append({'id': f'c{i:05d}', 'split': split, 'scene': sc, 'C': q, 'H': H, 's': s, 'kind': kind,
                  'ctx': [ref(c) for c in ctx], 'tgt': [ref(t) for t in tgt], **info})
summ = {'n_train': N_TRAIN, 'n_val': N_VAL, 'val_seqs': sorted(f'{a}/{b}' for a, b in VAL_SEQS),
        'kinds': {k: sum(c['kind'] == k for c in clips) for k in ('static', 'memory')},
        'scenes': {sc: sum(c['scene'] == sc for c in clips) for sc in SCENES},
        'mean_hist_frac_memory': float(np.mean([c['hist_frac'] for c in clips if c['kind'] == 'memory']))}
OUT.write_text(json.dumps({'schema': 's141-clips-v1', 'seed': 0, 'summary': summ, 'clips': clips}, indent=0) + '\n')
print(json.dumps(summ))
