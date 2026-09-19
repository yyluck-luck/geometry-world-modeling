# Innovation Round 7 — Registered RGB-D Future Geometry and Source Intervention Audit

**Date:** 2026-09-16 (Asia/Shanghai)  
**Role:** bounded 2025–2026 primary-source scan; compare candidate SOCF-A/FGB-SI against current benchmarks and memory systems.  
**Status:** literature evidence only; no project data, future answers, model inference, or Gate0 bypass. `new_method_validated=false`, `novelty_authorization=NONE`.

## Question

Can a contribution remain distinctive if it evaluates whether a *specific historical RGB-D memory source* changes an independently held-out future geometric state, under a fixed candidate pool and memory budget? The relevant unit is not retrieval rank or visual plausibility; it is source-level responsibility measured through a registered RGB-D/pose future outcome.

## Current primary-source pressure

| 2025–2026 work | What it establishes | Consequence for our claim |
|---|---|---|
| **Video World Models with Long-term Spatial Memory**, NeurIPS 2025 | Geometry-grounded point-map spatial memory plus episodic keyframes; stores/retrieves memory for revisit consistency. | Point-cloud memory and episodic retrieval are occupied baselines. A geometry-aware memory module alone is not new. It reports PSNR/SSIM/LPIPS/VBench and qualitative camera accuracy; our evaluation must use held-out RGB-D/pose and source-level interventions. |
| **GIM-World**, arXiv:2606.02436 (2026) | Implicit fixed-size memory, camera-queryable geometry supervision, information-guided pruning. | Fixed-size geometry memory and pruning are direct neighbors. “Geometry + pruning” cannot be the headline. A possible gap is a frozen *decision/evaluation contract* tied to externally supplied, held-out future RGB-D/pose reference, not another memory encoder. |
| **WorldTrace / Addressable Memory**, arXiv:2608.07408 (2026) | Virtual in-distribution positions keep compressed KV slots addressable; Field/Landmark compression; LoopBench revisit benchmark. | Addressability, landmark retention and long-detour revisit are occupied. SOCF-A must compare against addressable/landmark controls where consumer-compatible and must test geometric error rather than only recall/temporal metrics. |
| **World in World**, arXiv:2609.11548 (submitted 10 Sep 2026) | Training-free interface with camera/time-labeled evidence, persistent point correspondences, token-level support, and evidence-wise attention CFG. | Source/evidence labels, support and geometry-conditioned routing are now explicit in a contemporaneous method. A source tag, router, or per-evidence weight is not sufficient novelty. A remaining gap may be whether source conflict predicts *future metric geometry* before consumption and whether abstention helps at equal budget. |
| **WorldRoamBench**, arXiv:2606.31672 (2026) | Long-horizon open-world benchmark; segment-level drift; controllability-gated physics/3D consistency; action-decoupled scene-memory point-cloud protocol. | FGB-Future must expose a failure not captured by transition-localized point-cloud memory or segment drift. It must fix candidate pools and evaluate a specific source intervention, not rename a drift metric. |
| **MIND**, arXiv:2602.08025 (2026) | Closed-loop revisited benchmark with 250 videos, multiple action spaces and memory-consistency metrics. | Revisit memory and action generalization are established. MIND does not establish registered RGB-D sensor contracts or source-level causal responsibility; this is a possible but unverified distinction. |
| **PlayWorld**, arXiv:2608.13552 (2026) | Agent-player benchmark with 171 long-horizon objectives; geometry consistency, interaction fidelity, out-of-sight and insight evolution. | Objective-driven long-horizon evaluation is occupied. Our protocol must be a sensor-level, answer-isolated measurement rather than agent-player scoring. |
| **MBench**, arXiv:2606.00793 (2026) | Memory taxonomy: entity, environment and causal consistency; 12 subdimensions over real-captured long videos. | “Causal consistency” as a broad benchmark label is occupied. A narrower registered RGB-D future-geometry estimand and source intervention could differ, but only with an explicit proof of incremental coverage. |
| **What-If World**, arXiv:2605.27589 (2026) | 319 paired prompt interventions anchored on real frames; APEO scores adherence, physics, environment preservation and outcome divergence. | Counterfactual paired evaluation is no longer novel in general. Our distinction must be *memory-source intervention* with the same consumer, same candidate pool and registered metric/pose/depth answer, rather than prompt intervention. |
| **DiST-4D**, ICCV 2025 | Joint future metric-depth/RGB temporal prediction and spatial NVS with cycle consistency. | Future metric depth is an established output/representation. We should evaluate future depth as an answer, not claim predicting metric depth itself as new. |
| **WVD**, CVPR 2025 | Joint RGB+XYZ diffusion and reprojection optimization for 3D-consistent video/image tasks. | RGB/XYZ joint modeling and reprojection losses are strong geometry controls; our method must remain consumer-level and memory-source-specific. |
| **L3DE**, ICCV 2025 | Learned 3D evaluation using motion/depth/appearance cues rather than manual defect labels. | Learned geometry evaluation exists; a new metric needs a failure case and reliability validation. Registered sensor GT and explicit depth/pose errors are safer than inventing another perceptual score. |

## Defensible gap after this audit

A narrow, conditional contribution can remain distinct only as a **Source-Intervention Future Geometry (SIFG) protocol**:

> Under a frozen world-model consumer, fixed candidate pool, fixed memory budget, exact replay controls, and an answer-isolated registered RGB-D/pose split, quantify the paired effect of removing/replacing one historical source on future metric-depth, reprojection and pose outcomes; test whether a history-only conflict signal predicts the signed effect and supports abstention.

This is not yet a method. It is a measurement/benchmark hypothesis. SOCF-A is the possible policy (source-conflict score + abstain/route), while FGB-SI/SIFG is the evaluation contract. The distinction from current works depends on all of the following being true:

1. The intervention unit is a source-memory item actually consumed by the same VMem path, not a prompt, a global model input, or a post-hoc mask.
2. Historical RGB-D/intrinsics/extrinsics/timestamps are used to form the score; future RGB-D/pose is sealed until prediction and hash sealing finish.
3. The outcome is registered metric depth/pose/reprojection in an held-out future window, with RGB/ghosting secondary.
4. Candidate count, slot/token budget, model checkpoint, camera trajectory, RNG and denoising settings are identical across alternatives.
5. The effect is compared against recent/uniform/random, pose/FoV, coverage/landmark, confidence/uncertainty, addressable-memory and future-aware cache controls.
6. Source permutation and support/pose/edge-density matched placebos fail to reproduce the effect.

If any item is absent, the contribution should be called a diagnostic or negative result, not a causal method.

## Reviewer score (provisional, not measured)

| Candidate framing | Novelty | Scientific value | Feasibility after Gate0 | Neighbor risk | Review verdict |
|---|---:|---:|---:|---:|---|
| GRC-Memory = risk score + future utility + fixed budget | 3.0/10 | 7.0 | 6.0 | 9.5 | Reject as standalone; GIM-World, WorldTrace, Future Forcing and related selectors occupy the axes. |
| SOCF-A = history-only source conflict with abstention | 6.5/10 | 8.5 | 5.5 | 7.0 | Conditional; must beat uncertainty/pose/coverage/addressability/future-aware controls on held-out tail geometry. |
| FGB-SI = fixed-budget source-intervention future geometry benchmark | 7.0/10 | 8.5 | 7.0 | 6.5 | Safest current framing, but only if it measures a gap missed by WorldRoamBench/MIND/MBench/What-If. |
| SIFG + SOCF policy | 7.5/10 | 9.0 | 5.0 | 7.0 | Potentially strong joint contribution; no authorization until independent held-out evidence and cross-scene replication. |

## Cheapest decisive experiment after Gate0

**Experiment name:** *Registered RGB-D Source Swap with Future Geometry Scoring* (SIFG-01; downstream of S103 baseline).

- Freeze one candidate pool, `k`, source IDs/order, camera/K/extrinsics, temporal windows, checkpoint/weights, noise/RNG, denoising steps and output count.
- Fit conflict scores only on calibration history: reprojection residual, metric-depth disagreement, visibility conflict and source identity. Seal the selector before reading future answers.
- For each selected source, run exact paired interventions: original source versus removal or matched replacement. Recompute every downstream consumer state; do not freeze target-source descendants.
- Seal output artifacts and hashes, then open externally supplied, held-out future RGB-D/pose reference. Score depth AbsRel, metric reprojection, pose error, static-scene ghosting/high-frequency residual, and 95th percentile/CVaR tail.
- Compare to recent/uniform/random, pose/FoV, coverage/landmark, confidence/uncertainty, addressability/landmark and future-aware cache controls at identical candidate and compute budgets.
- Include exact-replay variance, source-ID permutation, support/pose/edge-density matched mask placebo, and per-scene paired bootstrap intervals.

**Promotion rule:** SOCF-A may be called a method only if it improves both mean and tail future geometry versus the strongest non-SOCF control on at least two independent held-out scenes and two horizons, while surviving placebos and replay-noise limits. Otherwise retain SIFG-01 as an evaluation or negative-mechanism result.

## Kill criteria

Stop method promotion if the signal is explained by pose/FoV/coverage/landmark/uncertainty, if the source intervention has no reproducible future depth/pose effect, if signs flip across scenes, if RGB improves while geometry worsens, if exact replay is as large as the effect, if downstream descendants are frozen, or if future answers influence selector/thresholds. Do not rename a benchmark score to rescue a failed method.

## Gate0 implication

The audit does not authorize a formal run. Gate0 still requires binding camera and depth semantics, pose/frame convention, one-to-one RGB-D pairing, future-GT isolation, independent held-out identity, fair budget, checkpoint/code hashes and independent readback. Once a signed PASS manifest exists, run selector-free VMem S103 first; only after its outputs are sealed may SIFG-01/SOCF-A be evaluated. Every long GPU run must be launched and monitored in the persistent remote `tmux`/`screen` workflow.

## Primary sources checked (accessed 2026-09-16)

- [World in World, arXiv:2609.11548](https://arxiv.org/abs/2609.11548)
- [GIM-World, arXiv:2606.02436](https://arxiv.org/abs/2606.02436)
- [WorldTrace / Addressable Memory, arXiv:2608.07408](https://arxiv.org/abs/2608.07408)
- [Video World Models with Long-term Spatial Memory, NeurIPS 2025](https://arxiv.org/abs/2506.05284)
- [WorldRoamBench, arXiv:2606.31672](https://arxiv.org/abs/2606.31672)
- [MIND, arXiv:2602.08025](https://arxiv.org/abs/2602.08025)
- [PlayWorld, arXiv:2608.13552](https://arxiv.org/abs/2608.13552)
- [MBench, arXiv:2606.00793](https://arxiv.org/abs/2606.00793)
- [What-If World, arXiv:2605.27589](https://arxiv.org/abs/2605.27589)
- [DiST-4D, ICCV 2025](https://mlanthology.org/iccv/2025/guo2025iccv-dist4d/)
- [World-consistent Video Diffusion (WVD), CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/html/Zhang_World-consistent_Video_Diffusion_with_Explicit_3D_Modeling_CVPR_2025_paper.html)
- [L3DE, ICCV 2025](https://openaccess.thecvf.com/content/ICCV2025/html/Chang_How_Far_are_AI-generated_Videos_from_Simulating_the_3D_Visual_ICCV_2025_paper.html)

**Evidence boundary:** current-year papers were read through primary arXiv/CVF/PMLR or official project pages. No search snippet or model-generated summary is treated as project evidence. No claim of novelty validation or Gate0 completion is made.
