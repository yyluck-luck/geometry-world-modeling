# R52 CGLR CPU protocol revision after R51

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only revision. Synthetic fixture only; do not execute it in this cycle. No real C8 RGB/depth, replay, GPU/Slurm submission, receipt mutation, or validation-flag change is permitted.

## Decision and boundary

R50 is revised before execution. The revision removes the tautological control construction identified in R51 and makes the camera query separation a computed property of a synthetic 3-D fixture. The protocol tests only deterministic operator conformance and identifiability on that fixture. It does not validate a learned world model, establish literature novelty, or authorize real-data rescoring.

The terminal outcomes are ordered as follows:

1. `H2_UNIDENTIFIABLE`: the required H2 camera-frame/pointmap provenance artifact is absent, ambiguous, or fails its declared identity check.
2. `REJECT_FIXTURE`: schema, geometry, projection, visibility, hash, or denominator integrity fails.
3. `UNTESTABLE_NO_DENOMINATOR`: a required view or channel has no computed evaluation cells.
4. `REJECT_CONTRACT`: the typed arm violates provenance, evidence immutability, support, conservation, or no-reveal identity.
5. `REJECT_NON_IDENTIFIABLE`: the typed arm is contract-conformant but its complete event signature is matched by a strong access-matched control.
6. `PASS_CONTRACT_REPLAY`: all synthetic contract checks pass and the typed arm is distinguishable from every strong control. This is a conformance result only.

The existing R50 negative baselines remain diagnostic, but no baseline that is denied the event residual, correspondence, or update budget is allowed to carry the identifiability decision.

## 1. H2 precondition and frozen scope

Before scoring any arm, require this independently reviewed object:

```json
{
  "frame_label": "optical_cv" or "vmem_gl",
  "source_manifest_sha256": "sha256 of exact producer and boundary files",
  "boundary_artifact_sha256": "sha256 of CPU-checkable pointmap/c2w artifact",
  "identity_formula": "inv(T_frame) @ X == p_frame",
  "max_abs_error": "number <= 1e-6",
  "status": "PASS"
}
```

The boundary artifact must contain a known camera-frame point, the producer pointmap-frame declaration, the exact `c2w`, the expected world point, and the operation used at the CUT3R/VMem boundary. A helper-function algebra check without a producer declaration is insufficient. Missing fields, an ambiguous frame label, or error above `1e-6` returns `H2_UNIDENTIFIABLE` before any arm is evaluated.

The source manifest paths stay explicit and are not treated as proof by themselves:

* `work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py`
* `work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/src/dust3r/utils/geometry.py`
* `work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/cloud_opt/dust3r_opt/optimizer.py`

R52 keeps the H2 fields as required placeholders in the design artifact. A future execution must fill them from the owner-reviewed artifact. No real C8 map, target RGB/depth, future camera answer, learned weight, or old receipt may be substituted.

## 2. Canonical synthetic fixture

The canonical object is UTF-8 JSON with sorted keys, separators `,` and `:`, no NaN/Inf, and all numeric values quantized to `q=1e-6` using nearest-even before hashing:

```json
{
  "schema": "cglr-cpu-protocol-v2-r52",
  "protocol_id": "R52_CGLR_20260924",
  "data_scope": "synthetic_only",
  "status": "DESIGN_ONLY",
  "deterministic": true,
  "rng_seed": 0,
  "dtype": "float64",
  "quantization": {"unit": 0.000001, "rounding": "nearest_even"},
  "units": {"world": "metre", "state": "quantized_micro"},
  "camera_convention": {
    "pose": "camera_to_world",
    "axes": "OpenCV_x_right_y_down_z_forward",
    "K": [[300,0,320],[0,300,240],[0,0,1]],
    "source_size": [640,480],
    "pixel_rule": "round_then_in_bounds",
    "occlusion_rule": "nearest_positive_depth_then_cell_id"
  },
  "h2_provenance": {"frame_label": "REQUIRED", "source_manifest_sha256": "REQUIRED", "boundary_artifact_sha256": "REQUIRED", "identity_formula": "REQUIRED", "max_abs_error": "REQUIRED", "status": "REQUIRED_PASS"},
  "patches": {"A": {"component": "surface_S"}, "C": {"component": "surface_S"}, "B": {"component": "unrelated_U"}, "U": {"component": "outside"}},
  "grid": {"rows": 4, "cols": 4, "spacing_m": 0.04, "cell_order": "row_major"},
  "cameras": {"context": "SEE_RULE", "reveal_A": "SEE_RULE", "negative_B": "SEE_RULE", "third_C": "SEE_RULE"},
  "world_points": "COMPUTED_AND_HASHED",
  "surface_normals": "COMPUTED_AND_HASHED",
  "projected_pixels": "COMPUTED_AND_HASHED",
  "visibility_masks": "COMPUTED_AND_HASHED",
  "state_pre": "AS_R50_CELL_EXPANDED",
  "truth": "AS_R50",
  "events": "SEE_SECTION_3",
  "correspondence": "SEE_SECTION_4",
  "hashes": "SEE_SECTION_6"
}
```

### 2.1 Deterministic world geometry and poses

Use identity rotation for all cameras and the following camera centres (the translation is the `c2w` fourth column):

```text
context    t=( 0, 0, 0)
reveal_A   t=( 0, 0, 0)
negative_B t=(-6, 0, 0)
third_C   t=( 6, 0, 0)
```

For patch centres use `A=(0,0,4)`, `C=(6,0,4)`, `B=(-6,0,4)`, and `U=(0,8,4)` metres. For row `r` and column `c` in `0..3`, expand 16 literal cell IDs and set

```text
p_patch[r,c] = centre_patch + (0.04*(c-1.5), 0.04*(r-1.5), 0)
n_patch[r,c] = (0,0,-1)
```

The patch labels A and C deliberately share `surface_S`, while their world locations are separated. This is a synthetic query-separation fixture, not a claim that two real views are independent.

### 2.2 Computed projection and visibility

For each camera and cell, compute `x_cam = R^T (p_world - t)`, reject non-positive depth, project

```text
u = 300*x_cam[0]/x_cam[2] + 320
v = 300*x_cam[1]/x_cam[2] + 240
pixel = (round(u), round(v))
```

Then require `0 <= u < 640`, `0 <= v < 480`, front-facing `dot(n, camera_center-p) > 0`, and nearest-positive-depth visibility at duplicate pixels. The exact cell-to-pixel records, depth, predicates, and binary masks are serialized before hashing. Manual visibility counts are expected values only; the implementation must recompute them. A mismatch returns `REJECT_FIXTURE`.

The expected computed result for the stated geometry is:

| camera | A | C | B | U |
|---|---:|---:|---:|---:|
| `reveal_A` | 16 | 0 | 0 | 0 |
| `negative_B` | 0 | 0 | 16 | 0 |
| `third_C` | 0 | 16 | 0 | 0 |

The expected table is not trusted unless generated from the points. Check every rotation for orthonormality and determinant `+1`. Require the reveal and third masks for C to have zero pixel intersection, while A and C retain the same component label. Any duplicate-pixel or occlusion ambiguity not resolved by the stated rule is `REJECT_FIXTURE`.

## 3. State and event table

Retain R50's state values and 16-cell broadcast rule: `a_pred` and `c_pred` start at `[0.1,0.1,1.0]`, `b_measured` at `[0.4,0.4,0.8]`, and `u_pred` at `[0.2,0.2,0.9]`; each slot value is expanded to all 16 cells in its patch before state metrics. The truth values remain A/C `[0.9,0.1,1.2]`, B `[0.2,0.5,0.7]`, and U `[0.2,0.2,0.9]`. Threshold is `tau_l2=0.25` and update budget is fixed across arms.

The event table is canonical and hashed. Each event includes a value, source provenance, correspondence target, and declared allowed support:

| event | value | source provenance | correspondence | allowed support |
|---|---|---|---|---|
| `none` | null | none | none | `{}` |
| `A_small` | `[0.2,0.1,1.02]` | predicted | `A_to_C` | A,C |
| `A_large` | `[0.9,0.1,1.2]` | predicted | `A_to_C` | A,C |
| `B_large` | `[0.1,0.5,0.7]` | measured | none | B |
| `A_large_measured` | `[0.9,0.1,1.2]` | measured override for A | `A_to_C` | A,C |
| `A_large_wrong_component` | `[0.9,0.1,1.2]` | predicted | `A_to_U_wrong` | A,U |

`A_large_measured` differs from `A_large` only in source provenance. `A_large_wrong_component` differs only in correspondence target. The event record is appended to evidence memory in all reveal arms; it never supplies the third-camera state directly.

## 4. Correspondence and access-matched arms

The canonical correspondence table contains `A_to_C` with 16 pairs and `A_to_U_wrong` with 16 fixed pairs. Every arm receives the same event residual, support, threshold, correspondence table, state, and budget; only the transition rule hash differs. The arm input must not be made weaker by removing any of these inputs.

### 4.1 Typed arm under test: `cglr_typed`

1. Append the event record to `E`; never insert predictions into `E`.
2. Compute `e = event.value - B_pre[event.patch]` and gate on `||e||_2 > tau_l2`.
3. Write a source slot only when its provenance is predicted.
4. Apply the same residual to the declared correspondence target when that target slot is predicted. For `A_large_wrong_component`, route to U and leave C unchanged; this is an intentional correspondence counterfactual.
5. Preserve every non-allowed cell byte-for-byte, including measured B and U unless U is the declared wrong target.

### 4.2 Strong controls (identifiability decision)

* `local_residual_no_provenance`: same residual, support, `A_to_C`/event correspondence, threshold, and budget as CGLR, but updates predicted and measured source/target slots alike. It must therefore write `A_large_measured` and `B_large` where CGLR does not.
* `local_residual_no_conservation`: same residual, provenance gate, correspondence, and budget as CGLR, performs the same allowed A/target update, then applies a fixed outside-support drift whose total per-channel L1 mass equals the allowed update mass. For each outside cell use `d_c = e_c*N_allowed/N_outside`; this is deterministic and predeclared.
* `mask_same_residual`: exact event residual and declared support, but bypasses both threshold and provenance checks. It must write `A_small` and measured slots, exposing whether a mask plus residual alone explains CGLR.

### 4.3 Retained diagnostic baselines

* `append_only`: append E and never rewrite B.
* `generic_global`: add the event residual to every B slot with fixed coefficient `0.25`, including measured and unrelated slots; this is a deterministic global-update diagnostic, not a capacity claim.
* `residual_transport_untyped`: transport through the declared correspondence regardless of provenance and enforce no conservation rule.
* `no_reveal`: do not append an event and return the exact pre-state.
* `shuffle_placebo`: use the typed rule with a fixed wrong A-to-U correspondence for ordinary `A_large`.

The retained baselines cannot rescue identifiability if all three strong controls are omitted or denied equal access.

## 5. Projection, output, and hash contract

Before arm execution, expand cell lists, quantize values, and compute these hashes:

* `world_points_sha256`, `surface_normals_sha256`, `projected_pixels_sha256`, and `visibility_masks_sha256`;
* `event_table_sha256`, `truth_sha256`, and cell-expanded `state_pre_sha256`;
* per-event `base_input_sha256` over geometry, poses, masks, state, event, correspondences, threshold, and budget;
* per-arm `arm_rule_sha256` over only the transition rule, and `arm_input_sha256 = SHA256({base_input_sha256, arm_rule_sha256})`;
* `B_post_sha256`, `E_post_sha256`, and per-camera `rendered_output_sha256`;
* H2 source-manifest and boundary-artifact hashes, plus `protocol_sha256` over this file's exact bytes.

`base_input_sha256` must be byte-identical across arms for a given event. `arm_id` is metadata and is excluded from the base hash; the rule hash is the sole intentional arm difference. Missing, stale, or inconsistent hashes return `REJECT_FIXTURE`. Existing C8 hashes and receipts are never overwritten.

## 6. Denominators and channel-separated metrics

All state cells are the 64 expanded cells A/C/B/U. For each event record:

* `N_allowed`: 32 for A-to-C or A-to-U updates, 16 for B-only, and 0 for `none`;
* `N_outside = 64 - N_allowed`;
* `N_eval_A`, `N_eval_C`, `N_eval_B`, and `N_eval_U`: counts recomputed from the camera masks, never copied from a hand-written count;
* `N_changed`: quantized state cells changed from `B_pre`, with per-channel `N_changed_appearance_1`, `N_changed_appearance_2`, and `N_changed_depth`;
* `N_evidence`: exact count of E records and an exact `E_post = E_pre union event` check.

For reveal_A, third_C, and negative_B, compute mean absolute error separately for `appearance_1`, `appearance_2`, and `metric_depth` over the relevant visible-cell denominator. Do not pool depth with appearance into the PASS criterion. If a required camera/channel denominator is zero, return `UNTESTABLE_NO_DENOMINATOR`; never report zero error for an empty set.

Report `outside_changed_cell_fraction = changed_outside_cells/N_outside` and per-channel outside L1 mass ratio as diagnostics. A zero allowed update uses `UNDEFINED_NO_CHANGE` for a ratio rather than manufacturing a zero. Locality precision and recall are defined over the event's declared allowed support and `N_changed`.

## 7. Terminal rules and falsification

`PASS_CONTRACT_REPLAY` requires all of the following:

1. H2 status is PASS; fixture schema, computed poses, projection masks, and all hashes are valid.
2. `none` and `no_reveal` preserve B and E byte-for-byte.
3. `A_small` appends its reveal but leaves the typed state unchanged because the residual is below threshold.
4. `A_large` reaches the declared A/C truth within per-channel quantization epsilon, changes only A/C, has zero outside changed cells, and preserves measured B.
5. `B_large` appends the measured reveal but does not rewrite measured B or C.
6. `A_large_measured` does not rewrite A or C; its only typed difference is the evidence append.
7. `A_large_wrong_component` updates only A/U under the declared wrong map and leaves C unchanged.
8. All three strong controls have the same base input for each event. Across the complete event vector, each differs from CGLR on its predeclared causal factor: no-provenance on a measured event, no-conservation on outside drift, and mask-same-residual on the small or measured event. If any strong control matches CGLR's complete signature, return `REJECT_NON_IDENTIFIABLE`.

Return `REJECT_CONTRACT` for any typed-arm provenance write, evidence mutation, support violation, conservation failure, no-reveal drift, or channel-specific truth failure. Return `REJECT_FIXTURE` for projection/visibility/hash/pose errors. Return `H2_UNIDENTIFIABLE` before all other outcomes when the provenance precondition is missing. A PASS is only a synthetic operator-conformance result; it does not authorize a learned-model claim, novelty claim, or C8 replay.

## 8. No-go boundaries

Do not add target RGB/depth, real C8 maps, future answers, learned weights, post-hoc thresholds, or scene_13/scene_14 as independent held-out data. Do not repair old C8 J through this fixture. Keep `new_method_validated=false` and `novelty_authorization=NONE`; keep RCA/BRD closure and the DCR operator review separate from this synthetic contract.

## Decision

**R52 status: REVISED / READY FOR OWNER REVIEW, NOT EXECUTION.** The R50 protocol is not accepted unchanged. Execution remains blocked until H2 provenance is independently supplied and an owner reviews the computed projection/mask fixture and strong-control signatures.
