#!/usr/bin/env python3
"""Independent C1 numeric kernel with a synthetic-only entry point.

This source does not import the primary C1 kernel.  It remains identity-unbound
and cannot read a score report or any C1 payload in its current form.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math


ROW = "C1"
SHAPE = (576, 576, 3)
REGIONS = (
    ("R1", (0, 192, 0, 192)),
    ("R2", (0, 192, 384, 576)),
    ("R3", (192, 384, 0, 192)),
    ("R4", (192, 384, 384, 576)),
)
PAIRS = ((1, 7), (2, 6), (3, 5))
PIXEL_COUNT = 147456
RGB_SCALAR_COUNT = 442368
FULL_PIXELS = 576 * 576
FULL_SCALARS = 576 * 576 * 3
THRESHOLD = 0.01


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def record(value: float, pixels: int, scalars: int) -> dict:
    require(math.isfinite(value) and value >= 0.0, "Invalid independent MSE")
    psnr = None if value == 0.0 else -10.0 * math.log10(value)
    return {
        "mse_float64": value,
        "mse_float64_hex": value.hex(),
        "psnr_db_float64": psnr,
        "psnr_db_display_when_zero": "+inf" if value == 0.0 else None,
        "pixels": pixels,
        "rgb_scalars": scalars,
    }


def outer4_independent(left, right, np):
    sum_of_squares = np.float64(0.0)
    number_of_scalars = 0
    regions = {}
    for name, bounds in REGIONS:
        y0, y1, x0, x1 = bounds
        x = left[y0:y1, x0:x1].astype(np.float64, copy=True)
        y = right[y0:y1, x0:x1].astype(np.float64, copy=True)
        x /= np.float64(255.0)
        y /= np.float64(255.0)
        delta = np.subtract(y, x, dtype=np.float64)
        local_sum = np.sum(np.multiply(delta, delta, dtype=np.float64), dtype=np.float64)
        count = int(delta.size)
        regions[name] = record(float(local_sum) / count, (y1 - y0) * (x1 - x0), count)
        sum_of_squares += local_sum
        number_of_scalars += count
    require(number_of_scalars == RGB_SCALAR_COUNT, "Independent M_outer4 count differs")
    return float(sum_of_squares) / number_of_scalars, regions


def recompute_frames(frames, np) -> dict:
    require(type(frames) in (list, tuple) and len(frames) == 9, "Independent IDs 0-8 required")
    bodies = []
    for frame_id, frame in enumerate(frames):
        require(type(frame) is np.ndarray and frame.dtype == np.uint8
                and frame.shape == SHAPE and frame.flags.c_contiguous,
                "Independent ID%d identity differs" % frame_id)
        bodies.append(hashlib.sha256(memoryview(frame).cast("B")).hexdigest())
    require(
        not (all(value == bodies[0] for value in bodies[1:]) or len(set(bodies[1:])) == 1),
        "Independent copy guard failed",
    )
    primary_mse, regions = outer4_independent(frames[0], frames[8], np)
    left = frames[0].astype(np.float64, copy=True)
    right = frames[8].astype(np.float64, copy=True)
    left /= np.float64(255.0)
    right /= np.float64(255.0)
    delta = np.subtract(right, left, dtype=np.float64)
    full_sum = np.sum(np.multiply(delta, delta, dtype=np.float64), dtype=np.float64)
    require(int(delta.size) == FULL_SCALARS, "Independent full-frame count differs")
    pairs = {}
    for first, second in PAIRS:
        value, _ = outer4_independent(frames[first], frames[second], np)
        pairs["%d_%d" % (first, second)] = record(value, PIXEL_COUNT, RGB_SCALAR_COUNT)
    event = primary_mse > THRESHOLD
    return {
        "schema": "s46-c1-independent-recompute-math-candidate-v1",
        "row": ROW,
        "primary": record(primary_mse, PIXEL_COUNT, RGB_SCALAR_COUNT),
        "per_region_diagnostic": regions,
        "full_frame_diagnostic": record(float(full_sum) / int(delta.size), FULL_PIXELS, FULL_SCALARS),
        "generated_only_pair_diagnostic_no_GT": pairs,
        "event_MSE_gt_0_01": event,
        "equality_is_not_event": primary_mse == THRESHOLD,
        "row_status": (
            "C1_TECHNICALLY_VALID_SEVERE_DISCREPANCY_EVENT"
            if event else "C1_TECHNICALLY_VALID_NO_SEVERE_DISCREPANCY_EVENT"
        ),
        "images_viewed_or_emitted": 0,
    }


def synthetic_self_test() -> dict:
    import numpy as np

    require(np.__version__ == "1.26.4", "Synthetic check requires NumPy 1.26.4")
    frames = [np.full(SHAPE, frame_id, dtype=np.uint8) for frame_id in range(9)]
    frames[8] = np.full(SHAPE, 255, dtype=np.uint8)
    result = recompute_frames(frames, np)
    require(result["primary"]["mse_float64_hex"] == float(1.0).hex(),
            "Independent synthetic primary MSE must equal one")
    require(result["event_MSE_gt_0_01"] is True and (THRESHOLD > THRESHOLD) is False,
            "Independent strict event boundary differs")
    return {
        "status": "PASS_SYNTHETIC_INDEPENDENT_MATH_ONLY",
        "row": ROW,
        "primary_mse_hex": result["primary"]["mse_float64_hex"],
        "strict_event": result["event_MSE_gt_0_01"],
        "c1_payload_or_pixel_access": 0,
        "primary_scorer_imports": 0,
        "model_readback_or_formal_score_calls": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic-self-test", action="store_true")
    args = parser.parse_args()
    require(
        args.synthetic_self_test,
        "NON_EXECUTABLE_RECOMPUTE_CANDIDATE: wait for a sealed primary C1 report, "
        "bind its identities, and obtain a different-author source review",
    )
    print(json.dumps(synthetic_self_test(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
