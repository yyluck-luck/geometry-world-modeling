# New proposal draft: lineage-aware memory fusion

> **STATUS CHANGED 2026-09-19: NO-GO AS WRITTEN.** The 800-GPU-hour tranche is **withdrawn** by the
> reviewer and **not** requested. The mechanism as specified has an algebraic weakness that this
> project verified numerically; see the appended section "Algebraic finding". The remaining
> question is far narrower than the draft claims. **Nothing below is authorised.**

2026-09-19. **Status: DRAFT AWAITING OWNER AND SUPERVISOR APPROVAL. Nothing is authorised.**
`new_method_validated=false`; `novelty_authorization=NONE`.

This is a **new project**, not a continuation. The previous project's branch stays closed and its
technical report stays final.

## 1. The mechanism

> **Generated historical views can retain shared errors despite having different appearances and
> viewpoints. A fusion module trained to model those cross-source error interactions, using the
> recorded generation ancestry, improves subsequent view fidelity over confidence-only and
> unrestricted learned fusion at matched context and computational budgets.**

Target task: **recurrent camera-conditioned generation of static indoor scenes**. Not dynamic-world
simulation, not generic video quality, not universal geometric correctness.

**What changes computationally.** Retrieval is held fixed; the same four selected images, cameras and
estimated geometry go to the method and its controls in replay tests. Each generated block records
which historical images conditioned it, giving a directed ancestry graph. A small network predicts a
positive-semidefinite error second-moment matrix per target location, conditioned on that graph plus
reliability descriptors, and the four sources are fused by the constrained weights that minimise
predicted joint error. The fused feature enters through a trained conditioning adapter.

**This requires a research fork with a new conditioning adapter.** The pinned artefact stays
unmodified. Backbone weights may stay frozen while the adapter and error model train.

**Consumers: VMem and the camera-conditioned DFoT checkpoint.** DFoT is the natural second
implementation because COVRAG itself uses it, which makes the closest-method comparison run on a
common backbone.

## 2. The honest novelty position

**Global novelty is UNVERIFIED and must not be asserted.** Classical correlated-estimate fusion is
old; placing it inside a video model is not sufficient. The project must establish that **generation
ancestry supplies error-dependence information beyond image similarity, individual confidence,
temporal distance, and generic learned attention** — which is exactly what baselines B6–B8 below
isolate.

The strongest objection, stated by the reviewer and accepted here: *"this is ordinary
correlated-estimate fusion with a graph-conditioned neural confidence model; attention could already
learn the same weighting."* **Potentially fatal.**

Prior art verified real by this project on 2026-09-19 (titles confirmed):

| id | title | relation |
|---|---|---|
| 2102.13090 | IBRNet: Learning Multi-View Image-Based Rendering | learned multi-view blending with feature mean/variance — the strongest alternative explanation |
| 2503.15742 | Uncertainty-Aware Diffusion Guided Refinement of 3D Scene | makes generic "uncertainty-aware generated-view use" unavailable |
| 2511.17932 | Novel View Synthesis from A Few Glimpses via Test-Time … | same |
| 2503.03751 | GEN3C: 3D-Informed World-Consistent Video Generation | generated-cache fusion; implementation details must be read |
| 1501.00994 | Online Reputation and Polling Systems: **Data Incest**, Social Learning | the classical graph-dependent correction for reused information |

**Novelty audit still owed before major funding:** full method of Julier & Uhlmann, *A non-divergent
estimation algorithm in the presence of unknown correlations*, ACC 1997 (beyond abstract); forward
and backward citation tracing from IBRNet and the two uncertainty papers; GEN3C's fusion details.

**A physical limitation of the mechanism:** it cannot repair an error present identically in every
available source. It needs useful differences among sources, and ancestry must predict them.

## 3. The decisive early experiment — matched-marginal ancestry

For a fixed scene and camera configuration: generate four alternative parent histories; for each of
four child cameras generate a child under each parent, giving a 4×4 table. Build four
**shared-parent** contexts from the rows, and four **mixed-parent** contexts by cyclic assignment.

**Every individual child image appears exactly once in each condition, at unchanged camera positions
and slots.** The per-view marginals are identical; only the grouping by ancestry changes. This
manipulates joint dependence rather than covariance alone.

Evaluate standard fusion, diagonal-error fusion, and joint-error fusion. **An effect that exists only
in this constructed grouping and not in ordinary rollouts is insufficient for the method paper.**

## 4. Data plan

| dataset | train | dev | **untouched eval** | reserve |
|---|---:|---:|---:|---:|
| **ScanNet++ v2** (real) | 300 | 60 | **200** | 100 |
| **Hypersim** (synthetic) | 300 | 40 | **40** | up to 81 |

Allocation targets, not verified qualifying counts. The 200 figure comes from the illustrative
`n ≈ (2.8σ/0.20)²` with a scene-level SD of 1.0 dB — **a conservative planning allocation, not a
power guarantee.** All captures of one physical environment stay in one split. The two original
exposed sequences are debugging material only. Claims are limited to "unseen during this project's
adapter training and development"; backbone pretraining exposure is unknown and must be disclosed.

**Critical path: ScanNet++ access requires application and approval — budget 2–6 calendar weeks.**
Non-commercial research use, redistribution restricted, researcher and supervisor signatures needed.
Hypersim is CC BY-SA 3.0, ~1.9 TB, 74,619 images; attribution and share-alike obligations need review
for derived artefacts. New Hypersim rendering is **not** assumed — its mesh assets require separate
purchase.

## 5. Baseline matrix

B0 native versioned state-isolated · B1 four most recent distinct · B2 evenly spaced · B3 FoV +
non-adjacent (Context as Memory rule) · B4 COVRAG residual coverage on its DFoT setup · B5
LongLive-RAG-style learned retrieval embedding, **labelled an adaptation** · B6 parameter/FLOP-matched
generic learned fusion receiving the same ancestry and reliability information · **B7 diagonal error
model** · **B8 full error moment without ancestry** · **B9 proposed lineage-aware fusion**.

B6–B9 share the retrieval rule and source budget; B3–B5 vary retrieval. **These two comparisons must
not be intermingled.** Cost accounting covers geometry inference, feature extraction, adapter
inference, retrieval and denoising — not selector milliseconds. Deployment target: **≤20% extra
end-to-end inference time** over the matched projected-feature baseline.

## 6. Endpoint and retention rule, fixed before test access

Primary: **mean RGB PSNR over calls 7–12, pooled MSE within each four-frame call before PSNR, then
averaged within scene.** Three independent training seeds for the proposed/diagonal comparison. No
best-of-seed selection. The reference-warped diagnostic keeps its qualified interpretation and
**never becomes a training reward**; the pose evaluator stays secondary and failure-aware.

Retention requires **all** of: ≥ +0.20 dB late-rollout mean over the diagonal control with a
scene-level interval excluding zero; positive replication on the second consumer reported separately;
**≥ +0.05 dB incremental over the no-ancestry full-matrix model, or the lineage claim fails**; no
material LPIPS deterioration (proposed non-inferiority margin 0.005); and no parameter-matched generic
attention model matching it at the same cost.

These are **new criteria**, not inherited authority from the failed duplicate-slot repair.

## 7. Budget and phases

Full envelope **17,000–37,000 H800 GPU-hours**, hard ceiling **38,000** without renewed approval;
12–15 months; an eight-H800 pool during main phases; ~10–16 TB working storage; one full-time student
plus ~0.25 research-engineering support for the first six months.

| phase | timing | stop condition |
|---|---|---|
| 0 novelty, licensing, interfaces | wk 1–2 | an existing method already supplies the mechanism; licences block intended use; second consumer unsupportable |
| 1 premise test | wk 3–6 | dependence useful only in constructed examples, or ancestry adds nothing beyond appearance/pose/age |
| 2 minimal trained prototype | mo 2–4 | better residual modelling does not translate into future-image benefit |
| 3 scale and lock | mo 4–8 | benefit disappears against strong controls; runtime exceeds the allowed trade-off |
| 4 untouched evaluation | mo 8–11 | predeclared claim fails — report it, do not search new test subsets |
| 5 manuscripts | mo 11–15 | Paper 1 lacks independent substance — combine rather than manufacture a second |

### What is actually being requested now

**Phases 0–1 only: six weeks, ≤ 800 GPU-hours.** Phase-1 screen requires ≥ 5% lower fused-feature
error for the joint model than the diagonal model on natural held-out diagnostic histories, **and**
incremental value from correct ancestry over the same model without it. If it passes, a prototype
tranche to a cumulative **3,000** GPU-hours — **not** the full 38,000.

## 8. Paper structure

| paper | question | venue |
|---|---|---|
| 1 — correlated generated-memory errors | does ancestry explain error dependence and downstream degradation beyond marginal quality, similarity, age and coverage? | TMLR, **if** it establishes consequential natural behaviour rather than a toy demonstration |
| 2 — lineage-aware memory fusion | can a deployable trained error model exploit that structure better than confidence-only and generic learned fusion? | CVPR/ICCV/ECCV |

**Do not force the split.** If the phenomenon is only interesting because the module fixes it, combine
into one stronger method paper. The existing audit is released as a technical report and artefact;
**further polishing capped at two person-weeks** and must not consume the method budget.

## 9. The honest summary

The reviewer can now supply a concrete computation, a discriminating experiment, a data plan and a
budget — which it could not under the old constraints. **So the constraints were a genuine blocker.**
But it explicitly cannot supply *"globally unoccupied and likely to produce two top-venue papers"*.

**Removing the constraints creates an executable project. It does not supply its scientific result or
its novelty automatically.** The recommended decision is therefore bounded: fund the six-week
premise-and-novelty phase; do not acquire the full corpus or commit a semester until it passes; if
ancestry carries no incremental information, or ordinary learned fusion explains the gain, **close the
proposal rather than rename it**.

---

# Algebraic finding (2026-09-19): the proposed matrix is not four independent unknowns

The reviewer identified a weakness deeper than the three structural risks this project raised.
**Every identity below was verified numerically here, not accepted on assertion.**

With `e_i = f_i − f*`, `M_ij = e_i·e_j/d`, `q_i = ‖f_i − f*‖²/d`, `D_ij = ‖f_i − f_j‖²/d`:

| identity | verified |
|---|---|
| `M_ij = (q_i + q_j − D_ij) / 2` | max error **4.4e-16** |
| `wᵀMw = qᵀw − ½ wᵀDw` on the simplex | max error **1.1e-15** over 2000 random points |
| `M + c·11ᵀ` leaves the optimal weights **unchanged**, shifting risk by exactly `c` | weights identical; shift exact |
| `−½ vᵀDv = ‖Σ vᵢfᵢ‖²/d` for `1ᵀv = 0` (convexity) | max error **7.1e-15** |

The reviewer's own worked example also reproduced exactly: with 0.9 correlation between sources 1–2,
diagonal-only weights `1/4` give risk **0.3625**; the full-matrix optimum is
`(0.1724, 0.1724, 0.3276, 0.3276)` with risk **0.3276**.

## What this does to the proposal

**The target cancels.** `e_i − e_j = f_i − f_j`, so the off-diagonal entries are determined by the
four individual expected errors plus the pairwise feature distances — and **`D` is computable from
source features the fusion system already holds.** The "cross-source error interactions" are not
independently unknown quantities.

**Therefore the draft's B7 (diagonal-only) is an insufficient comparator.** The decisive baseline is
**analytic completion**: predict the four `q_i`, compute `D` from the available aligned features, and
optimise `qᵀw − ½wᵀDw`. Beating diagonal-only would only show the value of using source differences
that were already available.

**Common-mode shared error is unactionable.** The most intuitive reading of "these views share an
error" is a `c·11ᵀ` component — and that provably does not change the weights. A model can predict
shared error more accurately while having no useful control action. If all four sources are
identical, reweighting cannot change the fused feature at all.

**The surviving question is much narrower than the draft claims:** does generation ancestry improve
prediction of the **four individual risks** `q_i`, or supply a useful inductive bias — beyond age,
observed feature dispersion and marginal confidence? That is a four-number prediction problem, not a
matrix-learning contribution.

## Additional Phase-0 stop conditions the reviewer supplied

1. **Block-level ancestry is deterministic, not merely chain-like.** If every call writes back and
   includes the newest frame, then `B_s ∈ Ancestors(B_t)` for **every** `s < t` by induction. So
   "has a shared generated ancestor" and transitive-set membership are constant or functions of birth
   time. The actual lineage *representation* must be specified and shown non-recoverable from B8's
   inputs — raw graph entropy is the wrong gate.
2. **Native DFoT does not rescue it.** Its `_predict_sequence` uses the last `c` tokens, which is
   recoverable from sequence position and context length. Only a memory-augmented wrapper could
   differ, and that needs its own audit.
3. **DFoT's own Appendix A.3 already derives covariance-aware linear aggregation** of multiple score
   estimates and inverse-variance weighting under independence. "Account for correlations when
   combining evidence" is therefore discussed by the proposed second consumer's own paper.
4. **A pose-only replay cannot settle native retrieval**, because VMem's future surfels depend on
   CUT3R reconstruction from stored images, not on poses alone. A surrogate simulation is labelled
   as such; a negative surrogate does not prove generated rollouts lack variation.
5. **Matched RGB marginals ≠ matched feature marginals.** If geometry or normalisation is rerun per
   group, the same image acquires different features. The manipulation must be defined at the fusion
   input.
6. **Support may be too thin.** Four selected images do not imply four valid observations per target
   location; locations with ≤1 supported source cannot benefit from reweighting at all.
7. **Adapter reachability.** If raw source latents still enter the backbone unchanged, the generator
   can ignore the fused map, and any gain may be adapter capacity rather than weighting.
8. **Cost feasibility moves to Phase 0**, but the QP is not obviously expensive: at K=4 there are only
   `2⁴−1 = 15` active sets, each at most a 4×4 solve, and the matrix depends on neither the noisy
   latent nor the timestep, so it can be computed **once per call** rather than at all 50 steps.

## Current status

**The appropriate next artefact is a source-and-algebra decision memo, optionally with a capped
synthetic microbenchmark of roughly two GPU-hours. Not 800 hours, and no corpus generation.**

If that memo cannot state **what ancestry adds beyond age** and **what the learned matrix adds beyond
analytic completion**, the proposal closes before Phase 1.

`new_method_validated=false`; `novelty_authorization=NONE`.
