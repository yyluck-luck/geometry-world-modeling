# Innovation Literature Scan: Geometry-aware Long-horizon World Modeling (2026-09-16)

**Scope.** Primary-source scan for recent top-conference or official proceedings work relevant to the proposal's long-horizon RGB-D/pose consistency and memory selection. This is an evidence map, not a novelty certificate. No paper model was run in this scan; claims below are mechanisms/experimental designs reported by the cited primary pages.

**Current project boundary.** `new_method_validated=false`, `novelty_authorization=NONE`. The current data contract still requires an independently qualified held-out RGB-D/pose split, frozen camera/depth conventions, and future-answer isolation before formal selector experiments.

## Evidence table

| Primary work | What it establishes | Direct overlap with this project | Testable gap / hypothesis for our work | Reviewer risk |
|---|---|---|---|---|
| **WorldMem (NeurIPS 2025 / arXiv:2504.12369)** | Stores frame/state memory (pose and timestamp), uses memory attention, FOV/time retrieval, and evaluates revisits and dynamic events. The paper notes that view overlap can fail when views are blocked. | Geometry-grounded long-term memory, explicit retrieve, revisit consistency. | **H1 (history-only risk):** a source-conflict/occlusion signal computed before the future query predicts future RGB-D/pose error better than FOV/time confidence. Must be tested on a legal held-out split with the same consumer and memory budget. | SOCF may look like a renamed retrieval confidence or an extension of FOV filtering unless it predicts held-out future loss and survives matched baselines. |
| **Video World Models with Long-term Spatial Memory (NeurIPS 2025)** | Separates working, spatial point-map, and episodic reference-frame memories; reports quality/consistency/context gains. | Long-term spatial memory and explicit 3D memory are already established. | **H2 (evaluation contract):** under identical slots, input bytes, forward count and generation steps, a future-state RGB-D/pose metric can distinguish history policies even when PSNR/LPIPS cannot. | A new memory selector without a new measurable problem is likely judged incremental. |
| **Long-Context State-Space Video World Models (ICCV 2025)** | Uses block-wise SSM scanning plus dense local attention to extend temporal memory; evaluates spatial retrieval/reasoning and efficiency. | Long context and memory efficiency are already pursued architecturally. | **H3 (failure localization):** source-level geometry conflict remains measurable after replacing temporal attention with a long-context state summary; if not, the proposed mechanism is backbone-specific. | A gain may be attributed to context length/SSM rather than geometry-risk selection. |
| **GEN3C (CVPR 2025)** | 3D-informed, camera-controlled, world-consistent video generation; establishes explicit 3D conditioning as a strong baseline family. | Camera control and 3D consistency target the same proposal outcome. | **H4 (consumer-level necessity):** a selector that changes only history admission should improve future depth/reprojection while keeping camera trajectory and generator fixed; compare against GEN3C-like geometry conditioning where available. | Improvements from stronger 3D conditioning can swamp a selector effect; must report same-generator paired comparisons. |
| **World-consistent Video Diffusion with Explicit 3D Modeling (CVPR 2025)** | Unifies single-image-to-3D, MVS and camera-controlled video through explicit 3D modeling. | Explicit geometry and cross-view consistency overlap strongly. | **H5 (model-agnostic measurement):** future-state score and source intervention should identify failure even when explicit 3D reconstruction metrics are good; otherwise the proposed benchmark adds no value. | Reviewers may view future RGB-D scoring as a repackaging of reconstruction/novel-view metrics. |
| **ViewRope (arXiv:2602.07854; ICLR World Models workshop 2026)** | Injects patch-level camera rays into attention and performs geometry-aware sparse frame selection; includes loop-closure diagnostics and counterfactual exclusion of selected frames. | It directly covers geometry-aware frame relevance and counterfactual selection. | **H6 (orthogonal mechanism):** source-conflict risk + abstention must improve tail future error even when ViewRope-style ray relevance is matched; otherwise SOCF is subsumed by geometry-aware attention. | Highest near-neighbor risk for “geometry-aware selection” and counterfactual claims. Do not claim those components as novel. |
| **Spatia (CVPR 2026)** | Maintains an updatable 3D point-cloud memory and updates it through visual SLAM with dynamic/static disentanglement. | Updatable spatial memory and dynamic handling overlap. | **H7 (admission/invalidation):** stale-memory invalidation should reduce leave-change-return failures without reducing static-scene coverage at equal update/slot cost. | DLV/admission could be seen as standard map maintenance; requires dynamic-specific causal failure evidence. |
| **WorldPack (under review TMLR, 2025)** | Combines trajectory packing with spatial scoring and adaptive compression; reports efficiency and long-horizon consistency. | Fixed-budget history compression and spatial scoring overlap. | **H8 (risk vs compression):** risk-aware selection should retain performance at equal packed-token/byte budget, and its benefit should concentrate in tail geometry errors rather than average image metrics. | A risk selector may be interpreted as another compression heuristic; equal token/latency accounting is essential. |

## Synthesis: what remains potentially distinct

1. **The measurable question is narrower than “geometry-aware memory.”** The nearest papers already cover geometry-conditioned storage, retrieval, point maps, sparse attention, dynamic updates, and counterfactual frame exclusion. The defensible gap is a *history-only, source-level risk prediction contract* evaluated against an independently held-out future RGB-D/pose target inside the same complete world-model consumer.
2. **SOCF-A is conditional, not established.** Its possible contribution is correlated source-geometry conflict plus calibrated abstention/invalidation. It is only distinguishable if it predicts future error and improves tail risk at equal budget after matching FOV/pose/visibility/ray relevance baselines.
3. **FGB-Future is the safer contribution.** A fixed-budget, future-state benchmark can remain scientifically useful if all selectors fail; it should be frozen before looking at held-out answers and should report RGB, depth, reprojection, pose, coverage, tail/CVaR, and cost together.
4. **Ghosting is a diagnostic axis.** Existing papers mostly emphasize PSNR/LPIPS/FVD, while the project has observed low MSE with high-frequency instability in sealed development outputs. This motivates a pre-registered ghosting/edge consistency metric, but it is not yet a causal mechanism or method result.

## Minimal falsification matrix

| Hypothesis | Cheapest decisive experiment | Kill criterion |
|---|---|---|
| H1: source-conflict predicts future error | Calibration-only fit; frozen test selector; AUROC/AUPRC and calibration at nominal 0.8/0.9 coverage | No improvement over confidence/visibility or coverage error > 0.05 |
| H2: future-state benchmark reveals differences | Same candidate pool, k=2/4/8, fixed seed and consumer; score after prediction seal | All methods tied within pre-registered tolerance, or metric direction conflicts across RGB/depth/pose |
| H3: mechanism is backbone-independent | Re-run selector-free diagnostic on one alternate long-context configuration, no method training | Signal disappears or is fully explained by context length |
| H4/H5: selector effect survives geometry-conditioned baselines | Paired same-generator source admission swap; externally supplied, held-out future RGB-D/pose reference | Mean and tail future loss do not improve, or only proxy image metrics improve |
| H6: SOCF is orthogonal to ray relevance | Add ViewRope/ray score as a fixed baseline feature; compare equal-budget selectors | SOCF adds <1% relative paired improvement and no tail/coverage advantage |
| H7: invalidation helps dynamic revisits | Leave-change-return trajectories; pre-registered two-strike invalidation and recovery | No reduction in stale-object error or static coverage regresses |
| H8: risk beats compression heuristic | Equal packed bytes/tokens and wall-clock; compare spatial score, random, recent, confidence, risk | Gain vanishes after equal-cost matching |

## Required report language

- “Recent primary work establishes X” may be used with a citation.
- “Our method is novel” is prohibited until the above tests, cross-scene replication, and independent review pass.
- A positive pre-Gate pilot is implementation evidence only; it cannot be promoted to scientific validation.

## Primary sources checked (accessed 2026-09-16, Asia/Shanghai)

- WorldMem, arXiv: https://arxiv.org/abs/2504.12369
- Video World Models with Long-term Spatial Memory, NeurIPS 2025: https://proceedings.neurips.cc/paper_files/paper/2025/hash/467655d26fcc207bca08915dc91964c6-Abstract-Conference.html
- Long-Context State-Space Video World Models, ICCV 2025: https://openaccess.thecvf.com/content/ICCV2025/html/Po_Long-Context_State-Space_Video_World_Models_ICCV_2025_paper.html
- GEN3C, CVPR 2025: https://openaccess.thecvf.com/content/CVPR2025/html/Ren_GEN3C_3D-Informed_World-Consistent_Video_Generation_with_Precise_Camera_Control_CVPR_2025_paper.html
- World-consistent Video Diffusion with Explicit 3D Modeling, CVPR 2025: https://openaccess.thecvf.com/content/CVPR2025/html/Zhang_World-consistent_Video_Diffusion_with_Explicit_3D_Modeling_CVPR_2025_paper.html
- ViewRope, arXiv: https://arxiv.org/abs/2602.07854
- Spatia, CVPR 2026: https://openaccess.thecvf.com/content/CVPR2026/papers/Zhao_Spatia_Video_Generation_with_Updatable_Spatial_Memory_CVPR_2026_paper.pdf
- WorldPack (working paper): https://openreview.net/pdf?id=zJuiG3PiNJ

## Provenance and limits

The search used official proceedings, OpenReview, and arXiv primary pages. CVF HTML pages returned HTTP 403 during one open attempt; their search-result metadata and canonical URLs were retained, and no performance number from those pages is used here. No external model was executed. The table is an innovation-risk and experiment-design artifact, not a novelty proof.

### Additional near-neighbor pressure (checked after initial table)

- **Memory Forcing (arXiv:2510.03198, ICLR 2026 submission)** combines hybrid training, chained forward training, point-to-frame retrieval, and incremental 3D reconstruction. This means a proposed DLV/invalidation or point-to-frame selector is not automatically new. A defensible difference would require a *history-only stale-risk predictor* evaluated on real leave-change-return RGB-D/pose trajectories at equal update and memory cost.
- **Future Forcing (arXiv:2605.30083, 2026)** proposes a training-free future-aware KV-cache policy using a proxy for future query distributions and affine-subspace token merging. Therefore “future-aware fixed-budget memory” is also a known algorithmic direction. FGB-Future must be framed around an independently held-out **future-state geometry evaluation contract**, not a generic future-aware cache policy; SOCF must show incremental value after matching Future-Forcing-style importance where feasible.
- **WorldPlay (arXiv:2512.14614)** uses reconstituted context memory and context forcing for long-term geometric consistency at real-time speed. This further raises the bar for any claim that memory re-access or context reconstruction alone is novel.

These additions strengthen the negative-space conclusion: the project should prioritize a strict measurement problem (future RGB-D/pose, source provenance, equal cost) and only promote a method if it survives these algorithmic near-neighbors.
