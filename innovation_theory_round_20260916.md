# Innovation Theory Round: Promising Directions for Long-Horizon Geometric Consistency

Date: 2026-09-16 (Asia/Shanghai)

Role: independent theory and reviewer-style comparison. This file is a research
decision aid, not a novelty certificate, a method result, or a GPU result.

Current project state remains:

```text
new_method_validated = false
novelty_authorization = NONE
```

The original proposal asks whether a dynamic 3D/4D world model can preserve
object position, depth, and camera geometry after a long interval, viewpoint
change, and possible occlusion. The present engineering state provides a real
H800 CUT3R component forward, but not a qualified held-out VMem/GRC result.
The saved S91R-C analysis is descriptive and non-causal: source identity
matching was only about 4.35--5.49%, while the all-new consumer became worse
on mean future AbsRel. It therefore cannot validate a selector.

## 1. Reviewer criteria

Scores are conditional potential scores on a 1--10 scale:

- Novelty potential: can the mechanism be an independent contribution after
  near-neighbor controls?
- Scientific value: does it answer an important unresolved question?
- Falsifiability: can a small, pre-registered experiment kill it?
- Feasibility: can the current VMem/VMem-consumer stack test it on H800?
- Near-neighbor risk: how likely a reviewer is to collapse it into an existing
  selector, gate, memory, or evaluation method? Higher is worse.

The scores are not current achievement scores. A candidate remains inactive
until it passes leakage, source-identity, fixed-budget, and held-out gates.

## 2. Comparative scorecard

| Rank | Candidate | Novelty | Value | Falsifiability | Feasibility | Near-neighbor risk | Reviewer verdict |
|---:|---|---:|---:|---:|---:|---:|---|
| 1 | FGB-Future: future-state geometric benefit as an evaluation problem | 8.0 | 9.0 | 9.0 | 7.5 | 5.5 | Strongest evaluation-first route; can survive method failure |
| 2 | SOCF-A: source-conflict prediction with abstention | 7.5 | 8.5 | 8.5 | 6.5 | 7.0 | Best method candidate, but only after causal source intervention |
| 3 | Correlated-error-aware memory selection | 8.0 | 8.5 | 7.5 | 6.5 | 7.0 | Most interesting mechanism inside SOCF; must beat coverage/diversity |
| 4 | Counterfactual source effect and signed future benefit | 8.5 | 8.5 | 8.0 | 5.5 | 6.5 | High scientific value; currently a measurement protocol more than a method |
| 5 | Ghosting mechanism decomposition | 6.5 | 9.0 | 9.0 | 8.0 | 5.0 | Highest information value per GPU hour; method claim not yet justified |
| 6 | CVaR/tail-risk memory policy | 7.0 | 8.0 | 8.0 | 6.5 | 7.0 | Promising only if future error is demonstrably heavy-tailed |
| 7 | Dynamic-landmark validity and invalidation (DLV) | 7.0 | 8.0 | 7.0 | 5.5 | 7.5 | Conditional on auditable observed change/revisit data |
| 8 | Conflict arbitration instead of unconditional blending | 6.5 | 7.5 | 8.0 | 7.5 | 8.0 | Useful engineering mechanism; high risk of being ordinary gating |
| 9 | Write-time admission control | 6.0 | 7.5 | 8.0 | 7.0 | 8.0 | Testable, but likely trades coverage for precision |
| 10 | Non-uniform-cost adaptive selection (EC2-style) | 6.0 | 7.0 | 8.0 | 7.0 | 8.0 | Good systems extension; weak as the central paper idea |
| 11 | Reliability calibration of memory-risk scores | 6.5 | 7.5 | 9.0 | 8.5 | 6.5 | Clean negative-result or benchmark companion |
| 12 | Event-gated replacement at change points (EGR) | 5.5 | 7.5 | 7.0 | 5.5 | 8.5 | Do not frame as a method before beating recency/visibility/event gates |

## 3. What each direction actually claims

### 3.1 FGB-Future: define the missing evaluation target

The claim is not “our selector is better.” It is:

> A memory system should be judged by whether history-only decisions improve
> an independently held-out future RGB-D/pose state under the same consumer,
> candidate pool, and computation budget.

This is defensible because replay similarity or current-view MSE can improve
without proving that a model remembers the world. Echo-Memory and R2M-Bench
provide direct pressure for a relative, open-domain revisit evaluation rather
than a raw replay score. The project can add geometry-specific future AbsRel,
pose/reprojection error, support localization, tail loss, coverage, and source
provenance.

Minimum test:

1. Freeze calibration trajectories and held-out trajectories separately.
2. Freeze the candidate pool, query poses, `k`, seeds, consumer, and compute
   accounting before reading held-out future answers.
3. Compare recent, random, pose, coverage/visibility, confidence, MI/GP,
   raw-context, and any proposed policy.
4. Serialize every selector decision and generated output, then open future
   RGB-D/pose only for scoring.
5. Report trajectory-level paired mean AbsRel, median, worst-5%/CVaR95,
   coverage, source overwrite, and reprojection/pose error.

Kill condition: if the protocol cannot distinguish memory policy from the raw
context or recent baseline, it is still a useful evaluation audit, but it
cannot support a new selector.

Reviewer judgement: this is the safest central scientific question because it
remains valuable if SOCF, CVaR, or GRC fails. It also aligns directly with the
proposal's long-horizon geometry objective.

### 3.2 SOCF-A: source-conflict prediction plus abstention

The proposed mechanism detects when two history sources make mutually
inconsistent geometric claims over the same support. It then chooses, replaces,
or abstains from using a conflicting source. The key distinction is not “use
geometry” but “detect a conflict that predicts the direction of downstream
future damage.”

History-only features may include:

- reprojection disagreement;
- depth residual and depth margin;
- visibility/occlusion conflict;
- source-level provenance and overwrite count;
- disagreement after conditioning on pose distance, coverage, and confidence.

Minimum test:

1. Calibrate the conflict score on development trajectories only.
2. On held-out trajectories, predict conflict and abstention without future
   RGB, depth, pose, masks, or future-validity fields.
3. Run a same-consumer source intervention: delete or replace exactly one
   source while recomputing all downstream descendants.
4. Keep prompt, query, seed, non-target memory, denoising schedule, and budget
   fixed; do not freeze descendants affected by the target source.
5. Test whether predicted conflict localizes to the provenance-changing region
   and predicts a signed future loss.

Kill condition: confidence, visibility, coverage, pose distance, or ordinary
retrieval explains the result; source identity cannot be tracked; replay
direction disagrees with future direction; or abstention has no paired future
benefit at the primary budget.

Reviewer judgement: the mechanism could be a paper contribution only after an
incremental out-of-sample result. A scalar risk score alone is not enough.

### 3.3 Correlated-error-aware selection

The strongest theoretical version of the original GRC idea is not “lower
individual risk is better.” It is:

> Two memories with similar marginal quality can have different joint value
> because their errors are correlated. Repeating a shared systematic error can
> reinforce a false surface and produce ghosting.

This differs from geometric diversity or coverage. Diversity compares input
locations or features; correlated-error selection compares residual structure.
Two spatially separated observations may still share the same estimator bias.

Minimum test:

1. Construct pairs or sets matched on marginal risk, confidence, pose
   distance, coverage, and slot count.
2. Estimate residual agreement only from history and development data.
3. Compare low-correlation and high-correlation sets in the same complete
   consumer.
4. Measure future geometric tail loss, ghosting rate, source overwrite, and
   support-localized error.

The key test is rank disagreement:

```text
coverage/MI ranking versus future-loss marginal ranking
```

If Spearman correlation is very high and the coverage-selected set is not less
reliable, this direction collapses into GIM-World-style selection. If rank
correlation is low and residual correlation predicts future damage after the
controls, it becomes a serious mechanism candidate.

Kill condition: marginal error matching cannot be achieved, correlation is
only a proxy for pose/coverage, or the effect disappears under same-region
matching.

Reviewer judgement: this is the best mathematical core for SOCF, but it should
not be presented as an independent method before the above rank and intervention
tests.

### 3.4 Counterfactual source effect and signed future benefit

For a target source `h_i`, compare complete consumer outputs under:

```text
F11: target source present with the original source
F00: target source absent or replaced by a predeclared matched source
```

The target source's descendants must be recomputed. The intervention effect is
the paired future loss difference after the prediction is sealed. A source can
have positive influence on the output while having negative future benefit, so
these must remain separate.

This direction has unusually high scientific value because it asks whether a
memory item caused a measurable change in a future state, rather than merely
correlating with it. However, it may become a measurement contribution unless
the source-level effect reveals a stable, history-only predictor that improves
the policy.

Kill condition: F11-F00 is smaller than exact-replay noise; source identity is
not preserved; localization is no better than matched mask placement; or the
effect is explained by changing total context quality.

### 3.5 Ghosting mechanism decomposition

The current observation “RGB MSE decreases while ghosting remains” should be
treated as a mechanism question, not as evidence that geometry improved.

The most useful decomposition is:

```text
geometry error
selection error
conditioning/blending error
sampling or modality-interpolation error
```

Candidate diagnostics include:

- hard selection versus soft blending;
- geometry trusted versus geometry perturbed;
- latent-space versus pixel-space mixing;
- late-step prediction variance in ghosting and clean regions;
- cross-view feature consistency and reprojection error;
- provenance-change masks and object duplication rate.

The project already has a 2x2 diagnostic skeleton and the S86/S87 warning that
MSE can hide structural artifacts. The diagnostic can be valuable even if no
new method survives. It becomes a method only if it leads to a targeted
intervention that beats the strongest architecture and selection controls.

Kill condition: all artifact variation is explained by global registration or
image quality; the 2x2 interaction is unstable; or a standard hard gate fully
removes the effect.

Reviewer judgement: highest immediate information value and lowest risk of
wasting H800 time, but likely a diagnostic/benchmark contribution unless paired
with a validated intervention.

### 3.6 CVaR and tail-risk policy

The proposed shift is from expected utility to tail protection:

```text
mean future loss  ->  CVaR_95 or worst-5% future geometric loss
```

The relevant cross-domain mathematical inspiration is risk-averse submodular
optimization. The transferable idea is that a policy can be acceptable on
average while catastrophically wrong on a small set of occlusion or revisit
queries.

Minimum test:

1. Freeze a history-only tail-risk score on development data.
2. Compare risk-neutral and CVaR policies at identical `k`, slots, forward
   count, and memory bytes.
3. Report the full risk-coverage curve, not only one selected percentile.
4. Stratify by viewpoint change, occlusion, and dynamic change.

First prerequisite: show that future geometric errors are actually heavy
tailed. If the empirical distribution is light-tailed or the same sources
always dominate both mean and tail, CVaR adds no meaningful decision rule.

Kill condition: no tail improvement, mean improvement only due to reduced
coverage, or CVaR ranking is equivalent to confidence/coverage.

Reviewer judgement: a strong secondary objective, unlikely to be the sole
contribution unless it exposes a reliable failure regime absent from existing
memory systems.

### 3.7 DLV: dynamic landmark validity and invalidation

ReWorld's pose-indexed landmark memory identifies dynamic-scene validity as an
open limitation. DLV would attach a history-only state to each stored landmark:
valid, uncertain, stale, or re-observe. The state changes only when a new
observation arrives and contradicts the stored support.

Minimum test requires at least one auditable observed-change revisit and one
static revisit. Compare DLV with pose-only, recent, coverage, confidence, and
ordinary event/transition gates under identical budgets.

Kill condition: no real observed change exists; the state is identical to
recency or visibility; dynamic labels use future frames; or static scenes
degrade beyond a frozen tolerance.

Reviewer judgement: promising but data-dependent. Do not simulate a dynamic
change and call it evidence.

### 3.8 Conflict arbitration, write admission, and non-uniform costs

These are useful submodules but weak central stories:

- Conflict arbitration replaces unconditional z-buffer or averaging with a
  confidence/provenance-aware resolution.
- Write admission prevents a surfel or memory item from entering the bank until
  enough observations agree.
- EC2-style selection prices memories by actual FLOPs, bytes, or attention cost
  rather than slot count.

Each is easy to falsify and may produce practical gains. Each also has high
collapse risk into known visibility gating, NMS, confidence weighting, or
systems optimization. Use them as controls or ablations unless a strong
mechanism result makes one indispensable.

## 4. Recommended research storyline

The most defensible sequence is:

```text
FGB-Future evaluation contract
        |
        v
Ghosting mechanism decomposition
        |
        v
Counterfactual source intervention
        |
        v
Correlated-error / SOCF-A pilot
        |
        v
CVaR tail-risk and DLV conditional extensions
```

Interpretation:

1. First establish that the proposal's future geometry target is measurable
   under legal held-out RGB-D/pose data.
2. Then identify whether the dominant failure is geometry, selection,
   blending, or modality interpolation.
3. If source intervention has a stable signed effect, test whether
   correlated-error conflict predicts it without future leakage.
4. Only after a positive pilot should CVaR or dynamic invalidation be added.

This sequence avoids a common reviewer objection: adding several plausible
modules before showing that the target failure exists and that the module is
the cause of improvement.

## 5. Final reviewer decision

The original GRC-Memory formulation remains too close to existing
geometry-aware, fixed-budget, future-aware selection work. The most promising
research object is a narrower claim:

> Under a fixed real memory and compute budget, can history-only evidence about
> source conflict and correlated geometric error predict the signed effect of
> retaining, replacing, or abstaining from a memory item on an independently
> held-out future geometric state?

This is currently a high-potential hypothesis, not a result. The primary
recommendation is to implement and freeze the FGB-Future evaluation contract
and the ghosting/counterfactual diagnostics first. SOCF-A with correlated-error
features is the leading method candidate only if it beats the strongest
non-SOCF controls and survives source-identity and leakage audits. CVaR and DLV
should remain conditional branches. If no candidate survives, the project still
has a credible path to a rigorous evaluation/negative-result paper aligned with
the proposal.

## 6. Sources and evidence used

This round was based on the project's source-checked reports and current ledger:

- GIM-World, arXiv:2606.02436
- Mem-World / W-VMem, arXiv:2606.18960
- Future Forcing, arXiv:2605.30083
- ViewRope, arXiv:2602.07854
- Spatia, CVPR 2026 Open Access
- WorldStereo, CVPR 2026 Open Access
- Echo-Memory, arXiv:2606.09803
- R2M-Bench, arXiv:2608.27328
- ReWorld, arXiv:2608.23565
- CUE-R, arXiv:2604.05467
- Utility-Oriented Visual Evidence Selection, arXiv:2605.13277
- Zhou & Tokekar, risk-averse submodular optimization, arXiv:1807.09358
- Golovin, Krause & Ray, noisy active learning with non-uniform cost,
  arXiv:1010.3091
- Blau & Michaeli, perception-distortion tradeoff, arXiv:1711.06077
- Aithal et al., mode interpolation in diffusion models, arXiv:2406.09358

The local source files consulted include:

- `work/remote_innovation_20260915/INNOVATION_SCAN_20260915.md`
- `work/remote_innovation_20260915/INNOVATION_IDEAS_20260915.md`
- `work/remote_innovation_20260915/latest/EVALUATION_AND_DATA_PLAN_20260915.md`
- `work/remote_innovation_20260915/latest/SCORING_PROTOCOL_DRAFT.md`
- `work/agents/innovation_topconf_matrix_20260915.md`
- `work/agents/innovation_redteam_continuous_20260915.md`
- `work/agents/innovation_continuous_next_20260915.md`

