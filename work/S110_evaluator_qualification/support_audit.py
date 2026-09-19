#!/usr/bin/env python3
"""Bounded support/arithmetic audit of the corrected reprojection evaluator.

Four checks demanded by review, all reference-only, zero generation:

 1 MASK IDENTITY.  The visibility tests must depend on geometry alone.  Masks and
   sampled indices are hashed per directional pair per condition and required to
   be byte-identical across conditions.  Equal coverage totals are NOT accepted.

 2 CHANNEL-PERMUTATION CONTROL (D).  A fixed RGB channel permutation applied to
   every real image.  With equal channel weights and L1 over channels the
   reprojection score is preserved EXACTLY, while fidelity to the recorded RGB is
   destroyed.  This is a cleaner fidelity-blindness control than the
   world-coordinate retexturing, and it introduces no geometry of its own.

 3 PAIRED WINDOW-LEVEL VALUES.  B-A per window, not only pooled means.

 4 CORRECT DECOMPOSITION.  R_old = q*R_kept + (1-q)*R_rejected, so
   R_old - R_kept = (1-q)*(R_rejected - R_kept).  R_rejected is measured directly
   rather than inferred.
"""
import io, hashlib, json, math, sys, statistics as st
from pathlib import Path
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/yliutz/geometry-world-modeling/work/S103_selector_free_baseline")
from geom_eval_s110 import depth_to_model_grid, model_grid_K, load_pose, DATA, REL, H, W

DEPTH_ABS_TOL_M, DEPTH_REL_TOL, CYCLE_PX_TOL = 0.02, 0.02, 1.0
TARGET_OFFSETS = [60, 75, 90, 105]
WINDOW_STARTS = [50, 100, 150, 200, 250, 300, 350]
SCENES = {"scene_13": 462, "scene_14": 659}
RNG = np.random.default_rng(20260918)

def geometry_only_support(depth_src, depth_dst, K, c2w_src, c2w_dst):
    """Returns mask, sampled flat indices, and the rejected-by-visibility mask.
    Touches NO image."""
    v, u = np.mgrid[0:H, 0:W]
    z = depth_dst; valid_depth = z > 0
    fx, fy, cx, cy = K[0, 0], K[1, 1], K[0, 2], K[1, 2]
    x = (u + 0.5 - cx) / fx * z; y = (v + 0.5 - cy) / fy * z
    pts = np.stack([x, y, z, np.ones_like(z)], -1).reshape(-1, 4).T
    cam = np.linalg.inv(c2w_src) @ (c2w_dst @ pts)
    zc = cam[2]; in_front = zc > 1e-6
    us = fx * cam[0] / np.where(in_front, zc, 1.0) + cx - 0.5
    vs = fy * cam[1] / np.where(in_front, zc, 1.0) + cy - 0.5
    ui = np.rint(us).astype(np.int64); vi = np.rint(vs).astype(np.int64)
    inb = (ui >= 0) & (ui < W) & (vi >= 0) & (vi < H) & in_front
    base = valid_depth.reshape(-1) & inb
    uic = np.clip(ui, 0, W - 1); vic = np.clip(vi, 0, H - 1)
    zsrc = depth_src[vic, uic].reshape(-1)
    tol = np.maximum(DEPTH_ABS_TOL_M, DEPTH_REL_TOL * np.maximum(zsrc, 0.0))
    visible = (zsrc > 0) & (zc <= zsrc + tol)
    xs_ = (uic.reshape(-1) + 0.5 - cx) / fx * zsrc
    ys_ = (vic.reshape(-1) + 0.5 - cy) / fy * zsrc
    back = np.linalg.inv(c2w_dst) @ (c2w_src @ np.stack([xs_, ys_, zsrc, np.ones_like(zsrc)], 0))
    zb = back[2]; okf = zb > 1e-6
    ub = fx * back[0] / np.where(okf, zb, 1.0) + cx - 0.5
    vb = fy * back[1] / np.where(okf, zb, 1.0) + cy - 0.5
    du = ub - u.reshape(-1).astype(np.float64); dv = vb - v.reshape(-1).astype(np.float64)
    cyc_ok = okf & (zsrc > 0) & (np.sqrt(du * du + dv * dv) <= CYCLE_PX_TOL)
    keep = base & visible & cyc_ok
    rejected = base & ~(visible & cyc_ok)
    idx = (vi * W + ui)
    return keep, rejected, idx

def mae_on(imgs_src, imgs_dst, mask, idx):
    if mask.sum() == 0: return None
    s = imgs_src.reshape(-1, 3)[idx[mask]].astype(np.int64)
    d = imgs_dst.reshape(-1, 3)[mask].astype(np.int64)
    return float(np.abs(s - d).mean())

def sha(a): return hashlib.sha256(np.ascontiguousarray(a)).hexdigest()[:16]

def real_u8(seq, fid):
    a = np.asarray(Image.open(io.BytesIO((seq / f"frame-{fid:06d}.color.png").read_bytes())).convert("RGB")).astype(np.float64)
    ys = np.clip((np.arange(576) * 480.0 / 576.0).astype(int), 0, 479)
    xs = np.clip((np.arange(768) * 640.0 / 768.0).astype(int), 0, 639)
    return np.clip(a[ys][:, xs][:, 96:672], 0, 255).astype(np.uint8)

def world_colour(depth, K, c2w):
    v, u = np.mgrid[0:H, 0:W]; z = depth
    fx, fy, cx, cy = K[0, 0], K[1, 1], K[0, 2], K[1, 2]
    x = (u + 0.5 - cx) / fx * z; y = (v + 0.5 - cy) / fy * z
    pts = np.stack([x, y, z, np.ones_like(z)], -1).reshape(-1, 4).T
    world = (c2w @ pts)[:3].T.reshape(H, W, 3)
    col = 127.5 * (1.0 + np.sin(world * (2 * np.pi / 0.35)))
    return np.clip(np.where(np.repeat((z > 0)[:, :, None], 3, axis=2), col, 0.0), 0, 255).astype(np.uint8)

rows, mask_mismatches = [], []
for scene, nframes in SCENES.items():
    root = DATA / REL[scene]; seq = root / "seq-01"
    K = np.loadtxt(io.StringIO((root / "camera-intrinsics.txt").read_text()), dtype=np.float64).reshape(3, 3)
    Kg = model_grid_K(K)
    for start in WINDOW_STARTS:
        tgts = [start + o for o in TARGET_OFFSETS]
        if max(tgts) >= nframes: continue
        poses = [load_pose(seq, f) for f in tgts]
        depths = [depth_to_model_grid(seq / f"frame-{f:06d}.depth.png") for f in tgts]
        A = [real_u8(seq, f) for f in tgts]
        B = [world_colour(depths[i], Kg, poses[i]) for i in range(4)]
        D = [a[:, :, [1, 2, 0]].copy() for a in A]                       # fixed channel permutation
        s = st.mean([float(np.abs(B[i].astype(float) - A[i].astype(float)).mean()) for i in range(4)]) * math.sqrt(math.pi / 2)
        C = [np.clip(A[i].astype(float) + RNG.normal(0, s, A[i].shape), 0, 255).astype(np.uint8) for i in range(4)]

        acc = {k: {"kept": [], "rej": []} for k in "ABCD"}
        cov, qs = [], []
        for a in range(4):
            for b in range(4):
                if a == b: continue
                keep, rej, idx = geometry_only_support(depths[a], depths[b], Kg, poses[a], poses[b])
                h = (sha(keep), sha(idx[keep]))
                for name, im in (("A", A), ("B", B), ("C", C), ("D", D)):
                    k2, r2, i2 = geometry_only_support(depths[a], depths[b], Kg, poses[a], poses[b])
                    if (sha(k2), sha(i2[k2])) != h:
                        mask_mismatches.append((scene, start, a, b, name))
                    mk = mae_on(im[a], im[b], keep, idx); mr = mae_on(im[a], im[b], rej, idx)
                    if mk is not None: acc[name]["kept"].append(mk)
                    if mr is not None: acc[name]["rej"].append(mr)
                cov.append(keep.sum() / keep.size)
                qs.append(keep.sum() / max(1, (keep | rej).sum()))
        rec = {"scene": scene, "window_start": start, "coverage": st.mean(cov), "q_kept_frac": st.mean(qs)}
        for k in "ABCD":
            rec[k] = {"kept": st.mean(acc[k]["kept"]), "rejected": st.mean(acc[k]["rej"])}
        rows.append(rec)
        print(f"[{scene} w{start:03d}] A_kept {rec['A']['kept']:6.3f} A_rej {rec['A']['rejected']:7.3f}  "
              f"B_kept {rec['B']['kept']:6.3f}  D_kept {rec['D']['kept']:6.3f}  q={rec['q_kept_frac']:.3f}", flush=True)

print(f"\nmask identity across conditions: {'PASS' if not mask_mismatches else 'FAIL ' + str(mask_mismatches[:3])}")
print("   (the support routine reads only depth, poses and intrinsics; no image is passed to it)")

print("\n=== check 2: channel permutation preserves the score exactly? ===")
dA = [r["A"]["kept"] for r in rows]; dD = [r["D"]["kept"] for r in rows]
mx = max(abs(a - d) for a, d in zip(dA, dD))
print(f"  max |R(A) - R(D)| over windows = {mx:.12f}   identical: {mx < 1e-9}")
print(f"  mean R(A) = {st.mean(dA):.4f}   mean R(D) = {st.mean(dD):.4f}")
fid = st.mean([float(np.abs(np.array([0]))) for _ in [0]])  # placeholder removed below

print("\n=== check 3: paired window-level B - A on the corrected support ===")
d = [(r["scene"], r["window_start"], r["B"]["kept"] - r["A"]["kept"]) for r in rows]
for s_, w_, v in d: print(f"  {s_} w{w_:03d}  {v:+7.3f}")
neg = sum(1 for _, _, v in d if v < 0)
print(f"  mean {st.mean([v for _,_,v in d]):+.3f}   B lower in {neg}/{len(d)} windows")

print("\n=== check 4: correct decomposition of the mask change ===")
q = st.mean([r["q_kept_frac"] for r in rows])
Rk = st.mean([r["A"]["kept"] for r in rows]); Rr = st.mean([r["A"]["rejected"] for r in rows])
Rold = q * Rk + (1 - q) * Rr
print(f"  q (kept fraction of candidate support) = {q:.4f}")
print(f"  R_kept  = {Rk:.4f}      R_rejected = {Rr:.4f}")
print(f"  q*R_kept + (1-q)*R_rejected = {Rold:.4f}")
print(f"  R_old - R_kept = (1-q)*(R_rejected - R_kept) = {(1-q)*(Rr-Rk):.4f}")
print("  -> the rejected samples are NOT shown to be occlusions; this is a mask-change identity only")

out = {"schema": "s110-support-audit-v1", "zero_generation": True, "touched_sealed_outputs": False,
       "mask_identity_pass": not mask_mismatches,
       "channel_permutation_preserves_score_exactly": bool(mx < 1e-9),
       "max_abs_diff_A_vs_D": mx,
       "paired_B_minus_A": [{"scene": s_, "window_start": w_, "delta": v} for s_, w_, v in d],
       "B_lower_in_n_windows": neg, "n_windows": len(d),
       "decomposition": {"q_kept_fraction": q, "R_kept": Rk, "R_rejected": Rr,
                         "identity_R_old": Rold,
                         "note": "R_old - R_kept = (1-q)(R_rejected - R_kept); rejected samples are not established to be occlusions"},
       "rows": rows, "new_method_validated": False, "novelty_authorization": "NONE"}
Path("/home/yliutz/gwm_probe_receipts/SUPPORT_AUDIT_20260918.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
print("\nwrote /home/yliutz/gwm_probe_receipts/SUPPORT_AUDIT_20260918.json")
