# R55 hostile audit of the R54 R52 manifest correction

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only audit. No fixture execution, real C8 data, replay, GPU/Slurm submission, receipt mutation, or validation-flag change.

## Verdict

**REVISE before owner acceptance.** R54 removes the invalid cross-camera pixel intersection, but two internal issues remain. First, the manifest labels hand-written visibility cell lists as `visibility_sets`; unless those are explicitly separated from run-time `computed_visibility_sets`, the fixture can pass by consulting its own expected answer. Second, several hash paths point to fields that do not exist in R52's canonical object. The strong arm access and conservative `PASS_CONTRACT_REPLAY` wording survive.

## Hostile findings

### 1. Visibility sets are still vulnerable to an oracle shortcut

R54 correctly says that query separation must be per camera and that pixels from different cameras are never intersected. However, the same manifest contains literal `visibility_sets` and `expected_counts`. If an implementation uses these arrays as the masks used for scoring, it can satisfy the query conditions without projecting the world points. R54's prose says to recompute masks, but the field names do not enforce that separation.

**Exact fix:** rename the literal declarations to `expected_visibility_sets` and `expected_visibility_counts`; create a separate run-time `computed_visibility_sets` object generated only from world points, camera poses, K, normals, and the manifest predicate. Query separation and denominator values must be evaluated from `computed_visibility_sets`, and `visibility_masks_sha256` must hash the computed camera-keyed records. A set mismatch between expected and computed values is `REJECT_FIXTURE`; the expected arrays may never substitute for computed masks.

### 2. Tie-breaking is not fully deterministic at quantized depth ties

`nearest_positive_depth_then_cell_id` names the order but does not say whether raw float depth or quantized depth is compared. Two implementations can disagree near a tie. Since R54 already mandates `q=1e-6`, define the exact key as `(round_nearest_even(z/q), cell_id)` and choose the lexicographic minimum among cells mapping to the same integer pixel. This is a contract clarification, not a new experiment.

### 3. R54 must explicitly supersede the old R52 pixel predicate

R52 §2.2 still contains the older prose `0 <= u < 640`, `0 <= v < 480` before rounding. R54 defines rounded-pixel bounds, but only says it “applies” the correction. An owner or implementation reading both files could apply the continuous predicate. Add a precedence sentence: “For projection, pixel bounds, occlusion, and query separation, R54 `visibility_v1` supersedes R52 §2.2; R52's continuous-coordinate bounds are informational only.”

### 4. Hash paths are not resolvable against the R52 schema

R54's path list includes:

* `#/state_pre_cells`, while R52 exposes `state_pre` and describes cell expansion only in prose;
* `#/event_instance`, while R52 exposes an `events` table;
* `#/threshold/tau_l2` and `#/update_budget`, which are not fields in the canonical object;
* `#/contract_manifest_sha256`, which is computed later but not declared as a top-level hash field;
* `#/transition_rule_id` and `#/transition_rule_parameters`, which are not part of the arm envelope.

Therefore two conforming implementations could hash different objects while claiming the same domain.

**Exact schema correction:** materialize these subjects in the execution envelope before hashing:

```json
{
  "state_pre_cells": "expanded_64_cell_array",
  "event_instance": "one_canonical_event_object",
  "threshold": {"tau_l2": 0.25},
  "update_budget": "canonical_budget_object",
  "contract_manifest_sha256": "computed_from_manifest_without_its_hash_field",
  "arm": {
    "arm_id": "metadata_only",
    "transition_rule_id": "canonical_rule_name",
    "transition_rule_parameters": "canonical_rule_parameters"
  }
}
```

Then use these exact JSON-pointer domains:

```text
base_input_paths = [
  #/camera_convention, #/cameras, #/patches, #/grid,
  #/world_points, #/surface_normals, #/projected_pixels,
  #/visibility_masks, #/state_pre_cells, #/event_instance,
  #/correspondence, #/threshold/tau_l2, #/update_budget,
  #/contract_manifest_sha256
]
arm_rule_paths = [
  #/arm/transition_rule_id,
  #/arm/transition_rule_parameters
]
```

`arm_id` remains excluded. `base_input_sha256` is identical across arms for one event; only `arm_rule_sha256` differs. The computed visibility masks, not expected visibility sets, are covered by the base-input domain through `#/visibility_masks`.

## Areas that pass the audit

* **Access-matched arms:** R54 preserves R52's equal event residual, support, correspondence, threshold, and budget for the three strong controls; only the transition rule differs. The measured and wrong-component events remain observable causal factors.
* **Query separation concept:** after the expected/computed split, the required conditions are `computed(reveal_A,C)=empty`, `computed(third_C,A)=empty`, `computed(reveal_A,A)=16`, and `computed(third_C,C)=16`, plus the analogous B negative view. No cross-camera pixel intersection is used.
* **PASS wording:** `PASS_CONTRACT_REPLAY` remains a synthetic conformance terminal. A complete-signature tie still yields `REJECT_NON_IDENTIFIABLE`; no method, novelty, C8, or GPU claim follows.

## Acceptance and stop rules after correction

Accept the manifest for owner review only after the expected/computed visibility split, quantized-depth tie key, R54-over-R52 precedence sentence, and materialized hash-path envelope are added. Until then:

* missing H2 provenance is `H2_UNIDENTIFIABLE`;
* expected/computed set mismatch or unresolved path is `REJECT_FIXTURE`;
* a strong-control tie is `REJECT_NON_IDENTIFIABLE`;
* typed-arm support/provenance/conservation/no-reveal failure is `REJECT_CONTRACT`;
* no GPU, replay, real C8, receipts, or validation flags are unlocked.

## Decision

**R55: REVISE.** R54's geometric direction is correct, but it is not yet owner-ready until expected visibility is separated from computed visibility and all hash paths resolve to materialized fields.
