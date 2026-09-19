# Innovation Direction Discriminating Experiments

Date: 2026-09-16 (Asia/Shanghai)

Status: experimental design only. No GPU job was run, no new data was read, and no
candidate has been validated. The project remains
`new_method_validated=false`, `novelty_authorization=NONE`, and `NO_METHOD_SELECTED`.

## 1. Scope and proposal alignment

The proposal asks whether a world model can maintain long-horizon geometric
consistency in dynamic 3D/4D scenes. The current evidence says that lower RGB
MSE can coexist with ghosting, so RGB reconstruction error cannot be the sole
claim of geometric improvement. The decisive question for the next stage is:

> Can a history-only signal identify which memory evidence will help or harm an
> unseen future RGB-D/pose query, under the same candidate pool and the same
> real computation budget, and can the full consumer preserve that advantage?

All experiments below use the same data contract:

* `CALIBRATION_ONLY` trajectories are used to choose thresholds or fit a risk
  map.
* `HELD_OUT_TEST` trajectories are never used for feature, threshold, baseline,
  or method selection.
* The selector sees only past RGB-D, camera intrinsics/extrinsics, timestamps,
  source IDs, and its declared history-only features.
* Future RGB, depth, pose, and masks are opened only after prediction artifacts
  are sealed.
* Every method receives the same candidate pool, output count, memory slots or
  tokens, forward budget, generation steps, random seeds, and resolution.
* Results are summarized per trajectory and per future query; pixels are not
  independent experimental units.

The first TUM RGB-D route should be treated as a qualification route. It is
acceptable for it to produce a null result or a data-contract failure. It
cannot silently replace the proposal's dynamic 3D/4D target if the trajectory
does not contain auditable temporal change or return events.

## 2. Triage of surviving directions

| ID | Direction | Role | Cheapest valid test | Kill condition |
|---|---|---|---|---|
| D1 | FGB-Future | New evaluation problem / benchmark candidate | History-only score prediction of future RGB-D/pose loss | No incremental prediction over pose, coverage, confidence, and utility controls |
| D2 | SOCF | Method candidate: source-conflict abstention | Predict conflict, then compare abstain/update under fixed budget | No conflict prediction, no future gain, or simple visibility gate matches it |
| D3 | Disagreement-weighted revision | Method candidate: weight contradictory evidence down and invalidate stale memory | Offline same-source conflict and leave/revisit replay | Error does not correlate with repetition, or revision loses coverage without reducing future error |
| D4 | CVaR memory policy | Risk objective candidate | Re-rank identical candidates and compare tail loss | No heavy tail, or CVaR does not improve worst-query/CVaR under matched cost |
| D5 | Ghosting mechanism decomposition | Mechanism/measurement candidate | Frame-internal ghost-region tests and condition-mixing controls | Predicted mechanism does not separate ghosting from ordinary misregistration/blur |
| D6 | DLV dynamic landmark validity | Conditional dynamic-scene candidate | Leave-return event with validity decay and re-observation | No auditable dynamic change/return event, or static performance degrades |
| D7 | EC2 heterogeneous-cost selection | Secondary systems candidate | Equal-FLOP rather than equal-slot sweep | Curves overlap after exact FLOP matching |
| D8 | Source intervention | Causal protocol supporting D1-D3 | Delete/replace one source with fixed exogenous state | Effect is below replay noise or not localized to the source support |

D1 and D5 are valuable even if no method survives. D2-D4 and D6 are methods
only if their predeclared predictions survive all controls. D8 is a mechanism
test, not an independent contribution by itself.

## 3. D1: Future-Geometric-Benefit (FGB-Future)

### Hypothesis

A history-only conflict/risk signal predicts signed future geometric benefit or
harm better than existing relevance signals. The signal must be useful on an
unseen future query, not merely correlate with current reconstruction quality.

### Cheapest experiment

Run a selector-free scoring evaluation on the same frozen candidate pool:
`recent`, `random` (five fixed seeds), `pose-distance`, `coverage/visibility`,
`confidence`, `depth-only`, `utility-only`, and the proposed conflict/risk
score. Do not change the world-model consumer yet. For each candidate, record
the history-only score before prediction seal. After sealing, compute the
future target loss and signed loss relative to the matched alternative.

### Variables and controls

* Independent variable: one frozen history-only score at a time.
* Dependent variables: future capped depth `AbsRel`, `Delta1`, pose/reprojection
  error, RGB perceptual error, ghost-area rate, and signed benefit.
* Controls: same source ID, candidate count, pose/FoV, visible support, number of
  valid depth pixels, forward count, and random seed where possible.
* Required strata: occlusion, return/revisit, large viewpoint change, static
  scene, and dynamic-change event.

### Primary metrics

Report trajectory-level paired differences, mean and median future AbsRel,
worst 5% query loss and CVaR, plus out-of-sample partial Spearman correlation
and AUROC for future conflict/harm. Calibration is reported separately as
nominal 0.8/0.9 coverage versus empirical coverage.

### Success gate

At least 30 held-out query units from at least 10 independent trajectories are
preferred for a final claim. At the main budget, the proposed score must improve
future mean AbsRel by at least 1% relative to the strongest non-proposed control,
with a trajectory-bootstrap 95% lower bound above zero. Partial AUROC must
exceed the strongest control by at least 0.05. These are screening thresholds,
not guarantees of publication.

### Kill criteria

Stop the method interpretation if future information enters the selector;
calibration/test identities overlap; the partial interval crosses zero; current
reconstruction improves while future depth or pose worsens; or a pose,
visibility, confidence, or utility-only score reaches the same result. Preserve
FGB-Future as an evaluation/negative-result protocol if it remains measurable.

## 4. D2: Source-Conflict Abstention (SOCF)

### Hypothesis

When two source memories disagree in a shared support region, refusing to merge
or consume the conflict is safer than blindly averaging or selecting by
confidence. The claim is specifically about source-level conflict and
abstention, not generic geometry-aware retrieval.

### Cheapest experiment

Use the same candidate pool and consumer for four policies:

1. strongest frozen non-SOCF baseline;
2. SOCF with conflict score and `keep`;
3. SOCF with conflict score and `abstain` or `re-observe`;
4. oracle conflict mask only as an upper bound, never as a deployable method.

Start with a small source-level replay before full generation. Delete or replace
one source item while keeping prompt, camera path, non-target memory, external
noise, seed, and initial pre-intervention state fixed. Recompute all downstream
states affected by the target source.

### Variables and controls

* Independent variable: policy action (`keep`, `abstain`, `replace`, or
  baseline) and conflict threshold fixed on calibration.
* Dependent variables: source overwrite rate, conflict-region IoU, future depth
  error, pose/reprojection error, ghost-area rate, coverage, and compute.
* Controls: exact candidate pool, `k=2,4,8`, source identity, token/slot count,
  memory bytes, forward count, generation steps, and five fixed random seeds.

### Success gate

Conflict prediction must beat the strongest non-SOCF predictor by AUROC >= 0.05
and pass the predeclared calibration tolerance. At `k=4`, the full consumer must
improve future mean AbsRel by >=1% relative with a non-crossing trajectory
bootstrap lower bound, while worst-5%/CVaR does not worsen by >5%. Removing the
conflict feature or abstention action must cause an interpretable degradation.

### Kill criteria

Stop if conflict prediction is no better than overlap/visibility; abstention
only improves coverage; source-intervention direction is inconsistent on most
trajectories; conflict IoU is below the predeclared threshold; or compute is
not matched. If it passes only the replay mechanism test but not future loss,
downgrade to a causal diagnostic.

## 5. D3: Disagreement-Weighted Revision and Invalidation

### Hypothesis

Repeated observation should increase trust only when observations agree.
Repeatedly observing a systematic geometric error should reduce trust or trigger
invalidation. This combines IDEA-1's disagreement weighting with IDEA-3's
revision semantics; they should not be presented as two separate inventions.

### Cheapest experiment

For each source/surfel or memory cell, compute:

* visit count;
* pairwise depth disagreement after projection;
* reprojection residual;
* visibility conflict;
* confidence and coverage controls.

First test the diagnostic prediction that visit count is not a reliable proxy
for accuracy and that disagreement predicts future error after matching coverage
and scene region. Then replay the same candidate pool with three policies:
`count-weighted`, `disagreement-weighted`, and `disagreement-weighted +
invalidation`. The invalidation threshold is chosen on calibration and frozen.

### Variables and controls

* Independent variable: evidence update rule.
* Dependent variables: future capped AbsRel, reprojection error, ghost-area
  rate, valid support coverage, memory size, and update latency.
* Controls: same candidate identities, source count, map resolution, token/slot
  budget, visibility support, and return/revisit strata.

### Success gate

Disagreement must add out-of-sample predictive information after visit count,
coverage, confidence, pose, and region controls. The revision policy must reduce
future geometric tail error without a coverage collapse; report the full
coverage-error curve. The sign must hold in both leave-revisit and non-revisit
strata, or the claim is restricted to the stratum where it holds.

### Kill criteria

Kill if disagreement is explained by coverage or scene identity; if count is
already as predictive; if invalidation merely removes useful coverage; if the
best threshold changes after test results; or if the effect appears only in
saved-data retrospective analysis and not in an unseen split.

## 6. D4: CVaR Memory Policy

### Hypothesis

Mean-risk selection can hide rare catastrophic geometric failures. A policy that
optimizes a calibrated tail objective can reduce worst-query future error under
the same memory and compute budget.

### Cheapest experiment

Do not train a model. On the identical candidate pool, compute `coverage-greedy`
or the strongest existing selector and a sequential CVaR policy for
`k=2,4,8`. Use a fixed calibration loss distribution and evaluate only once on
held-out queries. If the empirical future-loss distribution has no meaningful
tail, do not continue this direction.

### Variables and controls

* Independent variable: objective (`mean`, `CVaR_0.8`, `CVaR_0.9`) with the
  same selection features and budget.
* Dependent variables: mean, median, 90th percentile, worst-5%, CVaR, coverage,
  and wall time/FLOPs.
* Controls: identical candidate pool, random seeds, source IDs, `k`, token
  budget, and consumer.

### Success gate

The tail policy must reduce predeclared worst-query/CVaR without a material
mean-loss or coverage penalty, and the effect must remain under equal FLOPs.
Tail improvement alone is insufficient if it comes from discarding most
support.

### Kill criteria

Kill if the loss distribution is light-tailed; CVaR and mean produce the same
ordering; tail gains disappear after matching coverage; or the result depends
on selecting the favorable alpha or budget after seeing test outcomes.

## 7. D5: Ghosting Mechanism Decomposition

### Hypothesis

The observed MSE decrease with persistent ghosting may arise from posterior
mean/mode interpolation or soft condition mixing, rather than improved geometry.
The experiment separates geometry error, condition ambiguity, and generation
mixing.

### Cheapest experiment

Use saved latent/trajectory artifacts if and only if they are present and
hash-verified; otherwise record unavailable and do not claim execution. Compare
ghost regions with clean regions within the same output frame:

* late-step `x0` trajectory variance;
* final-step versus multi-step guidance;
* hard depth/source assignment versus soft blending;
* pixel-space versus feature/latent-space condition mixing.

The 2x2 design is `trusted geometry / perturbed geometry` crossed with
`ordinary RGB condition / geometry-constrained RGB condition`. It is a
diagnostic, separate from the future-memory-selection experiment.

### Variables and controls

* Independent variable: condition integrity and mixing location.
* Dependent variables: ghost-area rate, cross-view feature consistency,
  reprojection error, depth AbsRel, perceptual distance, and RGB MSE.
* Controls: same target, seed, denoising steps, camera path, output resolution,
  and mask area. Compare ghost versus clean regions within each frame.

### Success gate

The proposed mechanism must produce a predeclared within-frame separation and
explain the MSE/ghosting divergence. It must also survive a wrong-registration
control. A lower MSE without a lower geometric or ghosting metric is a negative
diagnostic, not a method success.

### Kill criteria

Kill the interpolation explanation if late-step variance does not differ,
hard selection is equally ghosted, pixel/latent mixing has no differential
effect, or the effect disappears after controlling for registration. Retain the
measurement lesson that MSE is insufficient if that lesson is robust.

## 8. D6: Dynamic Landmark Validity (DLV)

### Hypothesis

A landmark's historical validity should decay when the scene changes and be
restored only after a new observation confirms the landmark. This is conditional
on having a real, auditable leave-change-return event.

### Cheapest experiment

Search the qualified TUM RGB-D route for one predeclared dynamic event and one
static return event. If the data contain no suitable event, report a null
result and stop this direction. On a single valid event, compare:
`always-retain`, `pose/visibility gate`, and `validity-decay + re-observe`.
Use identical slots and source candidates.

### Variables and controls

* Independent variable: landmark state machine and re-observation rule.
* Dependent variables: return-view depth/pose error, ghost-area rate, coverage,
  false invalidation rate, and recovery latency.
* Controls: static regions, same camera path, same budget, and matched landmark
  support.

### Success gate

Validity decay must reduce return-event tail error while preserving static-region
performance and not requiring future labels at decision time. The effect must
repeat across at least two independent events before any method claim.

### Kill criteria

Kill if no auditable event exists, if static scenes degrade, if a simple
visibility/overlap gate matches it, or if thresholds require future annotations.

## 9. D7: Heterogeneous-Cost Selection (EC2)

### Hypothesis

Equal slot count is an inaccurate proxy for equal computation because memory
items have different token/FLOP/occupancy costs. Equal-FLOP selection may improve
future geometry at the same real cost.

### Cheapest experiment

For one fixed scene, sweep equal-slot and equal-FLOP selection over the same
candidate pool. Record real peak memory, forward count, selector wall time,
attention tokens, and total GPU time. This is a systems secondary result.

### Kill criteria

Kill if the equal-FLOP and equal-slot curves overlap within the predeclared
measurement tolerance, or if savings come from silently reducing output quality
or candidate support.

## 10. D8: Source-Level Counterfactual Intervention

### Role

This is the causal identification protocol shared by D1-D3, not a standalone
method. It tests whether a source actually changes the downstream future output
and whether the change is localized to the source's pre-intervention geometric
support.

### Required controls

Fix only exogenous pre-intervention conditions and non-target initial states:
prompt, camera path, external noise, RNG, retrieval identity where held fixed,
non-target memory, and other pre-intervention state. Recompute all descendants
of the target source. Freezing downstream latents would measure only a restricted
path effect, not a total effect.

### Metrics and kill criteria

Use replay noise from at least three exact replays, source-level provenance
change, support IoU, matched-mask localization, signed future loss, and placebo
mask sensitivity. Kill the mechanism interpretation if the effect is below replay
noise, source direction is unstable, localization does not beat matched-mask
placement, or a source-identity/coverage confound explains it.

## 11. Recommended execution order

1. Freeze the TUM/held-out data manifest and Gate 0 contract.
2. Run D5's saved-artifact availability audit; only execute if the raw arrays
   and hashes are present.
3. Run D1 as a low-cost selector-free predictive screen.
4. Run D8 on the smallest valid source set.
5. Only if D1 and D8 survive, run D2 SOCF in the full consumer.
6. Run D3 disagreement/revision as a same-pool ablation, not as a new branch
   before the baseline is frozen.
7. Run D4 CVaR only if the loss distribution is demonstrably heavy-tailed.
8. Run D6 only if a qualified dynamic leave-change-return event exists.
9. Run D7 as a secondary equal-FLOP systems analysis.
10. Run the final cross-scene and seed expansion only for directions that pass
    their cheap screen.

This ordering prevents an attractive positive signal from being promoted before
the proposal's actual future-geometry question and the strongest ordinary
explanations have been tested.
