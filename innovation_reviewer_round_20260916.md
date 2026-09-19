# Skeptical Top-Conference Review: Innovation Directions

Review date: 2026-09-16 (Asia/Shanghai)

## Scope and evidence boundary

This review reads the synchronized innovation files under
`work/remote_innovation_20260915/` and `work/agents/`. It is a novelty and
rejection-risk review, not a GPU result analysis. The current scientific
state remains:

`NO_METHOD_SELECTED`

`novelty_authorization=NONE`

`new_method_validated=false`

The review treats the following as established project evidence: the original
GRC selection story is heavily overlapped by GIM-World, Mem-World/W-VMem, and
Future Forcing; S99 found that low-disagreement block updates did not beat the
confidence-gain control; and the saved-data analysis has source-identity and
post-selection confounding. None of those facts proves that every geometry-risk
idea is impossible. They do rule out presenting the original GRC story as
already novel or already effective.

## Reviewer decision in one paragraph

If submitted today as “GRC-Memory: geometry-risk-calibrated fixed-budget
memory selection,” I would recommend **Reject and Pivot**. The title-level
mechanism combines axes already occupied by recent work, and the project's
own fixed-budget audit did not show a stable advantage over a simple confidence
control. The only potentially independent contribution is a narrower
problem definition: whether history-only, source-provenance-aware conflict
signals can predict a signed change in future RGB-D/pose loss for the actual
world-model consumer under matched budget and compute. That is currently a
**Borderline research question**, not a method result. It needs one frozen
held-out protocol before any architecture or training is justified.

## Rejection-risk matrix

Scores are reviewer estimates, not measured performance. Novelty and
scientific value are potential scores; feasibility is for the next
discriminating experiment on the available H800 setup.

| Direction | What it actually claims | Nearest overlap | Main rejection risk | Novelty potential | Science value | Feasibility | Verdict |
|---|---|---|---|---:|---:|---:|---|
| Original GRC-Memory | Geometry risk + future value + fixed budget selector | GIM-World; Mem-World/W-VMem; Future Forcing | Recombination of occupied axes; S99 did not beat confidence | 3.5/10 | 7.0/10 | 6.0/10 | Reject as current main method |
| Inconsistency/error-correlation weighting | Correlated systematic errors matter more than visit count or individual confidence | GIM-style conditional selection; geometry/visibility controls | “Error correlation” may be a renamed confidence, overlap, or pose signal; needs residualized test | 6.5/10 | 8.0/10 | 6.5/10 | Best method candidate, unverified |
| CVaR/tail-risk selector | Optimize worst future geometric failures rather than mean utility | Risk-averse submodular optimization; existing memory selectors | If future errors are not heavy-tailed, CVaR adds no mechanism; metric substitution alone is weak | 5.5/10 | 7.5/10 | 7.0/10 | Secondary candidate and diagnostic |
| Memory invalidation/revision | Later conflict can revoke or downgrade stale geometry | AnchorWeave-style local memory; stale-memory/retrieval repair literature | Generic cache eviction or dynamic-object filtering can explain it; novelty requires a distinct state transition and held-out gain | 5.5/10 | 8.0/10 | 6.0/10 | Conditional method candidate |
| Write-time admission | Do not commit a geometry item until multi-view consistency passes | Geometry confidence/visibility gating; SLAM map admission | Ordinary quality gate; coverage loss may explain apparent gain | 4.5/10 | 6.5/10 | 8.0/10 | Baseline/control, not headline |
| Confidence-weighted conflict arbitration | Replace raw z-buffer with conflict-aware arbitration | Geometry fusion, confidence fusion, AnchorWeave | Looks like engineering interpolation; no new problem definition | 3.5/10 | 6.0/10 | 8.0/10 | Do not headline |
| SOCF-A | Counterfactual source-conflict direction plus abstention | CUE-R intervention logic; ViewRope/SplaTAM overlap controls | Source identity, replay noise, and conflict may be proxy variables; causal wording can trigger rejection | 7.0/10 | 8.0/10 | 5.5/10 | Strongest falsification candidate |
| FVR | Residual future-value score after calibrated geometry risk | Utility-oriented visual evidence selection; Future Forcing | Residual can collapse to ordinary relevance/utility gating or leak future labels | 5.0/10 | 7.0/10 | 4.5/10 | Hold until SOCF evidence exists |
| DLV | Dynamic landmark validity state with abstention on leave/revisit transitions | ReWorld pose-indexed landmark memory; visibility/recency gates | No qualified dynamic revisit data; validity may equal conflict or recency | 6.0/10 | 7.5/10 | 4.5/10 | Conditional on data qualification |
| FGB-Future | Benchmark future geometric benefit of remembered evidence | R2M-Bench MemoryGain/NMR; Echo-Memory | Benchmark may be seen as a metric rename unless it exposes a reproducible failure omitted by existing benchmarks | 7.0/10 | 8.5/10 | 6.0/10 | Strongest problem/benchmark route |
| Ghosting causal decomposition | Separate geometry error, selection error, and condition mixing | Echo-Memory multi-branch evaluation; diffusion mode-interpolation work | Could remain a dataset-specific diagnostic and not a method | 6.0/10 | 8.0/10 | 7.0/10 | Essential diagnostic, not standalone method |
| Geometry-appearance interaction | 2x2 intervention explains why MSE improves while ghosting remains | Perceptual-distortion and condition-mixing literature | Interaction term alone is a statistical diagnostic, not a new algorithm | 5.5/10 | 7.5/10 | 8.0/10 | Run early; use to choose the method |

## Which directions are genuinely distinct?

### 1. Error-correlation structure

This is the cleanest possible method distinction among the current choices.
The claim is not “low geometric risk is good.” That claim was not supported by
S99. The narrower claim is:

> Two memory items can have similar marginal geometry error, but their
> correlated residuals can create a systematic future failure when consumed
> together.

This differs from GIM-World’s information/coverage selection and from
Mem-World’s future-conditioned nonredundancy because the object is the
**joint residual structure**, not coverage or relevance. It also differs from
ordinary confidence gating only if the residual correlation adds predictive
information after controlling confidence, pose distance, visibility, overlap,
coverage, and utility.

The required test is a residualized held-out prediction test, not a better
ranking picture. Fit or compute the correlation signal from history only, then
ask whether it predicts the signed future loss of a fixed-budget replacement.
If its incremental predictive value is zero, this direction is dead.

### 2. SOCF-A: conflict direction plus abstention

SOCF-A is more method-like than plain risk weighting because it makes a
decision under uncertainty: replace only when the estimated direction of the
source conflict is stable; otherwise abstain. Its possible contribution is the
**abstention rule**, not the words “counterfactual” or “source conflict”.

The closest threats are CUE-R for intervention language, ViewRope/SplaTAM for
geometric relevance and overlap controls, and existing cache gating for
abstention. The only defensible gap is a source-provenance-aware rule whose
history-only signal predicts future geometric loss in the actual consumer,
with the complete downstream path recomputed.

The main rejection trigger is causal overclaiming. An F11-F00 output change
shows influence. It does not show positive benefit. A source-ID change caused
by z-buffer competition must be reported, not hidden. If SOCF cannot beat
replay noise and matched non-SOCF controls, it becomes a negative evaluation.

### 3. FGB-Future: future geometric benefit as an evaluation problem

This is the strongest new-problem route. R2M-Bench and Echo-Memory make it
possible to argue that replay fidelity, current reconstruction, and memory
compactness are insufficient proxies. FGB-Future would define a reproducible
contract for asking whether remembered evidence improves an unseen future
geometric state under fixed context and compute.

However, the benchmark is only independent if it exposes a failure mode that
existing revisit-memory metrics cannot see, such as signed source-level benefit,
future depth/pose consistency, or a controlled geometry-versus-appearance
interaction. Calling a new score “future benefit” is not enough. The benchmark
needs an adversarial example, fixed data split, leakage audit, strong
baselines, and independent implementation.

### 4. DLV: dynamic validity and re-observation

DLV has a potentially meaningful setting difference: a memory item can be
valid before a dynamic change and invalid after the scene changes, then become
valid again after a later observation. This is more specific than generic
staleness. The problem is data. Without an auditable RGB-D/pose sequence with a
real leave/change/revisit event, DLV cannot be tested and should remain a
conditional idea.

## Directions that should not be the paper headline

Plain fixed-budget geometry-aware selection, ordinary confidence/visibility
gating, raw z-buffer replacement, generic stale-memory rejection, object-level
memory, Fisher/MI-only selection, and “conformal geometry memory” are too
close to existing components or too easy to explain as standard controls.
They can appear in the baseline matrix or ablations. They should not be
presented as the contribution.

CVaR is useful, but it is currently a **risk objective**, not a complete
method. It becomes interesting only if the future-error distribution is
demonstrably heavy-tailed and the tail improvement survives matched compute,
coverage, and confidence controls. Otherwise it is a metric substitution.

The M1–M8 ghosting mechanisms are valuable because they can identify the
failure cause. The strongest immediate diagnostic is the geometry/appearance
2x2 plus late-trajectory variance or cross-view consistency. A diagnostic
becomes a paper contribution only if it reveals a stable failure regime and
leads to a method that fixes that regime across scenes and consumers.

## Recommended primary hypothesis

Use the following as the current primary hypothesis, pending a frozen
held-out contract:

> **H1 (joint-conflict hypothesis):** Under a fixed candidate pool, source
> budget, generator, random state, and complete consumer path, a history-only
> estimate of correlated source-geometry conflict predicts the signed future
> RGB-D/pose loss of a memory replacement beyond pose distance, recency,
> visibility/coverage, confidence, and utility baselines. A selective policy
> that replaces only when the conflict direction is stable and otherwise
> abstains reduces the worst-tail future geometric loss without reducing
> valid coverage.

This hypothesis is deliberately stronger than “our selector looks better” and
easier to kill. It contains two separate claims:

1. **Prediction:** the conflict signal has incremental held-out predictive
   value.
2. **Decision:** the abstaining policy improves fixed-budget future loss.

The first claim must be tested before training or tuning a selector. If the
prediction claim fails, do not rescue the decision claim with a more complex
network.

## Minimum decisive experiment

Freeze before reading held-out future RGB-D/depth/pose:

1. Candidate pool, source IDs, query cameras, history-only features, budget,
   seeds, generator checkpoint, diffusion steps, and compute accounting.
2. Primary metric: paired future depth AbsRel plus p90 or CVaR tail loss;
   secondary metrics: pose/reprojection error, valid coverage, source-ID
   changes, abstention rate, forward count, and memory/latency cost.
3. Controls: recent, random, pose-distance, coverage/visibility,
   confidence-only, utility-only, GIM-style coverage/MI, and raw-context
   matched-capacity baseline.
4. Prediction seal containing masks, selected IDs, scores, and output hashes.
   Only then open future RGB-D/depth/pose answers.
5. Independent recomputation of one complete query from the sealed outputs.

Predeclared kill criteria:

- no qualified held-out RGB-D/pose data or any future information enters
  selection;
- conflict score adds no held-out predictive value after controls;
- SOCF-A cannot exceed exact-replay variation;
- policy gains come only from lower coverage, fewer forwards, altered source
  identity, or unequal update magnitude;
- tail improvement disappears under a fixed full-GT denominator;
- static revisits regress beyond the frozen tolerance;
- a simple overlap, visibility, confidence, pose, or coverage control matches
  the method;
- the result appears only in one scene or one consumer.

## Final recommendation to the root agent

Run the next work in this order:

1. Complete the data-qualification and implementation gates.
2. Run the geometry/appearance interaction diagnostic to determine whether
   ghosting is a geometry, selection, or mixing failure.
3. On qualified held-out data, test the incremental prediction part of H1.
4. Only if H1 survives, run SOCF-A abstention against all frozen controls.
5. Keep FGB-Future as the companion evaluation contribution if it exposes a
   failure missed by R2M-Bench/Echo-Memory.
6. Keep CVaR as a tail metric or secondary ablation unless it demonstrates a
   real heavy-tail mechanism.
7. If H1 fails, pivot to a negative evaluation/benchmark paper and do not
   add modules to preserve the original GRC story.

This review does not authorize a method claim, a novelty claim, or a
publication prediction. It identifies the smallest path that could earn those
claims through evidence.

