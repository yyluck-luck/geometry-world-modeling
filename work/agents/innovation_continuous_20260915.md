# Continuous innovation scan (2026-09-15)

Status: literature-grounded hypotheses only. `new_method_validated=false`; `novelty_authorization=NONE`. The source claims below were checked against full primary-paper pages/PDF landing pages, not search snippets. No paper implementation was run.

## Candidate 1 — source-conflict risk with abstention (SOCF-A)

**Nearest work.** ViewRope, *Geometry-Aware Rotary Position Embedding for Consistent Video World Model* (arXiv:2602.07854), uses camera-ray geometry in rotary embeddings and geometry-aware sparse historical attention. GIM-World, *Geometry-Aware Implicit Memory for Video World Models* (arXiv:2606.02436), compresses history into fixed-size tokens with a camera-queryable geometry head and information-guided pruning. Spatia, *Video Generation with Updatable Spatial Memory* (CVPR 2026), updates an explicit 3D memory and projects it along the next camera path.

**Mechanism-level difference.** These works make memory or attention geometry-aware. SOCF-A would leave the world-model backbone unchanged and compute a history-only, source-level pairwise reprojection conflict; a development-only leave-one-slot-out replay estimates the *direction* of replacement effect, and the test selector abstains when that direction is unstable. This is a narrower proposed distinction, not evidence of non-overlap.

**Falsifiable prediction.** Under a frozen candidate pool, query path, slot/token/forward budget and random state, calibrated conflict predicts the sign of each replacement's unseen future RGB-D/pose loss change after controlling recency, pose distance, visibility/coverage, confidence and utility. At nominal 0.8/0.9 coverage, empirical coverage stays within ±0.05 and the full consumer improves paired future AbsRel; otherwise the claim fails.

**Cheapest H800 test.** After Gate 0 and the frozen VMem baseline, use two development trajectories and two pre-declared leave/revisit queries. For `k=4`, replay one delete/replace intervention per candidate pair with identical seeds and steps. Seal predictions before opening future RGB-D/pose. Measure finite conflict features, source-provenance changes, signed future loss, calibration coverage, and rank correlation against recent/pose/coverage/confidence. This is a pilot, not validation.

**Kill criterion.** Stop if future fields are read before sealing; conflict is non-finite, exact-rank-equivalent to a simple control, has no out-of-sample signed predictive information, or improves only coverage/current RGB while future depth/pose is unchanged or worse. Also stop the method framing if the effect cannot be fairly matched to ViewRope/GIM-World-like relevance or Spatia-like memory under equal budget.

## Candidate 2 — future-value residual beyond calibrated risk (FVR)

**Nearest work.** GIM-World (arXiv:2606.02436) uses information-guided pruning for bounded implicit memory. WorldTrace, *Addressable Memory for Video World Models* (arXiv:2608.07408), makes cache entries addressable and stores landmarks at transitions. WorldMM (CVPR 2026) adaptively retrieves multiple memory types and temporal scales for long-video reasoning.

**Mechanism-level difference.** FVR would fit, on development trajectories only, a residual predictor of future geometric value after accounting for calibrated history risk, coverage, pose and confidence, then rank source replacements under a fixed real memory budget. The proposed increment is the residual test against strong selectors, not adaptive retrieval or compression itself. It is especially vulnerable to reducing to ordinary utility reweighting.

**Falsifiable prediction.** On held-out queries, the residual adds positive partial predictive information for signed future RGB-D/pose gain after all pre-declared controls, and its selector reduces mean or tail future loss at the same `k` and forward count. If it predicts only current reconstruction utility, the hypothesis is false.

**Cheapest H800 test.** Reuse the SOCF pilot's sealed predictions and candidate pool. Fit residual coefficients on at least three calibration trajectories; run one locked held-out development trajectory with `k=4`, comparing FVR, risk-only, utility-only, coverage, pose and recent. Report per-query signed loss, partial Spearman/AUROC, tail loss, and compute/memory. Do not access held-out future answers until prediction sealing.

**Kill criterion.** Kill if residual coefficients require held-out future answers, if utility-only or coverage/pose matches it, if partial predictive intervals cross zero, or if no paired future-loss improvement remains after equal-budget controls. Recast as an evaluation protocol if it predicts value but does not improve the consumer.

## Candidate 3 — event-gated memory replacement (EGR)

**Nearest work.** WorldPlay, *Towards Long-Term Geometric Consistency for Real-Time Interactive World Modeling* (ICML listing/arXiv:2512.14614), uses Reconstituted Context Memory to rebuild context from past frames and Context Forcing for long-range consistency. RELIC, *Interactive Video World Model with Long-Horizon Memory* (arXiv:2512.04040), stores compressed latent tokens with relative actions and absolute camera poses and trains long self-rollouts. Long-Context State-Space Video World Models (ICCV 2025) uses block-wise SSM scanning plus local attention for long temporal memory.

**Mechanism-level difference.** These nearest works change the architecture/training or maintain long-range context continuously. EGR would trigger a source replacement only at a history-only event detected from leave/revisit geometry (e.g., occlusion boundary plus stable conflict), with replacement count and compute fixed; between events it preserves the current memory. It therefore tests sparse intervention timing rather than adding another always-on memory architecture.

**Falsifiable prediction.** Conditional on matched event counts and candidate pools, event-gated replacement reduces future geometric tail loss more than equally many uniformly timed replacements, while no-event windows show no benefit. If gains track event frequency or coverage alone, the mechanism is not identified.

**Cheapest H800 test.** On two qualified development trajectories, pre-label event windows from history-only signals, then run paired equal-count replacements at event and non-event windows with the same consumer seed. Seal outputs first; score future depth/pose and provenance changes. This can run as a selector wrapper around the baseline and does not require training WorldPlay/RELIC/SSM models.

**Kill criterion.** Kill if natural events are absent/unstable, event and uniform replacement have indistinguishable paired future loss, event labels use future answers, or any improvement is explained by unequal replacement count, coverage, or compute. Do not claim architectural novelty from a wrapper result.

## Candidate 4 — counterfactual future-geometry benchmark (FGB-Future)

**Nearest work.** Geometry-guided Online 3D Video Synthesis with Multi-View Temporal Consistency (CVPR 2025) accumulates depth in TSDF-like image-space representations and uses it to guide blending. WorldPlay and the long-term-memory papers above evaluate long-horizon consistency/retrieval, while CUE-R (arXiv:2604.05467) supplies an analogous source-level remove/replace intervention idea in evidence selection.

**Mechanism-level difference.** FGB-Future is an evaluation contract: freeze history-only inputs and a real memory budget, intervene on one source item, and score the *signed* change in future RGB-D/pose loss after prediction sealing. It does not assert a new memory module. The key unit is a source intervention paired with an externally supplied, held-out future RGB-D/pose reference, rather than current geometry consistency or video appearance alone.

**Falsifiable prediction.** At fixed consumer, candidate pool and intervention budget, history-only conflict/risk should predict the sign and tail of future geometric loss better than current RGB MSE, coverage, or confidence. If no selector beats recent/random, the benchmark still yields a negative diagnostic but no method claim.

**Cheapest H800 test.** Run a small sealed replay: one qualified trajectory, three queries, four candidate slots, one intervention per query, and identical generation seeds. Save predictions and provenance before decoding future depth/pose; then compute paired signed AbsRel, pose/reprojection error where valid, and worst-query loss. The test is an evaluation-contract smoke test, not a general benchmark result.

**Kill criterion.** Kill the benchmark claim if identity/split/permissions cannot be audited, future answers are available to selection, intervention changes budget or randomness, or geometry scoring is unavailable. If future loss is not distinguishable from RGB-only artifacts, report that limitation explicitly.

## Decision

SOCF-A remains the sharpest method hypothesis because its single proposed increment is source-conflict direction plus abstention. FVR is lower priority because it may collapse to utility reweighting. EGR is conditional on observing real leave/revisit events. FGB-Future is the safest contribution candidate as an evaluation problem, but only if the data contract and future isolation pass. All four require Gate 0, a no-data model-load smoke, a frozen baseline, equal-budget controls, held-out future scoring, cross-scene confirmation and independent recomputation before any novelty or method claim.

## Primary sources checked

- ViewRope: https://arxiv.org/abs/2602.07854
- GIM-World: https://arxiv.org/abs/2606.02436
- Spatia: https://openaccess.thecvf.com/content/CVPR2026/papers/Zhao_Spatia_Video_Generation_with_Updatable_Spatial_Memory_CVPR_2026_paper.pdf
- WorldTrace: https://arxiv.org/abs/2608.07408
- WorldMM: https://openaccess.thecvf.com/content/CVPR2026/papers/Yeo_WorldMM_Dynamic_Multimodal_Memory_Agent_for_Long_Video_Reasoning_CVPR2026_paper.pdf
- WorldPlay: https://arxiv.org/abs/2512.14614
- RELIC: https://arxiv.org/abs/2512.04040
- Long-Context SSM: https://openaccess.thecvf.com/content/ICCV2025/html/Po_Long-Context_State-Space_Video_World_Models_ICCV_2025_paper.html
- Geometry-guided Online 3D Video Synthesis: https://openaccess.thecvf.com/content/CVPR2025/html/Ha_Geometry-guided_Online_3D_Video_Synthesis_with_Multi-View_Temporal_Consistency_CVPR_2025_paper.html
- CUE-R: https://arxiv.org/abs/2604.05467

Verification boundary: source pages establish the papers' stated mechanisms and evaluation settings. They do not establish non-overlap, replication, or any result for this project. No search snippet was used as proof, and no novelty was validated.
