# R51 hostile audit of the R50 CGLR CPU protocol

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only hostile review. No fixture execution, real C8 data, target RGB/depth, replay, GPU/Slurm submission, receipt mutation, or validation-flag change.

## Verdict

**REVISE before execution.** R50 is a useful state-machine sketch, but its current PASS_INFORMATION_PATHWAY_ONLY is not genuinely discriminating. The CGLR arm is given the intended residual/provenance/conservation behavior while several controls are deliberately weaker, and the camera/patch visibility counts are asserted without 3D point projections. The protocol can therefore pass by construction even when the claimed information pathway is not distinguishable. After the corrections below, the strongest admissible result is a synthetic contract-conformance pass; it remains no evidence of method novelty or learned-model benefit.

## 1. Tautological arm construction

### Finding

R50 defines CGLR to:

* threshold the residual;
* write only predicted slots;
* transfer through the oracle A-to-C map;
* preserve all outside slots.

The controls are not access-matched:

* mask_only_local uses a fixed residual independent of the event, so it is guaranteed to fail magnitude response;
* generic_global broadcasts with coefficient 0.25 and is guaranteed to drift;
* residual_transport_untyped is mainly tested on a measured B slot, so it is guaranteed to fail provenance;
* append_only never rewrites B and cannot use the same residual-to-C operator;
* shuffle_placebo is a wrong-component control, not a correspondence-matched transport control.

A CGLR signature that differs from these controls is therefore expected by definition. It does not identify an information-pathway advantage.

### Required arm corrections

Keep the existing controls as negative baselines, but add three strong, access-matched controls:

1. local_residual_no_provenance: receives the same event residual, support mask, A-to-C correspondence, threshold, and budget as CGLR; updates predicted and measured slots alike.
2. local_residual_no_conservation: receives the same residual, provenance gate, correspondence, and budget as CGLR; performs the same A/C update but adds a fixed, predeclared outside-support drift with equal update mass.
3. mask_same_residual: receives the exact event residual and A/C support, but bypasses residual threshold and provenance checks.

All arms must receive the same base-input hash. Only the arm-rule hash may differ. No control may be denied the oracle correspondence, event magnitude, or update budget. The protocol must state that controls are not capacity-matched learned models; they are deterministic operator controls with equal fixture information.

### Required event-factor corrections

Add two counterfactual events that change only one causal factor at a time:

* A_large_measured: identical to A_large in value, support, and correspondence, but the A slot provenance is changed from predicted to measured;
* A_large_wrong_component: identical residual and predicted provenance, but the correspondence target is U rather than C.

CGLR must refuse the first write and route the second only to the declared wrong component. These tests make provenance and correspondence observable rather than assumed.

## 2. Camera and patch visibility is currently asserted

R50 supplies camera matrices and visibility counts, but no world coordinates for A/C/B/U cells and no projected pixel masks. The counts could be written to match the desired answer even if the listed camera poses do not see those patches. The claim that C is disjoint from the reveal image plane is therefore not executable.

### Required fixture corrections

Add, for every cell:

* a deterministic world point and surface normal;
* the projected pixel under each c2w and K;
* positive-depth, in-bounds, and occlusion predicates;
* the exact binary camera mask and its SHA-256;
* the declared patch/camera intersection counts.

Require the fixture to recompute visibility from these points. Manual visibility counts become expected values only; a mismatch is REJECT_FIXTURE. Check every c2w rotation for orthonormality and determinant +1. Require:

* reveal_A sees all A cells and no C/B/U cells;
* third_C sees all C cells and no A/B/U cells;
* negative_B sees all B cells and no A/C/U cells;
* pixel-mask intersection between reveal_A and third_C for C is exactly zero;
* patch A and C share a component label but occupy disjoint image pixels at the reveal camera.

Do not use an abstract visibility count as proof of a camera-separated third query.

## 3. Hash and denominator gaps

### Hash corrections

R50's arm_input_sha256 rule removes arm_id and the arm rule, but this still needs two explicit fields:

* base_input_sha256: canonical hash of geometry, poses, visibility masks, state_pre, event, correspondence, threshold, and budget; identical byte-for-byte across all arms;
* arm_rule_sha256: canonical hash of only the arm transition rule.

Also record hashes for world_points, projected_pixels, visibility_masks, event table, truth table, state_pre cell-expanded representation, and every post-state/rendered output. The H2 source manifest and boundary artifact must be part of the protocol manifest but must not be silently replaced by fixture placeholders. Any missing or inconsistent hash is REJECT_FIXTURE.

### Denominator corrections

R50's N_outside correction is now numerically consistent only if patch values are explicitly broadcast to 16 cells. Add these fields to every event/arm result:

* N_allowed: 32 cells for A-to-C update, 16 cells for B-only update, 0 for no-reveal;
* N_eval_A, N_eval_C, N_eval_B, N_eval_U: projected visible cells, each expected to be 16 or 0 from the computed masks;
* N_changed: changed state cells after quantization;
* N_outside: N_state minus N_allowed, event-specific;
* N_ray-like is not used in this abstract test; do not reuse that name.

Report appearance_1, appearance_2, and metric_depth errors separately, each over the patch-cell denominator. A single unweighted L1 over mixed appearance/depth units can hide a depth failure. The combined score may be reported only as a predeclared diagnostic, never as the PASS criterion. If a denominator is zero, return UNTESTABLE_NO_DENOMINATOR rather than zero.

## 4. PASS is a conformance test, not novelty evidence

The current outcome name PASS_INFORMATION_PATHWAY_ONLY overstates what a hand-designed state machine can establish. Rename it PASS_CONTRACT_REPLAY (synthetic only) and require a predeclared event-signature table:

* none: exact B and E identity for every conservative arm;
* A_small: E appends the event, CGLR B is byte-identical, and no predicted slot changes;
* A_large: CGLR reaches the declared A/C truth within quantization epsilon, writes no B/U cells, and preserves measured B;
* B_large: CGLR does not write the measured B slot or C;
* A_large_measured: CGLR does not write the measured A slot;
* A_large_wrong_component: CGLR does not change C.

Then require the strong controls to receive the same event residual and correspondence. A protocol pass is accepted only when:

1. H2 provenance is PASS and all projection/mask/hashes are valid;
2. CGLR satisfies every predeclared event signature and exact conservation rule;
3. at least one strong control fails a different causal requirement under the same input, while no strong control matches CGLR's complete event signature;
4. no-reveal is byte-identical and evidence is append-only;
5. the third-camera mask is verified disjoint from the reveal camera mask.

If a control ties CGLR on the complete signature, return REJECT_NON_IDENTIFIABLE. If CGLR violates an invariant, return REJECT_CONTRACT. If H2 provenance is absent, return H2_UNIDENTIFIABLE before any arm score. Even PASS_CONTRACT_REPLAY is only an implementation/conformance result; it cannot authorize a learned-model or novelty claim.

## 5. Corrected arm matrix

The executed protocol should include at least:

| Arm | Same residual/support/correspondence? | Intended missing property |
|---|---:|---|
| cglr_typed | yes | none; reference operator |
| append_only | no B rewrite | no belief commit |
| generic_global | yes | no locality/conservation |
| local_residual_no_provenance | yes | no provenance gate |
| local_residual_no_conservation | yes | no outside conservation |
| mask_same_residual | yes | no threshold/provenance semantics |
| residual_transport_untyped | yes | writes regardless of typed state |
| no_reveal | no event | null counterfactual |
| wrong_component_placebo | yes | wrong correspondence |

The original R50 generic, mask, untyped, and shuffle arms remain useful only after these stronger controls are added. A control that is intentionally denied the residual or correspondence cannot support identifiability.

## 6. H2 and no-real-data boundary

The H2 object must contain a real source manifest and CPU-checkable boundary artifact before the fixture runs. The current REQUIRED placeholders are a schema, not a PASS. The protocol must never use C8 maps, target RGB/depth, future-camera answers, or C8 PSNR to choose H2, a control, a threshold, or a visibility mask.

### Final decision

R50 is **REVISE**. Do not execute it as written. After the arm-access, projection-mask, hash, denominator, and PASS-name corrections, the protocol can falsify implementation conformance and operator identifiability on synthetic data. It still cannot establish literature novelty, real-world C8 support, or generative-model benefit. Keep new_method_validated=false, novelty_authorization=NONE, RCA/BRD closed, and CGLR limited to a DCR operator/control.

