# R54 contract manifest correction for R52 CGLR

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only addendum. This file does not execute the fixture or unlock real C8, replay, GPU/Slurm, receipts, or validation flags.

## Purpose and status

This addendum applies the single R53 readiness correction to `CODEX_R52_CGLR_PROTOCOL_REVISION_20260924.md`. It replaces the invalid cross-camera pixel-set intersection requirement with per-camera/per-patch visibility sets and makes the projection and hash domains machine-readable. It does not change the CGLR arm semantics, event table, H2 precondition, or `PASS_CONTRACT_REPLAY` scope.

The manifest is a required fixture field. Missing or stale manifest hashes return `REJECT_FIXTURE`; missing or failed H2 provenance still returns `H2_UNIDENTIFIABLE` before any fixture score.

## 1. Canonical `contract_manifest`

Embed this object in the canonical fixture before computing `fixture_sha256`. The strings below are contract text, not measured results from real data.

```json
{
  "contract_manifest": {
    "schema": "cglr-contract-manifest-v1",
    "parent_protocol": "R52_CGLR_20260924",
    "serialization": {
      "encoding": "UTF-8",
      "json": "sorted_keys_separators_comma_colon",
      "numeric_quantization": "q=1e-6_nearest_even",
      "rounding": "nearest_even"
    },
    "visibility_v1": {
      "pose": "camera_to_world",
      "camera_to_camera": "x_cam = transpose(R) @ (p_world - t)",
      "continuous_projection": "u=fx*x_cam[0]/z+cx; v=fy*x_cam[1]/z+cy",
      "pixel": "i=round_nearest_even(u); j=round_nearest_even(v)",
      "in_bounds": "0 <= i < width and 0 <= j < height",
      "positive_depth": "z > 0",
      "front_facing": "dot(n, camera_center-p) > 0",
      "occlusion": "nearest_positive_depth_then_cell_id",
      "mask_record": ["camera_id", "patch_id", "cell_id", "pixel_i", "pixel_j", "z", "positive_depth", "in_bounds", "front_facing", "occluded"],
      "visibility_sets": {
        "context": {
          "A": ["A00","A01","A02","A03","A04","A05","A06","A07","A08","A09","A10","A11","A12","A13","A14","A15"],
          "C": [], "B": [], "U": []
        },
        "reveal_A": {
          "A": ["A00","A01","A02","A03","A04","A05","A06","A07","A08","A09","A10","A11","A12","A13","A14","A15"],
          "C": [], "B": [], "U": []
        },
        "negative_B": {
          "A": [], "C": [],
          "B": ["B00","B01","B02","B03","B04","B05","B06","B07","B08","B09","B10","B11","B12","B13","B14","B15"],
          "U": []
        },
        "third_C": {
          "A": [],
          "C": ["C00","C01","C02","C03","C04","C05","C06","C07","C08","C09","C10","C11","C12","C13","C14","C15"],
          "B": [], "U": []
        }
      },
      "expected_counts": {
        "context": {"A": 16, "C": 0, "B": 0, "U": 0},
        "reveal_A": {"A": 16, "C": 0, "B": 0, "U": 0},
        "negative_B": {"A": 0, "C": 0, "B": 16, "U": 0},
        "third_C": {"A": 0, "C": 16, "B": 0, "U": 0}
      },
      "query_separation": [
        "visible(reveal_A,A) has 16 cells",
        "visible(reveal_A,C) == empty",
        "visible(reveal_A,B) == empty",
        "visible(reveal_A,U) == empty",
        "visible(third_C,C) has 16 cells",
        "visible(third_C,A) == empty",
        "visible(third_C,B) == empty",
        "visible(third_C,U) == empty",
        "visible(negative_B,B) has 16 cells",
        "visible(negative_B,A) == empty",
        "visible(negative_B,C) == empty",
        "visible(negative_B,U) == empty"
      ],
      "component_condition": "patches A and C have component surface_S; component labels do not imply pixel overlap"
    },
    "hash_domains_v1": {
      "domain_prefixes": {
        "fixture": "cglr:r52:fixture:v1:",
        "base_input": "cglr:r52:base_input:v1:",
        "arm_rule": "cglr:r52:arm_rule:v1:",
        "arm_input": "cglr:r52:arm_input:v1:"
      },
      "fixture_context_paths": [
        "#/schema", "#/protocol_id", "#/data_scope", "#/status",
        "#/h2_provenance/frame_label", "#/h2_provenance/source_manifest_sha256",
        "#/h2_provenance/boundary_artifact_sha256", "#/contract_manifest"
      ],
      "base_input_paths": [
        "#/camera_convention", "#/cameras", "#/patches", "#/grid",
        "#/world_points", "#/surface_normals", "#/projected_pixels",
        "#/visibility_masks", "#/state_pre_cells", "#/event_instance",
        "#/correspondence", "#/threshold/tau_l2", "#/update_budget",
        "#/contract_manifest_sha256"
      ],
      "arm_rule_paths": [
        "#/transition_rule_id", "#/transition_rule_parameters"
      ],
      "excluded_from_base_and_rule": ["#/arm_id", "#/arm_name", "#/post_state", "#/post_evidence", "#/rendered_output"],
      "arm_id_in_base": false,
      "canonical_hash_formula": "SHA256(domain_prefix || canonical_json(extract(paths)))",
      "arm_input_formula": "SHA256(domain_prefix_arm_input || canonical_json({base_input_sha256, arm_rule_sha256}))"
    }
  }
}
```

## 2. Required computation and hash material

For every camera and every cell, serialize the camera-keyed `mask_record` after applying the rounded-pixel, positive-depth, front-facing, and nearest-depth/cell-ID rules. Compute `projected_pixels_sha256` from the records `(camera_id, cell_id, pixel_i, pixel_j, z)` and `visibility_masks_sha256` from `(camera_id, patch_id, cell_id, visible, predicate fields)`. A hand-written count is only an expected value; a recomputed set/count mismatch is `REJECT_FIXTURE`.

Compute `contract_manifest_sha256` over the manifest object with its own hash field excluded. Compute `fixture_context_sha256` using `fixture_context_paths`. For each event, extract exactly `base_input_paths` and compute:

```text
base_input_sha256 = SHA256(
  "cglr:r52:base_input:v1:" || canonical_json(extract(base_input_paths))
)
```

For each arm, extract exactly `arm_rule_paths` and compute:

```text
arm_rule_sha256 = SHA256(
  "cglr:r52:arm_rule:v1:" || canonical_json(extract(arm_rule_paths))
)
arm_input_sha256 = SHA256(
  "cglr:r52:arm_input:v1:" || canonical_json({
    "base_input_sha256": base_input_sha256,
    "arm_rule_sha256": arm_rule_sha256
  })
)
```

`arm_id` is metadata and is excluded from both input hashes. For a given event, every arm must report byte-identical `base_input_sha256`; only `arm_rule_sha256` and post-state/output hashes may differ. Hashing a post-state or output into `base_input_sha256` is a fixture error.

## 3. Query separation and terminal use

The protocol now uses only the per-camera predicates above. It never intersects pixel coordinates from `reveal_A` and `third_C`. Query separation is established by the empty/non-empty visibility sets in `query_separation`, together with the shared semantic component label for A/C. If any required set differs, return `REJECT_FIXTURE`; if a required view/channel denominator is empty after these checks, return `UNTESTABLE_NO_DENOMINATOR`.

The `PASS_CONTRACT_REPLAY` rules, strong-control comparison, H2 gate, no-reveal identity, and no-go boundaries in R52 remain unchanged. A future pass remains synthetic conformance only and cannot authorize real C8, method novelty, replay, GPU/Slurm, receipt edits, or validation-flag changes.

## Decision

**R54 status: ADDENDUM COMPLETE / DESIGN-ONLY.** The R53 visibility and hash-domain correction is concrete and ready for owner review. No fixture execution or external-state mutation was performed.
