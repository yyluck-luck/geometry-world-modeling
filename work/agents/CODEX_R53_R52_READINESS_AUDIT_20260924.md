# R53 owner-review readiness audit of R52

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only hostile audit. No fixture execution, real C8 data, replay, GPU/Slurm submission, receipt mutation, or validation-flag change.

## Verdict

**REVISE once before owner review.** R52 fixes the R51 tautological-control problem and its terminal wording is appropriately conservative. The remaining fatal ambiguity is the visibility contract: it asks for a pixel-mask intersection between two different camera image planes, while also using an underspecified `round_then_in_bounds` rule. A cross-camera pixel-set intersection is not a valid geometric separation test; it can be empty even when the same world patch is visible in both cameras. The hash prose is also easier to reproduce if the same correction provides an explicit field manifest.

## Audit findings

### 1. Computed visibility: one fatal ambiguity

The world-point construction is otherwise owner-reviewable: camera-to-world poses, patch centres, cell spacing, normals, positive depth, front-facing tests, nearest-depth tie-breaking, and expected per-camera counts are all explicit. The problem is the requirement to make the reveal and third-camera masks for C have “zero pixel intersection.” Their pixels live in different camera coordinate systems. Comparing `(i,j)` values across those systems is meaningless and can produce a false separation result.

There is a second wording mismatch: the schema says `round_then_in_bounds`, but the prose first checks continuous `u,v` bounds and only then rounds. The execution contract must use one predicate, or two implementations can disagree at an image boundary.

### 2. Access-matched arms: accepted after the visibility patch

The three strong controls now receive the same event residual, provenance, support, correspondence, threshold, and budget. Their differences are rule-level causal interventions: removing provenance gating, removing conservation, or bypassing threshold/provenance while retaining the residual and support. `A_large_measured` and `A_large_wrong_component` expose the two relevant factors. The diagnostic baselines are correctly excluded from the identifiability decision when they lack equal access.

One implementation detail must remain fixed in the canonical event object: the provenance override for `A_large_measured` and the target-map override for `A_large_wrong_component` belong to the event input, not to an arm rule. R52 states this in the table; the correction below makes it hash-visible.

### 3. Hash domains: conditionally acceptable, but currently prose-defined

R52 names the required hashes and requires canonical JSON, which is directionally sufficient. However, `base_input_sha256 over geometry, poses, masks, ...` is not an exact path list, and `arm_rule_sha256 over only the transition rule` leaves room for accidental inclusion of `arm_id` or event data. This is a reproducibility risk and should be fixed in the same small manifest block as the visibility predicate.

### 4. PASS wording: accepted

`PASS_CONTRACT_REPLAY` is correctly scoped to synthetic conformance. R52 requires a complete event-vector comparison against all three strong controls and keeps H2, learned-model benefit, novelty, and C8 replay separate. No wording change is required. A control tie still terminates as `REJECT_NON_IDENTIFIABLE`.

## One minimal correction

Add one machine-readable `contract_manifest` object to the canonical fixture and replace the cross-camera mask-intersection sentence with the following exact rules:

```json
{
  "contract_manifest": {
    "visibility_v1": {
      "camera_to_camera": "x_cam = transpose(R) @ (p_world - t)",
      "continuous_projection": "u=fx*x/z+cx; v=fy*y/z+cy",
      "pixel": "i=round(u); j=round(v)",
      "in_bounds": "0 <= i < width and 0 <= j < height",
      "positive_depth": "z > 0",
      "front_facing": "dot(n, camera_center-p) > 0",
      "occlusion": "nearest_positive_depth_then_cell_id",
      "required_sets": {
        "reveal_A:A": 16, "reveal_A:C": 0, "reveal_A:B": 0, "reveal_A:U": 0,
        "third_C:A": 0, "third_C:C": 16, "third_C:B": 0, "third_C:U": 0,
        "negative_B:A": 0, "negative_B:C": 0, "negative_B:B": 16, "negative_B:U": 0
      },
      "query_separation": [
        "visible(reveal_A,C) == empty",
        "visible(third_C,A) == empty",
        "visible(reveal_A,A) == 16",
        "visible(third_C,C) == 16"
      ]
    },
    "hash_domains_v1": {
      "base_input_paths": [
        "camera_convention", "cameras", "patches", "grid",
        "world_points", "surface_normals", "projected_pixels",
        "visibility_masks", "state_pre_cells", "event",
        "correspondence", "tau_l2", "update_budget"
      ],
      "arm_rule_paths": ["transition_rule_id", "transition_rule_parameters"],
      "arm_id_in_base": false,
      "domain_prefix": "cglr:r52:v1:",
      "serialization": "canonical_json_sorted_keys_comma_colon_utf8"
    }
  }
}
```

Compute visibility sets per camera and patch; never intersect pixel coordinates from different cameras. Hash the camera-keyed records `{camera, cell_id, pixel, depth, predicates}` so the image-plane identity is retained. Compute `base_input_sha256` as

```text
SHA256("cglr:r52:base_input:v1:" || canonical_json(extract(base_input_paths)))
```

and `arm_rule_sha256` as

```text
SHA256("cglr:r52:arm_rule:v1:" || canonical_json(extract(arm_rule_paths)))
```

with `arm_id` excluded from both. The resulting `contract_manifest_sha256` is included in the fixture hash and each arm's base-input record. This is one correction block: it makes the camera separation and the hash domains executable without changing the arm semantics or PASS terminal.

## Stop conditions

After applying the block, owner review may accept the R52 design for a later synthetic-only execution. Before that point:

* missing or failed H2 remains `H2_UNIDENTIFIABLE`;
* a computed visibility set that differs from the required table is `REJECT_FIXTURE`;
* any strong-control tie on the complete event vector is `REJECT_NON_IDENTIFIABLE`;
* any typed-arm conservation, provenance, evidence, or no-reveal violation is `REJECT_CONTRACT`;
* a zero required metric denominator is `UNTESTABLE_NO_DENOMINATOR`.

No GPU, Slurm, real C8, receipt, or validation flag is unlocked by this audit. Even a later `PASS_CONTRACT_REPLAY` remains a synthetic contract result.

## Decision

**R53: REVISE (one manifest correction), then owner-reviewable.** The R52 control design and PASS naming survive hostile review. Apply the manifest correction before any fixture execution; do not execute R52 as currently worded.
