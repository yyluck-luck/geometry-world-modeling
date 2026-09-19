# Live Primary-Source Innovation Scan — 2026-09-15

**Scope.** Bounded scan for a falsifiable research direction beyond GRC-Memory, aligned with the proposal's long-horizon geometric consistency problem. This note records literature evidence and a candidate only; it does **not** validate a method or authorize a novelty claim.

**Timestamp.** 2026-09-15 13:52 (Asia/Shanghai).  
**Method.** Primary-source conference pages, proceedings, official project pages, and arXiv records were read. Search date and URLs are retained below.

## Primary-source evidence

1. **Video World Models with Long-term Spatial Memory (NeurIPS 2025).** The paper introduces two long-term memory mechanisms: a global static point-map memory and sparse episodic reference frames, with retrieval for long-horizon revisits. The official proceedings abstract and paper describe geometry-grounded storage/retrieval and custom datasets. DOI: `10.52202/085713-1651`. Sources: [NeurIPS abstract](https://proceedings.neurips.cc/paper_files/paper/2025/hash/467655d26fcc207bca08915dc91964c6-Abstract-Conference.html), [paper PDF](https://proceedings.neurips.cc/paper_files/paper/2025/file/467655d26fcc207bca08915dc91964c6-Paper-Conference.pdf), [official code](https://github.com/spmem/spmem).

2. **Navigation World Models (CVPR 2025).** The model predicts future visual observations conditioned on navigation actions and uses imagined trajectories for planning/ranking. Its discussion explicitly says the model does not use an explicit structured environment map and remains limited on temporal dynamics. DOI: `10.1109/CVPR52734.2025.01472`. Sources: [CVPR open-access paper](https://openaccess.thecvf.com/content/CVPR2025/html/Bar_Navigation_World_Models_CVPR_2025_paper.html), [official code](https://github.com/facebookresearch/nwm).

3. **World-consistent Video Diffusion with Explicit 3D Modeling (CVPR 2025).** WVD jointly models RGB and XYZ frames and supports camera-trajectory-conditioned generation through explicit 3D coordinates. Source: [CVPR open-access paper](https://openaccess.thecvf.com/content/CVPR2025/html/Zhang_World-consistent_Video_Diffusion_with_Explicit_3D_Modeling_CVPR_2025_paper.html).

4. **Geometry Forcing (arXiv 2025, version 2 in 2026).** The method aligns intermediate video-diffusion representations with geometric-foundation features using angular and scale alignment objectives. This is a representation-training intervention, rather than a memory validity or selective-use protocol. DOI: `10.48550/arXiv.2507.07982`. Source: [arXiv record](https://arxiv.org/abs/2507.07982).

5. **GeoVideo (NeurIPS 2025).** The official NeurIPS abstract reports geometric regularization for video generation and gains in spatio-temporal coherence, shape consistency, and physical plausibility. Source: [NeurIPS abstract](https://proceedings.neurips.cc/paper_files/paper/2025/hash/536d18fbb454f80221465f1a42c6f389-Abstract-Conference.html).

6. **Quantitative Video World Model Evaluation for Geometric-Consistency (arXiv 2026 preprint).** PDI is presented as a geometry-specific diagnostic because common perceptual metrics can miss geometric failure modes. This supports separating RGB quality from geometric evaluation; it is not evidence for a memory-selection method. Source: [arXiv record](https://arxiv.org/abs/2605.15185).

## Gap that survives the scan

The recent methods cover (a) geometry-grounded memory storage/retrieval, (b) explicit 3D supervision or representation alignment, and (c) action-conditioned future prediction. I did **not** find, in the sources above, a demonstrated protocol that treats the validity of a remembered **landmark** as a state that can become invalid after dynamic change, and then measures the benefit of abstaining from that landmark during a later revisit under a fixed compute budget and future held-out geometry.

This is a gap candidate, not a proof of absence. A full nearest-neighbor search must still include dynamic-scene memory, cache invalidation, change-point detection, and selective prediction literature before any paper claim.

## Candidate beyond GRC-Memory: DLV (Dynamic-Landmark Validity)

### Problem statement

GRC-Memory scores/selects historical observations using calibrated per-observation geometry risk. A distinct extension is to represent memory as **landmark hypotheses** with an explicit validity state that can transition over time:

\[
 z_{j,t}\in\{\text{valid-static},\text{valid-dynamic},\text{invalid/unknown}\}.
\]

For landmark `j`, maintain a short history of independent reprojection/depth residuals and visibility events. At a revisit, the consumer receives either the landmark-conditioned feature or an abstention token. The decision is made at landmark level, not by ranking frames alone.

### Falsifiable hypothesis

> Under a fixed memory/compute budget and a held-out future trajectory, a landmark-level validity state with abstention reduces revisit geometric error and ghosting **only when** the scene contains genuine dynamic changes; on static scenes it must not degrade error relative to an equal-budget retrieval baseline.

This gives a built-in negative prediction: if DLV merely suppresses useful evidence, static-scene performance will drop or no better than random/recency selection.

### Minimal controlled pilot (after Gate 0)

- Freeze one candidate pool, one memory budget `k`, one target horizon, camera intrinsics/extrinsics, RGB-D pairing, and random seeds.
- Construct static and dynamic conditions from the same scene when possible: static replay, object-motion intervention, and visibility/occlusion intervention.
- Compare equal-budget baselines: recent-k, uniform/random-k, pose-distance-k, coverage-k, utility/confidence-k, GRC-Memory, and DLV.
- DLV ablations: no state transition (frame score only), no abstention, no dynamic residual, and oracle validity (upper bound only).
- Primary metrics: future depth AbsRel/RMSE, reprojection error on held-out geometry, revisit consistency, ghosting rate, and abstention risk-coverage curve. RGB MSE is secondary and cannot stand in for geometry.
- Use a pre-registered placebo: shuffle landmark validity labels within each scene. DLV should lose its advantage under the placebo.

### Kill criteria

Stop treating DLV as a method if any of the following occurs:

1. The validity score predicts source identity or scene identity rather than future geometric error (leakage/confounding).
2. Gains disappear after equalizing candidate pools, budget, and target horizon.
3. Static-scene performance degrades materially without a dynamic-scene benefit.
4. Ablation shows the effect comes only from fewer memory tokens or a hidden coverage advantage.
5. The apparent gain is only RGB perceptual quality while held-out geometry is unchanged or worse.

## Reviewer-style score (pre-experiment)

| Dimension | Score / 10 | Reason |
|---|---:|---|
| Novelty potential | 7.5 | Landmark validity state plus explicit abstention is more specific than frame ranking, but dynamic-memory and selective-prediction neighbors may reduce the score.
| Scientific value | 8.0 | Directly tests when long-term geometric memory should be trusted after scene change.
| Feasibility on H800 | 6.5 | Requires valid RGB-D/pose/time alignment and dynamic interventions; inference-only pilot is feasible once dependencies are ready.
| Evaluation risk | 6.0 | High risk of scene/source confounding, leakage, and unfair budget comparisons.
| Overall pre-experiment verdict | **Borderline candidate** | Keep as a falsifiable branch; do not replace GRC-Memory until primary-source neighbor audit and controlled pilot are complete.

## Relation to current project state

- This candidate does not change `novelty_authorization=NONE` or `new_method_validated=false`.
- It is blocked by the same data-qualification requirements as formal GRC: verified RGB-D, intrinsics/extrinsics, timestamps, held-out split, and future-GT isolation.
- The immediate scientific value is a sharper experiment: test whether memory invalidation is a *state-transition problem* rather than only a per-frame risk-ranking problem.
- No GPU run, model result, or future-GT score was produced by this scan.

## Next action

Run a focused nearest-neighbor audit for dynamic memory invalidation/change-point/selective prediction, then implement a data-free DLV state-machine simulator and unit tests. Only after Gate 0 and the implementation audit pass should the DLV pilot be submitted to H800.
