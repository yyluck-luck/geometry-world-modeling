# Source-checked innovation screen: SOCF-A and FVR

Date: 2026-09-15 (Asia/Shanghai)  
Status: literature-grounded candidate review only. `new_method_validated=false` and
`novelty_authorization=NONE` remain unchanged.

## What the primary papers establish

ViewRope introduces camera-ray-aware attention and a geometry-aware sparse historical-frame
attention mechanism. Its selection signal is ray/geometry relevance inside the model's attention
mechanism, rather than a post-hoc estimate of whether replacing one memory slot will improve an
unseen future query. Source: [Xiang et al., “Geometry-Aware Rotary Position Embedding for
Consistent Video World Model,” arXiv:2602.07854](https://arxiv.org/abs/2602.07854).

Spatia maintains an explicit 3D scene memory, updates it from previously generated frames, and
projects that memory along the next camera path to condition iterative video generation. Its
central operation is spatial-memory updating and conditioning, rather than calibrated candidate
replacement risk or abstention. Source: [Zhao et al., “Spatia: Video Generation with Updatable
Spatial Memory,” CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhao_Spatia_Video_Generation_with_Updatable_Spatial_Memory_CVPR2026_paper.pdf).

GIM-World compresses history into fixed-size implicit memory tokens, trains a camera-queryable
geometry head, and uses information-guided pruning. This is learned geometry-aware compression;
it does not by itself establish a test-time, same-pool, signed counterfactual value for replacing
one real slot. Source: [Wei et al., “Geometry-Aware Implicit Memory for Video World Models,”
arXiv:2606.02436](https://arxiv.org/abs/2606.02436).

WorldTrace adds addressable cache compression and landmark storage at detected transitions, with
an episodic-recall benchmark. It makes retrieval addressable and transition-aware, but its
reported object is cache organization and recall, not a calibrated predictor of future RGB-D/pose
loss under a fixed VMem slot budget. Source: [Wu et al., “Addressable Memory for Video World
Models,” arXiv:2608.07408](https://arxiv.org/abs/2608.07408).

These papers make the candidate distinction plausible at the mechanism level, but they do not
prove non-overlap. The relevant novelty question remains empirical: after matching backbone,
input permissions, slot/token budget, and query path, does the proposed signal add predictive
information beyond their relevance, memory, or transition heuristics?

## Exact incremental mechanism

The smallest defensible increment is **replacement-direction conflict plus abstention**:

1. For a candidate slot `i`, reproject its source geometry into the coordinate support of the
   other selected slots, without reading any future RGB, depth, pose, or mask.
2. Produce a conflict feature from pairwise disagreement (with visibility and source identity
   retained), then obtain a direction by a development-only leave-one-slot-out replay: would
   replacing `i` change the downstream consumer's predicted geometry in a harmful or helpful
   direction on development queries?
3. At test time, select the candidate with lower calibrated conflict only when the direction is
   stable across the frozen development replay; otherwise abstain and preserve the strongest
   non-SOCF baseline selection.

The incremental claim is therefore conditional and narrow: conflict stability plus abstention may
predict the *sign* of a future-loss change. “Conflict is lower,” “the output changes,” or “current
coverage improves” is not sufficient. FVR is a secondary rescue: fit a development-only residual
future-value score after risk, then test whether the residual adds information. It must not be
described as novel if it reduces to a reweighted coverage or utility selector.

## Small development-only pilot (screening, not validation)

Run only after Gate 0, the no-data model-load smoke, and the frozen VMem baseline are accepted.
Use **two development trajectories**, each with **two pre-declared leave/revisit queries**. This
pilot is deliberately too small for a generalisation or significance claim; it only tests whether
the implementation produces non-degenerate features and whether the candidate is worth a held-out
run.

For each query, freeze one candidate pool and a small slot budget (`k=4`), then create paired
leave-one-slot-out replacements. Save source IDs, reprojection support, conflict maps, consumer
outputs, and future RGB-D/pose answers in separate files. Selection may access history and camera
metadata only. Compare: recent, pose-distance, coverage, confidence-only, utility-only, SOCF-A,
and FVR. Keep identical random state, preprocessing, forward count, generation steps, and memory
tokens. Report raw per-query signed future-loss changes and missingness; do not pool pixels as
independent samples.

The pilot passes to a held-out study only if (a) conflict/replay features are finite and traceable,
(b) the abstention branch is exercised on at least one pre-declared query, (c) no future field was
read before prediction sealing, and (d) the direction is not trivially identical to recency,
coverage, pose, or confidence. These are implementation gates, not evidence of benefit.

## Fatal-flaw audit and kill rules

* **Potential novelty overlap (MAJOR, currently unverified):** ViewRope, GIM-World, Spatia, and
  WorldTrace already cover geometry-aware relevance, learned geometric compression, explicit 3D
  updating, and transition/landmark memory. Defense: retain the exact counterfactual signed-loss
  prediction and matched-budget comparison; if it collapses to an existing relevance or utility
  score, stop the method framing.
* **Leakage / unidentifiable value (CRITICAL if observed):** reading future depth/pose, tuning on
  held-out identities, or changing slot/compute budget makes the comparison invalid. If observed,
  stop the corresponding claim and preserve the failure record.
* **Data-refuted mechanism (CRITICAL if observed):** if the project's own controlled data show the
  proposed signal is no better than a simple control under the frozen contract, do not add seeds,
  alter caps, or rename the mechanism to recover a positive claim.

Pilot kill conditions are implementation-level only: no genuine leave/revisit query, degenerate or
non-finite conflict feature, future access before sealing, or exact rank equivalence with a simple
control. A pilot pass does not authorize a method claim. A later held-out study must still test
incremental prediction, fixed budgets, cross-scene behavior, complete ablations, and independent
readback.

## Reviewer verdict

SOCF-A is the sharper candidate because its one exact increment—stable counterfactual conflict
direction with abstention—can be separated from the four named families using a small paired pilot.
FVR is conditional and lower priority because its residual can easily become ordinary utility
reweighting. Both remain unvalidated research hypotheses.

