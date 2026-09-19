#!/usr/bin/env python3
"""Reference-only qualification of the cross-view reprojection evaluator.

Zero generation.  Touches no sealed output.  Uses only real RGB, sensor depth,
dataset poses and intrinsics -- the same inputs the evaluator already consumes.

It answers the question that must be answered before the evaluator is used on any
generated result: WHAT DOES ITS NUMBER MEAN?  Three reference conditions, all
scored by the project's own `reproject_pair`:

  A  FLOOR                real target frames, unmodified.  Any generated result
                          must be read against this, because sensor depth noise,
                          pose error, occlusion (the evaluator has no z-buffer or
                          forward-backward check) and nearest-neighbour sampling
                          already produce a non-zero reprojection MAE on ground
                          truth itself.

  B  CONSISTENT-BUT-WRONG every pixel is coloured by a deterministic function of
                          its world XYZ, so the same 3D surface point receives the
                          same colour in every view.  Appearance is entirely wrong;
                          cross-view agreement is near perfect by construction.
                          If B scores BETTER than A, the metric rewards shared
                          error rather than fidelity.

  C  INDEPENDENT-ERROR    real frames plus per-view independent noise, scaled so
                          that its mean absolute deviation from A matches B's.
                          Equal error energy, but not shared across views.

A < B would be a decisive demonstration on reference data alone.
"""
import io, json, math, sys, statistics as st
from pathlib import Path
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/yliutz/geometry-world-modeling/work/S103_selector_free_baseline")
from geom_eval_s110 import (reproject_pair, depth_to_model_grid, model_grid_K,
                            load_pose, DATA, REL, H, W)

TARGET_OFFSETS = [60, 75, 90, 105]
WINDOW_STARTS = [50, 100, 150, 200, 250, 300, 350]
SCENES = {"scene_13": 462, "scene_14": 659}
RNG = np.random.default_rng(20260918)

def real_u8(seq, fid):
    a = np.asarray(Image.open(io.BytesIO((seq / f"frame-{fid:06d}.color.png").read_bytes())).convert("RGB"))
    t = a.astype(np.float64)
    ys = np.clip((np.arange(576) * 480.0 / 576.0).astype(int), 0, 479)
    xs = np.clip((np.arange(768) * 640.0 / 768.0).astype(int), 0, 639)
    return np.clip(t[ys][:, xs][:, 96:672], 0, 255).astype(np.uint8)

def world_colour(depth, K, c2w):
    """Colour every pixel by a deterministic function of its world XYZ.
    The same surface point therefore gets the same colour in every view."""
    v, u = np.mgrid[0:H, 0:W]
    z = depth
    fx, fy, cx, cy = K[0, 0], K[1, 1], K[0, 2], K[1, 2]
    x = (u + 0.5 - cx) / fx * z
    y = (v + 0.5 - cy) / fy * z
    pts = np.stack([x, y, z, np.ones_like(z)], -1).reshape(-1, 4).T
    world = (c2w @ pts)[:3].T.reshape(H, W, 3)
    # smooth periodic map, so the field has real spatial structure rather than noise
    col = 127.5 * (1.0 + np.sin(world * (2 * np.pi / 0.35)))
    col = np.where(np.repeat((z > 0)[:, :, None], 3, axis=2), col, 0.0)
    return np.clip(col, 0, 255).astype(np.uint8)

def pair_mae(imgs, depths, Kg, poses):
    maes, covs, sc, inv, oob = [], [], 0, 0, 0
    for a in range(4):
        for b in range(4):
            if a == b: continue
            r = reproject_pair(imgs[a], imgs[b], depths[b], Kg, poses[a], poses[b])
            if r["mae_0_255"] is not None:
                maes.append(r["mae_0_255"]); covs.append(r["coverage"])
            sc += r["scored_pixels"]; inv += r["invalid_depth_pixels"]; oob += r["out_of_bounds_pixels"]
    return (st.mean(maes) if maes else None, st.mean(covs) if covs else 0.0, len(maes), sc, inv, oob)

def sd_of(imgs):
    return st.mean([float(np.asarray(i, dtype=np.float64).std()) for i in imgs])

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
        # independent noise with the SAME mean absolute deviation as B (|N(0,s)| has mean s*sqrt(2/pi))
        s = dev * math.sqrt(math.pi / 2.0)
        C = [np.clip(A[i].astype(np.float64) + RNG.normal(0.0, s, A[i].shape), 0, 255).astype(np.uint8)
             for i in range(4)]
        devC = st.mean([float(np.abs(C[i].astype(np.float64) - A[i].astype(np.float64)).mean()) for i in range(4)])
        rec = {"scene": scene, "window_start": start, "target_frame_ids": tgts,
               "mean_abs_dev_B_from_A": round(dev, 3), "mean_abs_dev_C_from_A": round(devC, 3)}
        for name, imgs in (("A_floor_real", A), ("B_consistent_wrong", B), ("C_independent_error", C)):
            mae, cov, npair, sc, inv, oob = pair_mae(imgs, depths, Kg, poses)
            sd = sd_of(imgs)
            rec[name] = {"reproj_mae": mae, "spatial_sd": sd,
                         "mae_per_sd": (mae / sd) if (mae is not None and sd > 1e-9) else None,
                         "coverage": cov, "pairs": npair,
                         "scored_px": sc, "invalid_depth_px": inv, "oob_px": oob}
        rows.append(rec)
        print(f"[{scene} w{start:03d}] A={rec['A_floor_real']['reproj_mae']:7.3f}  "
              f"B={rec['B_consistent_wrong']['reproj_mae']:7.3f}  "
              f"C={rec['C_independent_error']['reproj_mae']:7.3f}  "
              f"(equal-energy dev A->B {dev:.2f}, A->C {devC:.2f}, coverage {rec['A_floor_real']['coverage']:.3f})",
              flush=True)

print("\n=== summary over %d windows ===" % len(rows))
print(f"{'condition':22} {'reproj MAE':>11} {'spatial sd':>11} {'MAE/sd':>9} {'coverage':>9}")
summ = {}
for name, label in (("A_floor_real", "A  floor (real)"),
                    ("B_consistent_wrong", "B  consistent-wrong"),
                    ("C_independent_error", "C  independent-error")):
    m = st.mean([r[name]["reproj_mae"] for r in rows])
    sd = st.mean([r[name]["spatial_sd"] for r in rows])
    ps = st.mean([r[name]["mae_per_sd"] for r in rows])
    cv = st.mean([r[name]["coverage"] for r in rows])
    summ[name] = {"reproj_mae": m, "spatial_sd": sd, "mae_per_sd": ps, "coverage": cv,
                  "n_windows": len(rows)}
    print(f"{label:22} {m:11.3f} {sd:11.3f} {ps:9.4f} {cv:9.3f}")

a = summ["A_floor_real"]; b = summ["B_consistent_wrong"]
print(f"\nB beats the real-frame floor on raw MAE : {b['reproj_mae'] < a['reproj_mae']}"
      f"   ({b['reproj_mae']:.3f} vs {a['reproj_mae']:.3f})")
print(f"B beats the real-frame floor on MAE/sd  : {b['mae_per_sd'] < a['mae_per_sd']}"
      f"   ({b['mae_per_sd']:.4f} vs {a['mae_per_sd']:.4f})")

out = {"schema": "s110-reference-only-qualification-v1", "zero_generation": True,
       "touched_sealed_outputs": False,
       "purpose": "establish what the cross-view reprojection number means before it is used on any generated result",
       "conditions": {"A": "real target frames, unmodified",
                      "B": "pixels coloured by a deterministic function of world XYZ; same surface point, same colour in every view",
                      "C": "real frames plus independent per-view noise, mean-absolute-deviation matched to B"},
       "known_evaluator_limits_this_exposes": [
           "no z-buffer and no forward-backward visibility check, so occluded surfaces are sampled silently",
           "nearest-neighbour sampling",
           "the metric has no interpretable zero without this floor"],
       "summary": summ, "rows": rows,
       "new_method_validated": False, "novelty_authorization": "NONE"}
Path("/home/yliutz/gwm_probe_receipts/REFERENCE_FLOOR_20260918.json").write_text(
    json.dumps(out, indent=2, sort_keys=True) + "\n")
print("\nwrote /home/yliutz/gwm_probe_receipts/REFERENCE_FLOOR_20260918.json")
