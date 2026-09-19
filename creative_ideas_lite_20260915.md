# Creative, falsifiable candidates for long-horizon geometric consistency

审查日期：2026-09-15（Asia/Shanghai）  
状态：候选生成与审查；`new_method_validated=false`，`novelty_authorization=NONE`。  
范围：以下是待证伪的研究候选，不是已验证方法，也不授予论文创新性。

## Reviewer boundary

The useful claim is narrower than “better memory” or “more geometric consistency”: with the
candidate pool, query path, generator, random state, real memory-slot budget, and compute fixed,
the proposed signal must predict the **signed change in unseen future RGB-D/pose loss** after a
candidate replacement. A signal that only predicts current reconstruction, coverage, confidence,
or whether the output changes is insufficient.

## Candidate A — Counterfactual source-conflict abstention (SOCF-A)

**Mechanism.** For each candidate memory slot, replay its visible source geometry through the
other selected slots and estimate a localized source-conflict map. Select a low-conflict set, but
abstain (retain the baseline selection) when conflict direction is not stable under leave-one-slot-
out replay. The possible contribution is the *abstention rule tied to downstream signed future
loss*, rather than a new confidence threshold.

**Nearest alternatives and actual distinction.** ViewRope uses ray/geometry relevance for history
conditioning; Spatia maintains an updatable explicit spatial memory; GIM-World uses geometry and
mutual-information-style memory selection. SOCF-A acts on pairwise source conflict and predicts
the direction of a counterfactual slot replacement, with an explicit abstain action. It must still
be compared against recency, pose-distance, coverage/visibility, confidence-only, utility-only,
ViewRope-like relevance, and Spatia-like memory under matched budgets.

**Falsifiable prediction.** Within matched recency, pose, coverage, and confidence strata, the
conflict signal has positive out-of-sample partial rank correlation with future signed gain, and
abstention reduces both mean future capped AbsRel and the tail without reducing coverage below the
pre-registered allowance.

**Cheapest discriminating H800 experiment.** After Gate 0 and the frozen VMem baseline, use 3
calibration trajectories (3 queries each) to freeze conflict calibration and abstention. On 10
held-out trajectories (3 queries each), compare SOCF-A against strongest non-SOCF selector at
`k=4`, with `k=2,8` sensitivity, 5 random seeds, identical candidate pools and generation states.
Seal predictions before opening future depth/pose. Score trajectory-level future AbsRel, CVaR/
worst-5%, coverage, and partial Spearman/AUROC. This is a selector test, not a visual demo.

**Kill criterion.** Stop if partial prediction is no better than confidence/pose/coverage/utility,
if abstention does not improve the single primary endpoint, if replay direction disagrees on most
trajectories, or if the 1% mean-improvement / 5% tail-degradation gates fail.

## Candidate B — Future-value residual over geometry risk (FVR)

**Mechanism.** Treat calibrated geometric risk as only one covariate. Learn a residual value term
from development-only history and query metadata that estimates which future regions are likely to
be queried, then combine risk and residual under a fixed slot budget. The testable novelty is the
claim that *risk plus future-region value* resolves the risk/utility mismatch; no future test signal
may enter selection.

**Nearest alternatives and actual distinction.** GIM-World and geometry/MI selectors already use
geometry-related utility; ViewRope uses ray relevance; Spatia uses an explicit spatial memory.
FVR differs only if the residual is learned on development trajectories and is evaluated as an
out-of-sample correction to risk, with a fixed-budget selector and signed future geometry loss.
Without that incremental test it is a reweighting of known utility/coverage heuristics.

**Falsifiable prediction.** After controlling for risk, pose distance, coverage, confidence, and
utility-only score, the development-fitted residual predicts future signed gain on held-out
trajectories and improves the pre-registered `k=4` future AbsRel over calibrated-risk-only and the
strongest baseline.

**Cheapest discriminating H800 experiment.** Reuse the same frozen candidate-pool and baseline
artifacts as Candidate A. Fit the residual only on 3 development trajectories; lock its formula,
weights, and threshold; run the 10-trajectory held-out test with identical seeds, slot/token/
forward/generation budgets. Evaluate risk-only, residual-only, combined FVR, and strongest
baseline using paired trajectory tests and bootstrap intervals.

**Kill criterion.** Stop the method claim if residual partial correlation or AUROC crosses zero,
if combined FVR is no better than risk-only/utility-only, if the gain appears only on current
reconstruction, or if selecting residual features requires future RGB-D/pose.

## Candidate C — Event-gated memory replacement at leave/revisit change points (EGR)

**Mechanism.** Detect a pre-specified leave/revisit event from online camera motion and visibility
change. Keep stable slots during ordinary motion; at the event, replace only slots whose predicted
reprojection support is stale, while preserving a common-prefix anchor. The mechanism is an event
gating and partial replacement policy, not generic persistent state.

**Nearest alternatives and actual distinction.** Ordinary sliding/recent memory, temporal-nearest
selection, ViewRope history relevance, and Spatia updatable 3D memory all can change history. EGR
is distinct only through an explicit event trigger plus common-prefix preservation and a paired
replacement intervention. If no natural leave/revisit event exists, this candidate has no valid
setting and should be dropped.

**Falsifiable prediction.** On trajectories containing a pre-registered leave/revisit event and
large viewpoint change, EGR lowers future depth/pose loss at the event and during the next fixed
window at equal replacement count and memory budget, while showing no advantage on ordinary-motion
controls.

**Cheapest discriminating H800 experiment.** First run a data-only event audit on eligible ICL/TUM
trajectories; do not manufacture a change point. If qualified, freeze one event detector on
development data, then compare EGR, recent, temporal-nearest, coverage, and random with equal
replacement count over the next fixed future window. Use at least 3 development and 10 held-out
trajectories, with event/no-event strata and sealed future answers.

**Kill criterion.** Drop the route if the audit finds no natural event, if equal-count EGR is no
better than recent/coverage, if gains occur only from more slots or extra compute, or if ordinary-
motion controls show the same gain (making the event mechanism non-identifiable).

## Reviewer ranking and decision

Candidate A is the cleanest immediate falsification because it directly tests the project's
current unresolved prediction while adding an abstain control. Candidate B is a stronger rescue if
risk predicts conflict but not future utility, but it risks collapsing into a known utility
selector. Candidate C is high-risk and conditional on a genuine leave/revisit event; it should be
attempted only after the event audit.

No candidate should be called a method contribution until Gate 0, held-out isolation, equal-budget
comparison, cross-scene confirmation, ablations, and independent readback all pass. A negative
result remains a useful evaluation or failure-analysis result and does not justify renaming the
candidate.

## Evidence consulted

- `docs/RESEARCH_PLANS_EN.md` (S91–S103 contracts and claim boundary)
- `docs/RESEARCH_HANDOFF_CURRENT.md` (current H800/Gate 0 state and innovation status)
- `work/agents/innovation_falsification_matrix_20260915.md` (nearest alternatives, sample-size
  contract, thresholds, and mathematical counterexample)

