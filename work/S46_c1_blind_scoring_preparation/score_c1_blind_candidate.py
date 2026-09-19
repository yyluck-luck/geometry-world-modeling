#!/usr/bin/env python3
"""C1 blind-score mathematical candidate with a synthetic-only entry point.

This file freezes the row, mask, pairs, arithmetic, counts, and strict event.
It deliberately contains no C1 archive/readback path and cannot formally score
anything.  A later reviewed execution wrapper may bind terminal identities to
this unchanged kernel through the identity-only contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math


ROW = "C1"
SHAPE = (576, 576, 3)
PRIMARY_PAIR = (0, 8)
REGIONS = (
    ("R1", (0, 192, 0, 192)),
    ("R2", (0, 192, 384, 576)),
    ("R3", (192, 384, 0, 192)),
    ("R4", (192, 384, 384, 576)),
)
DIAGNOSTIC_PAIRS = ((1, 7), (2, 6), (3, 5))
PIXEL_COUNT = 147456
RGB_SCALAR_COUNT = 442368
FULL_FRAME_PIXEL_COUNT = 576 * 576
FULL_FRAME_RGB_SCALAR_COUNT = 576 * 576 * 3
MSE_THRESHOLD = 0.01
FROZEN_MATH_SHA256 = "9bee0abe9392e04e061adb7cf8b39297d7730e7045ed856486f1e03ee8d82812"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def metric_record(mse: float, pixels: int, scalars: int) -> dict:
    require(math.isfinite(mse) and mse >= 0.0, "MSE must be finite and nonnegative")
    return {
        "mse_float64": mse,
        "mse_float64_hex": mse.hex(),
        "psnr_db_float64": None if mse == 0.0 else -10.0 * math.log10(mse),
        "psnr_db_display_when_zero": "+inf" if mse == 0.0 else None,
        "pixels": pixels,
        "rgb_scalars": scalars,
    }


def mse_outer4(first, second, np):
    total = 0.0
    scalar_count = 0
    per_region = {}
    for name, (y0, y1, x0, x1) in REGIONS:
        left = np.asarray(first[y0:y1, x0:x1], dtype=np.float64) / 255.0
        right = np.asarray(second[y0:y1, x0:x1], dtype=np.float64) / 255.0
        squared_sum = float(np.sum(np.square(right - left), dtype=np.float64))
        count = int(left.size)
        per_region[name] = metric_record(
            squared_sum / count, (y1 - y0) * (x1 - x0), count
        )
        total += squared_sum
        scalar_count += count
    require(scalar_count == RGB_SCALAR_COUNT, "M_outer4 scalar count differs")
    return total / scalar_count, per_region


def score_frames(frames, np) -> dict:
    require(type(frames) in (list, tuple) and len(frames) == 9, "IDs 0-8 are required")
    checked = []
    body_hashes = []
    for frame_id, frame in enumerate(frames):
        require(
            type(frame) is np.ndarray and frame.dtype == np.uint8 and frame.shape == SHAPE,
            "ID%d must be exact uint8[576,576,3]" % frame_id,
        )
        require(frame.flags.c_contiguous, "ID%d must be C-contiguous" % frame_id)
        checked.append(frame)
        body_hashes.append(hashlib.sha256(memoryview(frame).cast("B")).hexdigest())
    copy_degenerate = (
        all(value == body_hashes[0] for value in body_hashes[1:])
        or len(set(body_hashes[1:])) == 1
    )
    require(not copy_degenerate, "DEGENERATE_COPY/CAMERA_CONTROL_UNRESOLVED")

    primary_mse, per_region = mse_outer4(
        checked[PRIMARY_PAIR[0]], checked[PRIMARY_PAIR[1]], np
    )
    full_delta = (
        np.asarray(checked[8], dtype=np.float64) / 255.0
        - np.asarray(checked[0], dtype=np.float64) / 255.0
    )
    require(int(full_delta.size) == FULL_FRAME_RGB_SCALAR_COUNT,
            "Full-frame scalar count differs")
    full_mse = float(np.sum(np.square(full_delta), dtype=np.float64)) / int(full_delta.size)
    pair_records = {}
    for left, right in DIAGNOSTIC_PAIRS:
        mse, _ = mse_outer4(checked[left], checked[right], np)
        pair_records["%d_%d" % (left, right)] = metric_record(
            mse, PIXEL_COUNT, RGB_SCALAR_COUNT
        )
    event = primary_mse > MSE_THRESHOLD
    return {
        "schema": "s46-c1-blind-score-math-candidate-v1",
        "row": ROW,
        "primary_pair": list(PRIMARY_PAIR),
        "primary": metric_record(primary_mse, PIXEL_COUNT, RGB_SCALAR_COUNT),
        "event_MSE_gt_0_01": event,
        "equality_is_not_event": primary_mse == MSE_THRESHOLD,
        "per_region_diagnostic": per_region,
        "full_frame_diagnostic": metric_record(
            full_mse, FULL_FRAME_PIXEL_COUNT, FULL_FRAME_RGB_SCALAR_COUNT
        ),
        "generated_only_pair_diagnostic_no_GT": pair_records,
        "row_status": (
            "C1_TECHNICALLY_VALID_SEVERE_DISCREPANCY_EVENT"
            if event else "C1_TECHNICALLY_VALID_NO_SEVERE_DISCREPANCY_EVENT"
        ),
        "cohort_status": "INCOMPLETE_C2_STILL_REQUIRED",
        "images_opened_or_emitted": 0,
    }


def synthetic_self_test() -> dict:
    import numpy as np

    require(np.__version__ == "1.26.4", "Synthetic check requires NumPy 1.26.4")
    frames = []
    for frame_id in range(9):
        value = np.full(SHAPE, frame_id, dtype=np.uint8)
        frames.append(value)
    frames[8] = np.full(SHAPE, 255, dtype=np.uint8)
    result = score_frames(frames, np)
    require(result["primary"]["mse_float64_hex"] == float(1.0).hex(),
            "Synthetic all-channel primary MSE must equal one")
    require(result["event_MSE_gt_0_01"] is True, "Synthetic strict event must be true")
    require((MSE_THRESHOLD > MSE_THRESHOLD) is False,
            "Strict equality boundary must not be an event")
    require(result["primary"]["pixels"] == PIXEL_COUNT
            and result["primary"]["rgb_scalars"] == RGB_SCALAR_COUNT,
            "Synthetic primary counts differ")
    return {
        "status": "PASS_SYNTHETIC_PRIMARY_MATH_ONLY",
        "row": ROW,
        "frozen_math_sha256": FROZEN_MATH_SHA256,
        "primary_mse_hex": result["primary"]["mse_float64_hex"],
        "strict_event": result["event_MSE_gt_0_01"],
        "c1_payload_or_pixel_access": 0,
        "model_readback_or_formal_score_calls": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic-self-test", action="store_true")
    args = parser.parse_args()
    require(
        args.synthetic_self_test,
        "NON_EXECUTABLE_CANDIDATE: bind terminal identities, obtain two source reviews, "
        "create the pre-score blindness attestation, and add a reviewed execution wrapper",
    )
    print(json.dumps(synthetic_self_test(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
