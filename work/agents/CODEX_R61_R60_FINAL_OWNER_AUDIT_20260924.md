# R61 final owner-readiness audit of R60 against the R52 contract

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only audit. No fixture execution, real C8 data, replay, GPU/Slurm submission, receipt mutation, or validation-flag change.

## Verdict

**REVISE before owner acceptance.** R60 has the right rejection intent, but its ordering is internally contradictory: the preflight requires materialized `computed.*` fields while the execution order says those fields are materialized only after preflight. R60 also lacks a complete arm-to-rule mapping, does not make supplied-hash recomputation a complete checklist, and states owner review as prose rather than a hard execution gate. These gaps could permit an implementation to skip a check or run before owner acceptance.

## Findings

### 1. Preflight ordering contradiction

R60 says:

* missing/placeholder required fields fail before canonicalization and hashing;
* computed geometry and `computed.*` are materialized only after `PASS_PREFLIGHT`.

Those statements cannot both hold because `#/computed/*` is a required field set. A placeholder is either rejected before it can be computed, or computed fields are produced before the full preflight.

### 2. H2 ordering can be blocked by hash extraction

`fixture_context_paths` include H2 source and boundary hashes. If an H2 field is absent, extracting the context domain before the H2 gate can produce `REJECT_FIXTURE` instead of the R52-required `H2_UNIDENTIFIABLE`. H2 must be checked before any hash domain that requires H2 values and before any arm score.

### 3. Arm identifier/rule mapping is incomplete

R60 requires a real `arm_id` and matching `transition_rule_id`, but it does not publish the one-to-one mapping or required parameter values. An implementation could label a `generic_global` rule as `cglr_typed`, or omit a strong-control parameter while still passing the type check.

### 4. Supplied hash recomputation needs an explicit checklist

R60 says a hash field must be recomputed, but does not enumerate every supplied value that must match. A stale `fixture_context_sha256`, `base_input_sha256`, or `arm_input_sha256` could therefore be treated as metadata unless the runner checks each one.

### 5. Owner acceptance is not a machine gate

R60 ends with “owner review ... required,” but the execution envelope has no required owner-acceptance field and no preflight failure if review is absent. The design could therefore be run by a script that honors only the type checks.

## Exact corrections

### A. Replace the single preflight with two phases

Use this order:

```text
phase_0_static_preflight:
  load schema, owner_gate, H2 object, world geometry, state, events, arms
  recursively reject forbidden markers in all supplied fields
  type-check all non-computed required fields and actual arm mapping
  if owner_gate.status != OWNER_ACCEPTED: return OWNER_REVIEW_REQUIRED

phase_1_materialize:
  compute world projections, rounded pixels, visibility predicates,
  computed_visibility_sets/counts, and all raw computed records
  materialize #/computed/* and state/event execution envelope
  recursively scan computed fields for markers and type-check them

phase_2_h2_gate:
  validate H2 frame label, source/boundary hashes, identity formula,
  and max_abs_error <= 1e-6
  if absent/ambiguous/failed: return H2_UNIDENTIFIABLE

phase_3_hash:
  canonicalize only after phases 0-2 pass
  recompute and verify every hash in the checklist below

phase_4_score:
  score arms only after all gates pass
```

`OWNER_REVIEW_REQUIRED` is a pre-execution terminal status for this design gate; it does not authorize any fixture scoring. If the existing terminal vocabulary must remain unchanged, encode it as `REJECT_FIXTURE(reason=OWNER_REVIEW_REQUIRED)`.

### B. Add a hard owner gate

Materialize this field outside the arm rule and require it in phase 0:

```json
{
  "owner_gate": {
    "status": "OWNER_ACCEPTED",
    "review_artifact_sha256": "64 lowercase hex characters",
    "accepted_protocol": "R60_R58_EXECUTION_PREFLIGHT_CORRECTION"
  }
}
```

`OWNER_ACCEPTED` is the only value that permits phases 1–4. The review hash is metadata and is not inserted into `base_input_sha256` or `arm_rule_sha256`; it is checked for format and included in the owner-gate audit record.

### C. Publish the complete arm mapping

The preflight must compare `arm_id`, `transition_rule_id`, and exact typed parameters against this table:

| arm_id | transition_rule_id | required rule parameters |
|---|---|---|
| `cglr_typed` | `cglr_typed` | threshold `on`; provenance `predicted_only`; correspondence `event_declared`; conservation `outside_zero`; evidence `append` |
| `append_only` | `append_only` | state write `none`; evidence `append` |
| `generic_global` | `generic_global` | broadcast coefficient `0.25`; evidence `append` |
| `mask_only_local` | `mask_only_local` | exact residual `fixed`; support `A_C`; threshold `bypass`; provenance `bypass`; evidence `append` |
| `residual_transport_untyped` | `residual_transport_untyped` | provenance `any`; correspondence `event_declared`; conservation `none`; evidence `append` |
| `no_reveal` | `no_reveal` | event action `none`; state write `none` |
| `shuffle_placebo` | `shuffle_placebo` | correspondence `fixed_wrong_component`; threshold `on`; provenance `predicted_only`; evidence `append` |
| `local_residual_no_provenance` | `local_residual_no_provenance` | provenance `any`; correspondence `event_declared`; threshold `on`; conservation `outside_zero`; evidence `append` |
| `local_residual_no_conservation` | `local_residual_no_conservation` | provenance `predicted_only`; correspondence `event_declared`; threshold `on`; conservation `equal_mass_drift`; evidence `append` |
| `mask_same_residual` | `mask_same_residual` | threshold `bypass`; provenance `bypass`; correspondence `event_declared`; conservation `outside_zero`; evidence `append` |

Any missing, extra, or mismatched parameter returns `REJECT_FIXTURE` before hashing.

### D. Recompute and verify every hash

After phases 0–2, recompute each supplied value and require exact equality:

```text
computed.projected_pixels_sha256
computed.visibility_masks_sha256
computed.computed_visibility_sets_sha256
computed.computed_visibility_counts_sha256
contract_manifest_sha256
fixture_context_sha256
base_input_sha256       (once per event and arm)
arm_rule_sha256         (once per arm)
arm_input_sha256        (once per event and arm)
```

The runner must report the raw-subject hash and supplied hash separately before comparison. A missing, placeholder, wrong-length, or mismatched value is `REJECT_FIXTURE`; supplied hashes are never trusted as inputs to their own recomputation. `arm_input_sha256` must equal the domain-separated hash of the recomputed base and rule hashes, and all arms for one event must share the same recomputed base hash.

## Decisions that pass

The computed-only visibility semantics, R56-over-R52 precedence, H2-before-arm-score requirement, no expected/post-state/target leakage in rule parameters, and `PASS_CONTRACT_REPLAY` limitation remain valid after the corrections above.

## Stop conditions

Until the two-phase ordering, owner gate, arm mapping, and hash checklist are added:

* do not run the synthetic fixture;
* do not read or rescore real C8 data;
* do not submit replay/GPU/Slurm jobs;
* do not modify receipts or validation flags.

After correction, H2 failure remains `H2_UNIDENTIFIABLE`; fixture/preflight/hash failure remains `REJECT_FIXTURE`; typed-arm contract failure remains `REJECT_CONTRACT`; a complete strong-control tie remains `REJECT_NON_IDENTIFIABLE`.

## Decision

**R61: REVISE.** R60 is close to owner-ready, but execution must be blocked until the two-phase preflight/H2 order, complete arm mapping, explicit hash recomputation checklist, and machine-enforced owner gate are added.
