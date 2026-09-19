# Innovation Frontier Next — recent-neighbor audit

- Date: 2026-09-12 (Asia/Shanghai)
- Scope: S92 tail-risk decomposition, S93 Gate-0 failures, S94 evaluation contract, and the GRC-Memory candidate.
- Status: literature-grounded frontier scan; no new method is validated.

## 1. What recent work already covers

| Work | Evidence-backed mechanism | Consequence for GRC-Memory |
|---|---|---|
| MemoNav (CVPR 2024) | Uses short-term, long-term, and working memory; a forgetting module retains an informative fraction for navigation. | “Keep only informative history” and a forgetting module are already established. GRC cannot claim novelty from a generic memory selector. It differs only if the selector is tied to calibrated geometric risk and an independent future-state target. |
| Learning 3D Persistent Embodied World Models (2025) | Predicts future RGB-D video, aggregates it into a persistent 3D map, and conditions generation on the map for long-horizon planning. | RGB-D future prediction plus persistent 3D memory is directly covered. A proposal that only adds “3D memory for long-horizon consistency” is not new. |
| Video World Models with Long-term Spatial Memory (2025) | Geometry-grounded long-term spatial memory with explicit storage and retrieval; custom data for 3D memory. | Geometry-grounded memory storage/retrieval is already a stated contribution. GRC needs a sharper problem definition and controlled selection/evaluation rather than another memory module. |
| WorldPlay (ICML/arXiv 2025–26) | Reconstituted Context Memory rebuilds context and uses temporal reframing to retain geometrically important long-past frames; context forcing preserves memory use during distillation. | “Geometrically important old frames should be retained” is already present. The unexplored candidate is whether measurable risk-calibrated historical evidence predicts future geometric error under a fixed budget, not whether old frames matter at all. |
| AutoScape (2025) | Joint RGB-D diffusion, point-cloud conditioning from previous keyframes, and warp-consistent guidance for long-horizon geometry. | RGB-D + existing geometry + warp consistency is covered on the generation side. It does not, from the abstract, define a calibrated observation-level selection objective. |
| Spatia (CVPR 2026) | Persistent 3D point-cloud memory, iterative video generation, and visual-SLAM memory updates; dynamic/static disentanglement. | Updatable spatial memory and long-horizon view consistency are covered. A risk-calibrated selector must be compared against persistent-map and SLAM-style memory, not presented as the first updateable spatial memory. |
| Geometry-as-context (CVPR 2026) | Iteratively estimates current-view geometry and uses a 3D scene to render/restore novel views in an autoregressive camera-controlled generator. | Geometry as conditioning/context is covered. It does not by itself establish that a historical frame's calibrated risk predicts a downstream future error. |
| Latent Spatial Memory for Video World Models (2026 preprint) | Persistent 3D cache directly in diffusion latent space to reduce generation cost and memory footprint. | Memory representation/compression is an active direction; fixed compute must be measured and compared against latent/explicit caches if GRC is implemented. |

## 2. Candidate claims that remain potentially independent

### Candidate A — a new evaluation problem (strongest, but still unverified)

**Question:** Under a fixed memory/computation budget, does the calibrated geometric risk of a historical observation predict its *incremental future RGB-D/pose error* when that observation is consumed by the world-model path?

This is narrower than “geometry-aware memory.” The proposed unit of analysis is an observation (or memory item), the target is a future query not used by selection, and the test requires the complete consumer path. A defensible contribution would require:

1. calibration data separated from all future evaluation queries;
2. exact source identity and frame-level provenance;
3. fixed budget (S94 contract: k=4, sensitivity k=2 and k=8) and equal compute/bytes/forward-count accounting;
4. at least five independent trajectories and three future queries per trajectory;
5. mean AbsRel plus worst-5% mass, CVaR95, reprojection/coverage, and latency/memory;
6. comparison against recent/random, pose-only, coverage, depth-only, confidence, WorldTrace/MemRoPE/WORLDMEM-style and Fisher/EIG selectors;
7. an independent target showing that a selector’s score predicts future risk, not only reconstruction quality at the current frame.

This is a candidate problem statement, not a validated method. S92 only shows descriptive tail-risk behavior in saved data; it does not show causal value of a selected memory.

### Candidate B — counterfactual memory value (high novelty, high risk)

For one history item, hold seed, query trajectory, model, other memories, and budget fixed; delete/replace only that item and measure future geometry change. This addresses incremental causal value more directly than correlation. It is expensive and only meaningful after Gate 0 supplies synchronized RGB-D/pose and a working consumer path. It must not be claimed from S91R/S91R-C.

### Candidate C — geometry–appearance interaction audit (best immediate diagnostic)

Use a preregistered 2x2 factorization: trusted vs perturbed geometry × ordinary vs geometry-constrained appearance. Test the interaction term on future depth/pose metrics. This could reveal why S86/S92 show many small improvements but a small high-error tail. It is an analysis contribution unless it yields a repeatable failure law across independent scenes.

## 3. Reviewer-style score and fatal-flaw check

| Proposed framing | Novelty if fully proven | Evidence now | Main reject reason |
|---|---:|---|---|
| “A geometry-aware memory module for long-horizon generation” | 3–5/10 | Covered by multiple recent memory/3D-map papers | Incremental combination of known memory and geometry components |
| “Conformal/calibrated risk for memory selection” alone | 3–5/10 | Calibration/conformal risk are established tools | Calibration is a tool, not a new world-model problem |
| Candidate A: fixed-budget future geometric value of historical evidence | 7–8/10 potential | Problem is not yet empirically established | Missing Gate-0 data and no complete consumer-path causal test |
| Candidate B: counterfactual incremental memory effect | 7–8.5/10 potential | Hypothesis only | Expensive design; stochastic generation confounds; data/compute risk |
| Candidate C: geometry–appearance interaction diagnosis | 6–7/10 potential | S86/S92 motivate it descriptively | Could remain a dataset-specific ablation |

**Current verdict:** keep Candidate A as the research-question candidate and use Candidate C as the immediate diagnostic. Do not title the paper around GRC-Memory as a validated method. S94’s stop rules remain active: no leakage, unfair budget, missing source identity, or failure to beat the strongest baseline may pass.

## 4. Data and evidence boundary

- TUM S93 frame probe is not a valid Gate 0: relative AVI PTS, no timestamped RGB-D pair, and the depth stream decoded as 8-bit RGB rather than verified 16-bit depth. An accidental full RGB AVI download is retained as an implementation audit and is not a scientific result.
- 3RScan S94 is the best current replacement candidate because official metadata advertises calibrated RGB-D, 6DoF poses, intrinsics, and reference/rescan groups. Locally only metadata and ZIP header/tail probes were obtained; full frame bodies, K/units, synchronization, and data-use authorization remain unverified. No S91/GRC run is permitted.
- S92 is descriptive saved-data analysis: high-magnitude error tails can offset many pixel-wise improvements. It does not establish geometry causality, future prediction, or selector superiority.

## Sources (official/primary pages)

- MemoNav CVPR 2024: https://openaccess.thecvf.com/content/CVPR2024/html/Li_MemoNav_Working_Memory_Model_for_Visual_Navigation_CVPR_2024_paper.html
- Learning 3D Persistent Embodied World Models: https://arxiv.org/abs/2505.05495
- Video World Models with Long-term Spatial Memory: https://arxiv.org/abs/2506.05284
- WorldPlay: https://arxiv.org/abs/2512.14614
- AutoScape: https://arxiv.org/abs/2510.20726
- Spatia CVPR 2026: https://openaccess.thecvf.com/content/CVPR2026/papers/Zhao_Spatia_Video_Generation_with_Updatable_Spatial_Memory_CVPR_2026_paper.pdf
- Geometry-as-context CVPR 2026: https://openaccess.thecvf.com/content/CVPR2026/html/Hu_Geometry-as-context_Modulating_Explicit_3D_in_Scene-consistent_Video_Generation_to_Geometry_Context_CVPR_2026_paper.html
- Latent Spatial Memory preprint: https://arxiv.org/abs/2606.09828
