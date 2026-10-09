# R68 H2 transform-direction correction for R66

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only addendum. No provenance is fabricated and no synthetic fixture, real C8 data, replay, GPU/Slurm job, receipt, or validation flag is executed or changed.

## Purpose and preserved authorization

This addendum applies R67 to `CODEX_R66_H2_OWNER_READINESS_CHECKLIST_20260924.md`. It preserves the hard `OWNER_ACCEPTED` scope, source-manifest identity checks, independent reviewer evidence, computed-only synthetic CPU boundary, and all no-go conditions. The only change is to make the H2 pose direction and identity operation unambiguous.

## 1. Canonical pose declaration

The boundary artifact must use these exact fields:

```json
{
  "pose_name": "T_c2w",
  "pose_direction": "camera_to_world",
  "pose_convention": "homogeneous_4x4_OpenCV_x_right_y_down_z_forward",
  "identity_formula": "inv(T_c2w) @ X_world == p_frame",
  "forward_check": "X_world_recomputed = T_c2w @ p_frame",
  "inverse_check": "p_frame_recomputed = inv(T_c2w) @ X_world"
}
```

All points are homogeneous 4-vectors with the final coordinate equal to one before comparison. `T_c2w` is the exact camera-to-world matrix used by the producer/boundary artifact; the name `T_frame` without a direction is not accepted.

## 2. Required bidirectional CPU checks

The independent reviewer must recompute both directions from the exact recorded matrix and vectors:

```text
X_world_recomputed = T_c2w @ [p_frame; 1]
p_frame_recomputed = inv(T_c2w) @ [X_world; 1]

err_forward = max(abs(X_world_recomputed - [X_world; 1]))
err_inverse = max(abs(p_frame_recomputed - [p_frame; 1]))
max_abs_error = max(err_forward, err_inverse)
```

The artifact passes the H2 identity check only when all operations are finite, the matrix is invertible under the recorded convention, and `max_abs_error <= 1e-6`. Record the raw matrix, both input vectors, both recomputed vectors, both component-wise error rows, and the final maximum. Do not report only a helper-function result.

The H2 object must use the same `pose_name`, `pose_direction`, identity formula, and final `max_abs_error`:

```json
{
  "h2_provenance": {
    "frame_label": "optical_cv" or "vmem_gl",
    "pose_name": "T_c2w",
    "pose_direction": "camera_to_world",
    "source_manifest_sha256": "actual 64-character lowercase SHA-256",
    "boundary_artifact_sha256": "actual 64-character lowercase SHA-256",
    "identity_formula": "inv(T_c2w) @ X_world == p_frame",
    "max_abs_error": "max(err_forward, err_inverse) <= 1e-6",
    "status": "PASS"
  }
}
```

Missing, marker-valued, malformed, ambiguous, or direction-inconsistent fields return `H2_UNIDENTIFIABLE` before any H2-dependent hash or arm score. No synthetic fixture may choose a pose direction to obtain a lower error.

## 3. Explicit alternate world-to-camera handling

An artifact may use a world-to-camera producer matrix only when it explicitly declares a distinct pose name and direction, for example:

```json
{
  "pose_name": "T_w2c",
  "pose_direction": "world_to_camera",
  "identity_formula": "T_w2c @ X_world == p_frame",
  "forward_check": "p_frame_recomputed = T_w2c @ X_world",
  "inverse_check": "X_world_recomputed = inv(T_w2c) @ p_frame"
}
```

The same bidirectional error definition applies. A matrix labeled `T_c2w` cannot use these formulas, and a matrix labeled `T_w2c` cannot use the camera-to-world formulas. Any missing or conflicting direction labels return `H2_UNIDENTIFIABLE`.

## 4. Source and reviewer requirements retained

The source manifest must still identify exact producer/boundary files, byte hashes, immutable source identifiers, retrieval time, and line references for the pose producer, pointmap frame, conversion, and inverse operation. The independent reviewer must recompute both checks from the source-identified artifact and record the PASS/FAIL rationale. No reviewer identity, timestamp, hash, or provenance value may be invented.

`OWNER_ACCEPTED` remains limited to synthetic CPU conformance. It does not authorize real C8 replay, learned-model or novelty claims, GPU/Slurm jobs, receipt edits, or validation-flag changes.

## Decision and blocks

**R68 status: TRANSFORM-DIRECTION CORRECTION COMPLETE / DESIGN-ONLY.** R66 now has an explicit `T_c2w` camera-to-world contract, bidirectional homogeneous checks, and a separately labeled world-to-camera alternative. Owner acceptance and independently reviewed H2 evidence remain required before any fixture execution.
