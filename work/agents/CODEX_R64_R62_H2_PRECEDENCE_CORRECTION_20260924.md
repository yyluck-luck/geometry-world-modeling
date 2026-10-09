# R64 H2 precedence correction for R62

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only addendum. No fixture execution, real C8 data, replay, GPU/Slurm submission, receipt mutation, or validation-flag change.

## Purpose and preserved gates

This addendum applies R63 to `CODEX_R62_R60_TWO_PHASE_OWNER_GATE_CORRECTION_20260924.md`. It preserves the hard `OWNER_ACCEPTED` gate, computed-only visibility, complete arm mapping, raw-versus-supplied hash verification, `PASS_CONTRACT_REPLAY`, and all existing no-go boundaries.

The only change is H2 classification and ordering:

```text
phase_0_static_preflight -> phase_1_materialize -> phase_2_H2_gate
  -> phase_3_hash_verification -> phase_4_arm_score
```

Phase 0 never classifies H2 provenance through the generic marker/type rejection. Phase 2 owns every H2 presence, marker, format, and identity decision and returns `H2_UNIDENTIFIABLE` before any H2-dependent hash extraction or arm score.

## 1. Phase 0 exclusion

The recursive marker/type scan in phase 0 must scan all supplied non-H2 fields, owner gate, static geometry, state, events, and arm objects, but it must exclude this exact subtree:

```text
#/h2_provenance/*
```

The exclusion applies only to classification. Phase 0 still verifies the owner gate:

```json
{
  "owner_gate": {
    "status": "OWNER_ACCEPTED",
    "review_artifact_sha256": "64 lowercase hexadecimal characters",
    "accepted_protocol": "R62_R60_TWO_PHASE_OWNER_GATE_CORRECTION"
  }
}
```

Missing or invalid owner acceptance remains `OWNER_REVIEW_REQUIRED` (or `REJECT_FIXTURE(reason=OWNER_REVIEW_REQUIRED)`) before materialization. H2 fields are not used by phase 0 to emit `REJECT_FIXTURE`.

## 2. Phase 1 materialization

After phase 0 passes, materialize `state_pre_cells`, `event_instance`, threshold/budget, world-point projections, and all `computed.*` visibility records. Scan the newly materialized computed fields for non-H2 forbidden markers and type errors. Expected visibility declarations cannot substitute for computed masks. Any non-H2 marker, missing computed field, wrong type, or duplicate cell remains `REJECT_FIXTURE` before phase 2.

## 3. Phase 2 H2 gate

Phase 2 must run before extracting `fixture_context_paths`, before calculating `fixture_context_sha256`, before any base/rule/arm hash, and before every arm score. Evaluate the H2 object as a single provenance contract:

```json
{
  "frame_label": "optical_cv" or "vmem_gl",
  "source_manifest_sha256": "64 lowercase hexadecimal characters",
  "boundary_artifact_sha256": "64 lowercase hexadecimal characters",
  "identity_formula": "inv(T_frame) @ X == p_frame",
  "max_abs_error": "finite number <= 1e-6",
  "status": "PASS"
}
```

Return `H2_UNIDENTIFIABLE` for any of the following, without attempting a hash or arm transition:

* `#/h2_provenance` is missing, null, or not an object;
* any required H2 field is absent or contains a forbidden marker (`REQUIRED`, `SEE_SECTION`, `AS_R50`, `PLACEHOLDER`, `TODO`, or any `COMPUTED_*` marker);
* `frame_label` is not exactly `optical_cv` or `vmem_gl`;
* either H2 SHA-256 field is missing, non-hex, or not exactly 64 lowercase hexadecimal characters;
* `identity_formula` does not equal the declared formula;
* `max_abs_error` is non-finite, missing, or greater than `1e-6`;
* `status` is not exactly `PASS`.

H2 marker/type failures are deliberately not `REJECT_FIXTURE`; they all represent unavailable or uninterpretable provenance and share the R52 terminal `H2_UNIDENTIFIABLE`.

## 4. Phase 3 and phase 4 after H2 PASS

Only after phase 2 returns `H2_PASS` may the runner:

1. extract `fixture_context_paths`, including H2 identifiers;
2. recompute and compare the computed, manifest, context, base-input, arm-rule, and arm-input hashes;
3. report raw-versus-supplied verification rows;
4. score any of the ten mapped arms.

A missing, marker-valued, malformed, or mismatched non-H2 hash remains `REJECT_FIXTURE`. A complete strong-control tie remains `REJECT_NON_IDENTIFIABLE`; typed-arm invariant failure remains `REJECT_CONTRACT`.

## 5. Design-only status and blocks

This addendum contains no owner acceptance artifact and therefore cannot pass phase 0 in the current design workspace. No real C8 data, replay, GPU/Slurm job, receipt edit, or validation-flag change is performed or unlocked.

## Decision

**R64 status: H2 PRECEDENCE CORRECTION COMPLETE / DESIGN-ONLY.** The generic phase-0 scan now excludes `#/h2_provenance/*`; phase 2 uniformly maps missing, marker, malformed, and identity-failing H2 to `H2_UNIDENTIFIABLE` before all H2-dependent hashes and arm scores.
