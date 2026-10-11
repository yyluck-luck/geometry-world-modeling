#!/usr/bin/env python3
"""S146 operational v1 pool (Amendment 3 / R267): rules 1 static, 2 mem_pose (S139 pose/NMS, fp32, last target), 4 nearest-4
(fp64 mean over the four targets, no NMS), 3 mem_vmem = VMem-KPS-original-operational-v1 output sorted by bank index, plus
native-order mem_vmem as a separate package. No CUT3R, no warps. Global availability gate: every window must have a validated
policy output (status OK, 4 unique raw ids, offered 32-frame bank, 3 KPS construction records with non-root counts [4,19,31]).
usage: pool_op_s146.py <stage12> <manifest_dir> <stepA_dir> <out POOL_OP.json>"""
import json, sys
from pathlib import Path
import numpy as np, torch
from scipy.spatial.transform import Rotation as Rot
STAGE, MD, SA, OUT = [Path(a) for a in sys.argv[1:5]]
ROOMS = ['apt1_kitchen', 'apt2_luke', 'office2_5a']
def geo64(a, b):
    tr = np.clip((np.trace(a[:3, :3].T @ b[:3, :3]) - 1) / 2, -1, 1); return float(np.linalg.norm(a[:3, 3] - b[:3, 3]) * 0.1 + np.arccos(tr))
def geo32(a, b):
    a = torch.from_numpy(np.asarray(a, np.float32)); b = torch.from_numpy(np.asarray(b, np.float32))
    tr = torch.clamp(torch.trace(a[:3, :3].T @ b[:3, :3]), -1.0, 3.0); return float(torch.norm(a[:3, 3] - b[:3, 3]) * 0.1 + torch.acos((tr - 1) / 2))
def select(cands, c2ws, target, thr, CTX=4):  # pose_arms_s139.select
    d = [geo32(target, c2ws[f]) for f in cands]; order = [cands[i] for i in np.argsort(np.array(d), kind='stable')]
    max_frames = min(CTX, len(cands), len(c2ws)); sel = [order[0]]; cur = thr
    while len(sel) < max_frames and cur >= 1e-5:
        for i in order[1:]:
            if len(sel) >= max_frames: break
            if all(geo32(c2ws[i], c2ws[j]) >= cur for j in sel): sel.append(i)
        if len(sel) < max_frames: cur /= 1.2
        else: break
    if len(sel) < max_frames: sel.extend([i for i in order if i not in sel][:max_frames - len(sel)])
    return sel
rows, unavailable = [], []
for room in ROOMS:
    M = json.loads((MD / f'WINDOW_MANIFEST_{room}.json').read_text()); root = STAGE / room
    R = {r['window_id']: r for r in json.loads((SA / room / 'RETRIEVAL_RECEIPT.json').read_text())['records']}
    pose = lambda ref: np.loadtxt(root / ref.split('/')[0] / f"frame-{ref.split('/')[1]}.pose.txt").reshape(4, 4)
    for w in M['windows']:
        bank, tg = w['bank'], w['targets']; r = R.get(w['window_id'], {}); order = {x: i for i, x in enumerate(bank)}
        raw = (r.get('raw_contexts') or {}).get('memory_nms_on_clean', [])
        kl = r.get('kps_log', []); counts = [len(l.get('finite_at_best', [])) for l in kl]
        ok = (r.get('status') == 'OK' and len(raw) == 4 and len(set(raw)) == 4 and all(x in order for x in raw) and not set(raw) & set(tg)
              and r.get('bank') == bank and counts == [4, 19, 31])
        if not ok: unavailable.append({'window_id': w['window_id'], 'status': r.get('status'), 'raw': raw, 'kps_counts': counts, 'error': r.get('error')}); continue
        bp = [pose(x) for x in bank]; tp = [pose(x) for x in tg]
        pw = sorted(geo32(bp[i], bp[j]) for i in range(5) for j in range(i + 1, 5)); thr = pw[int(len(pw) * 0.5)]
        tq = tp[-1].copy(); tq[:3, :3] = Rot.from_quat(Rot.from_matrix(tq[:3, :3]).as_quat()).as_matrix()
        dist = [np.mean([geo64(b, t) for t in tp]) for b in bp]
        sets = {1: list(w['static_recent']), 2: [bank[i] for i in select(list(range(32)), bp, tq, thr)],
                3: sorted(raw, key=lambda x: order[x]), 4: [bank[i] for i in sorted(np.argsort(np.array(dist), kind='stable')[:4])]}
        uniq = {}
        for rule in (1, 2, 3, 4):
            key = tuple(sorted(sets[rule], key=lambda x: order[x])); assert len(set(key)) == 4; uniq.setdefault(key, []).append(rule)
        packs = [{'set_id': 's' + '-'.join(map(str, lab)), 'rules': lab, 'ctx_refs': list(k)} for k, lab in uniq.items()]
        nat = tuple(raw)
        if nat in uniq: packs[[tuple(p['ctx_refs']) for p in packs].index(nat)]['also_native_order'] = True
        else: packs.append({'set_id': 'nat3', 'rules': [], 'native_order_of_rule': 3, 'ctx_refs': list(nat)})
        dH = min(geo32(tq, bp[i]) for i in range(20)); dC = min(geo32(tq, bp[i]) for i in range(20, 32))
        rows.append({'window_id': w['window_id'], 'room': room, 'scene_dir': room, 'convention': 'gl', 'bank': bank, 'targets': tg,
                     'rules': {str(k): v for k, v in sets.items()}, 'sets': packs, 'history_favourable': bool(dH < dC),
                     'stepA': {'raw_order': raw, 'frac_history': r.get('frac_history_in_context'), 'n_surfels': r.get('n_surfels'),
                               'kps': [{k: l.get(k) for k in ('median_reproj_px', 'sigma', 'finite_at_best', 'positive_depth_frac')} for l in kl]}})
res = {'schema': 's146-op-pool-v1', 'policy': 'VMem-KPS-original-operational-v1', 'n_windows': len(rows), 'unavailable': unavailable, 'windows': rows}
OUT.write_text(json.dumps(res, indent=1, default=float) + '\n')
print('windows available', len(rows), 'unavailable', len(unavailable), [u['window_id'] for u in unavailable])
if unavailable or len(rows) != 24: sys.exit(5)   # OPERATIONAL_PANEL_UNAVAILABLE
