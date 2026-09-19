# Innovation Round 4 — Selective Prediction, Conformal Risk, and Provenance-Aware Memory Abstention

**Date:** 2026-09-16 (Asia/Shanghai)

**Status:** literature-grounded candidate analysis; no formal GPU run, no future-GT read, `novelty_authorization=NONE`, `new_method_validated=false`.

## Research question

Can a world model decide that a historical RGB-D observation is unsafe to use, or should request a re-observation, using a calibrated estimate of *future geometry risk*? The candidate action is source-level abstention (`accept`, `ignore`, or `reobserve`) under a fixed memory/compute budget.

This must be distinguished from the weaker question “does a confidence score correlate with current reconstruction error?” The proposal requires future camera-conditioned RGB-D/pose prediction, source identity, and an independent held-out scene.

## What the primary literature already covers

1. **Conformal Risk Control (CRC).** Angelopoulos et al., ICLR 2024, extend conformal prediction to control the expected value of a bounded monotone loss with finite-sample marginal guarantees. This is a generic post-hoc risk-control framework; it does not specify memory items, source provenance, temporal state transitions, or a world-model consumer. See the official OpenReview entry: https://openreview.net/forum?id=33XGfHLtZg (accessed 2026-09-16).
2. **Conformal regression with a reject option.** Johansson, Sönströd, and Boström, PMLR 230, 2024, use difficulty estimates and Mondrian conformal regression to reject expected inaccurate predictions while retaining valid intervals for non-rejected predictions. The reject decision is instance-level and generic; it is not a source intervention in a multi-memory generative pipeline. Official paper: https://proceedings.mlr.press/v230/johansson24a.html.
3. **Uncertainty-aware CQR.** Rossellini, Barber, and Willett, AISTATS 2024, separate aleatoric and epistemic uncertainty in conformalized quantile regression and improve conditional coverage empirically. This motivates separating sensor ambiguity from geometry-estimation uncertainty, but it does not address a source-level memory action or future trajectory error. Official paper: https://proceedings.mlr.press/v238/rossellini24a.html.
4. **Risk control for generative image outputs.** Teneggi et al., ICML 2023, introduce K-RCPS for high-dimensional conformal risk control of diffusion-model samples. Their calibration concerns output intervals and image risk, rather than whether one historical source should be consumed by a future-view world model. Official paper: https://proceedings.mlr.press/v202/teneggi23a/teneggi23a.pdf.
5. **Robust conformal sets.** Zargarbashi, Akhondzadeh, and Bojchevski, ICML 2024, handle perturbations and contaminated calibration data. This is relevant because temporal/scene shift can invalidate ordinary exchangeability, but robust CP alone does not create provenance-aware memory selection. Official paper: https://proceedings.mlr.press/v235/h-zargarbashi24a.html.

The project’s existing literature audit also covers future-aware memory and geometry-conditioned retrieval. Therefore, “add a conformal threshold,” “add an uncertainty gate,” or “reject stale frames” is not an independent novelty claim by itself.

## Distinctness audit

| Candidate | Unit of action | Calibration target | Consumer/future target | Distinct from this project? |
|---|---|---|---|---|
| Generic selective regression | one input/prediction | current response loss or interval coverage | same prediction | No; use as a baseline |
| Global CRC / K-RCPS | output set/image | bounded output loss | output interval or image risk | No; use as a baseline |
| Difficulty-based conformal reject | one instance | conditional difficulty bins | rejected prediction quality | No; use as a baseline |
| Future-aware memory retrieval | memory set/frame | retrieval or future objective | future view, often without abstention guarantee | Near work; direct comparison required |
| Provenance-aware memory abstention | source item/action | source-level risk under fixed calibration | future RGB-D/pose effect of the selected memory | **Potentially distinct only if the source-level, action-level contract is demonstrated** |

The potentially distinct contribution is therefore a *measurement/problem formulation*: calibration is attached to a named memory source and an action (`accept/ignore/reobserve`), while the loss is measured on an independently held-out future state after the normal consumer path. This is not yet a method contribution. A theorem would additionally need an explicit data-assumption treatment for serial dependence, scene shift, and set-level interactions.

## Proposed candidate (conditional; do not train yet)

For source (i), compute only pre-future quantities (x_i): reprojection residual, depth consistency, visibility conflict, pose uncertainty, source age, and consumer-visible provenance. On a calibration split, define a future geometry loss (L_i^{future}) only after predictions and parameters are sealed. A split-conformal threshold (q_{1-\alpha}) can produce an abstention rule

\[
 a_i = \mathbf{1}\{s(x_i) \le q_{1-\alpha}\},
\]

but the guarantee is only valid under the stated calibration assumptions. For sequential trajectories, ordinary exchangeability is doubtful; use scene/block splits and report marginal coverage only unless a valid shift-robust method is proved and implemented.

At set level, selection is constrained by a fixed budget (k):

\[
S = \operatorname{TopK}_{i\in C}(a_i,\;u_i), \quad |S|\le k,
\]

where (u_i) is a pre-future utility score. The primary outcome is not interval coverage alone: it is future camera-conditioned geometry error (depth AbsRel, pose error, and localized reprojection error) at matched acceptance/compute cost. Set-level interaction means per-source conformal validity cannot automatically imply validity of (S); this is a central falsification point.

## Exact controls for the first legal experiment

Freeze before reading held-out future answers:

- one candidate pool (C), one RGB-D/pose timestamp rule, one history horizon, one held-out scene, and one future horizon;
- source IDs, candidate order, model/weight/source SHA, RNG/noise, inference steps, image resolution, and GPU budget;
- calibration scenes separate from the held-out scene; no future RGB/depth/pose bytes or metrics loaded before manifests and outputs are sealed;
- (k\in\{1,3,5\}) and identical token/frame/time budgets for every method;
- the same generated future targets and exact replay seeds for paired methods.

Required baselines:

1. no-memory/current-context only;
2. random selection (fixed seed, repeated);
3. recency;
4. camera-pose/FoV proximity;
5. geometry residual threshold without calibration;
6. learned/difficulty-only selective regression gate (no source provenance);
7. global CRC/conformal threshold on the same geometry score;
8. source-level calibrated abstention (candidate);
9. oracle future utility (upper bound only; never an deployable method).

Report risk–coverage curves, acceptance rate, re-observation rate, future depth AbsRel, metric/relative pose error, localized reprojection error, tail risk (CVaR at preregistered level), wall-clock, memory/token cost, and 95% paired bootstrap intervals over target instances and scenes. Include a source-ID permutation placebo and a support-area/mask-matched placebo.

## Minimum falsification experiment

This cannot be run formally until Gate 0 supplies a legal held-out RGB-D/pose scene. The following is the smallest decisive protocol:

1. Use at least two calibration scenes and one untouched held-out scene, with a preregistered future horizon (e.g., short and long). Build the candidate pool once.
2. Fit three selectors on calibration scenes only: (A) uncalibrated geometry threshold, (B) generic difficulty/conformal reject, and (C) provenance-aware source abstention. Keep (k), accepted-source fraction, and compute identical.
3. On the held-out scene, run exact paired VMem inference for each selector with common noise and all non-target inputs fixed. Read future answers only after prediction manifests are sealed.
4. Compare each selector against the same-pool baselines at matched coverage and budget. Use paired bootstrap by target sequence, not individual pixels as independent samples.
5. Run two placebos: shuffle source IDs while preserving all residual values; and replace selected sources with mask/pose/support-matched sources. A claimed provenance effect must disappear under the first placebo and exceed the second.

**Decision rule:** retain the candidate only if it reduces future geometry loss at matched coverage/cost with a confidence interval excluding zero in every preregistered horizon and in at least two held-out scenes, while calibration error remains within the preregistered tolerance. Otherwise, retain the result as a benchmark/negative finding and do not claim a method.

## Kill criteria

Stop or downgrade the candidate if any of the following occurs:

- no improvement over generic difficulty/conformal reject at matched coverage and compute;
- source-ID permutation preserves the apparent gain;
- gains vanish under support/pose-matched replacement or are explained by recency/pose proximity;
- calibration is valid only on the calibration scene but fails on the held-out scene, or temporal dependence invalidates the claimed guarantee;
- per-source scores predict historical residuals but not future geometry;
- the effect appears only in one scene, one horizon, or static scenes;
- any set-level gain disappears when source interactions are recomputed by the real consumer;
- exact-replay noise is as large as the claimed effect;
- the candidate requires tuning thresholds after held-out outcomes are viewed.

## Current decision

This direction is a **conditional measurement/selection hypothesis**, not a validated method. Conformal risk and generic rejection are mandatory controls, not novelty. The only possible independent claim is that source-provenance-aware, action-level abstention predicts and improves future geometry under a fixed consumer budget, survives source-ID and matched-support placebos, and remains useful across held-out scenes. If that contract is not met, promote FGB-Future as the paper’s evaluation problem or report the negative result.

## 2025–2026 primary-source update (re-prioritized)

The 2024 papers above are baseline controls. A newer scan materially tightens the novelty boundary:

- **KOWCPI (ICLR 2025).** Lee, Xu, and Xie use kernel-weighted quantile estimation for dependent time-series nonconformity scores, with asymptotic conditional coverage under mixing assumptions and empirical rolling coverage. This is directly relevant to trajectory data: ordinary split conformal is not enough for our sequential setting. Official conference paper: https://proceedings.iclr.cc/paper_files/paper/2025/hash/058983528186511a74968e88a6d0ad63-Abstract-Conference.html (paper PDF linked there; accessed 2026-09-16).
- **High Probability Risk Control Under Covariate Shift (COPA/PMLR 2025).** Almeida et al. importance-weight calibration losses to handle covariate shift in learn-then-test risk control. This is a required stress-test if calibration scenes and held-out scenes differ; it makes a plain global calibration threshold an inadequate novelty claim. Official paper: https://proceedings.mlr.press/v266/almeida25a.html.
- **Conformal Risk Training (NeurIPS 2025).** Yeh et al. extend CRC to optimized certainty-equivalent risks, including CVaR, and differentiate through risk control during training. Therefore “we use CVaR/conformal tail risk” is already covered at the generic risk-control level. Official paper: https://proceedings.neurips.cc/paper_files/paper/2025/hash/6559542f75b4452ebaaf82094c7defb7-Abstract-Conference.html.
- **Selective Omniprediction and Fair Abstention (NeurIPS 2025).** Casacuberta and Kanade give selective classifiers that optimize abstention for a class of losses and support group-conditional guarantees. A learned abstention head or a group-conditioned threshold is not enough for novelty. Official paper: https://proceedings.neurips.cc/paper_files/paper/2025/hash/3826a7e2a07ee41ca42eaf57ed337df4-Abstract-Conference.html.
- **Conformal Reliability (ICML 2026; arXiv 29 May 2026).** Gao et al. define a worst-case metric over a calibrated prediction set for conditional generation and optimize it in a latent space. This is an especially close evaluation precedent: a future-world-model paper must distinguish a source/action decision from merely reporting worst-case reliability of generated outputs. Primary paper and code: https://arxiv.org/abs/2605.30807 and https://ggc29.github.io/CReL/.
- **Conformal Risk-Averse Decision Making with Action Conditional Guarantee (ICML 2026 listing; arXiv 4 June 2026).** Zhu et al. condition conformal safety guarantees on the action selected and optimize action-conditional risk. This substantially overlaps the phrase “action-level calibrated abstention.” Primary paper: https://arxiv.org/abs/2606.05551; official ICML listing: https://icml.cc/virtual/2026/poster/65697. Our only possible difference is that an action is a named historical source consumed by a generative world-model path, and the outcome is an independently measured future RGB-D/pose state with source-level causal intervention.
- **ICML 2026 official listings** also include Conditional Quantile Adjusted Conformal Prediction for Time Series (poster 64983) and Conformal Reliability (poster 66398); the conference downloads page is the authoritative listing, but the poster pages were inaccessible to this retrieval client. https://icml.cc/Downloads/2026.

### Updated reviewer judgment

The 2025–2026 literature lowers the prior novelty score for “provenance-aware conformal abstention” from **conditional 7/10 to conditional 5.5/10**. It is not a safe standalone method claim. The candidate can survive only as a source-level *world-model measurement/decision problem* if all of the following are observed: (i) exact source identity remains available through the real consumer path; (ii) the source action changes future geometry when intervened on, beyond replay noise; (iii) gains survive KOWCPI/shift-aware calibration controls, generic selective prediction, CVaR/OCE controls, action-conditional calibration, source-ID permutation, and support-matched placebos; and (iv) the effect replicates across scenes and horizons. If any condition fails, use FGB-Future as the benchmark/evaluation contribution and report the negative result.
