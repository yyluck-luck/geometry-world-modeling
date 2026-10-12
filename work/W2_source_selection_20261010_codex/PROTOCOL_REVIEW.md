# W2 pre-freeze rejection review

Workspace: Local Mac.
Review recorded: 2026-10-10 13:59:24 UTC, from the current clock.
Verdict: **PASS FOR BOUNDED EXECUTION of the exact design below.** No blocking scientific-design flaw remains within the stated pilot claim. This is a design review, not a claim of implementation correctness or experimental success.

## Inputs received

- The owner's authorization, relayed by the root agent: one small source-only selector pilot on new scenes, compared with c0 and inverse-depth median fusion; test concentration of gains and stop if unsupported.
- The root agent's accepted specification and correction in this conversation: scenes 01-04; starts 0,120,240,360; MAX bidirectional point-to-epipolar-line distance at most 1 pixel; score-tie tolerance 1e-12; all stated aggregate, scene, concentration, deletion-sensitivity, and abstention gates.
- Previously inspected W1 artifacts under `/Users/rocket/Documents/Codex/2026-10-10/i-m-sharing-my-github-repo/work/week1-wt/work/W1_joint_geometry_20261010_codex`: `PROTOCOL.md`, `RESULT.md`, `scores/RESULTS.json`, `scores/DERIVED_DIAGNOSTICS.json`, and the predictor/scorer implementation. W1 established an offline opportunity but did not establish a usable selector; its medoid and concentrated gains motivate this bounded test.

No W2 source images, target images, sensor depths, candidate predictions, or outcomes were opened by this reviewer. No new literature search, model execution, GPU use, remote connection, or scoring was performed. All numerical thresholds below are ANALYTICAL design choices, not measured results.

## Exact reviewed design

Freeze four new scenes, 01-04, with starts 0,120,240,360 if metadata establishes availability. Retain W1 source offsets 0,15,30,45 and target offsets 60,75,90,105. These frame intervals do not overlap. Finalize exact frame identities before reading new-scene image/depth content. Inadequate metadata or missing files is an execution limitation, not permission to replace difficult observed windows.

The selector reads source RGB, source poses/intrinsics, and predicted geometry only. For every unordered source pair, obtain deterministic mutual SIFT matches passing the Lowe ratio 0.75 in both directions. Matching configuration and software versions are fixed before execution. Filter matches using the MAX of the two point-to-epipolar-line distances, at most 1 pixel; positive triangulated depth in both source cameras; and calibrated source-ray parallax at least 1 degree. Keep both endpoints within the predetermined geometry crop. Match identity and these filters are independent of candidates and never use sensor depth or target appearance.

A usable pair has at least 20 accepted matches. A window requires at least three usable pairs forming a connected graph over all four source frames. Otherwise the selector abstains to c0, records the reason, and retains the window in every main evaluation denominator.

For each candidate and each retained match, measure source-to-source reprojection endpoint error in both directions using its predicted source depths. Cap each directional error at 32 pixels. Nonfinite/nonpositive depth, behind-camera projection, or out-of-image projection receives 32 pixels. No match is dropped according to candidate validity, confidence, visibility, or error. Average the two directions, average matches within each usable pair, then average pairs equally. Select one complete candidate for the entire window. Among scores within 1e-12 of the minimum, choose the lowest candidate ID.

Compare against c0 and inverse-depth median fusion constructed from the same four candidate reconstructions and source identities. Preserve W1's frozen sensor-relative correspondence endpoint and candidate-independent evaluation support. Matching, selection scores, selected IDs, fallback decisions, and prediction hashes must be sealed before sensor-depth evaluation. This compares accuracy under shared candidate computation; it does not claim equal cost with a standalone c0 inference.

## Accepted decision rules

All gates are required; comparisons are made separately against BOTH c0 and fusion:

1. At least 5% aggregate relative error reduction, with equal window/scene weighting.
2. Strictly positive mean improvement in each of the four scenes.
3. Remove the two windows with the largest absolute error reductions for that comparator, then require at least 2.5% relative reduction on the remaining windows. The complete-panel result remains primary and is always retained.
4. The sum of the two largest positive window gains divided by total signed window gain is at most 50%. A nonpositive net gain cannot pass; do not divide by its absolute value or replace the denominator with positive gains only.
5. Abstention-to-c0 in at most 25% of planned windows. Abstentions remain in all preceding gates.

Failure of any scientific gate stops this selector as tested. Missing outputs, changed frozen inputs, broken selection/measurement separation, or invalid evaluation support is INCOMPLETE/INVALID, not a scientific negative. No tuning from W1 or W2 outcomes, candidate expansion, automatic pivot, or renamed retry belongs to this authorization.

## Remaining limitations, not execution blockers

Mutual SIFT and epipolar filtering can still retain wrong repeated-texture matches. Sparse textured support may rank geometry poorly on untextured surfaces. Limited parallax can cause fallback even when candidate differences matter elsewhere. The independent sensor endpoint and all-window fallback accounting test whether these weaknesses defeat the proposed selector; the protocol must not repair them after viewing outcomes.

A pass supports this deterministic source-only selector on this small new-scene panel. It does not establish novelty, calibrated posterior uncertainty, a learned multimodal consumer, video quality gains, or population significance. Treat the pilot as exploratory, report all scene/window outcomes and concentration diagnostics, and make no confidence-interval or broad generalization claim from four scenes.

The implementation should be checked against this exact contract when available. That is an implementation check, not a new literature or authorization loop. The requested post-result review is one bounded support/stop decision, with no automatic pivot.

Changed file: this review only. Follow-up: freeze and verify the implementation, execute the authorized panel, then apply the fixed gates.
