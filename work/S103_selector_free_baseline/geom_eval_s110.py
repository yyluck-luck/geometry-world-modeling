#!/usr/bin/env python3
"""Cross-view reprojection consistency: a geometry-sensitive evaluator.

Motivation.  The RGB metric used so far cannot see geometric self-consistency,
and the external audit (P5.2) confirmed no geometry evaluator existed.  Estimating
depth from the generated RGB would introduce the shared-source bias the audit
warns about (P5.3), especially since CUT3R is inside the memory arm.

This evaluator avoids that entirely.  It warps one GENERATED target view into
another GENERATED target view using ONLY the dataset's own Kinect depth and
poses, and measures whether the two generated images agree where they should.
No depth is estimated from the predictions, so no estimator bias enters.

Explicit accounting, per audit N08: every pixel is classified as scored,
invalid-depth, or out-of-bounds, and all three counts are reported.  Nothing is
silently dropped.

Gauge note: depth is metric from the sensor and poses come from the dataset's
RGB-D Mapping reconstruction, so this measures consistency with that reference
frame, not with physical ground truth (audit N-2 / Brachmann et al. ICCV 2021).

DEVELOPMENT scope.
"""
import io, json, math, statistics as st, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
from PIL import Image
import dataset_geometry

DATA = Path("/home/yliutz/datasets")
REL = {"scene_13": "heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13",
       "scene_14": "heldout_3dmatch_scene14/extracted/rgbd-scenes-v2-scene_14"}
H = W = 576

def require(value, message):
    if not value:
        raise RuntimeError(message)


def model_grid_K(K):
    k = K.astype(np.float64).copy()
    k[0] *= 768.0 / 640.0
    k[1] *= 576.0 / 480.0
    k[0, 2] -= 96.0
    return k

def depth_to_model_grid(path, dataset_id="rgbd-scenes-v2"):
    """Native 640x480 -> 768x576 -> crop x[96:672].  Nearest only: depth must not
    be interpolated across discontinuities or into invalid (zero) pixels.

    Addendum A2: the divisor is looked up per dataset, never hardcoded.  This
    file previously assumed /1000 for every dataset, which is correct for
    RGB-D Scenes v2 and wrong by 5x for TUM.
    """
    conv = dataset_geometry.get(dataset_id)
    d = np.asarray(Image.open(io.BytesIO(Path(path).read_bytes()))).astype(np.float64)
    expected = (conv.native_wh[1], conv.native_wh[0])
    require(d.shape == expected, f"{dataset_id}: depth shape {d.shape} != {expected}")
    d = np.where(d == conv.invalid_depth_value, 0.0, d)
    ys = np.clip((np.arange(576) * 480.0 / 576.0).astype(int), 0, 479)
    xs = np.clip((np.arange(768) * 640.0 / 768.0).astype(int), 0, 639)
    return (d[ys][:, xs][:, 96:672]) / conv.depth_divisor

def pred_u8(frame):
    img = frame.transpose(1, 2, 0)
    if float(img.min()) < -0.1:
        img = (img + 1.0) / 2.0
    return np.clip(img * 255.0, 0, 255).astype(np.uint8)

def load_pose(seq, fid):
    return np.loadtxt(io.StringIO((seq / f"frame-{fid:06d}.pose.txt").read_text()),
                      dtype=np.float64).reshape(4, 4)

def reproject_pair(img_src, img_dst, depth_dst, K, c2w_src, c2w_dst):
    """Warp src into dst's frame using dst depth; compare with dst image."""
    v, u = np.mgrid[0:H, 0:W]
    z = depth_dst
    valid_depth = z > 0
    fx, fy, cx, cy = K[0, 0], K[1, 1], K[0, 2], K[1, 2]
    x = (u + 0.5 - cx) / fx * z
    y = (v + 0.5 - cy) / fy * z
    pts = np.stack([x, y, z, np.ones_like(z)], -1).reshape(-1, 4).T      # 4xN
    world = c2w_dst @ pts
    cam = np.linalg.inv(c2w_src) @ world
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
    n_scored = int(mask.sum())
    if n_scored == 0:
        return {"scored_pixels": 0, "invalid_depth_pixels": n_invalid_depth,
                "out_of_bounds_pixels": n_oob, "total_pixels": n_total,
                "coverage": 0.0, "mae_0_255": None}
    src_flat = img_src.reshape(-1, 3)
    dst_flat = img_dst.reshape(-1, 3)
    sampled = src_flat[(vi[mask] * W + ui[mask])]
    target = dst_flat[mask]
    mae = float(np.abs(sampled.astype(np.int64) - target.astype(np.int64)).mean())
    return {"scored_pixels": n_scored, "invalid_depth_pixels": n_invalid_depth,
            "out_of_bounds_pixels": n_oob, "total_pixels": n_total,
            "coverage": n_scored / n_total, "mae_0_255": mae}

def main():
    RUNDIR = Path(sys.argv[1])
    RECEIPT_NAME = sys.argv[2] if len(sys.argv) > 2 else "MEMVSTATIC_RECEIPT.json"
    receipt = json.loads((RUNDIR / RECEIPT_NAME).read_text())
    rows, dcache, pcache = [], {}, {}
    for run in receipt["runs"]:
        scene, tgts = run["scene"], run["target_frame_ids"]
        root = DATA / REL[scene]; seq = root / "seq-01"
        if scene not in pcache:
            K = np.loadtxt(io.StringIO((root / "camera-intrinsics.txt").read_text()),
                           dtype=np.float64).reshape(3, 3)
            pcache[scene] = model_grid_K(K)
        Kg = pcache[scene]
        arr = np.load(RUNDIR / f'{run["tag"]}.npy')
        imgs = [pred_u8(arr[i]) for i in range(4)]
        poses = [load_pose(seq, f) for f in tgts]
        maes, cov, inv, oob, sc = [], [], 0, 0, 0
        for a in range(4):
            for b in range(4):
                if a == b: continue
                key = (scene, tgts[b])
                if key not in dcache:
                    dcache[key] = depth_to_model_grid(seq / f"frame-{tgts[b]:06d}.depth.png")
                r = reproject_pair(imgs[a], imgs[b], dcache[key], Kg, poses[a], poses[b])
                if r["mae_0_255"] is not None:
                    maes.append(r["mae_0_255"]); cov.append(r["coverage"])
                inv += r["invalid_depth_pixels"]; oob += r["out_of_bounds_pixels"]; sc += r["scored_pixels"]
        rows.append({"tag": run["tag"], "scene": scene, "window_start": run["window_start"],
                     "arm": run["arm"], "seed": run["seed"], "n_pairs_scored": len(maes),
                     "reprojection_mae_0_255": st.mean(maes) if maes else None,
                     "mean_coverage": st.mean(cov) if cov else 0.0,
                     "scored_pixels": sc, "invalid_depth_pixels": inv, "out_of_bounds_pixels": oob})

    by_arm = defaultdict(list)
    for r in rows:
        if r["reprojection_mae_0_255"] is not None:
            by_arm[r["arm"]].append(r["reprojection_mae_0_255"])
    print(f"{'arm':12} {'n':>3} {'reproj MAE':>11} {'sd':>7}   (lower = more geometrically consistent)")
    arm_stats = {}
    for arm, v in sorted(by_arm.items(), key=lambda kv: st.mean(kv[1])):
        arm_stats[arm] = {"n": len(v), "mean_reproj_mae": st.mean(v),
                          "sd": st.stdev(v) if len(v) > 1 else 0.0}
        print(f"{arm:12} {len(v):3d} {st.mean(v):11.4f} {arm_stats[arm]['sd']:7.4f}")

    paired = defaultdict(dict)
    for r in rows:
        paired[(r["scene"], r["window_start"], r["seed"])][r["arm"]] = r["reprojection_mae_0_255"]
    arms = sorted(by_arm)
    contrasts = {}
    if len(arms) == 2:
        a, b = arms
        diffs = [v[a] - v[b] for v in paired.values() if a in v and b in v and None not in (v.get(a), v.get(b))]
        if diffs:
            m = st.mean(diffs); sd = st.stdev(diffs) if len(diffs) > 1 else 0.0
            neg = sum(1 for d in diffs if d < 0)
            contrasts[f"{a}_minus_{b}"] = {"n_pairs": len(diffs), "mean": m, "sd": sd,
                                           "n_better_for_first": neg}
            print(f"\npaired: {a} - {b} = {m:+.4f} MAE  sd {sd:.4f}  n={len(diffs)}  "
                  f"first better in {neg}/{len(diffs)}")

    cov_all = [r["mean_coverage"] for r in rows]
    out = {"schema": "s110-cross-view-reprojection-consistency-v1",
           "method": ("warp one generated target view into another using only dataset Kinect depth "
                      "and dataset poses; no depth is estimated from predictions"),
           "gauge_note": ("poses are RGB-D Mapping reconstruction output, so this measures "
                          "consistency with that reference frame, not physical ground truth"),
           "mean_coverage": st.mean(cov_all) if cov_all else 0.0,
           "per_arm": arm_stats, "paired_contrasts": contrasts, "rows": rows,
           "scientific_result": False, "new_method_validated": False, "novelty_authorization": "NONE"}
    (RUNDIR / "GEOMETRY_CONSISTENCY.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(f"\nmean valid-pixel coverage {out['mean_coverage']:.3f}; scored {len(rows)} runs")


if __name__ == "__main__":
    main()
