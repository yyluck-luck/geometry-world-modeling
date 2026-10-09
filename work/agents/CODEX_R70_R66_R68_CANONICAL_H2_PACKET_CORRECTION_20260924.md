# R70 canonical H2 packet correction for R66/R68

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only addendum. No provenance is fabricated and no synthetic fixture, real C8 data, replay, GPU/Slurm job, receipt, or validation flag is executed or changed.

## Purpose and precedence

This addendum applies R69 to `CODEX_R66_H2_OWNER_READINESS_CHECKLIST_20260924.md` and `CODEX_R68_R66_H2_TRANSFORM_DIRECTION_CORRECTION_20260924.md`. It defines one canonical H2 packet for owner review and marks all earlier R66 `T_frame` formulas and inverse-direction instructions superseded. R70 does not expand authorization beyond synthetic CPU conformance.

The accepted manifest chain is explicit:

```text
R52_CGLR_CPU_PROTOCOL_20260924
 -> R62_R60_TWO_PHASE_OWNER_GATE_CORRECTION
 -> R64_R62_H2_PRECEDENCE_CORRECTION
 -> R68_R66_H2_TRANSFORM_DIRECTION_CORRECTION
 -> R70_R66_R68_CANONICAL_H2_PACKET_CORRECTION
```

An owner artifact may use the exact latest ID `R70_R66_R68_CANONICAL_H2_PACKET_CORRECTION` or list this complete ordered chain. An artifact naming only R64 or an earlier packet is stale and returns `OWNER_REVIEW_REQUIRED`.

## 1. One canonical `h2_provenance` schema

The owner/reviewer packet must contain exactly this pose convention and field set:

```json
{
  "h2_provenance": {
    "frame_label": "optical_cv" or "vmem_gl",
    "pose_name": "T_c2w",
    "pose_direction": "camera_to_world",
    "pose_convention": "homogeneous_4x4_OpenCV_x_right_y_down_z_forward",
    "source_manifest_sha256": "actual 64-character lowercase SHA-256",
    "boundary_artifact_sha256": "actual 64-character lowercase SHA-256",
    "identity_formula": "inv(T_c2w) @ X_world == p_frame",
    "forward_formula": "X_world_recomputed = T_c2w @ p_frame",
    "inverse_formula": "p_frame_recomputed = inv(T_c2w) @ X_world",
    "max_abs_error": "actual finite numeric measurement",
    "error_threshold": 0.000001,
    "status": "PASS"
  }
}
```

`max_abs_error` is a numeric value, not an expression or prose string. It must equal the recorded `max(err_forward, err_inverse)` and satisfy `max_abs_error <= error_threshold`. The source and boundary hashes must be exact lowercase hexadecimal strings. No field may contain `REQUIRED`, `SEE_SECTION`, `AS_R50`, `COMPUTED_*`, `PLACEHOLDER`, or any other marker.

## 2. Required bidirectional boundary evidence

The immutable boundary artifact records the exact `T_c2w`, camera-frame point `p_frame`, world point `X_world`, units, source frame declaration, and operation direction. The independent reviewer computes homogeneous four-vectors:

```text
X_world_recomputed = T_c2w @ [p_frame; 1]
p_frame_recomputed = inv(T_c2w) @ [X_world; 1]
err_forward = max(abs(X_world_recomputed - [X_world; 1]))
err_inverse = max(abs(p_frame_recomputed - [p_frame; 1]))
max_abs_error = max(err_forward, err_inverse)
```

The review artifact stores both recomputed vectors, component-wise error rows, the measured numeric maximum, and the PASS/FAIL decision. A helper-function algebra check without the producer pointmap-frame declaration remains insufficient.

An explicitly world-to-camera producer is a separate variant only when all fields are renamed and labeled:

```json
{
  "pose_name": "T_w2c",
  "pose_direction": "world_to_camera",
  "identity_formula": "T_w2c @ X_world == p_frame",
  "forward_formula": "p_frame_recomputed = T_w2c @ X_world",
  "inverse_formula": "X_world_recomputed = inv(T_w2c) @ p_frame"
}
```

The packet must never mix the `T_c2w` and `T_w2c` variants. Missing/conflicting labels or formulas return `H2_UNIDENTIFIABLE`.

## 3. Superseded R66 fields and formulas

The following R66 text is superseded and must not be copied into an executable packet:

* `identity_formula = inv(T_frame) @ X == p_frame`;
* `X_world_recomputed = inv(T_frame) @ p_frame`;
* any H2 object lacking `pose_name`, `pose_direction`, `pose_convention`, `forward_formula`, `inverse_formula`, or numeric `error_threshold`;
* any `max_abs_error` string such as `"actual finite value <= 1e-6"` or `"max(err_forward, err_inverse) <= 1e-6"`;
* any owner packet accepted only as `R64_R62_H2_PRECEDENCE_CORRECTION`.

The exact R70 schema above is the only valid H2 packet for readiness and phase-2 gating.

## 4. Updated owner gate

The owner acceptance object must use the latest protocol/manifest and retain synthetic-only scope:

```json
{
  "owner_gate": {
    "status": "OWNER_ACCEPTED",
    "review_artifact_sha256": "actual 64-character lowercase SHA-256",
    "accepted_protocol": "R62_R60_TWO_PHASE_OWNER_GATE_CORRECTION",
    "accepted_manifest": "R70_R66_R68_CANONICAL_H2_PACKET_CORRECTION",
    "accepted_manifest_chain": [
      "R52_CGLR_CPU_PROTOCOL_20260924",
      "R62_R60_TWO_PHASE_OWNER_GATE_CORRECTION",
      "R64_R62_H2_PRECEDENCE_CORRECTION",
      "R68_R66_H2_TRANSFORM_DIRECTION_CORRECTION",
      "R70_R66_R68_CANONICAL_H2_PACKET_CORRECTION"
    ],
    "decision_scope": "synthetic_cpu_conformance_only",
    "decision_time_utc": "actual ISO-8601 timestamp",
    "reviewer_role": "actual independent reviewer identity or approved institutional role"
  }
}
```

No owner value, reviewer identity, timestamp, or hash is fabricated in this design file. Missing/stale authorization returns `OWNER_REVIEW_REQUIRED` before materialization or H2 scoring.

## 5. Updated CPU entry conditions

Before a synthetic CPU conformance run, require all of the following:

1. `owner_gate.status=OWNER_ACCEPTED`, latest R70 manifest ID/chain, and recomputed review hash;
2. canonical H2 fields `pose_name=T_c2w`, `pose_direction=camera_to_world`, `pose_convention`, exact formulas, numeric `max_abs_error`, `error_threshold=1e-6`, valid source/boundary hashes, and `status=PASS`;
3. boundary artifact forward and inverse errors independently recomputed from homogeneous vectors with `max(err_forward,err_inverse) <= 1e-6`;
4. no R66 superseded formula or marker remains in the packet or extracted H2 hash subject;
5. phase-0/phase-1 preflight and computed-only visibility/hash checks pass;
6. all ten arm IDs/rules/typed parameters and supplied-hash equality checks pass;
7. the run is deterministic, synthetic-only, CPU-only, and immutable with no real C8 or target-sensor input.

Any failure stops before arm score. H2 absence, marker, direction conflict, malformed formula, non-numeric error, or error above threshold is `H2_UNIDENTIFIABLE`; stale owner authorization is `OWNER_REVIEW_REQUIRED`; other schema/hash failures are `REJECT_FIXTURE`.

## Decision and blocks

**R70 status: CANONICAL H2 PACKET COMPLETE / DESIGN-ONLY.** R66/R68 now share one explicit `T_c2w` packet, numeric bidirectional error field, latest owner manifest chain, and updated CPU entry gate. No real C8, replay, GPU/Slurm, receipt, or validation-flag action is authorized or performed.
