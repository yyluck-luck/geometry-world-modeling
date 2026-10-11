# W2: source-only selection of complete geometry on new scenes

Status: PRE-RUN. Frozen execution hashes and exact UTC time will be in FREEZE.json.
Owner authorization in this chat on 2026-10-10: run a small candidate-selection experiment without
true depth, freeze first, compare with canonical single geometry and simple fusion on new scenes,
check concentration, inspect S141 without duplicate work, and stop when unsupported.

## Question and scientific boundary

Can fixed source-RGB correspondences choose one complete CUT3R geometry candidate that reduces
future-view sensor-relative correspondence error on new project scenes, beyond c0 and simple fusion,
without relying on a small number of beneficial windows?

W1 exposed scenes 13/14 and found an offline GT-oracle opportunity; it did not find a useful deployable
selector. Its medoid and fusion controls were worse than c0, and gains concentrated in two windows.
The current selector is a classical, deterministic SIFT reprojection selector, not a novel method,
learned uncertainty model, calibrated posterior, or video generation intervention. Constants below
are ANALYTICAL design choices fixed before new image content or outcomes, not tuned on this panel.
No selector search or development fit is run on W1 or the new panel in this protocol.

## New-scene panel and acquisition

Fixed scene IDs: RGB-D Scenes v2 01,02,03,04; sequence seq-01. These were selected by ascending ID,
not visual or outcome inspection. Four windows per scene start at 0,120,240,360. Source offsets are
0,15,30,45 and future target offsets 60,75,90,105. Intervals do not overlap. MANIFEST.json contains
the exact identities. The archive catalogs must confirm every required file through frame 000465
before this protocol is frozen. A missing file stops this planned panel as INCOMPLETE; no content-driven
scene/window replacement is permitted. New means no recorded prior project experiment on these scenes
in the inspected repository; the scenes are not proven absent from foundation-model pretraining.

Before freeze, only official archive headers and ZIP central-directory metadata are accessed. After
freeze, fetch only scene K, source RGB, source/target poses, and source/target sensor depths; target RGB
is unnecessary and is not downloaded. Range identity, CRC and SHA receipts preserve provenance.
Downloading/decompressing a depth PNG is not interpreting its image array; no sensor-depth decoder
is called until both candidate and selector outputs have been sealed.

RGB-D Scenes v2 comes through the documented 3DMatch archive format: registered native 640x480 RGB/depth,
depth millimetres with zero invalid, and optical camera-to-world poses. Poses are dataset estimates
and are common permitted inputs to every arm; no claim of depth-independent camera estimation is made.
Primary source: cached official 3DMatch page and RGB-D Scenes v2 README in the original project's
work/S102_gate0_3dmatch/adapter_v1/sources. Archive live identities are saved in catalog/.

## Candidate construction and fair arms

Reuse W1's pinned CUT3R checkpoint, source, KPS, corrected half-pixel native-to-model mapping, known
optical poses, free fitted focal, niter=0, seed0, float32 and TF32 off. Model input preparation is
byte-identical to W1 generate_candidates.py. Four cyclic orders c0=[0,1,2,3], c1=[1,2,3,0],
c2=[2,3,0,1], c3=[3,0,1,2] see the same four RGB/pose identities; restore all outputs to canonical IDs.
Each candidate comprises the complete tuple of four source depth maps. Confidence never filters
selector matches or evaluation support. New-scene candidates are run once and reused by every arm.

Arms: canonical c0; per-source median inverse-depth fusion of the four candidates (same as W1);
one complete candidate selected by the source-only rule below. Also report all fixed orders,
the medoid, and whole-window GT oracle as diagnostics; they cannot replace the primary comparisons.
The selector and fusion both consume four reconstructions. c0 needs only one; report this compute
difference and selection runtime without claiming equal cost or a speed advantage.

Execution: local CPU, two disjoint window shards, four torch threads per process, matched runtime.
S141 A/B training/evaluation chains on TACC are separate and are not duplicated or interrupted.
No new video generation or training is part of this experiment. Source/checkpoint hashes remain
in PINNED_INPUTS.json and FROZEN_CUT3R_CODE.json; exact commands will be in RUN_COMMANDS.sh.

## Frozen source-only selector

Use existing OpenCV 4.11.0, cv2.setNumThreads(1), cv2.setRNGSeed(0). Native source RGB -> grayscale.
SIFT parameters: nfeatures=4096, nOctaveLayers=3, contrastThreshold=0.04, edgeThreshold=10, sigma=1.6.
This uses standard SIFT descriptor matching; no novelty is claimed. Reference inspected before design:
https://docs.opencv.org/4.13.0/da/df5/tutorial_py_sift_intro.html (OpenCV's primary documentation).
The protocol's numeric thresholds are fixed pilot choices, not claimed to be optimal or universal.

For all six unordered source pairs, exact L2 k-nearest matching (k=2) in both directions:
1. Strict Lowe ratio <0.75 in both directions and mutual correspondence identity.
2. Both subpixel endpoints map inside the fixed CUT3R crop using W1's half-pixel nearest mapping.
3. Known-K/pose epipolar consistency: MAX of the two point-to-epipolar-line distances <=1 native pixel.
4. World-ray parallax >=1 degree, and source-only triangulation has finite positive depth in both
   cameras. These checks use only matched RGB coordinates and supplied cameras, never candidate depth.

Keep all accepted matches. A usable pair has >=20 matches. Require >=3 usable pairs and a connected
graph spanning all four source identities. Otherwise abstain to c0, retaining the window in scoring.
No outcome-based reattempt or fallback after selection.

For each candidate, sample its predicted source depth at each accepted fractional native keypoint
using the fixed nearest model-grid mapping; unproject the native keypoint with native K and project
it into the other observed source camera. Evaluate both directions against the observed SIFT match.
Per-direction loss is min(EPE,32 pixels)/32. Nonfinite/nonpositive depth, behind-camera, nonfinite or
out-of-image projection receives 1. No candidate-specific support, confidence weighting, occlusion
rejection, or denominator removal. Average both directions and matches within each usable pair,
then average usable pairs equally. Choose the minimum-scoring complete candidate for the entire
window; scores within 1e-12 of the minimum tie to lowest candidate ID.

Save all fixed matches, pair eligibility, per-candidate residuals/scores, selected identity,
abstention reason, source hashes, camera identities, runtime and code/candidate hashes. The selector
reads only source RGB, source poses, K and predicted candidates. It may read target IDs as metadata,
but never target image/depth arrays, target poses for selection, or any sensor depth values.

## Freeze and evaluation boundary

FREEZE.json binds protocol, manifest, model-source/code hashes, selector/evaluator and tests before
new scene payload access, candidate inference or match extraction. CANDIDATE_SEAL.json binds all
64 predictions. SELECTION_SEAL.json binds all16 source-only decisions and match records before
opening sensor depth. The evaluator verifies both seals and frozen code. A GT-oracle diagnostic
can only be computed after selection is irrevocably saved; it never changes selected IDs.

Reuse W1's primary endpoint exactly: native stride4 points inside fixed crop; finite sensor depth
0<d<10m; four-neighbour depth interior jump <=0.05m; measured source points projected into target,
positive z and rounded target pixel in bounds, target interior valid, abs(projected_z-sensor_z)<=0.05m.
This support is identical for all arms and independent of candidate/selector. Compare continuous
predicted and measured target coordinates. Loss=min(EPE/800,1); invalid candidate depth/projection
receives1. Mean tuples per window, equal windows per scene, equal scenes overall. Report capped
pixel equivalents. The secondary non-interior stratum retains finite-depth and visibility checks
but does not replace the primary. Missing primary support in any window is INVALID, not a negative.

## Pass/stop rules, including concentration

All conditions must hold for GO_TO_NEXT_SMALL_PILOT; otherwise STOP_TESTED_SELECTOR:
- At least5% aggregate error reduction versus BOTH c0 and fusion.
- Positive mean reduction in EVERY scene against BOTH comparators.
- Remove the two largest positive-gain windows separately for each comparator (ties by window ID).
  On the remaining windows, with equal scene weighting retained, at least2.5% reduction versus that
  comparator must remain. This is a predeclared robustness analysis, not exclusion from the main score.
- For each comparator, the two largest positive window contributions sum to at most50% of net total
  improvement. Compute contributions with original equal scene/window weights; nonpositive net gain
  automatically fails this gate. Also report the positive-gain-only denominator descriptively.
- Source-only abstention in at most25% of all windows. Fallbacks remain part of every comparison.

Report each scene, each window, selection frequencies, abstentions, matching coverage, all fixed-order
errors and the oracle gap. Four scenes do not establish population-level effectiveness; do not turn
the many pixel correspondences into independent samples. Report no population significance claim.
Pose error, repeated textures, sparse texture/low parallax, and sparse-to-dense mismatch can defeat
the selector. A null/negative result stops this exact rule; no threshold tuning, changed panel,
second selector, renamed retry, or training sweep is launched after the result.

Engineering/provenance failures yield INCOMPLETE/INVALID, preserving receipts. Repair only execution
bugs with dated amendments, never hiding failed attempts or changing science after outcomes.
Tests are implementation checks, not research results. Run root unittest and stage tests; no root
linter is configured. Keep new_method_validated=false and novelty_authorization=NONE.
