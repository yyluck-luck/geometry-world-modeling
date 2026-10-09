# S132 RCA/BRD CPU Contract (design-only)

Status: `CONTRACT_ONLY`  
Date: 2026-09-24 (Asia/Shanghai)  
Validation flags: `new_method_validated=false`; `novelty_authorization=NONE`.

## Purpose and decision boundary

This document freezes the cheapest falsification step for the two surviving mechanism
hypotheses from R42:

* **RCA (Revealed-Contradiction Attribution):** route a delayed RGB-D residual to a
  scene-surface, camera-gauge, or transient/sensor explanation before allowing a hidden
  generative belief to change.
* **BRD (Bidirectional Reveal Deletion):** use an independently identified negative reveal
  (free space or a different measured surface) to delete/downweight a predicted-only ghost
  surface while preserving measured evidence.

This is a CPU data and scoring contract. It does not authorize an adapter, diffusion,
training, new weights, Slurm, or any formal VMem/GRC run. The C8 support audit job 609623
is an already-authorized diagnostic and is kept on its own execution path.

If the contracts fail, the corresponding method is rejected before implementation. If both
fail or collapse into the controls, the next research object is the DCR setting/benchmark,
not a renamed architecture.

## Inputs and episode roles

Use eight development/held-out-design episodes only after the owner-approved C8 support
and delivery status is reconciled. Every episode has immutable roles:

1. `context`: four delivered RGB-D frames and their poses; these are the only inputs used
   to construct the pre-reveal hidden prediction.
2. `pre_reveal_query`: one camera-conditioned query used only to seal the pre-reveal
   prediction and its independent geometry mask.
3. `reveal`: a later RGB-D observation with pose and a provenance record. RGB and depth
   are withheld from any rule that constructs the support mask; the depth/pose packet is
   the measured evidence.
4. `future_queries`: at least two held-out camera poses after the reveal. Their RGB-D
   references are opened only after all arm predictions and hashes are sealed.

The geometric masks and pose perturbation labels are generated from an independent
geometry source. The target RGB is never used to select an episode, construct a mask,
choose a branch, or tune a threshold.

## RCA routing contract

### Frozen labels

Each episode contains four sealed perturbation cases with the same pre-reveal belief:

* `scene_surface`: a real static surface/appearance change in canonical world coordinates;
* `camera_gauge`: slot-0 reference, translation-scale, or pose perturbation;
* `transient_sensor`: moving content, sensor noise, or a non-repeatable observation;
* `depth_corruption`: an invalid or corrupted depth packet.

The labels are used only for the routing confusion matrix. They are not available to the
router at inference time.

### Frozen router outputs

For residual `r` and pre-reveal belief `B`, compute three auditable scores:

* `L_scene = log p(reveal | B, fixed pose)`;
* `L_gauge = log p(reveal | B, declared pose/scale perturbation family)`;
* `L_trans = log p(reveal | declared transient/association corruption family)`.

The router emits exactly one of `SCENE_WRITE`, `GAUGE_DIAGNOSTIC`,
`TRANSIENT_HOLD`, or `INVALID_DEPTH`. The event record stores scores, perturbation
family, correspondence IDs, support mask hash, and source hashes. Only `SCENE_WRITE`
may alter a future hidden-belief packet; the other branches must not write scene content.

### RCA estimands and controls

Primary estimands are macro-averaged routing accuracy and false scene-write rate, with
the full 32-case denominator (8 episodes × 4 labels). Secondary estimands are future
camera RGB/depth error and outside-support drift after applying the frozen route.

Controls use the same residuals, data, masks, and budgets:

* `append_only`: append the reveal without attribution;
* `robust_global`: one generic robust/global update;
* `pose_only`: gauge correction without scene writing;
* `RCA`: typed routing with scene-only write permission;
* `label_shuffle`: predeclared label/permutation placebo for the routing evaluator.

Kill RCA if any of the following holds: routing cannot separate `scene_surface` from
`camera_gauge`; `robust_global` matches RCA on future RGB/depth and false scene writes;
RCA only improves the reveal camera; the gain disappears after C8 RS canonicalization;
or a delayed reveal is not necessary for the effect. Routing accuracy alone is never a
method result.

## BRD reveal contract

Each of eight episodes contains a matched positive/negative reveal pair over the same
pre-reveal hidden prediction and target ray bundle:

* `positive`: the predicted-only surface is measured at the declared support;
* `negative`: the same bundle measures free space or a different nearer surface.

The evidence ledger is immutable. BRD may change only predicted-only hypotheses in the
support mask; it may not edit measured surfaces, camera state, or unrelated hidden
regions. A negative reveal must be identifiable from depth/pose and independent geometry,
without reading target RGB.

### BRD estimands and controls

Primary estimands are ghost-surface precision/recall and depth error on the future-query
support, with denominators frozen before prediction sealing. Secondary estimands are
generated-RGB geometry error, measured-region drift, and outside-support drift on both
future cameras. Report positive and negative reveal effects separately.

Controls use identical episode roles, seeds, and capacity:

* `append_only`: keep the reveal as a new token but do not delete hypotheses;
* `generic_completion`: capacity-matched completion update;
* `global_update`: unconstrained belief update;
* `BRD`: signed positive/negative hypothesis update;
* `no_reveal`: same pre-reveal state and future queries;
* `support_shuffle`: predeclared support permutation placebo.

Kill BRD if negative evidence cannot be identified without target RGB, if it simply erases
all hidden content, if occupancy/free-space controls match it, if measured geometry drifts,
or if ghost reduction does not transfer to both future cameras.

## Shared integrity and scoring rules

* Freeze code, masks, labels, thresholds, seeds, episode IDs, arm order, and denominator
  specification before opening any future RGB-D reference.
* Hash every input packet, independent geometry mask, prediction, event record, and arm.
* Keep failed, invalid, and abstained cases in the intention-to-treat denominator; never
  replace it with a complete-case denominator.
* Apply the C8 RS canonicalization to every camera-conditioned comparison.
* Use paired same-seed prediction only as a variance control; it is not novelty evidence.
* A CPU pass proves only contract arithmetic, provenance, and mask behavior. It does not
  establish model quality, 3-D accuracy, or method validity.

## R44 threshold correction

The R43 numbers proposed for recall, false-write rate, outside-support drift, and third-camera
success are **pilot screens only**, not evidence-grade acceptance gates. A scene-recall value
such as 6/8 is a point estimate with a wide exact-binomial confidence interval; it cannot support
a claim of recall at 0.75. The false scene-write denominator is the 24 non-scene cases (not all
32 labelled cases). For a future evidence package, at least 36 non-scene cases with zero false
writes would be needed for a one-sided 95% upper bound at 0.10; S132 does not claim that sample
size.

Outside-support conservation is checked by exact equality of serialized untouched-state hashes
where the representation permits it. If a representation is numerically continuous, use an
independently replay-calibrated absolute and relative tolerance; do not assert an arbitrary
1e-6 threshold. S132 also sets future_scoring_permitted=false, so third-camera RGB/depth
scoring is not part of this contract. Any later pilot must obtain a new owner-reviewed contract
and report a paired effect with an interval; a sign-only 7/8 screen is not validation.

## Prerequisites and stop conditions

Prerequisites: (1) C8 support/delivery audit receipt and job outcome; (2) independent
geometry-mask source; (3) complete episode manifest with future-query roles; (4) two-author
review of this contract; (5) JSON/schema and hash checks pass. Until all five are present,
the only permitted work is contract repair or read-only audit.

Stop with `BLOCKED_OWNER_REVIEW` if a prerequisite is missing, `UNTESTABLE_SUPPORT` if
support provenance cannot distinguish physical scarcity from delivery/indexing, and
`REJECTED_PRIOR_ART` if the routed or deletion mechanism is indistinguishable from the
matched controls or known robust pose/occupancy methods.

## Next action

Wait for the R43 innovation adjudication memo and the remote C8 job 609623 receipt. Then
run schema/hash/self-consistency checks locally. No GPU or formal baseline is authorized by
this contract.
