# R71 final hostile audit of the R70 canonical H2 packet

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only audit. No provenance is fabricated and no fixture, real C8 data, replay, GPU/Slurm job, receipt, or validation flag is executed or changed.

## Verdict

**REVISE once before final acceptance.** R70's manifest chain, transform direction, supersession statement, H2 ordering, and synthetic-only authorization are coherent. One concrete schema flaw remains: the canonical JSON example still represents `max_abs_error` as the string `"actual finite numeric measurement"`, which can be copied as a string despite the requirement that it be a measured finite number.

## Audit results

### Manifest chain: PASS

R70 consistently names the ordered chain:

```text
R52 -> R62 -> R64 -> R68 -> R70
```

The owner gate accepts the latest R70 ID or the complete chain. An R64-only or earlier packet is stale and stops at `OWNER_REVIEW_REQUIRED`.

### Transform direction and superseded formulas: PASS

The executable packet uses `pose_name=T_c2w`, `pose_direction=camera_to_world`, and the paired forward/inverse homogeneous operations. R70 explicitly marks the old R66 `T_frame` formulas superseded. The separately labeled `T_w2c` variant cannot be mixed with the `T_c2w` variant.

### H2/status precedence and scope: PASS

The R64 phase-0 H2-subtree exception and phase-2 `H2_UNIDENTIFIABLE` handling remain intact. H2 is checked before H2-dependent hashes and arm scores. `OWNER_ACCEPTED` remains limited to synthetic CPU conformance and does not authorize C8 replay, novelty, GPU/Slurm, receipts, or flags.

### Numeric error typing: REVISE

R70 states that `max_abs_error` is numeric, but its canonical schema block contains:

```json
"max_abs_error": "actual finite numeric measurement"
```

The same issue appears in the source/boundary hash fields as descriptive strings. A copied packet could pass superficial schema inspection while carrying text instead of a measured value.

## One minimal correction

Replace the R70 schema example with a typed template that cannot be mistaken for an executable value:

```json
{
  "h2_provenance": {
    "frame_label": "<actual optical_cv or vmem_gl>",
    "pose_name": "T_c2w",
    "pose_direction": "camera_to_world",
    "pose_convention": "homogeneous_4x4_OpenCV_x_right_y_down_z_forward",
    "source_manifest_sha256": "<actual lowercase hex; reject angle-bracket markers>",
    "boundary_artifact_sha256": "<actual lowercase hex; reject angle-bracket markers>",
    "identity_formula": "inv(T_c2w) @ X_world == p_frame",
    "forward_formula": "X_world_recomputed = T_c2w @ p_frame",
    "inverse_formula": "p_frame_recomputed = inv(T_c2w) @ X_world",
    "max_abs_error": 0.0,
    "error_threshold": 0.000001,
    "status": "PASS"
  }
}
```

`0.0` is a type exemplar only; execution must replace it with the measured finite `max(err_forward, err_inverse)`. Add the preflight rule `type(max_abs_error) is numeric` and reject any string, angle-bracket marker, non-finite value, or value above `error_threshold` as `H2_UNIDENTIFIABLE`. Apply the same explicit type/format checks to the two SHA-256 fields.

## Stop conditions

Until the numeric template/type rule is applied, do not accept the H2 packet. After correction:

* stale owner chain is `OWNER_REVIEW_REQUIRED`;
* missing/ambiguous/malformed H2 or non-numeric/error-bound failure is `H2_UNIDENTIFIABLE`;
* other schema/hash failures are `REJECT_FIXTURE`;
* no real C8, replay, GPU/Slurm, receipt, or validation-flag action is unlocked.

## Decision

**R71: REVISE once, then PASS-ready.** No flaw remains in the manifest chain, transform formulas, precedence, or authorization scope; make the numeric H2 field type impossible to misread before final acceptance.
