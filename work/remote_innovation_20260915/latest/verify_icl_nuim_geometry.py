#!/usr/bin/env python3
"""S104 qualification: verify ICL-NUIM depth scale and pose convention from the
official archive alone, before any CUT3R prediction is scored.

Why this exists
---------------
The S104 CUT3R run produced predictions, but scoring them against ICL-NUIM
ground truth requires three things that were NOT established when the run was
made:

  1. camera intrinsics          -> now sourced from the official ICL-NUIM
                                   ``codes.html`` page (fx=481.20, fy=-480.00,
                                   cx=319.50, cy=239.50; fy is negative)
  2. the raw 16-bit depth scale -> NOT stated on the page for the
                                   TUM-compatible PNG distribution
  3. pose direction             -> whether ``livingRoom0.gt.freiburg`` rows are
                                   camera-to-world or world-to-camera

Rather than assume (2) and (3), this script measures them.  ICL-NUIM living
room is a *static, noise-free synthetic* scene, which gives a decisive test:
if the depth scale and the pose direction are both correct, then 3D points
reconstructed from one frame must land on the surfaces seen by another frame.
A wrong scale or a transposed pose breaks that agreement immediately.

The test therefore needs no model, no network and no extra download.  It reads
only the archive that is already on disk.

Hypotheses swept
----------------
  depth scale   : 1/1000 (millimetres), 1/5000 (TUM PNG convention), 1/10000
  pose direction: row used directly as camera-to-world (c2w), versus its
                  inverse treated as camera-to-world (i.e. the file stores w2c)

Read-only: opens the archive, writes nothing except its JSON report.

Usage
-----
    python3 verify_icl_nuim_geometry.py \
        --archive /home/yliutz/datasets/icl_nuim/living_room_traj0_frei_png.tar.gz \
        --out RESULTS.json
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import tarfile
from pathlib import Path

import numpy as np
from PIL import Image

# Official intrinsics, ICL-NUIM codes page (fetched 2026-09-15):
#   K = [481.20, 0, 319.50; 0, -480.00, 239.50; 0, 0, 1]
#   "Note that the focal length on the y-axis is negative."
FX, FY, CX, CY = 481.20, -480.00, 319.50, 239.50

REF_FRAME = 1
TGT_FRAMES = (31, 61, 91)
DEPTH_SCALES = (1 / 1000.0, 1 / 5000.0, 1 / 10000.0)


def read_pose_table(text: str) -> dict[int, np.ndarray]:
    """Parse ``livingRoom0.gt.freiburg``: frame_idx tx ty tz qx qy qz qw."""
    table: dict[int, np.ndarray] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        f = line.split()
        if len(f) != 8:
            raise ValueError(f"expected 8 columns, got {len(f)}: {line!r}")
        idx = int(float(f[0]))
        t = np.array([float(f[1]), float(f[2]), float(f[3])], dtype=np.float64)
        q = np.array([float(f[4]), float(f[5]), float(f[6]), float(f[7])], dtype=np.float64)
        n = np.linalg.norm(q)
        if n < 1e-12:
            raise ValueError(f"zero-norm quaternion at frame {idx}")
        q /= n
        x, y, z, w = q
        rot = np.array([
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ], dtype=np.float64)
        m = np.eye(4)
        m[:3, :3] = rot
        m[:3, 3] = t
        table[idx] = m
    return table


def read_depth(tf: tarfile.TarFile, name: str) -> np.ndarray:
    fh = tf.extractfile(name)
    if fh is None:
        raise FileNotFoundError(name)
    arr = np.asarray(Image.open(io.BytesIO(fh.read())))
    if arr.dtype != np.uint16:
        arr = arr.astype(np.uint16)
    return arr


def backproject(depth_m: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Pixel grid (N,2) and camera-frame points (N,3). fy is negative by design."""
    h, w = depth_m.shape
    v, u = np.mgrid[0:h, 0:w]
    z = depth_m.reshape(-1).astype(np.float64)
    u = u.reshape(-1).astype(np.float64)
    v = v.reshape(-1).astype(np.float64)
    ok = z > 0
    u, v, z = u[ok], v[ok], z[ok]
    x = (u - CX) * z / FX
    y = (v - CY) * z / FY
    return np.column_stack((u, v)), np.column_stack((x, y, z))


def project(points_cam: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Project camera-frame points to pixels; returns (uv, z). fy is negative."""
    z = points_cam[:, 2]
    safe = np.where(np.abs(z) < 1e-12, np.nan, z)
    u = FX * points_cam[:, 0] / safe + CX
    v = FY * points_cam[:, 1] / safe + CY
    return np.column_stack((u, v)), z


def evaluate(ref_depth_m: np.ndarray, ref_c2w: np.ndarray,
             tgt_depth_m: np.ndarray, tgt_c2w: np.ndarray) -> dict:
    """Reconstruct target points in world, reproject into the reference view,
    and compare the reprojected depth with the reference's own GT depth."""
    _, pts_tgt_cam = backproject(tgt_depth_m)
    pts_world = pts_tgt_cam @ tgt_c2w[:3, :3].T + tgt_c2w[:3, 3]
    # world -> reference camera
    pts_ref_cam = (pts_world - ref_c2w[:3, 3]) @ ref_c2w[:3, :3]
    uv, z = project(pts_ref_cam)

    h, w = ref_depth_m.shape
    uu = np.rint(uv[:, 0]).astype(np.int64)
    vv = np.rint(uv[:, 1]).astype(np.int64)
    inside = (uu >= 0) & (uu < w) & (vv >= 0) & (vv < h) & (z > 0)
    coverage = float(inside.mean())

    if inside.sum() < 100:
        return {"coverage": coverage, "n_compared": int(inside.sum()),
                "median_abs_rel": None, "median_abs_mm": None}

    z_ref = ref_depth_m[vv[inside], uu[inside]].astype(np.float64)
    z_pred = z[inside]
    valid = z_ref > 0
    if valid.sum() < 100:
        return {"coverage": coverage, "n_compared": int(valid.sum()),
                "median_abs_rel": None, "median_abs_mm": None}
    z_ref, z_pred = z_ref[valid], z_pred[valid]
    abs_rel = np.abs(z_pred - z_ref) / z_ref
    return {
        "coverage": coverage,
        "n_compared": int(z_ref.size),
        "median_abs_rel": float(np.median(abs_rel)),
        "median_abs_mm": float(np.median(np.abs(z_pred - z_ref)) * 1000.0),
        "frac_within_1pct": float((abs_rel < 0.01).mean()),
        "frac_within_5pct": float((abs_rel < 0.05).mean()),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("RESULTS.json"))
    args = ap.parse_args()

    frames = (REF_FRAME,) + TGT_FRAMES
    raw: dict[int, np.ndarray] = {}
    pose_text = None
    with tarfile.open(args.archive, "r:gz") as tf:
        for m in tf.getmembers():
            if m.name.endswith("gt.freiburg"):
                pose_text = tf.extractfile(m).read().decode("utf-8", "replace")
            base = m.name.rsplit("/", 1)[-1]
            if m.name.startswith("depth/") and base[:-4].isdigit() and int(base[:-4]) in frames:
                raw[int(base[:-4])] = read_depth(tf, m.name)
    if pose_text is None:
        raise RuntimeError("no *.gt.freiburg member found")
    missing = [f for f in frames if f not in raw]
    if missing:
        raise RuntimeError(f"depth frames missing from archive: {missing}")

    poses = read_pose_table(pose_text)

    results = {}
    for scale in DEPTH_SCALES:
        depth_m = {f: raw[f].astype(np.float64) * scale for f in frames}
        for pose_mode in ("c2w_direct", "c2w_inverse"):
            per_pair = {}
            for tgt in TGT_FRAMES:
                ref_c2w = poses[REF_FRAME]
                tgt_c2w = poses[tgt]
                if pose_mode == "c2w_inverse":
                    ref_c2w = np.linalg.inv(ref_c2w)
                    tgt_c2w = np.linalg.inv(tgt_c2w)
                per_pair[f"1->{tgt}"] = evaluate(depth_m[REF_FRAME], ref_c2w,
                                                depth_m[tgt], tgt_c2w)
            valid = [v["median_abs_rel"] for v in per_pair.values()
                     if v["median_abs_rel"] is not None]
            results[f"scale=1/{int(round(1/scale))}|pose={pose_mode}"] = {
                "depth_scale": scale, "pose_mode": pose_mode,
                "pairs": per_pair,
                "mean_median_abs_rel": float(np.mean(valid)) if valid else None,
            }

    ranking = sorted(
        ({"key": k, "mean_median_abs_rel": v["mean_median_abs_rel"]}
         for k, v in results.items() if v["mean_median_abs_rel"] is not None),
        key=lambda r: r["mean_median_abs_rel"])

    report = {
        "schema": "s104-icl-nuim-geometry-qualification-v1",
        "archive": str(args.archive.resolve()),
        "archive_bytes": args.archive.stat().st_size,
        "archive_sha256_expected": "4eca8c2e9f77c1bd7436c746d22ea6144b8c01fe9bc29a84e734186823f1f1ad",
        "intrinsics": {"fx": FX, "fy": FY, "cx": CX, "cy": CY,
                       "source": "official ICL-NUIM codes page (VaFRIC/codes.html), fetched 2026-09-15",
                       "note": "official page states the y-axis focal length is negative"},
        "reference_frame": REF_FRAME,
        "target_frames": list(TGT_FRAMES),
        "pose_file_rows": len(poses),
        "method": ("static synthetic scene: back-project target-frame GT depth, place in world via "
                   "GT pose, reproject into reference view, compare against reference GT depth"),
        "hypotheses": results,
        "ranking_best_first": ranking,
        "model_execution": False,
        "cut3r_prediction_used": False,
        "note": ("Reads ICL-NUIM ground-truth depth and pose for DATA QUALIFICATION only. "
                 "The S104 CUT3R prediction was sealed before this check and is not used here."),
    }
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(f"intrinsics fx={FX} fy={FY} cx={CX} cy={CY}")
    print(f"{'hypothesis':<34} {'mean median |Δz|/z':>20}")
    for r in ranking:
        print(f"{r['key']:<34} {r['mean_median_abs_rel']:>20.6f}")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
