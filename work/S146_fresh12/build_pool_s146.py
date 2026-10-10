#!/usr/bin/env python3
"""S146 pool (adapter of S143 build_pool_s143.py + S139 pose_arms_s139.py; per-room root, K, convention).
  phase1: build_pool_s146.py 1 <stage12> <manifest_dir> <CONVENTION.json> <POOL_phase1.json>
          rules 1 static, 2 S139 pose/NMS (fp32, last target, threshold from the first 5 bank frames), 4 nearest-4 (fp64 mean
          over the four targets, no NMS), 5 coverage-greedy (one CUT3R + KPS call on the 32 bank frames, geometry poses,
          1/4-res forward-splat support union, finite-KPS gate), 6 random (one default_rng(259) stream over the declared
          room/window order). CPU.
  phase2: build_pool_s146.py 2 <POOL_phase1.json> <stepA_dir> <POOL.json>
          rule 3 = step-A mem_vmem membership sorted by bank index; native-order mem_vmem as a separate package; validity gates
          (status OK, four unique raw ids, exact 32-frame memory coverage, finite KPS); sets sorted by bank index; identical
          ordered tuples merged (native-order merged only if identical as an ordered tuple).
Geometry poses: gl winner -> raw pose P; native winner -> P.F (F = diag(1,-1,-1,1)); pose-distance rules are invariant."""
import json, sys, time
from pathlib import Path
import numpy as np

PHASE = sys.argv[1]
ROOMS = ['apt1_kitchen', 'apt2_luke', 'office2_5a']


def geo64(a, b):  # S143 rule 4 distance (fp64)
    tr = np.clip((np.trace(a[:3, :3].T @ b[:3, :3]) - 1) / 2, -1, 1)
    return float(np.linalg.norm(a[:3, 3] - b[:3, 3]) * 0.1 + np.arccos(tr))


if PHASE == '1':
    STAGE, MD, CONV, OUT = Path(sys.argv[2]), Path(sys.argv[3]), json.loads(Path(sys.argv[4]).read_text()), Path(sys.argv[5])
    conv = {r['room']: r['winner'] for r in CONV['rows']}
    assert set(conv) == set(ROOMS) and all(v in ('gl', 'native') for v in conv.values())
    HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
    import s141_common as C
    import torch
    import modeling.pipeline as PM
    from cloud_opt.dust3r_opt import init_im_poses as IIP
    from utils import tensor_to_pil
    import kps
    LOG = []; kps.install(IIP, log=LOG)
    ck = str(C.WEIGHTS / 'cut3r_512_dpt_4_64.pth'); PM.add_path_to_dust3r(ck)
    model = PM.ARCroco3DStereo.from_pretrained(ck).to('cpu').eval()
    F = np.diag([1.0, -1.0, -1.0, 1.0])

    def geo32(a, b):  # pose_arms_s139.geo (torch fp32)
        a = torch.from_numpy(np.asarray(a, np.float32)); b = torch.from_numpy(np.asarray(b, np.float32))
        tr = torch.clamp(torch.trace(a[:3, :3].T @ b[:3, :3]), -1.0, 3.0)
        return float(torch.norm(a[:3, 3] - b[:3, 3]) * 0.1 + torch.acos((tr - 1) / 2))

    def select(cands, c2ws, target, thr, CTX=4):  # pose_arms_s139.select, verbatim logic
        d = [geo32(target, c2ws[f]) for f in cands]
        order = [cands[i] for i in np.argsort(np.array(d), kind='stable')]
        max_frames = min(CTX, len(cands), len(c2ws)); sel = [order[0]]; cur = thr
        while len(sel) < max_frames and cur >= 1e-5:
            for i in order[1:]:
                if len(sel) >= max_frames: break
                if all(geo32(c2ws[i], c2ws[j]) >= cur for j in sel): sel.append(i)
            if len(sel) < max_frames: cur /= 1.2
            else: break
        if len(sel) < max_frames: sel.extend([i for i in order if i not in sel][:max_frames - len(sel)])
        return sel

    def depth640(d):
        v0, u0 = np.mgrid[0:480, 0:640]
        x = np.round(((u0 + 0.5) * 1.2 - 96) * 512 / 576 - 0.5).astype(int); y = np.round((v0 + 0.5) * 1.2 * 512 / 576 - 64 - 0.5).astype(int)
        ok = (x >= 0) & (x < 512) & (y >= 0) & (y < 384); out = np.zeros((480, 640)); out[ok] = d[y[ok], x[ok]]; return out

    from scipy.spatial.transform import Rotation as Rot
    rng = np.random.default_rng(259); rows = []; t0 = time.time()
    for room in ROOMS:
        M = json.loads((MD / f'WINDOW_MANIFEST_{room}.json').read_text()); root = STAGE / room
        K = np.loadtxt(root / 'camera-intrinsics.txt').reshape(3, 3)
        pose = lambda ref: np.loadtxt(root / ref.split('/')[0] / f"frame-{ref.split('/')[1]}.pose.txt").reshape(4, 4)
        gpose = (lambda ref: pose(ref)) if conv[room] == 'gl' else (lambda ref: pose(ref) @ F)

        def cover(depth, Tc, Tt, step=4):  # S143 build_pool_s143.cover with this room's K
            Hh, Ww = 480, 640; v, u = np.mgrid[0:Hh:step, 0:Ww:step]; d = depth[::step, ::step]; m = d > 0
            pix = np.stack([u[m], v[m], np.ones(m.sum())], 0)
            Xw = Tc[:3, :3] @ ((np.linalg.inv(K) @ pix) * d[m]) + Tc[:3, 3:4]; Xt = Tt[:3, :3].T @ (Xw - Tt[:3, 3:4])
            z = Xt[2]; ok = z > 1e-3
            uu = np.floor((K[0, 0] * Xt[0, ok] / z[ok] + K[0, 2]) / step).astype(int); vv = np.floor((K[1, 1] * Xt[1, ok] / z[ok] + K[1, 2]) / step).astype(int)
            inb = (uu >= 0) & (uu < Ww // step) & (vv >= 0) & (vv < Hh // step)
            c = np.zeros((Hh // step, Ww // step), bool); c[vv[inb], uu[inb]] = True; return c

        for w in M['windows']:
            bank, tg = w['bank'], w['targets']; bp = [pose(r) for r in bank]; tp = [pose(r) for r in tg]
            sets = {1: list(w['static_recent'])}
            pw = sorted(geo32(bp[i], bp[j]) for i in range(5) for j in range(i + 1, 5)); thr = pw[int(len(pw) * 0.5)]
            tq = tp[-1].copy(); tq[:3, :3] = Rot.from_quat(Rot.from_matrix(tq[:3, :3]).as_quat()).as_matrix()
            sets[2] = [bank[i] for i in select(list(range(len(bank))), bp, tq, thr)]
            dist = [np.mean([geo64(b, t) for t in tp]) for b in bp]
            sets[4] = [bank[i] for i in sorted(np.argsort(np.array(dist), kind='stable')[:4])]
            LOG.clear()
            pils = [tensor_to_pil(C.load_rgb_path(root / r.split('/')[0] / f"frame-{r.split('/')[1]}.color.png")) for r in bank]
            gp = np.array([gpose(r) for r in bank], dtype=np.float32); gt = [gpose(r) for r in tg]
            with torch.no_grad():
                out = PM.run_inference_from_pil(pils, model, poses=gp, depths=None, lr=0.01, niter=0, device='cpu')
            kl = [dict(l) for l in LOG]
            assert len(kl) == 1 and kl[0].get('kps') == 'OK' and np.isfinite(kl[0]['sigma']) and np.isfinite(kl[0]['median_reproj_px']) \
                and all(f is not None and np.isfinite(f) and f > 0 for f in kl[0]['focals']), ('rule-5 geometry invalid', w['window_id'], kl)
            cov = [[cover(depth640(d[0].detach().float().numpy()), gp[i].astype(np.float64), gt[j]) for j in range(4)] for i, d in enumerate(out['depths'])]
            sel = []; gains = []; union = [np.zeros_like(cov[0][0]) for _ in range(4)]
            for _ in range(4):
                gain = [(-1 if i in sel else sum(int((union[j] | cov[i][j]).sum()) for j in range(4))) for i in range(len(bank))]
                best = int(np.argmax(gain)); sel.append(best); union = [union[j] | cov[best][j] for j in range(4)]; gains.append(int(gain[best]))
            sets[5] = [bank[i] for i in sorted(sel)]
            sets[6] = [bank[i] for i in sorted(rng.choice(len(bank), 4, replace=False))]
            dH = min(geo32(tq, bp[i]) for i in range(20)); dC = min(geo32(tq, bp[i]) for i in range(20, 32))
            rows.append({'window_id': w['window_id'], 'room': room, 'scene_dir': room, 'convention': conv[room], 'pair': room,
                         'targets': tg, 'bank': bank, 'rules_phase1': {str(k): v for k, v in sets.items()}, 'kps_log': kl,
                         'greedy_union_pixels': gains, 'union_coverage': float(np.mean([u.mean() for u in union])),
                         'mean_pose_distance': dist, 'history_favourable': bool(dH < dC), 'min_geo_hist': dH, 'min_geo_recent': dC})
            print(w['window_id'], 'cov', round(rows[-1]['union_coverage'], 3), 'HF', dH < dC, f'{time.time() - t0:.0f}s', flush=True)
    OUT.write_text(json.dumps({'schema': 's146-pool-phase1-v1', 'conventions': conv, 'windows': rows}, indent=1) + '\n')
else:
    P1, SA, OUT = json.loads(Path(sys.argv[2]).read_text()), Path(sys.argv[3]), Path(sys.argv[4])
    recs = {}
    for room in ROOMS:
        R = json.loads((SA / room / 'RETRIEVAL_RECEIPT.json').read_text())
        for r in R['records']: recs[r['window_id']] = r
    rows = []
    for w in P1['windows']:
        r = recs[w['window_id']]; bank = w['bank']; order = {x: i for i, x in enumerate(bank)}
        raw = r['raw_contexts']['memory_nms_on_clean']
        assert r['status'] == 'OK', (w['window_id'], 'step A blocked')
        assert len(raw) == 4 and len(set(raw)) == 4, (w['window_id'], 'not four unique retrieved ids', raw)
        assert sorted(r['memory_frames']) == sorted(bank), (w['window_id'], 'memory coverage', len(r['memory_frames']))
        assert all(l.get('kps') == 'OK' and np.isfinite(l.get('sigma', np.nan)) for l in r['kps_log']), (w['window_id'], 'step-A KPS')
        sets = {int(k): v for k, v in w['rules_phase1'].items()}; sets[3] = sorted(raw, key=lambda x: order[x])
        uniq = {}
        for rule in range(1, 7):
            key = tuple(sorted(sets[rule], key=lambda x: order[x])); assert len(set(key)) == 4
            uniq.setdefault(key, []).append(rule)
        packs = [{'set_id': 's' + '-'.join(map(str, lab)), 'rules': lab, 'ctx_refs': list(k)} for k, lab in uniq.items()]
        nat = tuple(raw)
        if nat in uniq: packs[[tuple(p['ctx_refs']) for p in packs].index(nat)]['also_native_order'] = True
        else: packs.append({'set_id': 'nat3', 'rules': [], 'native_order_of_rule': 3, 'ctx_refs': list(nat)})
        rows.append(dict({k: v for k, v in w.items() if k != 'rules_phase1'}, rules={str(k): v for k, v in sets.items()}, sets=packs,
                         stepA={'raw_order': raw, 'frac_history': r.get('frac_history_in_context'), 'n_surfels': r.get('n_surfels'), 'seconds': r.get('seconds')}))
    OUT.write_text(json.dumps({'schema': 's146-pool-v1', 'conventions': P1['conventions'], 'windows': rows}, indent=1) + '\n')
    print('windows', len(rows), 'packages', sum(len(w['sets']) for w in rows))
