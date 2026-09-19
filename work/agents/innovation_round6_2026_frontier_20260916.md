# 2026 Frontier Innovation Scan: Long-Horizon Geometric Memory

**Date:** 2026-09-16 (Asia/Shanghai)  
**Scope:** Primary-source scan of 2026 papers/preprints relevant to long-horizon world models, dynamic 3D memory, and reliability/abstention. This is a novelty audit and experiment proposal; it does not validate a method and does not authorize a formal GPU run before Gate 0.

## Evidence boundary

The search was refreshed against 2026 primary pages on 2026-09-16. Conference status is stated conservatively: WorldStereo and Dynamic Visual SLAM are identified as CVPR 2026 papers; ReWorld, AlayaWorld v1.1, WorldRoamBench, Future Forcing, and Next Forcing are 2026 arXiv reports unless a conference venue is explicitly confirmed on the primary page. Search snippets and secondary summaries are not treated as evidence of our method's effectiveness.

## 2026 frontier findings

| Work | 2026 status and mechanism | Direct overlap with our candidate | Defensible remaining gap |
|---|---|---|---|
| **ReWorld** (arXiv:2608.23565, Aug. 2026) | Mixed local/global attention, pose-indexed landmark bank, bounded KV cache, sparse-history training, palindrome revisit trajectories. | Strong overlap with fixed-budget long-horizon memory and pose/landmark retrieval. | It does not define source-level geometric conflict, calibrated abstention, or a held-out future RGB-D/pose intervention contract. SOCF-A must beat pose/landmark and recent/uniform controls at equal budget. |
| **AlayaWorld v1.1** (arXiv:2608.13492, Aug. 2026) | Streaming 3D point-cache renderer, motion-aware latent conditioning, causal memory encoding, hard memory dropout, unified causal-VAE protocol. | Strong overlap with explicit 3D cache and memory validity under long generation. | No source-conflict risk score or selective write/abstain rule tied to externally supplied, held-out future RGB-D/pose reference. |
| **WorldRoamBench** (arXiv:2606.31672, Jun. 2026) | Open-world benchmark with action, segment-level visual drift, controllability-gated physics/3D consistency, transition-localized point-cloud memory evaluation. | Direct pressure on FGB-Future as a benchmark/evaluation claim. | FGB-Future can be distinct only by fixing a candidate pool and memory budget, intervening on one source item, and measuring signed future RGB-D/pose change on an held-out future split. It must report whether the intervention changes geometry, not only aggregate drift. |
| **WorldStereo** (CVPR 2026; arXiv:2603.02049) | Global Geometric Memory and Spatial Stereo Memory; incrementally merged point-cloud cache plus correspondence-constrained attention. | Direct overlap with geometry-aware memory and 3D correspondence retrieval. | It is a memory/conditioning architecture. Our possible increment is a consumer-agnostic *decision contract* that can reject an inconsistent source before it enters memory, but this is only credible if it improves future geometry at equal compute. |
| **Dynamic Visual SLAM using a General 3D Prior** (CVPR 2026) | Filters dynamic regions with feed-forward reconstruction and aligns depth with patch-based bundle adjustment. | Overlap with dynamic landmark invalidation (DLV) and geometry conflict signals. | DLV must show a long-horizon memory consequence (leave-change-return or occlusion reappearance) beyond standard dynamic-region filtering; otherwise it is a rebranding of SLAM filtering. |
| **Future Forcing** (arXiv:2605.30083, May 2026) | Training-free future-aware KV cache policy using pre-RoPE query stationarity, future query proxy, and affine-subspace merging. | Direct overlap with “future-aware fixed-budget selection.” | FGB-Future cannot claim future-aware selection as new. Its contribution must be the future-state *evaluation protocol* and source intervention; SOCF-A must compare against a Future-Forcing-style importance control where feasible. |
| **Next Forcing** (arXiv:2606.11187, Jun. 2026) | Multi-chunk prediction auxiliary modules supervise several future horizons and accelerate inference. | Reinforces that future prediction is already a model/training axis. | Our question must remain memory evidence validity, not another future-prediction loss. |
| **USplat4D: Uncertainty Matters in Dynamic Gaussian Splatting** (ICLR 2026) | Per-Gaussian time-varying uncertainty and a spatio-temporal graph propagate reliable motion cues through occlusion. | Overlap with uncertainty-weighted dynamic landmarks and the intuition that repeatedly observed geometry is a reliable anchor. | SOCF-A must operate at *source-memory admission/abstention* level and demonstrate future RGB-D benefit; a per-primitive uncertainty module alone is no longer novel. |
| **FreeScale: Scaling 3D Scenes via Certainty-Aware Free-View Generation** (CVPR 2026) | Certainty-aware view sampling chooses novel views least affected by reconstruction errors, with a view-graph curriculum. | Overlap with geometry-risk/certainty-guided selection. | Our possible distinction is selecting historical evidence for a fixed world-model consumer and scoring externally supplied, held-out future RGB-D/pose reference, rather than selecting synthetic training views. Any view-coverage selector is a required baseline. |

## Reviewer-style novelty matrix (current candidate definitions)

Scores are provisional review estimates, not measured results (10 = strongest). “Neighbor risk” is the likelihood that reviewers regard the idea as an incremental recombination.

| Candidate | Novelty | Scientific value | Feasibility after Gate 0 | Neighbor risk | Verdict |
|---|---:|---:|---:|---:|---|
| Original GRC-Memory (risk + future utility + fixed budget) | 3.5 | 7.0 | 6.0 | 9.0 | Reject as a standalone headline; occupied axes are now too close to ReWorld/AlayaWorld/Future Forcing. |
| **SOCF-A** (source-conflict direction + calibrated abstention) | 7.0 | 8.5 | 5.5 | 6.5 | Strongest conditional method candidate. Must prove incremental future-tail benefit after pose/coverage/landmark/Future-Forcing controls. |
| **FGB-Future** (fixed-budget future-state evaluation contract) | 7.0 | 8.8 | 7.5 | 6.0 | Safest problem/benchmark route. Must expose a failure omitted by WorldRoamBench and avoid metric renaming. |
| DLV (dynamic landmark invalidation) | 6.0 | 8.0 | 5.0 | 7.5 | Conditional; only after real dynamic/occlusion episodes and comparison to dynamic SLAM filtering. |
| Counterfactual source intervention as a diagnostic | 7.5 | 8.5 | 5.0 | 5.5 | High-value measurement module; best way to test whether SOCF signal is causal rather than a proxy. |

**Reliability-specific warning.** 2026 work already treats uncertainty as a mechanism for dynamic 3D reconstruction (USplat4D), certainty as a sampling policy (FreeScale), and abstention as a general reliability control. Therefore, the word *uncertainty*, a conformal quantile, or an abstention threshold cannot be the contribution by itself. The unit that may remain distinctive is a frozen source intervention whose outcome is an independently held-out future geometric state under an explicitly charged memory budget.

## One decisive post-Gate-0 experiment

**Experiment name:** *Equal-Budget Source-Intervention Future Geometry Test* (FGB-SI; S106 after baseline sealing).

**Question:** Does a history-only source-conflict signal identify which memory item changes an independently held-out future geometry outcome, beyond pose distance, visibility/coverage, landmark retrieval, and future-aware cache importance?

**Protocol:**

1. Freeze one candidate pool per sequence and a real memory budget `k` (token/slot/VRAM accounting). Freeze RNG, model checkpoint, denoising steps, camera trajectory, and all consumer settings.
2. Build calibration scores from history only: reprojection residual, depth disagreement, visibility conflict, source identity, pose distance, coverage, and a confidence baseline. Do not access future frames during selector construction.
3. For each candidate source `i`, run paired interventions: keep every condition and random seed fixed, then remove or replace only `i`. Seal outputs before reading future GT.
4. Score an held-out future segment with depth AbsRel, scale-aware reprojection error, pose error, static-scene ghosting/edge metrics, coverage, and upper-tail/CVaR error. Report paired deltas and bootstrap confidence intervals by scene, not only pooled averages.
5. Compare recent-k, uniform-k, random-k (20 seeds), pose-distance-k, coverage-k, landmark-bank/retrieval, confidence-k, Future-Forcing proxy (when implementation-compatible), SOCF-A, and oracle upper bound. Every method receives identical candidate pool and budget.
6. Run a source-permutation negative control and an exact-replay noise test. If SOCF-A cannot beat replay variation or fails to predict signed future deltas, kill the method claim and retain FGB-SI as an evaluation/negative-result contribution.

**Primary confirmatory endpoint:** mean paired future-depth AbsRel delta and 95th-percentile/CVaR delta relative to the strongest non-SOCF selector, averaged per held-out scene.  
**Secondary endpoints:** reprojection, pose, ghosting, static-scene regression, abstention rate, wall-time, and peak VRAM.  
**Success rule:** SOCF-A must improve both mean and tail future geometry on at least two independent held-out scenes, survive source-permutation and replay-noise controls, and show no pre-registered static-scene regression. Otherwise no method promotion.

## Implication for Gate 0 and GPU scheduling

This scan does not justify bypassing Gate 0. The first formal GPU job remains selector-free VMem baseline (S103), launched only after the camera/depth/pose/future-isolation/held-out/budget manifest is signed. FGB-SI is a later experiment and must run through the persistent remote `tmux`/`screen` launcher. No result in this note is a real-data method result.

## Sources (primary)

- [ReWorld, arXiv:2608.23565](https://arxiv.org/abs/2608.23565)
- [AlayaWorld v1.1, arXiv:2608.13492](https://arxiv.org/abs/2608.13492)
- [WorldRoamBench, arXiv:2606.31672](https://arxiv.org/abs/2606.31672)
- [WorldStereo, CVPR 2026 / arXiv:2603.02049](https://github.com/FuchengSu/WorldStereo)
- [Dynamic Visual SLAM using a General 3D Prior, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Zhong_Dynamic_Visual_SLAM_using_a_General_3D_Prior_CVPR_2026_paper.html)
- [Future Forcing, arXiv:2605.30083](https://arxiv.org/abs/2605.30083)
- [Next Forcing, arXiv:2606.11187](https://arxiv.org/abs/2606.11187)
- [USplat4D, ICLR 2026](https://proceedings.iclr.cc/paper_files/paper/2026/hash/26300457961c3e056ea61c9d3ebec2a4-Abstract-Conference.html)
- [FreeScale, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Jiang_FreeScale_Scaling_3D_Scenes_via_Certainty-Aware_Free-View_Generation_CVPR_2026_paper.html)

**Status:** `frontier_scan_complete=true`; `new_method_validated=false`; `novelty_authorization=NONE`.
