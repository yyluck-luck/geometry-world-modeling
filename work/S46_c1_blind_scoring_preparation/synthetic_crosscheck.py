#!/usr/bin/env python3
"""Cross-check the two independent C1 math candidates on synthetic arrays only."""
from __future__ import annotations

import json

import numpy as np

import recompute_c1_independent_candidate as independent
import score_c1_blind_candidate as primary


def main() -> int:
    if np.__version__ != "1.26.4":
        raise RuntimeError("Synthetic cross-check requires NumPy 1.26.4")
    frames = []
    yy, xx = np.indices((576, 576), dtype=np.uint16)
    for frame_id in range(9):
        frame = np.empty((576, 576, 3), dtype=np.uint8)
        frame[..., 0] = ((xx + frame_id * 7) % 256).astype(np.uint8)
        frame[..., 1] = ((yy + frame_id * 11) % 256).astype(np.uint8)
        frame[..., 2] = ((xx + yy + frame_id * 13) % 256).astype(np.uint8)
        frames.append(frame)
    left = primary.score_frames(frames, np)
    right = independent.recompute_frames(frames, np)
    fields = (
        "primary",
        "per_region_diagnostic",
        "full_frame_diagnostic",
        "generated_only_pair_diagnostic_no_GT",
        "event_MSE_gt_0_01",
        "equality_is_not_event",
        "row_status",
    )
    mismatches = [field for field in fields if left[field] != right[field]]
    if mismatches:
        raise RuntimeError("Synthetic candidate disagreement: " + repr(mismatches))
    print(json.dumps({
        "status": "PASS_SYNTHETIC_CROSS_IMPLEMENTATION_EXACT_AGREEMENT",
        "checked_fields": list(fields),
        "row": "C1",
        "c1_payload_or_pixel_access": 0,
        "images_viewed": 0,
        "model_readback_or_formal_score_calls": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
