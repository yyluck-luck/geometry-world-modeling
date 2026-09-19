# Innovation Rotation 3: Counterfactual Provenance and Tail-Risk Abstention

**Date:** 2026-09-16 (Asia/Shanghai)  
**Role:** bounded innovation search and falsification design  
**Status:** candidate hypotheses only; `novelty_authorization=NONE`, `new_method_validated=false`, `NO_METHOD_SELECTED`.  
**GPU status:** no formal GPU experiment was launched by this rotation.

## Scope and question

The project asks whether long-horizon geometry memory can preserve future RGB-D/pose state after viewpoint change and occlusion. The narrow question for this rotation is:

> After controlling for surprise, uncertainty, pose distance, ray relevance, coverage, and context quality, is there any source-level counterfactual effect or tail-risk/abstention mechanism that remains an independent research contribution?

Here, **surprise** means history-only novelty or residual change; **uncertainty** means history-only predictive spread/confidence; **pose distance** is relative camera translation/rotation; and **ray relevance** is the pre-intervention projected support overlap with the target query rays. These controls must be computed before opening future answers.

## Evidence qualification before any claim

The existing S100 score schema contains 144 rows with `coverage`, `valid_only_absrel`, `delta1_all_gt`, and paired arm labels, but no fields for surprise, uncertainty, pose distance, ray relevance, or future-loss labels. The schema check therefore returns `NOT_IDENTIFIABLE_FROM_S100_SCHEMA`. S100 cannot establish novelty after these controls. Its near-zero paired benefit and sign reversals remain descriptive only.

Evidence receipt: `work/agents/innovation_round3_counterfactual_data_check.json`.

## Primary-source pressure test

1. **Video World Models with Long-term Spatial Memory (NeurIPS 2025)** uses geometry-grounded spatial and episodic memory, surfel/point-map storage, and retrieval for revisit consistency. It evaluates long-horizon consistency, but does not estimate the signed downstream effect of one source after a complete source intervention. [NeurIPS paper](https://proceedings.neurips.cc/paper_files/paper/2025/file/467655d26fcc207bca08915dc91964c6-Paper-Conference.pdf)
2. **Spatia: Video Generation with Updatable Spatial Memory (CVPR 2026)** maintains an explicit 3D point cloud, renders a scene projection video, and retrieves reference frames. Its closed-loop revisit metrics and memory ablations are strong controls, but they do not provide a source-level counterfactual or a geometry-tail risk/coverage guarantee. [CVPR paper](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhao_Spatia_Video_Generation_with_Updatable_Spatial_Memory_CVPR_2026_paper.pdf)
3. **Long-Context State-Space Video World Models (ICCV 2025)** addresses long memory through a block-wise SSM plus local attention; its distinction is architecture and efficiency, not source provenance or selective abstention. [ICCV paper](https://openaccess.thecvf.com/content/ICCV2025/papers/Po_Long-Context_State-Space_Video_World_Models_ICCV2025_paper.pdf)
4. **Future Forcing (2026 preprint)** uses a future-query proxy to score and merge KV tokens under a fixed cache budget. This occupies future-aware cache selection, but its object is AR temporal KV compression rather than a 3D source intervention whose complete consumer path is recomputed. [Paper](https://arxiv.org/abs/2605.30083)
5. **GIM-World (2026 preprint)** uses camera-queryable geometry supervision and information-guided pruning with a fixed cardinality budget. This occupies geometry-aware implicit memory and MI-like pruning; it does not test a source's signed future effect after residualizing ray relevance and uncertainty. [Paper](https://arxiv.org/abs/2606.02436)
6. **Selective Regression under Fairness Criteria (ICML 2022)** formalizes abstention and risk/coverage trade-offs, including calibration conditions. It is a methodological control for abstention, not a geometry-memory contribution. [ICML paper](https://proceedings.mlr.press/v162/shah22a.html)
7. **R2M-Bench (2026 preprint)** demonstrates that absolute revisit similarity can be confounded by slow or unchanged rollouts and proposes gap-matched relative consistency. Any project result must use this kind of relative calibration or an equivalent control. [Paper](https://arxiv.org/abs/2608.27328)
8. **Risk-averse submodular optimization** supplies a mathematical CVaR precedent, so CVaR alone cannot be a novelty claim. [Zhou & Tokekar](https://arxiv.org/abs/1807.09358)

**Reviewer implication:** provenance-aware intervention and geometry-tail evaluation are not automatically new; their only possible independent increment is an out-of-sample, source-level, future-state result that survives the listed controls and matched baselines.

## Candidate hypotheses

### H1 — Residualized source counterfactual effect

**Claim to test:** for a source `h_i` selected during ordinary operation, deleting/replacing only `h_i` while recomputing all descendants changes future geometric loss in a source-localized way, and the signed effect is predictable from history-only source conflict after controlling for surprise, uncertainty, pose distance, ray relevance, coverage, source age, and context quality.

Let `Y(h_i)` and `Y(h_i^-)` be complete consumer outputs under the original and predeclared replacement conditions. Define `tau_i = L_geo(Y(h_i)) - L_geo(Y(h_i^-))`. Fit a cross-fitted residual model on calibration trajectories:

`tau_i = f(conflict_i, surprise_i, uncertainty_i, pose_i, ray_i, coverage_i, age_i, quality_i) + epsilon_i`.

The novelty-relevant test is the incremental out-of-sample contribution of `conflict_i` over a control-only model containing all nuisance variables. Report paired future depth AbsRel, pose/reprojection error, provenance-change localization, and exact-replay variance.

**Nearest-work difference:** unlike NeurIPS 2025 spatial memory, Spatia, Future Forcing, and GIM-World, the estimand is a *signed source intervention effect* with the target source's downstream latent/attention/output descendants recomputed. This is a measurement protocol first; it becomes a method only if a history-only score predicts the effect and improves a policy.

**Cheapest falsification:** after Gate 0, use one fixed candidate pool and one source per query. Run three exact replays for `F11` and `F00`, then a single cross-fitted control-vs-control+conflict regression on sealed development trajectories. No selector training is needed. Open held-out future RGB-D/pose only after intervention hashes and scores are sealed.

**Kill criteria:**
- `F11-F00` is no larger than exact-replay variation;
- conflict adds no held-out predictive value (predeclared delta-R² or paired loss threshold);
- localization is no better than area/shape/edge-density-matched masks;
- effect disappears after ray relevance or uncertainty matching;
- effect changes sign under source-preserving placebos;
- source identity or complete downstream recomputation cannot be audited.

**Potential reviewer score:** novelty 7.5/10, value 8.5/10, feasibility 5.5/10, near-work risk 7/10. Verdict: strongest scientific falsification candidate, not yet a method.

### H2 — Correlated-error tail amplification

**Claim to test:** two memory sets matched on individual geometry quality can differ in future tail loss because their residual errors are correlated over the same support. The correlation statistic predicts p90/CVaR future geometric failures beyond surprise, uncertainty, pose, ray relevance, coverage, and confidence.

For a set `S`, estimate history-only residual covariance `C_S` over overlapping projected rays. Compare matched sets with similar marginal risk and ray coverage but different `||C_S||` or average pairwise residual correlation. The key prediction is:

`E[CVaR_α(L_future) | high correlation] > E[CVaR_α(L_future) | low correlation]`

at equal budget and coverage, even when mean marginal risk is matched.

**Nearest-work difference:** GIM-World's information-guided pruning and Mem-World's non-redundant retrieval target information/coverage or rendering redundancy; Future Forcing targets future query attention in a KV cache. H2 targets *joint estimator-error dependence*, a different object. CVaR itself has prior optimization theory, so only the geometry-memory failure regime and evidence can support an independent contribution.

**Cheapest falsification:** before any training, construct matched pairs from development trajectories using the same candidate pool and `k`. Compute correlation/coverage scores from history only; use one baseline consumer forward per set if saved outputs are unavailable. The decisive statistic is whether correlation retains incremental rank/predictive value after matching and residualization. If not, no tail-risk method should be built.

**Kill criteria:**
- heavy-tail evidence is absent (CVaR and mean rank the same sets);
- correlation is explained by pose, ray overlap, uncertainty, or coverage;
- matched sets cannot be constructed without changing budget or source count;
- high-correlation sets do not worsen future p90/CVaR;
- a coverage/diversity/confidence baseline matches the effect;
- tail gains come from lower valid coverage or a smaller denominator.

**Potential reviewer score:** novelty 7.0/10, value 8.0/10, feasibility 6.5/10, near-work risk 7/10. Verdict: plausible mathematical core for SOCF, conditional on a real heavy-tail signal.

### H3 — Calibrated abstention under fixed future-state risk

**Claim to test:** when the history-only conflict direction is uncertain, abstaining from a memory replacement (retain baseline or request re-observation) yields a better risk–coverage curve for future geometry than confidence-only, uncertainty-only, pose-only, ray-relevance-only, or generic cache gating, at the same source budget and compute.

Define an abstention score `a_i` from calibration-only conflict uncertainty and a predeclared cost `c_abstain`. Evaluate selective risk:

`R(κ) = E[L_future | accepted at coverage κ] + c_abstain(1-κ)`.

The required primary comparison is area under the risk–coverage curve and p90/CVaR at matched coverage, not the best point chosen after reading held-out results.

**Nearest-work difference:** ICML selective regression supplies the abstention formalism; existing spatial memories and stale-memory gates supply domain controls. The possible difference is a *geometry-specific abstention contract* tied to source provenance and future RGB-D/pose loss, with explicit re-observation semantics. Without a future-state benefit, this collapses to ordinary confidence gating.

**Cheapest falsification:** use frozen calibration scores and one held-out trajectory family. Produce a predeclared risk–coverage table for five policies: confidence, uncertainty, pose, ray relevance, and conflict-abstention. No model training is required; only the same consumer outputs and held-out answer scoring are needed.

**Kill criteria:**
- conflict abstention does not dominate confidence/uncertainty at any matched coverage;
- improvement is only due to dropping hard rays or lowering coverage;
- abstention cost is tuned after held-out outcomes;
- static revisits regress beyond tolerance;
- one generic gate matches the risk–coverage curve;
- no auditable re-observation action exists.

**Potential reviewer score:** novelty 6.5/10, value 8.0/10, feasibility 7.0/10, near-work risk 8/10. Verdict: useful policy test; high risk of being ordinary selective prediction unless source provenance adds measurable incremental value.

## Decision and next action

1. Do **not** claim any of H1–H3 as a validated method.  
2. Preserve the current Gate 0 boundary and do not read held-out answers early.  
3. After Gate 0, test H1's replay/noise and incremental prediction first. If H1 fails, run H2's matched-tail diagnostic only if the future-error distribution is heavy-tailed. Run H3 only if a real abstention/re-observation operation is available.  
4. Keep the dedicated innovation rotation active, but rotate to a new bounded question after this report; do not repeat the same literature search without a new falsification target.

## Source and evidence boundary

- Source retrieval was done in English against primary paper pages/PMLR/OpenReview/CVF/arXiv records on 2026-09-16.
- Existing S100 evidence is saved-data retrospective evidence, not an independent held-out result.
- The schema check intentionally read field names only and performed no model inference and no future-GT read.
