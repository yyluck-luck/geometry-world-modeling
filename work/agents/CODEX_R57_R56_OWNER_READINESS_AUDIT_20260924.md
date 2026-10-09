# R57 owner-readiness audit of the R56 oracle-free correction

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only hostile audit. No fixture execution, real C8 data, replay, GPU/Slurm submission, receipt mutation, or validation-flag change.

## Verdict

**REVISE once before owner acceptance.** R56 correctly separates expected from computed visibility in its prose, fixes quantized-depth tie-breaking, and makes the R56-over-R52 precedence explicit. The remaining issue is schema-level: the hash paths `#/projected_pixels` and `#/visibility_masks` still do not resolve to a named, materialized computed object in the R52/R56 fixture, and R56 does not define an explicit fixture-integrity exclusion domain. Without this, an implementation can hash a placeholder or accidentally include expected sets.

## Audit results

### Expected versus computed fields

The intent is sound: expected sets/counts are reviewer declarations, while computed sets drive scoring. R56 excludes expected values from `contract_manifest_paths`, `base_input_paths`, and `arm_rule_paths`. However, it does not provide one machine-readable exclusion list covering every hash domain, and it does not state how `fixture_sha256` is formed. Add an explicit `excluded_from_all_hash_domains` list and make fixture integrity use the same computed-only subjects.

### Computed fields and path resolution

R56 says the runner produces computed projections and masks, but its base-input list still names top-level `#/projected_pixels` and `#/visibility_masks` without declaring those fields in the materialized envelope. `computed_visibility_sets` is described as run-time only but is not a hash path. An owner cannot reproduce the base hash from the published schema.

### Arm input hashes

The per-event rule is otherwise correct: `event_instance` is in the shared base input, the arm rule is the only arm-specific domain, and `arm_id` is excluded. Add one invariant that `transition_rule_parameters` cannot contain event data, expected visibility, or post-state values. This keeps access matching auditable.

### R56/R52 precedence

The precedence statement is unambiguous: `visibility_v2` controls projection, rounded-pixel bounds, occlusion, and query separation, and supersedes R52 §2.2. No semantic correction is required there.

## Exact minimal schema/path correction

Add the following materialized object before computing any hash:

```json
{
  "computed": {
    "projected_pixels": "camera-keyed records for every cell",
    "visibility_masks": "camera-keyed predicate and visible records for every cell",
    "computed_visibility_sets": "camera -> patch -> visible cell IDs",
    "computed_visibility_counts": "camera -> patch -> count",
    "projected_pixels_sha256": "computed hash",
    "visibility_masks_sha256": "computed hash"
  },
  "hash_exclusions": {
    "excluded_from_all_hash_domains": [
      "#/contract_manifest/visibility_v2/expected_visibility_sets",
      "#/contract_manifest/visibility_v2/expected_visibility_counts",
      "#/post_state", "#/post_evidence", "#/rendered_output"
    ]
  }
}
```

Replace the R56 `base_input_paths` entries with these exact paths:

```text
#/camera_convention
#/cameras
#/patches
#/grid
#/world_points
#/surface_normals
#/computed/projected_pixels
#/computed/visibility_masks
#/computed/computed_visibility_sets
#/computed/computed_visibility_counts
#/state_pre_cells
#/event_instance
#/correspondence
#/threshold/tau_l2
#/update_budget
#/contract_manifest_sha256
```

Define the fixture context hash explicitly as:

```text
fixture_context_paths = [
  #/schema, #/protocol_id, #/data_scope, #/status,
  #/h2_provenance/frame_label,
  #/h2_provenance/source_manifest_sha256,
  #/h2_provenance/boundary_artifact_sha256,
  #/contract_manifest_sha256,
  #/computed/projected_pixels_sha256,
  #/computed/visibility_masks_sha256
]
fixture_context_sha256 = SHA256(
  "cglr:r56:fixture_context:v2:" ||
  canonical_json(extract(fixture_context_paths))
)
```

Expected visibility declarations are excluded from `contract_manifest_sha256`, `fixture_context_sha256`, `base_input_sha256`, `arm_rule_sha256`, `arm_input_sha256`, every metric, and every query condition. They may be compared against the computed sets only to emit `REJECT_FIXTURE` on a mismatch. This removes the last expected-answer path from scoring and hashing.

Add this arm-rule invariant:

```text
transition_rule_parameters may contain only the predeclared arm rule;
it must not contain event_instance, expected_visibility_*, computed post-state,
rendered output, or target truth.
```

The existing formulas remain valid after the path replacement:

```text
base_input_sha256 = SHA256("cglr:r56:base_input:v2:" || canonical_json(extract(base_input_paths)))
arm_rule_sha256  = SHA256("cglr:r56:arm_rule:v2:"  || canonical_json(extract(arm_rule_paths)))
arm_input_sha256 = SHA256("cglr:r56:arm_input:v2:" || canonical_json({base_input_sha256, arm_rule_sha256}))
```

## Stop conditions

After this path/envelope correction, owner review may accept the design for a later synthetic-only execution. Until then:

* unresolved computed paths or expected-field leakage is `REJECT_FIXTURE`;
* missing or failed H2 remains `H2_UNIDENTIFIABLE`;
* a strong-control tie remains `REJECT_NON_IDENTIFIABLE`;
* typed-arm invariant failure remains `REJECT_CONTRACT`;
* no fixture, replay, real C8, GPU/Slurm, receipt, or validation-flag change is authorized.

## Decision

**R57: REVISE.** R56's oracle-free semantics, arm access matching, and R52 precedence survive. Add the computed-envelope paths and explicit all-domain exclusions before owner acceptance.
