I'll give a concise research second opinion using only the material in the prompt.

---

# Second Opinion: GRC-Memory and S90 Evidence Plan

## Supported facts (from the prompt)

- S87: a single-seen static scene, single blend at 0.75 gave lower four-target mean RGB MSE (0.0512) than the 50-step geometry-guided arm (0.0524); target 22 got worse (0.0748 vs 0.0683) with visible ghosting. This refutes only "multi-step guidance is necessary for that mean," nothing about geometry or novelty.
- S90: one frozen 512-byte Range at offset 11460608 returned exact HTTP 206, TLS 0, archive size 12064450560, valid `00000/00134.depth.exr` tar header. No RGB/depth body or model ran.
- Real matched RGB/depth/camera views are not yet available; data risk is high.
- Upstream facts: conformal risk control takes a global lambda on an n×lambda bounded monotone loss table with empirical-risk correction; FisherRF selects future informative poses/EIG; NVF averages ray entropy and composes opacity visibility. None justifies the candidate's specific constructions.

## The two strongest fatal flaws

**Flaw 1 — The risk-prediction object is not a groundable future loss.** The hypothesis needs "lower pre-selection geometry risk ⇒ lower held-out future position error." But at selection time you have no ground-truth future state, so the "predicted geometry loss" and the held-out error are correlated only if the surrogate is a genuinely calibrated estimate of that future loss. Nothing in the design establishes that. If the surrogate is instead a proxy (coverage, visibility), then the claim "lower risk ⇒ lower error" is unfalsifiable-in-principle until real matched future states exist, and the existing evidence (S87/S90) provides none. The core hypothesis is currently *untestable with available data*, which is worse than merely unsupported.

**Flaw 2 — Calibration leaks the future target through the selection itself.** The cleanest candidate actually *does* leak: the per-candidate risk quantile and "score" must be conditioned on which history the selector *will* pick, but a selector choosing by that same risk sees a hindsight-biased subset — the very future error used for calibration is partly a function of the selected set. So a conformal bound computed on "all candidates" does not transfer to "the selected subset." This is a selection-induced distribution shift, and the proposal nowhere separates calibrating on random/uniform eligibility from evaluating on greedy selection.

## Correcting the formulation for computability and no-leak

Make everything a function of past obs + requested target camera only, and freeze it:

- Let each candidate history item `i` (or set `S`) have features `f_i ∈ history-only space`. Define a fixed *pre-selection score* `s_i = g(f_i; θ_g)`, trained once and never re-fit on future ground truth at selection time.
- Calibration uses a held-out split of *past* trajectories where, for each query, you *simulate* the selection forward in time using only data available before that query, then compare against the realized next state (which is "future" relative to that query but known in the split). This is the one defensible pattern: it is exactly cross-validation-in-time.
- The bound must be per-decision rule, computed on the *selected subsets* of the held-out split, not on pooled candidates.

Concretely: calibrate the empirical selection rule `S = argmax s` on the training split; record the realized future error `L(S)`; report a risk bound only over those realized draws. Any quantile taken on the raw candidate residual vector (the struck S87/CRC pattern) is dropped.

## Which conformal guarantee is defensible

The only defensible guarantee is **marginal**, of the Conformal Risk Control form: `P(R(S) ≤ R̂ + correction) ≥ 1−α`, where `R̂` is an empirical risk over the held-out split and the correction is the CRC quantile of item/set losses. Valid under: (a) exchangeability between calibration draws and test draws *of the same decision rule*; (b) the loss table is monotone-bounded in lambda and you take the corrected quantile, not `Q_(1−α)` on a 3-vector; (c) you do **not** assign a per-candidate independent quantile. It is marginal/aggregate, not conditional, not per-candidate, and not a set-coverage guarantee. Conditional claims (per-candidate error) are not supported by the cited method and need separate, stronger assumptions (e.g., validity within strata), which you have not stated. Distribution shift between the two S87/S90 regimes (different scenes, single vs multi-step, archive vs live) breaks exchangeability unless you only ever calibrate and evaluate within one regime.

## Why the sums and the `1−1/e` claim fail

- **Per-item risk sums:** A sum of independent per-item risks ignores that membership is coupled: including item A changes the environment/trajectory the future state depends on, so `L(S)` is not `Σ L(i)`. Even with no coupling, sums of per-item risk need an independence/Rademacher-style inequality, not the quantile shortcut.
- **Submodular-marginal story:** For a `(1−1/e)` ratio — and more strongly for the strict additive-conformal claim — you need the utility to be nonnegative monotone submodular under the *cardinality constraint that is actually binding*. A learned or geometry-derived utility (Fisher/EIG, coverage, confidence) is typically neither submodular nor monotone nondecreasing under your fixed-memory/compute constraints. The moment the constraint is cost-based or non-uniform, the greedy guarantee collapses. The bridge "greedy geometry selection ≈ submodular maximization" is asserted, not shown.

## Cheapest runnable counterexample tests (no validation claims)

Without real data, priority is falsification of components, in order:

1. **Leak test:** Monte-Carlo where future ground truth is known; compute candidate risk on *all* candidates vs on the `argmax s` selected subset; if the quantile shifts, the per-candidate bound is invalid. Pure numpy.
2. **Non-submodularity counterexample:** enumerate small universes (n≈8) with a synthetic learned utility; check whether `argmax-s` greedy beats random only when utility happens to be submodular; find one log-concave/coverage combo where it strictly fails the additive-ratio claim.
3. **Sum-vs-joint test:** with synthetic coupled losses (e.g., distance-only), confirm `Σ per-item risk` over/under-covers the true joint risk.
4. **State only what the test shows.** Each is a unit counterexample, not scientific validation.

## Minimum real-data experiment that could reject the core hypothesis

Requirement: matched RGB/depth/camera for a *temporal* corpus (the current single S87 scene and the S90 archive header cannot reject anything). Concretely:

- **Splits:** time-ordered by scene/trajectory; train on scenes 1–k for the surrogate, calibrate on k+1…k+m by forward simulation, test on the rest. Never interleave.
- **Baselines (identical eligible history, features, k, compute):** recent-frame, camera-distance, random, coverage, Fisher/EIG, confidence-only, utility-only.
- **Metrics:** held-out future position error (the decisive one), plus RGB/depth MSE as secondary; report per-target so the S87 target-22 regression is explicitly checked, not hidden in the mean.
- **Stop rule (pre-registered):** reject the hypothesis if either (a) risk-aware selection does not beat the best baseline on mean held-out error within a pre-specified margin, or (b) the CRC-corrected marginal risk bound is violated more than α on the test split, or (c) per-target worst-case error worsens (the S87 pattern) beyond tolerance. Pre-register the margin/tolerance before looking at test numbers.

## Adopt / revise / reject decisions

- **(a) Conformal calibration: revise.** Keep CRC but only as a marginal aggregate risk bound with monotone-bounded losses and the corrected quantile; drop per-candidate/3-vector quantiles.
- **(b) Fisher/EIG: adopt as baseline only.** NVF/FisherRF prior work already covers it; it is a required comparator, not contribution.
- **(c) NVF-style visibility: reject as novelty.** Prior component, appropriate as a feature.
- **(d) Full GRC-Memory: revise toward the narrow falsifiable claim** ("risk-aware past-memory selection beats stated baselines under fixed memory/compute, with a defensible marginal risk bound"). As currently stated — with the leak, the unconditional per-candidate quantile, and no real data — the "New Problem + New Method" story is not defensible.

---

**Assumptions I'm making:** that "future state" is measured by position error, that matched RGB/depth/camera will eventually arrive, and that the user wants the framing reduced to the narrowest falsifiable claim. If any of these differ, the minimum-experiment section changes. **The next cheapest check** is test 1 (leak/coupling counterexample), which is doable now without any of the risky real data.
