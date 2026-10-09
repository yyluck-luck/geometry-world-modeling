# R72 typed-H2 template correction for R70

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only addendum. No provenance is fabricated and no synthetic fixture, real C8 data, replay, GPU/Slurm job, receipt, or validation flag is executed or changed.

## Purpose and preserved gates

This addendum applies R71 to `CODEX_R70_R66_R68_CANONICAL_H2_PACKET_CORRECTION_20260924.md`. It preserves the complete R70 manifest chain, `OWNER_ACCEPTED` scope, H2 precedence, source/boundary identity review, synthetic-only CPU entry conditions, and all no-go boundaries. The only change is to make executable H2 fields unambiguously typed and measured.

## 1. Typed executable H2 template

Use this as the only executable H2 object shape. Angle-bracket text is a documentation marker and must be replaced before execution; it is never a valid field value.

```json
{
  "h2_provenance": {
    "frame_label": "<actual optical_cv or vmem_gl>",
    "pose_name": "T_c2w",
    "pose_direction": "camera_to_world",
    "pose_convention": "homogeneous_4x4_OpenCV_x_right_y_down_z_forward",
    "source_manifest_sha256": "<actual lowercase 64-hex hash>",
    "boundary_artifact_sha256": "<actual lowercase 64-hex hash>",
    "identity_formula": "inv(T_c2w) @ X_world == p_frame",
    "forward_formula": "X_world_recomputed = T_c2w @ p_frame",
    "inverse_formula": "p_frame_recomputed = inv(T_c2w) @ X_world",
    "max_abs_error": 0.0,
    "error_threshold": 0.000001,
    "status": "PASS"
  }
}
```

`max_abs_error: 0.0` is a numeric type exemplar only. Before phase-2 H2 PASS, replace it with the measured finite value `max(err_forward, err_inverse)` from the immutable boundary artifact. No executable H2 field may contain descriptive strings such as `actual finite numeric measurement`, `finite number <= 1e-6`, or `max(err_forward, err_inverse) <= 1e-6`.

## 2. Required type and marker checks

Before accepting H2, enforce all of these checks:

* `frame_label` is exactly `optical_cv` or `vmem_gl` and is a string;
* `pose_name` is exactly `T_c2w` and `pose_direction` exactly `camera_to_world` for the canonical variant;
* `pose_convention`, `identity_formula`, `forward_formula`, and `inverse_formula` are exact strings from R70;
* `source_manifest_sha256` and `boundary_artifact_sha256` match `^[0-9a-f]{64}$` and are independently recomputed from the recorded artifacts;
* `max_abs_error` is a finite JSON number, not a string or Boolean;
* `error_threshold` is the finite JSON number `0.000001`;
* `max_abs_error == max(err_forward, err_inverse)` within the declared numeric serialization, and `max_abs_error <= error_threshold`;
* `status` is exactly `PASS`.

Reject the H2 packet as `H2_UNIDENTIFIABLE` if any executable H2 string contains an angle-bracket marker, `COMPUTED_*`, `REQUIRED`, `SEE_SECTION`, `AS_R50`, `PLACEHOLDER`, `TODO`, or a descriptive measurement expression. The same rejection applies to non-hex hash text, uppercase hash text, missing fields, non-finite numbers, or a stale measured error.

## 3. Measured replacement and bidirectional evidence

The reviewer must replace the numeric exemplar with measured evidence generated from the exact `T_c2w` and vectors in the boundary artifact:

```text
X_world_recomputed = T_c2w @ [p_frame; 1]
p_frame_recomputed = inv(T_c2w) @ [X_world; 1]
err_forward = max(abs(X_world_recomputed - [X_world; 1]))
err_inverse = max(abs(p_frame_recomputed - [p_frame; 1]))
max_abs_error = max(err_forward, err_inverse)
```

Record the two raw vectors, component-wise errors, numeric maximum, threshold, source/boundary hashes, reviewer decision, and tool/runtime. A helper-function result without the producer pointmap-frame declaration is insufficient. Do not round a failing error down to the threshold.

An explicitly world-to-camera artifact must use the separately named `T_w2c` variant and its own formulas from R70; it cannot satisfy the canonical `T_c2w` packet by relabeling a matrix.

## 4. Owner and phase ordering retained

The R70 owner gate remains:

```text
accepted_manifest = R70_R66_R68_CANONICAL_H2_PACKET_CORRECTION
```

or the complete ordered R52→R62→R64→R68→R70 chain. The R64/R70 phase sequence remains:

```text
phase_0_static_preflight -> phase_1_materialize -> phase_2_H2_gate
  -> phase_3_hash_verification -> phase_4_arm_score
```

The H2 type/marker checks occur in phase 2 after owner acceptance and computed materialization but before any H2-dependent hash extraction or arm score. Missing or invalid owner acceptance remains `OWNER_REVIEW_REQUIRED`; invalid H2 remains `H2_UNIDENTIFIABLE`.

## 5. Synthetic CPU entry update

The first CPU-only run may be considered only when:

1. owner gate is `OWNER_ACCEPTED` with the R70 manifest ID/chain;
2. every executable H2 field passes the exact type/marker/formula checks above;
3. `max_abs_error` is the measured numeric bidirectional error and is at most `1e-6`;
4. source/boundary hashes and reviewer evidence match;
5. computed visibility, arm mapping, and all supplied-hash checks pass;
6. the run is deterministic, synthetic-only, CPU-only, and immutable.

No real C8 target RGB/depth, future camera answer, learned weight, replay, GPU/Slurm job, receipt edit, or validation-flag change is authorized by this template.

## Decision

**R72 status: TYPED-H2 TEMPLATE CORRECTION COMPLETE / DESIGN-ONLY.** Executable H2 fields now have numeric error/threshold types, measured replacement rules, exact marker/hash rejection, and no descriptive measurement strings. Owner acceptance and independent H2 evidence remain required before any fixture execution.
