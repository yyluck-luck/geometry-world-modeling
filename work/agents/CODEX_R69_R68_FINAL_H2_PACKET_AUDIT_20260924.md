# R69 final hostile audit of the R68 H2 packet

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only audit. No provenance is fabricated and no fixture, real C8 data, replay, GPU/Slurm job, receipt, or validation flag is executed or changed.

## Verdict

**REVISE once before accepting the packet.** R68's transform operations are correct in isolation, and R66's source/boundary evidence requirements remain useful. The combined packet still has concrete schema drift: R66 retains the old `T_frame` identity formula and does not require `pose_name`/`pose_direction`; the owner gate accepts only the older R64 manifest; and the R68 example represents `max_abs_error` as an expression string instead of a numeric measured value.

## Findings

### 1. Canonical H2 fields are not merged

R66 §2 and §4 still show:

```text
inv(T_frame) @ X == p_frame
```

R68 correctly replaces this with explicit `T_c2w` camera-to-world fields and bidirectional checks, but it does not mark every R66 occurrence as superseded. R66 §6's CPU entry condition also checks only the old identity formula and omits pose direction.

### 2. Numeric field type is ambiguous

R68's example uses:

```json
"max_abs_error": "max(err_forward, err_inverse) <= 1e-6"
```

This is a description, not a measured number. The executable H2 object must contain a finite numeric value; the threshold and formula belong in separate fields.

### 3. Owner acceptance points at a stale manifest

R66's owner artifact requires:

```text
accepted_manifest = R64_R62_H2_PRECEDENCE_CORRECTION
```

After R68 changes the H2 pose schema, an owner acceptance that names only R64 does not authorize the corrected packet. The owner gate must name R68 or a canonical chain that explicitly includes it.

### 4. Source and boundary paths otherwise agree

The three source paths, byte-hash requirement, line references, boundary artifact contents, independent reviewer evidence, and no-real-data scope are consistent. The correction below only changes the canonical H2 schema, owner manifest ID, and CPU entry fields.

## Exact packet correction

Declare one canonical H2 schema and use it in R66, R68, the owner gate, and the CPU entry checklist:

```json
{
  "h2_provenance": {
    "frame_label": "optical_cv" or "vmem_gl",
    "pose_name": "T_c2w",
    "pose_direction": "camera_to_world",
    "pose_convention": "homogeneous_4x4_OpenCV_x_right_y_down_z_forward",
    "source_manifest_sha256": "64 lowercase hex",
    "boundary_artifact_sha256": "64 lowercase hex",
    "identity_formula": "inv(T_c2w) @ X_world == p_frame",
    "forward_formula": "X_world_recomputed = T_c2w @ p_frame",
    "inverse_formula": "p_frame_recomputed = inv(T_c2w) @ X_world",
    "max_abs_error": 0.0,
    "error_threshold": 0.000001,
    "status": "PASS"
  }
}
```

At execution, `max_abs_error` is the measured finite number
`max(err_forward, err_inverse)`, not a string. The boundary artifact stores the actual vectors/matrix and both component error rows. If the producer is genuinely world-to-camera, use a separate explicit variant:

```json
{
  "pose_name": "T_w2c",
  "pose_direction": "world_to_camera",
  "identity_formula": "T_w2c @ X_world == p_frame",
  "forward_formula": "p_frame_recomputed = T_w2c @ X_world",
  "inverse_formula": "X_world_recomputed = inv(T_w2c) @ p_frame"
}
```

Never mix fields from the two variants. Any missing or conflicting pose fields return `H2_UNIDENTIFIABLE`.

Update the owner artifact to:

```text
accepted_manifest = R68_R66_H2_TRANSFORM_DIRECTION_CORRECTION
```

or to an explicit ordered manifest chain that includes R64 and R68. Update R66 §6's CPU entry condition to require `pose_name`, `pose_direction`, `pose_convention`, both formulas, numeric `max_abs_error`, and `error_threshold` in addition to the existing H2 fields.

## Stop conditions after correction

* stale old-formula packet or stale accepted manifest: `OWNER_REVIEW_REQUIRED`;
* missing/ambiguous/malformed pose or H2 identity: `H2_UNIDENTIFIABLE`;
* non-numeric error, inconsistent error rows, or hash mismatch: `REJECT_FIXTURE`;
* no fixture, real C8, replay, GPU/Slurm, receipt, or validation-flag action is unlocked.

## Decision

**R69: REVISE once.** Apply the canonical H2 packet merge, numeric error field, and R68 owner-manifest update before accepting the readiness checklist. No provenance or reviewer value was fabricated.
