# S77 frozen saved-match wrong-label control

Source preparation only. An independent author must review the exact source and contract before root runs any numerical evaluation. No result is claimed here.

## Question and contrast

Does each generated target retain a smaller fixed epipolar residual under its requested camera label than under one preselected wrong target label? Fix 20↔23 and 21↔22. This exact generated contrast was not found in the inspected S73/S74 source and protocols: S73 computes only correct-F generated residuals; S74 computes wrong-F residuals only for real matches. The contrast is identifiable as label sensitivity on existing matches; it cannot identify the true camera or a memory mechanism. The dataset and preceding diagnostics have already been seen, so this is exploratory, not prospectively unseen confirmation.

## Inputs and unchanged quantities

Reuse accepted S73 all 12 rows (real/A0/B × targets20–23), original real source19 anchor count N and anchor coordinates. Keep each row's source and target coordinates, keypoint IDs, source frame, target image, full raw row count and correct residuals unchanged. No swapping of coordinate/image rows. Reuse S74 saved normalized F for the wrong target camera and bind it through both contracts to the same S72 real-geometry receipt and acceptance. Save that old geometry-separation record before residual computation; it is reused evidence, not a new separation measurement. There is no depth field or inferred depth and no new 4×4 pose evaluation.

## Frozen arithmetic

For each of the eight generated rows calculate l_target=F_wrong x and l_source=F_wrong^T y, numerator=y^T F_wrong x, and the arithmetic mean of the two unsigned point-to-line distances. Preserve S74 finite-line rule and norm>1e-12. Original correct residuals are reused, not refitted or recomputed. Scalar Python floating-point fsum/hypot implements the same equation, not bit-identical NumPy BLAS ordering; independent arithmetic review should use finite absolute+relative tolerance (recommended 1e-9 + 1e-10×magnitude px), with validity changes near epsilon reported rather than hidden. The four real wrong-residual arrays are reused from S74 and marked as such; their summaries are not new real-data evidence. No new dependency/model import.

The primary paired delta is wrong minus correct on identical raw match rows valid under both labels. Preserve raw correct/wrong arrays, all raw delta positions with null for excluded rows, separate invalid indices and their union count, N, M/N, unmatched count, valid/N, source and target coverage, and per-label error distributions. Report q25/q50/q75/q95, maxima, delta minima/maxima and positive/negative/zero counts. The inherited 2/5/10px cutoffs are descriptive only. No correction, fitting, matching, post-hoc threshold, extra permutation, bootstrap or significance claim. Image-domain counts use native576×576 coordinates; they do not filter rows. Common 3D FOV, depth, occlusion and cheirality are unobserved and must not be invented.

## Support and decision rule

Primary eight generated rows each retain their own same-point paired support. Keep all four target rows per arm even if empty; all4-positive is null when ANY target median is undefined, otherwise the conjunction of strictly positive medians. Real reused rows have a separate labeled event. No pooled count substitutes for an all4 event.

Two distinct secondary support families are frozen: (1) each arm on the original S73 correct-valid three-arm source-ID support, recording any additional wrong-invalid exclusions per arm; (2) the subset valid under all six labels (correct and wrong × real/A0/B), recording dropped original IDs and size/N. The original raw intersection and correct-common IDs must match S73 exactly, and the original S73 shared-support object is saved unchanged. Each secondary family has its own all4 null-first event. Neither replaces primary support or silently overwrites the old support. Original target23 absent shared support remains absent.

## Execution and boundaries

Create-only execution_01; exact contract SHA argument; 25-second internal budget plus root-owned external30-second process-group timeout, recommended1GiB RSS/100MiB output ceiling. Failure writes FAILED_PRESERVED without overwriting prior results. Independent source review, root source/pin review, actual invocation receipt, then a separate independent numerical result review are required before scientific use. No launch authorization is supplied by this source delivery.

An all4 positive event would support only conditional wrong-label sensitivity, not successful camera calibration, a clean rigid response, SD2.1 component compatibility, generalization or dynamic-memory innovation. S76's relative yaw response, S74's real calibration sensitivity and this label permutation control answer different questions. A negative or null event is retained as counterevidence/insufficient support.

## Workflow application

Apply the existing Supervisor-Skills small frozen experiment and failure-analysis route, plus local Claude sci-scientific-critical-thinking guidance on construct validity, confounding, selection and calibrated claims. No Claude model was invoked. The intervention and support accounting are the useful scientific work; this source-only delivery adds no neural experiment or fabricated result.
