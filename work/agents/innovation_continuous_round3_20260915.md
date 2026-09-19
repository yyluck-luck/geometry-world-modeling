# Continuous innovation scan, round 3 (2026-09-15)

Status: bounded primary-source check; hypothesis/null result only. `new_method_validated=false`; `novelty_authorization=NONE`.

## Additional primary source checked

**WorldStereo: Bridging Camera-Guided Video Generation and Scene Reconstruction via 3D Geometric Memories** (Zhang et al., arXiv:2603.02049, 2026), primary HTML paper: https://arxiv.org/abs/2603.02049. The paper describes an incrementally updated global point-cloud cache (GGM), a retrieved-view spatial-stereo memory with explicit 3D correspondences (SSM), and a fixed trajectory order selected for reconstruction. It reports a 100-scene memory-component benchmark and trajectory-order ablations. These are source claims only; this project did not reproduce them.

## Candidate check and nearest-work boundary

The only plausible extra direction suggested by this source is **trajectory-order-aware memory replacement**: choose which view/slot to admit next using predicted downstream reconstruction value of the remaining camera path. WorldStereo already occupies the main mechanism space—incremental 3D cache updates, retrieved reference views, 3D correspondence guidance, and trajectory ordering. Its ordering is a camera-path/reconstruction heuristic, so a selector based only on pose distance, overlap/coverage, current utility, confidence, or recency would be an expected reparameterization rather than a distinct contribution.

The narrow residual candidate would have to use a history-only estimate of *future-path marginal value after those controls are frozen*: the signed change in downstream geometric loss caused by replacing one source under the same candidate pool and fixed budget. This is materially the same identification burden as SOCF-A/FVR. The additional source therefore supplies no evidence that a new information channel exists beyond recency, pose, coverage, confidence, and utility.

**Round-3 result: null for a new candidate.** WorldStereo strengthens the occupied-design-space warning. Keep SOCF-A as the only currently testable primary candidate; do not add a trajectory-order method name or claim novelty from this scan.

## Falsifiable prediction (if retained as a diagnostic only)

After fitting all coefficients on development trajectories, a history-only trajectory-order residual would predict the sign of held-out future RGB-D/pose loss change from one replacement with positive incremental partial information beyond recency, pose distance, visibility/coverage, confidence, and current utility. At fixed `k`, memory tokens, forward count, steps, seed, and candidate pool, its selector would reduce paired future geometric loss on held-out queries. If the residual has no positive incremental information or its ranking is identical to a control, the diagnostic is falsified.

## Minimal test

Only after Gate 0, no-data model-load smoke, and the frozen VMem baseline: use the existing SOCF pilot contract, two development trajectories for calibration and one locked development trajectory for screening. For each of two predeclared leave/revisit queries, hold `k=4`, candidate identities, consumer seed, forward count, and compute fixed. Seal the history-only residual, selected IDs, abstention decision, and provenance before opening future RGB-D/pose. Compare recent, pose, coverage, confidence, utility, SOCF-A, and the trajectory-order residual; report per-query signed future AbsRel, valid pose/reprojection error, partial rank information, and compute. This is a falsification screen, not validation.

## Kill criterion

Retire this direction immediately if the source/path residual is non-finite, requires future answers, changes the budget, has exact rank equivalence with recency/pose/coverage/confidence/utility/SOCF-A, or shows no out-of-sample signed predictive information and paired future-loss improvement. Also retire it if no auditable multi-view path with held-out future scoring exists. A pass would authorize only a larger held-out experiment; it would not establish novelty or method validity.

## Evidence boundary

WorldStereo's paper establishes its stated architecture, trajectory-order ablations, and benchmark setup (paper lines 30–48, 75–105, 182–203, 271–274 in the HTML view). It does not establish non-overlap with this project's selectors, causal replacement benefit, or validation on this project's data. No implementation, model run, RGB-D/pose scoring, or novelty validation occurred in this round.
