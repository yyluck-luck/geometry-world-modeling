# R62 two-phase preflight, owner gate, and hash-verification correction

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only addendum. No fixture execution, real C8 data, replay, GPU/Slurm submission, receipt mutation, or validation-flag change.

## Purpose and fixed order

This addendum applies R61 to `CODEX_R60_R58_EXECUTION_PREFLIGHT_CORRECTION_20260924.md`. It preserves R52/R56 visibility precedence, computed-only scoring, H2 provenance, the access-matched arms, and `PASS_CONTRACT_REPLAY` as a synthetic conformance terminal.

The only permitted execution order is:

```text
phase_0_static_preflight -> phase_1_materialize -> phase_2_H2_gate
  -> phase_3_hash_verification -> phase_4_arm_score
```

`phase_0_static_preflight` checks owner authorization and all supplied non-computed schema. `phase_1_materialize` creates the computed envelope but does not hash or score. `phase_2_H2_gate` runs before any hash domain that requires H2 fields. `phase_3_hash_verification` recomputes every supplied hash and reports raw versus supplied values. Only `phase_4_arm_score` may execute arm transitions.

## 1. Hard owner gate

The fixture must contain this authorization object before phase 0 can pass:

```json
{
  "owner_gate": {
    "status": "OWNER_ACCEPTED",
    "review_artifact_sha256": "64 lowercase hexadecimal characters",
    "accepted_protocol": "R62_R60_TWO_PHASE_OWNER_GATE_CORRECTION"
  }
}
```

Any status other than the exact string `OWNER_ACCEPTED`, a missing or malformed review hash, or a protocol mismatch returns `OWNER_REVIEW_REQUIRED` (or `REJECT_FIXTURE(reason=OWNER_REVIEW_REQUIRED)` if the existing terminal vocabulary is enforced) before materialization, hashing, H2 scoring, or arm execution. The review hash is checked for authorization but is excluded from `base_input_sha256` and `arm_rule_sha256`.

The design artifact intentionally has no owner acceptance value. It therefore remains non-executable until the owner supplies this object and independently supplies the H2 provenance artifact.

## 2. Complete ten-arm identifier/rule mapping

Phase 0 must compare `arm_id`, `transition_rule_id`, and the exact typed parameter object against this table. Any missing, extra, mismatched, or marker-valued parameter is `REJECT_FIXTURE`.

| `arm_id` = `transition_rule_id` | Exact typed parameters |
|---|---|
| `cglr_typed` | `state_write=typed_local`; `threshold_gate=on`; `provenance_gate=predicted_only`; `correspondence_mode=event_declared`; `conservation_mode=outside_zero`; `evidence_action=append` |
| `append_only` | `state_write=none`; `threshold_gate=off`; `provenance_gate=none`; `correspondence_mode=none`; `conservation_mode=none`; `evidence_action=append` |
| `generic_global` | `state_write=global_broadcast`; `broadcast_coefficient=0.25`; `threshold_gate=off`; `provenance_gate=any`; `correspondence_mode=all_slots`; `conservation_mode=none`; `evidence_action=append` |
| `mask_only_local` | `state_write=local_fixed`; `fixed_residual=[0.4,0.0,0.1]`; `support_mode=A_C`; `threshold_gate=off`; `provenance_gate=off`; `correspondence_mode=event_declared`; `conservation_mode=outside_zero`; `evidence_action=append` |
| `residual_transport_untyped` | `state_write=transport`; `threshold_gate=on`; `provenance_gate=any`; `correspondence_mode=event_declared`; `conservation_mode=none`; `evidence_action=append` |
| `no_reveal` | `state_write=none`; `event_action=none`; `threshold_gate=none`; `provenance_gate=none`; `correspondence_mode=none`; `conservation_mode=none`; `evidence_action=none` |
| `shuffle_placebo` | `state_write=typed_local`; `threshold_gate=on`; `provenance_gate=predicted_only`; `correspondence_mode=fixed_wrong_component_A_to_U`; `conservation_mode=outside_zero`; `evidence_action=append` |
| `local_residual_no_provenance` | `state_write=local_residual`; `threshold_gate=on`; `provenance_gate=any`; `correspondence_mode=event_declared`; `conservation_mode=outside_zero`; `evidence_action=append` |
| `local_residual_no_conservation` | `state_write=local_residual`; `threshold_gate=on`; `provenance_gate=predicted_only`; `correspondence_mode=event_declared`; `conservation_mode=equal_mass_drift`; `evidence_action=append` |
| `mask_same_residual` | `state_write=local_residual`; `threshold_gate=off`; `provenance_gate=off`; `correspondence_mode=event_declared`; `conservation_mode=outside_zero`; `evidence_action=append` |

The table is a closed mapping. No arm may supply event-specific residuals, visibility, truth, post-state, or target data through its rule parameters. All arms for one event must receive one shared base input; the table is the only rule-level difference.

## 3. Phase 0: static preflight

Before any computed geometry or hash:

1. Recursively scan all supplied non-computed fields, H2 fields if present, owner gate, event table, state schema, and arm objects for the R60 forbidden markers (`COMPUTED_*`, `metadata_only`, `canonical arm name`, `canonical rule-only JSON`, `REQUIRED`, `SEE_SECTION`, `AS_R50`, `PLACEHOLDER`, and `TODO`).
2. Require `owner_gate.status=OWNER_ACCEPTED` and validate the review hash/protocol string.
3. Validate static types and uniqueness of camera, patch, cell, event, and arm identifiers.
4. Validate the ten-arm mapping above, including exact typed parameter keys and value domains.
5. Validate that `transition_rule_parameters` contains none of: event ID/value/residual, expected or computed visibility, target truth, future camera answer, target RGB/depth, post-state, post-evidence, rendered output, or post-hoc metric.

The phase-0 scan does not require computed fields or H2 to be valid yet; those are handled in phases 1 and 2. Any phase-0 failure stops with `OWNER_REVIEW_REQUIRED` or `REJECT_FIXTURE` and performs no hashing or score.

## 4. Phase 1: materialize computed state

Only after phase 0 passes, materialize the following with no hashing:

* `state_pre_cells`: exactly 64 row-major cell records with ID, patch, value, provenance;
* `event_instance`: one expanded event object with event ID, patch/value, provenance, correspondence, and allowed support;
* `threshold.tau_l2=0.25` and the fixed update-budget object;
* world-point projections and the R56 rounded-pixel/quantized-depth visibility records;
* `computed.projected_pixels`, `computed.visibility_masks`, `computed_visibility_sets`, and `computed_visibility_counts`.

After materialization, recursively scan these fields for forbidden markers and perform strict type/length/finite-value checks. Computed visibility sets/counts must be generated from computed mask records, never copied from expected declarations. A missing field, placeholder, non-finite value, duplicate cell, wrong count, or expected-mask substitution is `REJECT_FIXTURE` before H2 or hashing.

## 5. Phase 2: H2 gate before H2-dependent hashes

After phase 1 and before phase 3, require the independently reviewed H2 object:

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

If any H2 field is absent, ambiguous, malformed, or fails the error bound, return `H2_UNIDENTIFIABLE` before extracting or hashing `fixture_context_paths`, before any arm hash, and before any arm score. H2 cannot select an arm or alter the shared base input.

## 6. Phase 3: exhaustive supplied-hash verification

After phases 0–2 pass, recompute each hash from its raw subject. For every hash, persist a verification row with `hash_name`, `domain_prefix`, `raw_subject_sha256`, `supplied_hash`, and `equal`.

The complete checklist is:

| Hash name | Raw subject |
|---|---|
| `computed.projected_pixels_sha256` | canonical `computed.projected_pixels` records |
| `computed.visibility_masks_sha256` | canonical `computed.visibility_masks` records |
| `computed.computed_visibility_sets_sha256` | canonical computed visibility sets |
| `computed.computed_visibility_counts_sha256` | canonical computed visibility counts |
| `contract_manifest_sha256` | exact R58/R60 rule paths, excluding expected values |
| `fixture_context_sha256` | schema/status, H2 identifiers, manifest hash, and computed hashes |
| `base_input_sha256` | exact shared base paths, once per event and arm |
| `arm_rule_sha256` | exact arm ID-mapped rule ID and typed rule parameters, once per arm |
| `arm_input_sha256` | canonical object containing recomputed base and rule hashes |

For each row, a missing, marker-valued, wrong-format, or unequal supplied hash returns `REJECT_FIXTURE`. Supplied hash values are never used as inputs to recompute themselves. All arms for one event must have equal recomputed `base_input_sha256`; only their recomputed `arm_rule_sha256` may differ. The owner-gate review hash is not part of arm input domains.

## 7. Phase 4: arm score

Only after `OWNER_ACCEPTED`, phase-0/1 preflight, H2 PASS, and all phase-3 hash rows equal may the runner score the ten arms. Apply R52/R56 computed-only query separation, channel denominators, strong-control signature comparison, no-reveal identity, and `PASS_CONTRACT_REPLAY` rules. A strong-control complete-signature tie is `REJECT_NON_IDENTIFIABLE`; typed-arm invariant failure is `REJECT_CONTRACT`.

## 8. Scope and stop conditions

This is a design addendum only. No real C8 data, replay, GPU/Slurm job, receipt edit, or validation-flag change is performed or unlocked. Missing owner acceptance stops at `OWNER_REVIEW_REQUIRED`; H2 failure stops at `H2_UNIDENTIFIABLE`; schema/computed/hash failure stops at `REJECT_FIXTURE`.

## Decision

**R62 status: TWO-PHASE OWNER-GATE CORRECTION COMPLETE / DESIGN-ONLY.** The preflight/materialization/H2/hash/score order, hard owner gate, complete arm mapping, and exhaustive raw-versus-supplied hash verification are explicit. Owner acceptance and H2 provenance remain prerequisites for any fixture execution.
