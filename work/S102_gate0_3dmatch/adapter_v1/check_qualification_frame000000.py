#!/usr/bin/env python3
"""Bounded, CPU-only adapter qualification on the already exposed scene13 frame 0.

This runner is intentionally not a history-window or held-out experiment. It
does not glob the scene, inspect future paths, construct a model, or score a
prediction. It checks source decoding, metric conversion, projection algebra,
the VMem 576-square preprocessing contract, and fail-closed role/path guards.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np

from rgbd_scenes_v2 import (
    EXPECTED_K,
    OUTPUT_HW,
    SOURCE_HW,
    decode_depth_mm,
    decode_rgb,
    optical_c2w_to_vmem_input,
    parse_K,
    parse_c2w,
    preprocess_rgb,
    project,
    read_bound,
    unproject,
)

ROOT = Path(__file__).resolve().parent
STAGE = ROOT / "qualification_input"
MANIFEST = json.loads((ROOT / "QUALIFICATION_ACCESS_MANIFEST.json").read_text())
FILES = MANIFEST["files"]


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    # Only the four pre-exposed files named in the manifest are touched.
    k = parse_K(read_bound(STAGE, "camera-intrinsics.txt", FILES, "calibration_intrinsics"))
    rgb = decode_rgb(read_bound(STAGE, "seq-01/frame-000000.color.png", FILES,
                                "exposed_qualification_rgb"))
    raw, z_m, valid = decode_depth_mm(read_bound(STAGE, "seq-01/frame-000000.depth.png", FILES,
                                                 "exposed_qualification_depth"))
    c2w = parse_c2w(read_bound(STAGE, "seq-01/frame-000000.pose.txt", FILES,
                               "exposed_qualification_pose"))

    check(rgb.shape == (*SOURCE_HW, 3) and rgb.dtype == np.uint8, "RGB shape/dtype")
    check(raw.shape == SOURCE_HW and raw.dtype == np.uint16, "depth shape/dtype")
    check(np.array_equal(valid, raw != 0), "invalid depth rule is raw==0")
    check(np.allclose(z_m[valid], raw[valid].astype(np.float64) / 1000.0), "mm to metre scale")
    check(np.isfinite(c2w).all() and np.allclose(c2w[3], [0, 0, 0, 1]), "C2W homogeneous row")
    check(np.allclose(k, EXPECTED_K, rtol=0, atol=1e-8), "frozen K")

    # Projection round trip uses the source-backed half-pixel convention.
    sample = valid & (raw > 0)
    yy, xx = np.where(sample)
    # Deterministic spread across the valid image; no score-based selection.
    take = np.linspace(0, len(xx) - 1, num=min(128, len(xx)), dtype=np.int64)
    xyz = unproject(z_m, k, 0.5)
    pts = xyz[yy[take], xx[take]]
    uv = project(pts, k, 0.5)
    expected_uv = np.stack([xx[take], yy[take]], axis=-1).astype(np.float64)
    check(np.max(np.abs(uv - expected_uv)) < 1e-10, "projection round trip")

    rgb576, k576, geometry = preprocess_rgb(rgb, k)
    check(rgb576.shape == (3, *OUTPUT_HW) and rgb576.dtype == np.float32, "VMem RGB tensor shape")
    check(float(rgb576.min()) >= -1.00001 and float(rgb576.max()) <= 1.00001, "RGB [-1,1] range")
    check(geometry["resized_hw"] == [576, 768], "VMem resize geometry")
    check(geometry["crop_left_top"] == [96, 0], "VMem centre crop geometry")
    expected_k576 = np.array([[648.0254784, 0, 288], [0, 648.0254784, 288], [0, 0, 1]], dtype=np.float64)
    check(np.allclose(k576, expected_k576, rtol=0, atol=1e-7), "K576 scale/crop")
    vmem_pose = optical_c2w_to_vmem_input(c2w)
    check(np.allclose(vmem_pose, c2w @ np.diag([1, -1, -1, 1])), "VMem pose conversion")

    # Role and traversal guards must fail closed.
    try:
        read_bound(STAGE, "seq-01/frame-000000.depth.png", FILES, "future_depth")
    except PermissionError:
        denied_role = True
    else:
        denied_role = False
    try:
        read_bound(STAGE, "seq-01/../seq-01/frame-000000.color.png", FILES, "exposed_qualification_rgb")
    except ValueError:
        denied_traversal = True
    else:
        denied_traversal = False
    check(denied_role and denied_traversal, "fail-closed role/path guards")

    output = {
        "schema": "gwm-3dmatch-scene13-adapter-qualification-v1",
        "status": "PASS_QUALIFICATION_ONLY",
        "scope": "only scene13 seq-01 frame-000000 plus camera-intrinsics.txt; no future/outcome/model",
        "dataset_id": MANIFEST["dataset_id"],
        "scene_id": MANIFEST["scene_id"],
        "frame_id": 0,
        "source_contract": {
            "rgb": "24-bit RGB PNG, 640x480",
            "depth": "16-bit greyscale PNG, raw millimetres; invalid raw==0; z_m=raw/1000",
            "pose": "4x4 camera-to-world, metres; RGB-D Mapping estimate",
            "K": k.tolist(),
            "pixel_center": 0.5,
            "distortion": "none documented in converted scene source; no undistortion applied"
        },
        "observed_frame0": {
            "rgb_sha256": FILES["seq-01/frame-000000.color.png"]["sha256"],
            "depth_sha256": FILES["seq-01/frame-000000.depth.png"]["sha256"],
            "pose_sha256": FILES["seq-01/frame-000000.pose.txt"]["sha256"],
            "depth_zero_count": int((raw == 0).sum()),
            "depth_positive_count": int(valid.sum()),
            "depth_raw_min_positive": int(raw[valid].min()),
            "depth_raw_max": int(raw.max()),
            "pose_translation_m": c2w[:3, 3].tolist()
        },
        "preprocessing": {**geometry, "K576": k576.tolist(), "normalization": "rgb/255 then 2*x-1"},
        "checks": {
            "native_shapes_and_dtypes": True,
            "depth_unit_and_invalid_rule": True,
            "projection_round_trip_max_abs_px": float(np.max(np.abs(uv - expected_uv))),
            "K576_scale_crop": True,
            "vmem_pose_conversion": True,
            "denied_future_role": denied_role,
            "denied_path_traversal": denied_traversal
        },
        "limitations": [
            "scene13 frame000000 is previously exposed qualification evidence only",
            "frame order is not a hardware timestamp",
            "pose is an RGB-D Mapping estimate, not motion-capture ground truth",
            "half-pixel convention is a declared development compatibility choice",
            "this does not qualify the full scene, held-out windows, VMem inference, or any method"
        ],
        "formal_experiment_eligibility": "NOT_GRANTED",
        "new_method_validated": False,
        "novelty_authorization": "NONE"
    }
    (ROOT / "QUALIFICATION_RESULT.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
