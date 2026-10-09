# R58 materialized computed-envelope correction for R56

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only addendum. No fixture execution, real C8 data, replay, GPU/Slurm submission, receipt mutation, or validation-flag change.

## Purpose and precedence

This addendum applies the R57 owner-readiness corrections to `CODEX_R56_R54_ORACLE_FREE_CORRECTION_20260924.md`. It preserves the R52 H2 gate, event table, access-matched arms, channel metrics, and `PASS_CONTRACT_REPLAY` terminal. R56 `visibility_v2` remains the precedence rule over R52 §2.2 for projection, rounded-pixel bounds, occlusion, and query separation.

The computed envelope below is materialized from world points and camera geometry before any fixture, context, base-input, arm-rule, or arm-input hash is computed. Expected visibility declarations are excluded from every hash and never act as run-time masks.

## 1. Required materialized envelope

Add these top-level fields to the synthetic execution fixture. The strings are schema descriptions; a future runner must replace every `COMPUTED_BEFORE_HASH` value with canonical records before hashing.

```json
{
  "computed": {
    "projected_pixels": "COMPUTED_BEFORE_HASH: camera-keyed record for every cell",
    "visibility_masks": "COMPUTED_BEFORE_HASH: camera-keyed predicate and visible record for every cell",
    "computed_visibility_sets": "COMPUTED_BEFORE_HASH: camera -> patch -> visible cell IDs",
    "computed_visibility_counts": "COMPUTED_BEFORE_HASH: camera -> patch -> integer count",
    "projected_pixels_sha256": "COMPUTED_FROM_PROJECTED_PIXELS",
    "visibility_masks_sha256": "COMPUTED_FROM_VISIBILITY_MASKS",
    "computed_visibility_sets_sha256": "COMPUTED_FROM_COMPUTED_SETS",
    "computed_visibility_counts_sha256": "COMPUTED_FROM_COMPUTED_COUNTS"
  },
  "contract_manifest_sha256": "COMPUTED_FROM_MANIFEST_RULE_PATHS",
  "hash_exclusions": {
    "excluded_from_all_hash_domains": [
      "#/contract_manifest/visibility_v2/expected_visibility_sets",
      "#/contract_manifest/visibility_v2/expected_visibility_counts",
      "#/post_state",
      "#/post_evidence",
      "#/rendered_output",
      "#/target_truth"
    ]
  },
  "arm": {
    "arm_id": "metadata_only",
    "transition_rule_id": "canonical arm name",
    "transition_rule_parameters": "canonical rule-only JSON"
  }
}
```

The runner must materialize `state_pre_cells`, `event_instance`, `threshold.tau_l2`, and `update_budget` as required by R56 before this envelope is hashed:

```json
{
  "state_pre_cells": "64 row-major cell records with id, patch, value, provenance",
  "event_instance": "one expanded event object for the current event",
  "threshold": {"tau_l2": 0.25},
  "update_budget": {
    "max_transition_steps": 1,
    "max_state_cells_touched": 64,
    "max_evidence_appends": 1,
    "state_update_order": "row_major_cell_id"
  }
}
```

`COMPUTED_BEFORE_HASH` is a precondition, not a permitted literal value during an execution. Any placeholder, missing record, or hash computed before the envelope is complete returns `REJECT_FIXTURE`.

## 2. Computed-only visibility and hash material

Use the R56 `visibility_v2` algorithm: compute camera-frame coordinates, continuous projection, nearest-even integer pixels, rounded-pixel bounds, positive depth, front-facing, and quantized-depth/cell-ID occlusion. Serialize all camera-keyed records, including non-visible cells and predicate fields. Derive `computed_visibility_sets` and `computed_visibility_counts` only from records with `visible=true`.

The following hashes are computed over the materialized computed fields, never over expected declarations:

```text
projected_pixels_sha256 = SHA256(
  "cglr:r58:projected_pixels:v1:" ||
  canonical_json(computed.projected_pixels)
)

visibility_masks_sha256 = SHA256(
  "cglr:r58:visibility_masks:v1:" ||
  canonical_json(computed.visibility_masks)
)

computed_visibility_sets_sha256 = SHA256(
  "cglr:r58:visibility_sets:v1:" ||
  canonical_json(computed.computed_visibility_sets)
)

computed_visibility_counts_sha256 = SHA256(
  "cglr:r58:visibility_counts:v1:" ||
  canonical_json(computed.computed_visibility_counts)
)
```

All query separation predicates, `N_eval_*` denominators, rendered metrics, locality metrics, and arm signatures use the computed sets/counts. Expected sets may be compared only to emit `REJECT_FIXTURE` on a mismatch; they cannot be read to select visible cells.

## 3. Exact hash domains

Use these JSON-pointer lists after the materialized envelope is complete:

```text
contract_manifest_paths = [
  #/contract_manifest/schema,
  #/contract_manifest/parent_protocol,
  #/contract_manifest/supersedes,
  #/contract_manifest/serialization,
  #/contract_manifest/visibility_v2/pose,
  #/contract_manifest/visibility_v2/camera_to_camera,
  #/contract_manifest/visibility_v2/continuous_projection,
  #/contract_manifest/visibility_v2/pixel,
  #/contract_manifest/visibility_v2/in_bounds,
  #/contract_manifest/visibility_v2/positive_depth,
  #/contract_manifest/visibility_v2/front_facing,
  #/contract_manifest/visibility_v2/occlusion_key,
  #/contract_manifest/visibility_v2/occlusion,
  #/contract_manifest/visibility_v2/mask_record_fields,
  #/contract_manifest/hash_domains_v2
]

fixture_context_paths = [
  #/schema, #/protocol_id, #/data_scope, #/status,
  #/h2_provenance/frame_label,
  #/h2_provenance/source_manifest_sha256,
  #/h2_provenance/boundary_artifact_sha256,
  #/contract_manifest_sha256,
  #/computed/projected_pixels_sha256,
  #/computed/visibility_masks_sha256,
  #/computed/computed_visibility_sets_sha256,
  #/computed/computed_visibility_counts_sha256
]

base_input_paths = [
  #/camera_convention, #/cameras, #/patches, #/grid,
  #/world_points, #/surface_normals,
  #/computed/projected_pixels, #/computed/visibility_masks,
  #/computed/computed_visibility_sets, #/computed/computed_visibility_counts,
  #/state_pre_cells, #/event_instance, #/correspondence,
  #/threshold/tau_l2, #/update_budget, #/contract_manifest_sha256
]

arm_rule_paths = [
  #/arm/transition_rule_id,
  #/arm/transition_rule_parameters
]
```

Define the hashes with domain-separated canonical JSON:

```text
contract_manifest_sha256 = SHA256(
  "cglr:r58:contract_manifest:v1:" ||
  canonical_json(extract(contract_manifest_paths))
)

fixture_context_sha256 = SHA256(
  "cglr:r58:fixture_context:v1:" ||
  canonical_json(extract(fixture_context_paths))
)

base_input_sha256 = SHA256(
  "cglr:r58:base_input:v1:" ||
  canonical_json(extract(base_input_paths))
)

arm_rule_sha256 = SHA256(
  "cglr:r58:arm_rule:v1:" ||
  canonical_json(extract(arm_rule_paths))
)

arm_input_sha256 = SHA256(
  "cglr:r58:arm_input:v1:" ||
  canonical_json({
    "base_input_sha256": base_input_sha256,
    "arm_rule_sha256": arm_rule_sha256
  })
)
```

The manifest rule paths intentionally exclude `expected_visibility_sets` and `expected_visibility_counts`. The fixture context, base-input, arm-rule, arm-input, projection, mask, set, and count hashes therefore contain no expected visibility values. A full event-vector comparison still uses computed outputs only.

## 4. Arm-rule non-leakage invariant

For each event, all arms receive byte-identical `base_input_sha256`. `arm_id` is metadata and is excluded from both input domains. `transition_rule_parameters` may contain only predeclared rule parameters, for example threshold-gate mode, provenance-gate mode, correspondence mode, conservation mode, evidence action, and fixed broadcast coefficient.

The following are forbidden in `transition_rule_parameters` and return `REJECT_FIXTURE` if present:

* `event_instance`, event ID/value, or event-specific residual;
* `expected_visibility_sets`, `expected_visibility_counts`, or any expected answer;
* `computed_visibility_sets`, target truth, future camera answer, or target RGB/depth;
* `post_state`, `post_evidence`, rendered output, or any post-hoc metric.

The arm rule may branch on the shared event and computed geometry through the declared rule semantics, but it may not receive those values through its hash-specific parameter object. A control tie on the complete computed event signature remains `REJECT_NON_IDENTIFIABLE`.

## 5. Scope and stop conditions

R52's H2 gate, strong controls, channel-separated denominators, no-reveal identity, and `PASS_CONTRACT_REPLAY` rules remain unchanged with the computed-only visibility substitution. Missing or failed H2 remains `H2_UNIDENTIFIABLE`; incomplete computed envelope or expected-field leakage is `REJECT_FIXTURE`; typed-arm invariant failure is `REJECT_CONTRACT`.

No H2 provenance, real C8 data, replay, GPU/Slurm job, receipt edit, or validation-flag change is performed or unlocked by this correction.

## Decision

**R58 status: CORRECTION COMPLETE / DESIGN-ONLY.** The computed envelope, computed-only path domains, fixture context hash, all-domain exclusions, and arm-rule non-leakage invariant are now explicit. Owner review is required before any fixture execution.
