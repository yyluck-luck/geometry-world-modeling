# R48 red-team audit of the R47 source-boundary contract

Date: 2026-09-24 (Asia/Shanghai)  
Scope: design-only hostile review. No replay, real-data re-score, receipt mutation, GPU/Slurm submission, or validation-flag change.

## Verdict

**R47 is acceptable as a design draft but rejected as an executable evidence contract until the corrections below are adopted.** The main failure is H2 identifiability: the proposed fixture can verify the algebra of CUT3R's documented depth-to-camera helper, but it cannot by itself establish the coordinate frame of the actual learned pointmaps emitted at the CUT3R/VMem boundary. A source formula test must therefore end in H2_UNIDENTIFIABLE when the producer does not provide an explicit pointmap-frame declaration and a CPU-checkable identity artifact. R47 also permits calibration own-ray data to freeze H1/H2 and intrinsics, which is unnecessary model selection on exposed development data. Transform and intrinsic choices must be frozen by source and synthetic checks; only the scalar metric calibration may use scene_13.

## What survives the audit

1. R47 preserves the correct infrastructure boundary: no GPU, no Slurm, no edits to remote_support_609623/, and no validation-flag changes.
2. The source anchors are adequate: the producer transform and evaluator join are cited at run_support_retrieval_v2.py:94-103, pipeline.py:950-955, and compute_support_masks.py:81-100; CUT3R cam2world/depth formulas are cited at geometry.py:199-232 and optimizer.py:102-121,251-261.
3. H1 is algebraically identifiable relative to the stored maps: if the renderer receives T_cv F, its query point must be F3 p_cv. This does not certify the upstream CUT3R map.
4. The denominator structure is mostly explicit: target pixels are the valid-depth model-visible crop, J fractions use N_eval, correlation is undefined for <=10 valid rays, and aggregation is per-target then per-window.
5. R47 already states that scene_13 and scene_14 form an exposed C8 development panel. This wording must be carried through every result label.

## Critical correction A: H2 is not identifiable from the current fixture alone

R47 section 4 item 3 says that applying depthmap_to_camera_coordinates plus geotrf recovers known points under P0 and treats P1 as a counterexample. That tests a hand-constructed optical pointmap. It does not identify the frame of the learned pointmaps produced by run_inference_from_pil and global alignment. A learned model could emit optical points, flipped points, or a normalized frame while the helper remains OpenCV-style. The C8 receipt contains rendered maps, not a proof of the learned pointmap frame.

Required replacement:

1. Split H2 into H2-source and H2-model-boundary.
2. H2-source may pass only if the source fixture verifies both the helper algebra and an explicit producer field such as pointmap_frame=optical_cv or pointmap_frame=vmem_gl, with a hash and line-level provenance.
3. H2-model-boundary requires an independent CPU-checkable artifact at the CUT3R boundary: a known camera-frame pointmap, known c2w, and expected world point after the exact boundary operation. If the actual model output frame is not documented or cannot be exercised in the available CPU environment, record H2_UNIDENTIFIABLE; do not select P0/P1 from C8 scores.
4. A synthetic fixture may reject an inconsistent candidate, but it cannot prove that the real learned model uses the surviving candidate without this frame declaration/artifact.

This is a hard stop, not an invitation to tune a transform.

## Critical correction B: remove calibration leakage

R47 section 6 currently says calibration own-ray pairs and the synthetic receipt “freeze H1/H2, depth scale, and intrinsic convention.” This lets exposed scene_13 target depth select a transform or K variant. Change the roles:

* **Source/synthetic stage:** freeze H1, H2, K, crop, principal point, units, rounding, and tolerance. No real C8 map, target depth, PSNR, or future query may choose among candidates.
* **Calibration stage:** use scene_13 only to estimate the single positive metric scale lambda after all conventions are frozen. Report all candidate diagnostics, but do not use their relative score to change the frozen candidate.
* **Analysis-held-out stage:** apply the frozen convention and lambda to scene_14 without refitting.

If the owner wants to use scene_13 to choose among source-supported alternatives, that is ordinary development tuning and must be labelled as such; it cannot be presented as an independent convention validation.

## Critical correction C: exposed development split and split freeze

Both scene_13 and scene_14 are exposed development data. Use the exact label **analysis-held-out development scene**, never “independent,” “unseen,” “blind,” or “test.” Remove R47's permission to reverse the scene order after the design is written. The split must be frozen in the owner receipt before any real-data metric is read:

* calibration: scene_13, all seven starts;
* analysis-held-out development: scene_14, all seven starts.

A reversed split requires a new contract revision before execution and cannot be chosen after inspecting corrected values. No result from this split supports cross-dataset generalization.

## Critical correction D: denominator for the transfer fraction

R47 section 7 asks for the fraction of held-out own-ray pairs satisfying the frozen depth tolerance but does not name its denominator. Add:

    N_ray(t) = count of pixels satisfying J_own_ray before depth tolerance.
    depth_consistency(t) = count(J_own_ray and abs(r/lambda-z)<=TOL(z)) / N_ray(t).

If N_ray(t)=0, report UNTESTABLE_NO_RAY, not zero. Keep the existing J_own, J, and J_cos denominators as N_eval(t); these are different estimands. Keep correlation's N_ray>10 requirement. For lambda, report N_cal_ray and estimate the median over exactly those finite positive pairs; do not silently clip or winsorize. The contract must state that target depth is read only by the declared CPU scoring/calibration process, never by the producer or candidate-selection fixture.

## Critical correction E: controls and H1/H2 interaction

Add these controls to the frozen fixture receipt:

* a known optical pointmap rendered with T_cv and queried with raw p_cv;
* the same map queried with F3 p_cv (frame-mismatch negative control);
* a known flipped pointmap rendered with T_cv F and queried with F3 p_cv (H1 positive control);
* P0/P1 source-boundary identity checks with explicit pointmap-frame labels;
* inverse-pose, pre-multiply, unit 1e3, unit 1e-3, half-pixel, and resize/crop controls.

Do not score H1-F as evidence for H2. A successful evaluator repair can coexist with an upstream-invalid surfel map. If H2 remains unresolved, the only valid result is a source-contract failure and no real-data DCR interpretation.

## Corrected minimal execution contract

1. **Pre-freeze:** record the exposed-development status, scene split, source hashes, receipt hash, candidate table, and command-discovery output. No real score is read while choosing H1/H2/K.
2. **Synthetic/source stage:** run the explicit optical and flipped pointmap fixtures, verify the algebraic identities, and require a pointmap-frame declaration/artifact. Fail with H2_UNIDENTIFIABLE when missing.
3. **Calibration stage:** after conventions are frozen, estimate one lambda from scene_13 N_cal_ray pairs only. This is calibration, not validation.
4. **Analysis-held-out stage:** apply the frozen convention and lambda once to scene_14. Report per-target N_eval, N_ray, depth-consistency numerator/denominator, correlation count, and window means. Do not refit or choose a candidate.
5. **Decision:** only if H1, H2, and scale transfer pass the declared checks may an owner consider a new convention-consistent C8 replay. The output remains a development-panel diagnostic, not a method result or generalization claim.

## Rejection / stop conditions

Reject the R47 execution contract if:

* H2 has no explicit pointmap-frame provenance or CPU-checkable boundary artifact;
* any real calibration metric chooses H1, H2, K, crop, units, or tolerance;
* scene_14 is described as blind/independent/test or the scene order is changed after metrics are visible;
* N_ray=0 is encoded as zero, or the depth-consistency denominator is omitted;
* target RGB/future RGB/PSNR enters convention selection, or target depth enters the producer;
* multiple source-supported transforms remain plausible;
* a receipt or frozen C8 artifact is overwritten, or any GPU/Slurm command is run;
* corrected C8/DCR claims are promoted beyond an exposed-development infrastructure diagnostic.

Current decision: **R47 design = ACCEPT WITH CORRECTIONS; executable contract = REJECT UNTIL H2 provenance and leakage/denominator corrections are recorded.** Keep new_method_validated=false, novelty_authorization=NONE, RCA/BRD closed, and DCR real-data claims blocked.

