# R56 oracle-free correction for the R54 R52 manifest

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only addendum. No fixture execution, real C8 data, replay, GPU/Slurm submission, receipt mutation, or validation-flag change.

## Purpose and precedence

This addendum applies every R55 correction to the R54 manifest. It preserves the R52 arms, events, H2 gate, and `PASS_CONTRACT_REPLAY` terminal. For projection, pixel bounds, occlusion, and query separation, this R56 `visibility_v2` contract **supersedes R52 §2.2**; the older continuous-coordinate bounds are informational only.

The central oracle-free rule is strict: `expected_visibility_sets` are reviewer declarations only. Every query condition, denominator, output metric, visibility hash, base-input hash, and arm comparison uses only `computed_visibility_sets` produced from world points and camera geometry at execution time. Expected sets cannot be used as run-time masks.

## 1. Corrected manifest schema

Embed the following fields in the canonical synthetic fixture. The `expected_*` fields are excluded from all arm/query/metric hashes. The `computed_*` fields are produced by the fixture runner and are the only visibility inputs to scoring.

```json
{
  "contract_manifest": {
    "schema": "cglr-contract-manifest-v2-r56",
    "parent_protocol": "R52_CGLR_20260924",
    "supersedes": ["R54.visibility_v1", "R52.section_2_2_projection_text"],
    "serialization": {
      "encoding": "UTF-8",
      "json": "sorted_keys_separators_comma_colon",
      "numeric_quantization": "q=1e-6_nearest_even"
    },
    "visibility_v2": {
      "pose": "camera_to_world",
      "camera_to_camera": "x_cam = transpose(R) @ (p_world - t)",
      "continuous_projection": "u=fx*x_cam[0]/z+cx; v=fy*x_cam[1]/z+cy",
      "pixel": "i=round_nearest_even(u); j=round_nearest_even(v)",
      "in_bounds": "0 <= i < width and 0 <= j < height",
      "positive_depth": "z > 0",
      "front_facing": "dot(n, camera_center-p) > 0",
      "occlusion_key": "(round_nearest_even(z/q), cell_id)",
      "occlusion": "among cells at one integer pixel, choose lexicographic minimum occlusion_key",
      "mask_record_fields": ["camera_id", "patch_id", "cell_id", "pixel_i", "pixel_j", "z", "z_q", "positive_depth", "in_bounds", "front_facing", "occluded", "visible"],
      "expected_visibility_sets": {
        "context": {"A": ["A00","A01","A02","A03","A04","A05","A06","A07","A08","A09","A10","A11","A12","A13","A14","A15"], "C": [], "B": [], "U": []},
        "reveal_A": {"A": ["A00","A01","A02","A03","A04","A05","A06","A07","A08","A09","A10","A11","A12","A13","A14","A15"], "C": [], "B": [], "U": []},
        "negative_B": {"A": [], "C": [], "B": ["B00","B01","B02","B03","B04","B05","B06","B07","B08","B09","B10","B11","B12","B13","B14","B15"], "U": []},
        "third_C": {"A": [], "C": ["C00","C01","C02","C03","C04","C05","C06","C07","C08","C09","C10","C11","C12","C13","C14","C15"], "B": [], "U": []}
      },
      "expected_visibility_counts": {
        "context": {"A": 16, "C": 0, "B": 0, "U": 0},
        "reveal_A": {"A": 16, "C": 0, "B": 0, "U": 0},
        "negative_B": {"A": 0, "C": 0, "B": 16, "U": 0},
        "third_C": {"A": 0, "C": 16, "B": 0, "U": 0}
      },
      "computed_visibility_sets": "RUN_TIME_ONLY_FROM_WORLD_POINTS",
      "computed_visibility_counts": "RUN_TIME_ONLY_FROM_COMPUTED_SETS",
      "query_separation_over_computed_only": [
        "computed(reveal_A,A) has 16 cells",
        "computed(reveal_A,C) == empty",
        "computed(reveal_A,B) == empty",
        "computed(reveal_A,U) == empty",
        "computed(third_C,C) has 16 cells",
        "computed(third_C,A) == empty",
        "computed(third_C,B) == empty",
        "computed(third_C,U) == empty",
        "computed(negative_B,B) has 16 cells",
        "computed(negative_B,A) == empty",
        "computed(negative_B,C) == empty",
        "computed(negative_B,U) == empty"
      ],
      "component_condition": "A and C have component surface_S; component labels do not imply pixel overlap"
    },
    "hash_domains_v2": {
      "domain_prefixes": {
        "contract_manifest": "cglr:r56:contract_manifest:v2:",
        "fixture_context": "cglr:r56:fixture_context:v2:",
        "base_input": "cglr:r56:base_input:v2:",
        "arm_rule": "cglr:r56:arm_rule:v2:",
        "arm_input": "cglr:r56:arm_input:v2:"
      },
      "contract_manifest_paths": [
        "#/contract_manifest/schema", "#/contract_manifest/parent_protocol",
        "#/contract_manifest/supersedes", "#/contract_manifest/serialization",
        "#/contract_manifest/visibility_v2/pose",
        "#/contract_manifest/visibility_v2/camera_to_camera",
        "#/contract_manifest/visibility_v2/continuous_projection",
        "#/contract_manifest/visibility_v2/pixel",
        "#/contract_manifest/visibility_v2/in_bounds",
        "#/contract_manifest/visibility_v2/positive_depth",
        "#/contract_manifest/visibility_v2/front_facing",
        "#/contract_manifest/visibility_v2/occlusion_key",
        "#/contract_manifest/visibility_v2/occlusion",
        "#/contract_manifest/visibility_v2/mask_record_fields",
        "#/contract_manifest/hash_domains_v2"
      ],
      "fixture_context_paths": [
        "#/schema", "#/protocol_id", "#/data_scope", "#/status",
        "#/h2_provenance/frame_label", "#/h2_provenance/source_manifest_sha256",
        "#/h2_provenance/boundary_artifact_sha256", "#/contract_manifest_sha256"
      ],
      "base_input_paths": [
        "#/camera_convention", "#/cameras", "#/patches", "#/grid",
        "#/world_points", "#/surface_normals", "#/projected_pixels",
        "#/visibility_masks", "#/state_pre_cells", "#/event_instance",
        "#/correspondence", "#/threshold/tau_l2", "#/update_budget",
        "#/contract_manifest_sha256"
      ],
      "arm_rule_paths": [
        "#/arm/transition_rule_id", "#/arm/transition_rule_parameters"
      ],
      "excluded_from_base_and_rule": [
        "#/arm/arm_id", "#/arm/arm_name", "#/post_state",
        "#/post_evidence", "#/rendered_output",
        "#/contract_manifest/visibility_v2/expected_visibility_sets",
        "#/contract_manifest/visibility_v2/expected_visibility_counts"
      ],
      "arm_id_in_base": false,
      "canonical_hash_formula": "SHA256(domain_prefix || canonical_json(extract(paths)))",
      "arm_input_formula": "SHA256(domain_prefix_arm_input || canonical_json({base_input_sha256, arm_rule_sha256}))"
    }
  }
}
```

## 2. Computed visibility and anti-oracle checks

For each camera/cell, compute `x_cam`, continuous `(u,v)`, integer `(i,j)` with nearest-even rounding, and `z_q=round_nearest_even(z/q)`. Apply positive-depth, rounded-pixel bounds, and front-facing predicates. At each integer pixel, choose the lexicographic minimum `(z_q, cell_id)`; set `visible=true` only for the winning cell with all predicates true. Serialize every camera-keyed mask record, including non-visible cells and predicate values.

Create `computed_visibility_sets[camera][patch]` from records with `visible=true`. Compare it with `expected_visibility_sets` only for fixture-integrity reporting. A mismatch returns `REJECT_FIXTURE`; execution must still use the computed set for every denominator, query condition, and render selection. If an implementation reads an expected list to form a mask, return `REJECT_FIXTURE` for oracle contamination.

Compute `projected_pixels_sha256` from computed records `(camera_id, cell_id, pixel_i, pixel_j, z, z_q)` and `visibility_masks_sha256` from computed records `(camera_id, patch_id, cell_id, visible, predicate fields)`. Expected sets and counts are excluded from both hashes, from `base_input_sha256`, and from arm signatures. There is no cross-camera pixel intersection.

## 3. Materialized R52 hash subjects

Before any arm hash is computed, materialize this execution envelope for each event and arm:

```json
{
  "state_pre_cells": "64 row-major cell records expanded from R52 slots",
  "event_instance": {
    "event_id": "one of none/A_small/A_large/B_large/A_large_measured/A_large_wrong_component",
    "patch": "canonical patch or null",
    "value": "canonical quantized vector or null",
    "source_provenance": "canonical provenance label",
    "correspondence_id": "canonical correspondence or none",
    "allowed_support": "canonical cell-id list"
  },
  "threshold": {"tau_l2": 0.25},
  "update_budget": {
    "max_transition_steps": 1,
    "max_state_cells_touched": 64,
    "max_evidence_appends": 1,
    "state_update_order": "row_major_cell_id"
  },
  "contract_manifest_sha256": "computed from contract_manifest_paths",
  "arm": {
    "arm_id": "metadata_only",
    "transition_rule_id": "canonical arm name",
    "transition_rule_parameters": "canonical quantized JSON rule parameters"
  }
}
```

`state_pre_cells` must have exactly 64 records with cell ID, patch, value, and provenance; it is not a prose alias. `event_instance` is one expanded event object, not the whole event table. `threshold`, `update_budget`, `contract_manifest_sha256`, and the two `arm.*` rule fields are materialized before extraction, so every R54/R55 path resolves. The arm ID is metadata only and is excluded from base and rule hashes.

For each event, compute:

```text
contract_manifest_sha256 = SHA256(
  "cglr:r56:contract_manifest:v2:" ||
  canonical_json(extract(contract_manifest_paths))
)

base_input_sha256 = SHA256(
  "cglr:r56:base_input:v2:" ||
  canonical_json(extract(base_input_paths))
)

arm_rule_sha256 = SHA256(
  "cglr:r56:arm_rule:v2:" ||
  canonical_json(extract(arm_rule_paths))
)

arm_input_sha256 = SHA256(
  "cglr:r56:arm_input:v2:" ||
  canonical_json({"base_input_sha256": base_input_sha256,
                  "arm_rule_sha256": arm_rule_sha256})
)
```

For a given event, all arms must have byte-identical `base_input_sha256`; only `arm_rule_sha256` and post-state/output hashes may differ. A post-state, expected visibility set, or expected count in any base-input or arm-rule extraction is a `REJECT_FIXTURE` condition.

## 4. Scope and stop conditions

The R52 strong controls, event signatures, channel denominators, H2 gate, and `PASS_CONTRACT_REPLAY` terminal remain unchanged except that all visibility-derived quantities now use computed sets. Missing or failed H2 remains `H2_UNIDENTIFIABLE`; projection/mask/hash contamination is `REJECT_FIXTURE`; a strong-control tie is `REJECT_NON_IDENTIFIABLE`; typed-arm invariant failure is `REJECT_CONTRACT`.

No H2 provenance, real C8 data, replay, GPU/Slurm job, receipt edit, or validation-flag change is performed or unlocked by this design correction.

## Decision

**R56 status: CORRECTION COMPLETE / DESIGN-ONLY.** R55's oracle and hash-path issues are resolved in this addendum. Owner review is required before any fixture execution.
