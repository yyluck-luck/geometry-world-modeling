#!/usr/bin/env python3
"""Reference floor with visibility handling: z-buffer plus forward-backward check.

The existing evaluator warps every valid-depth pixel of the destination view into
the source view and samples there, with no test that the surface point is actually
VISIBLE in the source.  Occluded points are sampled silently, which inflates the
reprojection MAE in a content-dependent way.  This module adds the two standard
tests, using ONLY sensor depth and dataset poses -- nothing is estimated from any
image.

  Z-BUFFER TEST.  The point's depth in the source camera, z_c, is compared with
  the source view's OWN sensor depth at the landing pixel.  If z_c exceeds it by
  more than the tolerance, the point is behind the surface the source actually
  sees, so it is occluded and is rejected instead of sampled.

  FORWARD-BACKWARD TEST.  The landing pixel is unprojected with the source's own
  sensor depth and projected back into the destination view.  If it does not
  return within the pixel tolerance, the correspondence is not self-consistent
  and is rejected.

Thresholds are DECLARED HERE BEFORE THE RUN.  Primary: depth tolerance
max(0.02 m, 2% of range), cycle tolerance 1.0 px.  Two alternates are reported
as a descriptive sensitivity check only; the primary is not chosen after seeing
results.

Zero generation.  No sealed output is read.
"""
import io, json, math, sys, statistics as st
from pathlib import Path
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/yliutz/geometry-world-modeling/work/S103_selector_free_baseline")
from geom_eval_s110 import depth_to_model_grid, model_grid_K, load_pose, DATA, REL, H, W

DEPTH_ABS_TOL_M = 0.02      # declared in advance
DEPTH_REL_TOL   = 0.02      # declared in advance
CYCLE_PX_TOL    = 1.0       # declared in advance
ALTERNATES = [(0.01, 0.01, 0.5), (0.05, 0.05, 2.0)]

TARGET_OFFSETS = [60, 75, 90, 105]
WINDOW_STARTS = [50, 100, 150, 200, 250, 300, 350]
SCENES = {"scene_13": 462, "scene_14": 659}
RNG = np.random.default_rng(20260918)


def reproject_pair_v2(img_src, img_dst, depth_src, depth_dst, K, c2w_src, c2w_dst,
                      use_zbuffer, use_cycle, dabs=DEPTH_ABS_TOL_M, drel=DEPTH_REL_TOL,
                      cyc=CYCLE_PX_TOL):
    v, u = np.mgrid[0:H, 0:W]
    z = depth_dst
    valid_depth = z > 0
    fx, fy, cx, cy = K[0, 0], K[1, 1], K[0, 2], K[1, 2]
    x = (u + 0.5 - cx) / fx * z
    y = (v + 0.5 - cy) / fy * z
    pts = np.stack([x, y, z, np.ones_like(z)], -1).reshape(-1, 4).T
    world = c2w_dst @ pts
    w2c_src = np.linalg.inv(c2w_src)
    cam = w2c_src @ world
    zc = cam[2]
    in_front = zc > 1e-6
    us = fx * cam[0] / np.where(in_front, zc, 1.0) + cx - 0.5
    vs = fy * cam[1] / np.where(in_front, zc, 1.0) + cy - 0.5
    ui = np.rint(us).astype(np.int64); vi = np.rint(vs).astype(np.int64)
    inb = (ui >= 0) & (ui < W) & (vi >= 0) & (vi < H) & in_front
    mask = valid_depth.reshape(-1) & inb

    n_total = mask.size
    n_invalid_depth = int((~valid_depth).sum())
    n_oob = int((valid_depth.reshape(-1) & ~inb).sum())
    n_occluded = n_cycle = 0

    uic = np.clip(ui, 0, W - 1); vic = np.clip(vi, 0, H - 1)
    zsrc_at = depth_src[vic, uic].reshape(-1)

    if use_zbuffer:
        tol = np.maximum(dabs, drel * np.maximum(zsrc_at, 0.0))
        src_valid = zsrc_at > 0
        visible = src_valid & (zc <= zsrc_at + tol)
        n_occluded = int((mask & ~visible).sum())
        mask = mask & visible

    if use_cycle:
        zs = zsrc_at
        xs_ = (uic.reshape(-1) + 0.5 - cx) / fx * zs
        ys_ = (vic.reshape(-1) + 0.5 - cy) / fy * zs
        p_src = np.stack([xs_, ys_, zs, np.ones_like(zs)], 0)
        back = np.linalg.inv(c2w_dst) @ (c2w_src @ p_src)
        zb = back[2]
        ok_front = zb > 1e-6
        ub = fx * back[0] / np.where(ok_front, zb, 1.0) + cx - 0.5
        vb = fy * back[1] / np.where(ok_front, zb, 1.0) + cy - 0.5
        du = ub - u.reshape(-1).astype(np.float64)
        dv = vb - v.reshape(-1).astype(np.float64)
        cycle_ok = ok_front & (zs > 0) & (np.sqrt(du * du + dv * dv) <= cyc)
        n_cycle = int((mask & ~cycle_ok).sum())
        mask = mask & cycle_ok

    n_scored = int(mask.sum())
    if n_scored == 0:
        return {"scored_pixels": 0, "invalid_depth_pixels": n_invalid_depth,
                "out_of_bounds_pixels": n_oob, "occluded_pixels": n_occluded,
                "cycle_rejected_pixels": n_cycle, "total_pixels": n_total,
                "coverage": 0.0, "mae_0_255": None}
    src_flat = img_src.reshape(-1, 3); dst_flat = img_dst.reshape(-1, 3)
    sampled = src_flat[(vi[mask] * W + ui[mask])]
    target = dst_flat[mask]
    mae = float(np.abs(sampled.astype(np.int64) - target.astype(np.int64)).mean())
    return {"scored_pixels": n_scored, "invalid_depth_pixels": n_invalid_depth,
            "out_of_bounds_pixels": n_oob, "occluded_pixels": n_occluded,
            "cycle_rejected_pixels": n_cycle, "total_pixels": n_total,
            "coverage": n_scored / n_total, "mae_0_255": mae}


def real_u8(seq, fid):
    a = np.asarray(Image.open(io.BytesIO((seq / f"frame-{fid:06d}.color.png").read_bytes())).convert("RGB"))
    t = a.astype(np.float64)
    ys = np.clip((np.arange(576) * 480.0 / 576.0).astype(int), 0, 479)
    xs = np.clip((np.arange(768) * 640.0 / 768.0).astype(int), 0, 639)
    return np.clip(t[ys][:, xs][:, 96:672], 0, 255).astype(np.uint8)

def world_colour(depth, K, c2w):
    v, u = np.mgrid[0:H, 0:W]
    z = depth
    fx, fy, cx, cy = K[0, 0], K[1, 1], K[0, 2], K[1, 2]
    x = (u + 0.5 - cx) / fx * z; y = (v + 0.5 - cy) / fy * z
    pts = np.stack([x, y, z, np.ones_like(z)], -1).reshape(-1, 4).T
    world = (c2w @ pts)[:3].T.reshape(H, W, 3)
    col = 127.5 * (1.0 + np.sin(world * (2 * np.pi / 0.35)))
    return np.clip(np.where(np.repeat((z > 0)[:, :, None], 3, axis=2), col, 0.0), 0, 255).astype(np.uint8)

def run(imgs, depths, Kg, poses, zb, cy_, **kw):
    maes, covs, occ, cyc, sc = [], [], 0, 0, 0
    for a in range(4):
        for b in range(4):
            if a == b: continue
            r = reproject_pair_v2(imgs[a], imgs[b], depths[a], depths[b], Kg,
                                  poses[a], poses[b], zb, cy_, **kw)
            if r["mae_0_255"] is not None:
                maes.append(r["mae_0_255"]); covs.append(r["coverage"])
            occ += r["occluded_pixels"]; cyc += r["cycle_rejected_pixels"]; sc += r["scored_pixels"]
    return {"mae": st.mean(maes) if maes else None, "coverage": st.mean(covs) if covs else 0.0,
            "occluded_px": occ, "cycle_rejected_px": cyc, "scored_px": sc, "pairs": len(maes)}

SETTINGS = [("baseline_no_checks", False, False), ("zbuffer_only", True, False),
            ("cycle_only", False, True), ("zbuffer_and_cycle", True, True)]

rows = []
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
        dev = st.mean([float(np.abs(B[i].astype(np.float64) - A[i].astype(np.float64)).mean()) for i in range(4)])
        s = dev * math.sqrt(math.pi / 2.0)
        C = [np.clip(A[i].astype(np.float64) + RNG.normal(0.0, s, A[i].shape), 0, 255).astype(np.uint8) for i in range(4)]
        devC = st.mean([float(np.abs(C[i].astype(np.float64) - A[i].astype(np.float64)).mean()) for i in range(4)])
        rec = {"scene": scene, "window_start": start, "dev_B": round(dev, 3), "dev_C": round(devC, 3)}
        for name, zb, cy_ in SETTINGS:
            rec[name] = {cond: run(im, depths, Kg, poses, zb, cy_)
                         for cond, im in (("A", A), ("B", B), ("C", C))}
        for i, (da, dr, cp) in enumerate(ALTERNATES):
            rec[f"alt{i}_zbuffer_and_cycle"] = {"tol": [da, dr, cp],
                "A": run(A, depths, Kg, poses, True, True, dabs=da, drel=dr, cyc=cp)}
        rows.append(rec)
        b = rec["baseline_no_checks"]["A"]; f = rec["zbuffer_and_cycle"]["A"]
        print(f"[{scene} w{start:03d}] floor  raw {b['mae']:6.3f} (cov {b['coverage']:.3f})"
              f"  ->  z+cycle {f['mae']:6.3f} (cov {f['coverage']:.3f})", flush=True)

print(f"\n=== floor by visibility setting, mean over {len(rows)} windows ===")
print(f"{'setting':22} {'A floor':>9} {'coverage':>9} {'B':>9} {'C':>9}")
summ = {}
for name, _, _ in SETTINGS:
    a = st.mean([r[name]["A"]["mae"] for r in rows]); ca = st.mean([r[name]["A"]["coverage"] for r in rows])
    bb = st.mean([r[name]["B"]["mae"] for r in rows]); cc = st.mean([r[name]["C"]["mae"] for r in rows])
    summ[name] = {"A_mae": a, "A_coverage": ca, "B_mae": bb, "C_mae": cc,
                  "A_occluded_px": sum(r[name]["A"]["occluded_px"] for r in rows),
                  "A_cycle_rejected_px": sum(r[name]["A"]["cycle_rejected_px"] for r in rows)}
    print(f"{name:22} {a:9.3f} {ca:9.3f} {bb:9.3f} {cc:9.3f}")

dB = st.mean([r["dev_B"] for r in rows]); dC = st.mean([r["dev_C"] for r in rows])
print(f"\n=== consistency-vs-independence, cost per unit appearance deviation ===")
print(f"{'setting':22} {'B/unit':>9} {'C/unit':>9} {'ratio':>8}")
for name, _, _ in SETTINGS:
    pb = summ[name]["B_mae"] / dB; pc = summ[name]["C_mae"] / dC
    summ[name]["cost_ratio_C_over_B"] = pc / pb
    print(f"{name:22} {pb:9.4f} {pc:9.4f} {pc/pb:7.1f}x")

print(f"\n=== tolerance sensitivity on the floor (descriptive only) ===")
for i, (da, dr, cp) in enumerate(ALTERNATES):
    a = st.mean([r[f"alt{i}_zbuffer_and_cycle"]["A"]["mae"] for r in rows])
    c = st.mean([r[f"alt{i}_zbuffer_and_cycle"]["A"]["coverage"] for r in rows])
    print(f"  depth tol max({da} m, {dr:.0%}), cycle {cp} px -> floor {a:.3f}, coverage {c:.3f}")
print(f"  PRIMARY: max({DEPTH_ABS_TOL_M} m, {DEPTH_REL_TOL:.0%}), cycle {CYCLE_PX_TOL} px "
      f"-> floor {summ['zbuffer_and_cycle']['A_mae']:.3f}, coverage {summ['zbuffer_and_cycle']['A_coverage']:.3f}")

out = {"schema": "s110-visibility-corrected-floor-v1", "zero_generation": True,
       "touched_sealed_outputs": False,
       "declared_thresholds": {"depth_abs_tol_m": DEPTH_ABS_TOL_M, "depth_rel_tol": DEPTH_REL_TOL,
                               "cycle_px_tol": CYCLE_PX_TOL, "declared_before_run": True},
       "alternates_are_descriptive_only": True,
       "summary": summ, "mean_dev_B": dB, "mean_dev_C": dC, "rows": rows,
       "new_method_validated": False, "novelty_authorization": "NONE"}
Path("/home/yliutz/gwm_probe_receipts/VISIBILITY_FLOOR_20260918.json").write_text(
    json.dumps(out, indent=2, sort_keys=True) + "\n")
print("\nwrote /home/yliutz/gwm_probe_receipts/VISIBILITY_FLOOR_20260918.json")
