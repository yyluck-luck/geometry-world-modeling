# Continuous red-team scorecard: SOCF-A, FVR, and EGR

Date: 2026-09-15 (Asia/Shanghai)  
Role: skeptical reviewer; evidence audit only.  
Status: `new_method_validated=false`; `novelty_authorization=NONE`.

## Evidence boundary

The project has not yet run a qualified held-out VMem/GRC experiment. Remote weight transfer is
partial, Gate 0 is still blocked, and recent H800 work proves environment/import readiness only.
The strongest relevant saved-data evidence is S91R-C: disagreement had positive leave-one-target
ΔR² (mean about 0.01463, 4/4 held-out targets positive), but source identity matched only about
4.35–5.49% and the all-new consumer became worse on mean future AbsRel. This is a descriptive,
non-causal signal; it cannot validate any selector.

## Reviewer scorecard

| Candidate | Current verdict | Main reason | Fatal flaw status |
|---|---|---|---|
| **SOCF-A**: source-conflict plus stable replacement direction and abstention | **Borderline candidate; evaluation first** | The signed replacement-direction prediction is a potentially identifiable increment, but current evidence does not establish same-source intervention, held-out benefit, or independence from confidence/coverage/pose. | **CRITICAL if any future read or source-identity failure occurs**; otherwise MAJOR novelty/causal risk |
| **FVR**: calibrated future-value residual after geometry risk | **Lower-priority; likely pivot** | A residual learned from development utility can collapse into ordinary utility/relevance gating. Without a predeclared residual target available before test sealing, it is post-selection influence or leakage. | **CRITICAL if test future loss informs the score or threshold**; otherwise MAJOR overlap/identifiability risk |
| **EGR**: event-gated replacement | **Do not frame as a method yet** | “Event” gates are readily equivalent to transition detection, visibility, recency, or camera-path relevance. No evidence separates the gate from these controls under equal budgets. | **CRITICAL if event labels use future frames**; otherwise MAJOR mechanism-collapse risk |

## Fatal-flaw tests and stop rules

### 1. Leakage and unavailable future labels — hard stop

The selector may read only history available at decision time, camera metadata permitted by the
contract, and frozen calibration parameters. It must not read future RGB, depth, pose, masks,
future-validity masks, or future-derived support before prediction sealing. Calibration and test
trajectory identities must be disjoint. Future answers may be opened only after the source choice
and abstention decision are serialized. Any violation stops the corresponding scientific claim;
the run is retained as a failed audit, with no threshold or cap repair.

The S91R-C correction is a concrete warning: quantile boundaries computed after a future-valid
mask made future validity enter grouping. Future-validity must be applied only after boundaries
are fixed from past finite/positive values.

### 2. Post-selection influence is not causal benefit — hard stop for causal wording

A risk score predicting future error is not evidence that replacing a particular source caused
the change. The prior saved-data source identity mismatch prevents causal interpretation. A valid
test therefore needs paired leave-one-slot-out interventions on the same candidate pool, same
consumer, same random state, and same query; it must preserve source identity through the complete
consumer path. Report signed future loss per intervention, not only correlation, coverage, or
output change. If source identity cannot be traced, retain only an evaluation association claim.

### 3. Fixed-budget fairness — hard stop

All selectors must share candidate pool, slot budget (`k=4` primary; `k=2,8` frozen sensitivity),
memory tokens, GPU cache, host memory, forward count, generation steps, random state, and a
predeclared selection-time/read-cost budget. Abstention must consume the same accounting or be
reported as a separately priced policy. A method that wins by retaining more context, extra
replays, future inspection, or a stronger backbone is not a fair selector comparison.

### 4. Mechanism collapse — hard stop for novelty framing

SOCF-A must retain incremental predictive information after controlling recent, random,
pose-distance, coverage/visibility, confidence, utility-only, and ray-relevance controls. FVR
must beat utility-only after its residual is frozen. EGR must beat event/transition, recency,
visibility, and camera-path gates. Exact rank equivalence, or no out-of-sample gain after controls,
means the contribution is an evaluation result or engineering heuristic; stop calling it a new
method.

### 5. Mathematical counterexample the experiments must survive

Lower historical conflict need not mean higher future value. For candidates A and B, let
`q_A=0.10 < q_B=0.20`, while future-region costs are `w_A=100` and `w_B=1`. Then expected losses
`w_A q_A=10` and `w_B q_B=0.2`; choosing the lower-risk A is worse. Thus SOCF cannot claim a
monotone risk-to-value law without testing signed future effects across occlusion, revisit, and
viewpoint strata. A repeated reversal is a pivot condition, not a reason to retune the threshold.

## Required held-out decision contract

1. Use at least 3 development trajectories for calibration and at least 10 independent held-out
   trajectories with at least 3 future queries each; query is not an independent pixel.
2. Freeze strongest baseline, score transformation, abstention threshold, caps, and aggregation
   on development only. Open held-out future answers after prediction sealing.
3. Main endpoint: trajectory-level paired future mean AbsRel at `k=4`; also report median,
   worst-5%/CVaR, coverage, and signed per-source intervention effects.
4. Require SOCF partial Spearman/AUROC incremental over strongest baseline, with a predeclared
   positive bootstrap interval and AUROC margin of at least 0.05; require at least 1% relative
   mean improvement at `k=4` with a trajectory-bootstrap lower bound above zero and no more than
   5% tail worsening. These are screening gates, not proof of broad generalisation.
5. Stop if the effect is confined to one trajectory, one seed, one cap, one occlusion level, or
   one consumer; if confidence/coverage/pose/utility explains it; or if removing conflict,
   residual, or abstention leaves performance unchanged.

## Literature overlap pressure

Recent primary work already covers substantial neighboring mechanisms: ViewRope uses
geometry/ray-aware historical attention; Spatia maintains and projects explicit 3D memory;
GIM-World uses camera-queryable geometry, information-guided pruning, and bounded history;
WorldTrace makes transition/landmark memory addressable; MemLearner learns to query context.
These establish that geometry-aware relevance, memory updating, pruning, and transition gating
are occupied design space. The only defensible incremental claim is the narrowly testable,
history-only signed counterfactual prediction with abstention under fixed budgets—and it remains
unverified.

Primary sources: [ViewRope](https://arxiv.org/abs/2602.07854), [Spatia](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhao_Spatia_Video_Generation_with_Updatable_Spatial_Memory_CVPR_2026_paper.pdf), [GIM-World](https://arxiv.org/abs/2606.02436), [WorldTrace / Addressable Memory](https://arxiv.org/abs/2608.07408), [MemLearner](https://arxiv.org/abs/2606.31734), and [WorldStereo](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhang_WorldStereo_Bridging_Camera-Guided_Video_Generation_and_Scene_Reconstruction_via_3D_CVPR_2026_paper.pdf).

## Final reviewer recommendation

Do not spend implementation effort on FVR or EGR until SOCF-A passes the leakage, identity,
budget, and mechanism-collapse gates. Even a clean pilot pass authorizes only a held-out test.
If SOCF-A fails any hard stop, publish/retain the result as a negative evaluation of geometry-risk
selection and return to failure analysis; do not rename the selector or widen the claim.

Evidence consulted: `RESEARCH_MEMORY.md` (S91R-C, S92, S94, current Gate 0/H800 state),
`work/S91R_saved_future_error_reanalysis/CONTROL_AUDIT_REPORT.md`,
`work/agents/creative_ideas_source_checked_20260915.md`, and
`work/agents/innovation_falsification_matrix_20260915.md`.
