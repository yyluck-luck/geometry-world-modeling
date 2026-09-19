# Innovation Rotation 5 — Mechanism-Level Decomposition of Long-Horizon Ghosting

**Date:** 2026-09-16 (Asia/Shanghai)  
**Role:** bounded literature pressure test and pre-Gate experiment design  
**Status:** diagnostic/measurement candidate only; `novelty_authorization=NONE`, `new_method_validated=false`. No formal GPU run and no future-GT read were performed.

## Research question

The current VMem evidence contains a dangerous mismatch: RGB MSE can decrease while generated views still show ghosting, duplicated contours, smearing, and incorrect object shape. The narrow question is:

> Is long-horizon ghosting caused primarily by geometry error, appearance ambiguity, or an interaction in which appearance evidence amplifies a geometry conflict?

This is a mechanism question. It is stronger than asking whether an RGB score improved, but it does not by itself establish a new memory-selection method.

## What the recent primary literature already covers

1. **ViewDiff (CVPR 2024)** inserts 3D volume-rendering and cross-frame-attention layers into a pretrained diffusion U-Net and uses autoregressive multi-view generation. This makes geometry-conditioned cross-frame fusion an existing strong comparator; a new appearance/geometry gate cannot be presented as novel without a mechanism-level result beyond this precedent. Official CVPR page: https://openaccess.thecvf.com/content/CVPR2024/html/Hollein_ViewDiff_3D-Consistent_Image_Generation_with_Text-to-Image_Models_CVPR_2024_paper.html
2. **Geometry-guided Online 3D Video Synthesis with Multi-View Temporal Consistency (CVPR 2025)** uses refined depth, color-difference masks, TSDF accumulation in image space, and a blending network to address view and temporal consistency. It directly motivates a baseline that separates geometry accumulation from appearance blending. Official paper: https://openaccess.thecvf.com/content/CVPR2025/papers/Ha_Geometry-guided_Online_3D_Video_Synthesis_with_Multi-View_Temporal_Consistency_CVPR_2025_paper.pdf
3. **MET3R (CVPR 2025)** introduces a metric for measuring multi-view consistency in generated images. Its existence means that a proposed decomposition must report a geometry-aware multi-view metric, not rely on RGB MSE or qualitative examples alone. Official paper: https://openaccess.thecvf.com/content/CVPR2025/papers/Asim_MET3R_Measuring_Multi-View_Consistency_in_Generated_Images_CVPR_2025_paper.pdf
4. **Video Harmonization with Triplet Spatio-Temporal Variation Patterns (CVPR 2024)** models short-term spatial and long-term global/dynamic appearance variation and introduces a temporal-consistency metric. This is a precedent for measuring appearance consistency separately from geometry, so an appearance branch is a control and not an automatic contribution. Official CVPR page: https://openaccess.thecvf.com/content/CVPR2024/html/Guo_Video_Harmonization_with_Triplet_Spatio-Temporal_Variation_Patterns_CVPR_2024_paper.html
5. **Interventional Causal Representation Learning (ICML 2023)** shows why observational correlations are insufficient for identifying latent factors and studies identification under interventions. For this project, the implication is methodological: a 2x2 observational correlation is not enough to call the interaction causal; the geometry and appearance factors must be manipulated independently under a frozen consumer. Official PMLR page: https://proceedings.mlr.press/v202/ahuja23a.html

These works collectively make “add geometry guidance”, “add cross-frame attention”, “add a temporal consistency metric”, or “use a geometry/appearance gate” ordinary controls. The possible contribution is a *future-state mechanism diagnosis* that proves when an interaction, rather than either factor alone, determines long-horizon failure and that this diagnosis survives independent scenes and consumer-level interventions.

### Current-year (2025–2026) pressure test

The most relevant current-year evidence is already close to the proposal's setting:

- **Video World Models with Long-term Spatial Memory (NeurIPS 2025, published in NeurIPS 38 Main Conference)** uses geometry-grounded long-term spatial memory for revisit consistency. Its unit is a memory framework with store/retrieve mechanisms, so a source-level geometry/appearance interaction must beat this as a same-consumer diagnostic rather than compare only to no-memory. Official record: https://proceedings.neurips.cc/paper_files/paper/2025/hash/467655d26fcc207bca08915dc91964c6-Abstract-Conference.html (record accessed 2026-09-16).
- **Long-Context State-Space Video World Models (ICCV 2025)** trades block-wise SSM temporal memory against dense local attention and evaluates long-range memory. This is a strong architecture/long-context control; the proposed 2x2 experiment must hold architecture and context length fixed, otherwise an interaction can be an artifact of memory capacity. Official paper: https://openaccess.thecvf.com/content/ICCV2025/papers/Po_Long-Context_State-Space_Video_World_Models_ICCV2025_paper.pdf (record accessed 2026-09-16).
- **GeometryCrafter (ICCV 2025)** integrates per-frame geometry priors into a video-diffusion geometry estimator and evaluates across seven unseen datasets. This supports cross-dataset evaluation and warns that flickering/inaccurate geometry priors can contaminate a geometry/appearance diagnosis. Official paper: https://www.openaccess.thecvf.com/content/ICCV2025/papers/Xu_GeometryCrafter_Consistent_Geometry_Estimation_for_Open-world_Videos_with_Diffusion_Priors_ICCV2025_paper.pdf (record accessed 2026-09-16).
- **How Far Is Video Generation from World Model: A Physical Law Perspective (ICML 2025)** evaluates whether generated videos obey physical laws rather than relying only on visual similarity. This reinforces the requirement that future depth/pose/reprojection outcomes be primary and RGB MSE secondary. Official PMLR record: https://proceedings.mlr.press/v267/kang25g.html (record accessed 2026-09-16).
- A 2026 **Quantitative Video World Model Evaluation for Geometric-Consistency** preprint reports geometry-specific failures missed by perceptual metrics. It is not yet a peer-reviewed conference source; it is useful as a measurement warning only, not a novelty precedent. Official preprint: https://arxiv.org/abs/2605.15185 (record accessed 2026-09-16).

The 2024 CVPR/ICML works above are retained as established baselines. The 2025–2026 papers make the novelty bar stricter: the interaction must be measured in a long-horizon world-model consumer, across unseen scenes, with geometry-first outcomes and architecture/memory controls.


## Exact 2x2 experiment (pre-registered before formal execution)

Let `G` denote the geometry evidence supplied to the consumer and `A` the appearance evidence supplied by the historical memory. Both factors must have equal information budget across arms.

### Geometry factor

- `G+` (trusted geometry): calibrated RGB-D, intrinsics/extrinsics, timestamp pairing, and a fixed projection/visibility rule. The geometry input is not the future answer.
- `G-` (controlled geometry corruption): perturb only the geometry channel using a predeclared corruption family (depth scale/translation perturbation, pose perturbation, or structured local reprojection displacement), while retaining the same source RGB and the same number of geometry tokens. Corruption parameters are sampled before opening future answers and are recorded in the manifest.

The perturbation must be strong enough to create a measurable reprojection/depth residual but must not delete RGB pixels or change the candidate count. A no-op `G+` and an independently generated corruption seed are retained as controls.

### Appearance factor

- `A-` (ordinary appearance): the historical RGB condition passes through the frozen baseline consumer with no additional appearance-consistency operation.
- `A+` (appearance-consistent control): apply a fixed, predeclared appearance-only operation that matches source color statistics/illumination to the target context while preserving geometry and spatial support. The operation may be a photometric normalization or the existing appearance-consistency control, but it must not access future RGB/depth/pose and must use the same compute budget in all arms.

The final implementation must choose one operation and freeze it before looking at held-out results. If no valid future-independent appearance operation can be implemented, set `A+=A-` and report the unavailable cell rather than inventing a substitute.

### The four arms

| Arm | Geometry | Appearance | Purpose |
|---|---|---|---|
| `G+ A-` | trusted | ordinary | baseline consumer with geometry protected |
| `G+ A+` | trusted | appearance control | isolated appearance effect under good geometry |
| `G- A-` | corrupted | ordinary | isolated geometry failure |
| `G- A+` | corrupted | appearance control | interaction test: does appearance control amplify or suppress geometry error? |

For every arm, hold fixed candidate IDs/order, source RGB, target camera, diffusion noise, RNG, denoising steps, model/weights, resolution, output count, and GPU/compute budget. Recompute all downstream consumer states naturally; do not freeze target-source descendants when estimating a total consumer effect.

### Primary estimands

Let `L(G,A)` be a predeclared future-state loss measured only after prediction artifacts are sealed. Use depth AbsRel, metric/relative pose error, and localized reprojection error as primary geometry outcomes. RGB MSE, LPIPS, and a preregistered ghosting/temporal consistency statistic are secondary; MSE alone cannot validate geometry.

Define the appearance main effect at trusted geometry:

`Delta_A_plus = L(G+, A+) - L(G+, A-)`.

Define the geometry main effect under ordinary appearance:

`Delta_G = L(G-, A-) - L(G+, A-)`.

Define the interaction contrast (difference-in-differences):

`Delta_int = [L(G-, A+) - L(G-, A-)] - [L(G+, A+) - L(G+, A-)]`.

A positive `Delta_int` means the appearance operation changes the corrupted-geometry loss more than the trusted-geometry loss; the sign must be interpreted with the loss convention, not with image quality impressions. Report scene-level paired confidence intervals and exact replay variance. Also report the same contrast for each target, not only a pooled mean.

### Ghosting mechanism readout

For each predicted target, save four maps with identical color scales: RGB residual, depth residual, reprojection displacement, and source-support overlap. A ghosting candidate is accepted as *geometry-localized* only if duplicated contours overlap regions with elevated reprojection/depth residual and the pattern exceeds a support-area/edge-density-matched mask placebo. If RGB residual increases without a geometry residual or if the artifact follows global VAE/decoder changes, classify it as appearance/decoder or mixed and do not call it geometric.

## Cross-scene test

The first legal test requires at least two calibration scenes and one untouched held-out scene. The paper-quality test should use three calibration scenes and two held-out scenes, with at least one real RGB-D trajectory and one synthetic/controlled trajectory; synthetic and real results must remain separate. All scenes use the same four arms, candidate-pool construction, corruption distribution, appearance operation, budget, and primary metrics.

Before opening held-out answers:

1. Freeze scene IDs, source/target time windows, timestamp matching, camera convention, depth units, invalid-value handling, candidate order, corruption seeds, appearance parameters, model/weight/source hashes, and GPU budget.
2. Run calibration scenes only to estimate replay variance and choose no post-hoc thresholds. If a threshold is needed, fit it on calibration scenes and lock it.
3. Seal predictions, hashes, and manifests for every arm.
4. Only then read held-out RGB-D/pose answers and score all four arms.
5. Use scene/block bootstrap, not individual pixels as independent samples. Report both pooled and per-scene contrasts, plus confidence intervals and missing-data denominators.

Mandatory controls are: (i) geometry-only and appearance-only baselines, (ii) ordinary VMem consumer without the proposed operation, (iii) equal-budget hard-selection or no-memory control, (iv) source-ID permutation placebo, (v) support/pose/edge-density matched mask placebo, and (vi) exact replay with common noise. A method that wins only against an unbalanced control is not informative.

## Can this support a method?

**Default verdict: diagnostic benchmark/measurement, not a method.** A 2x2 contrast can demonstrate an interaction, but a routing gate or weighted fusion trained on this contrast would be a conventional extension of ViewDiff/geometry-guided blending/temporal harmonization. It becomes a conditional method candidate only if all of the following hold:

1. `Delta_int` is non-zero with a preregistered effect threshold and 95% interval excluding zero in at least two held-out scenes and both short and long horizons.
2. The interaction predicts future depth/pose/reprojection failures out of scene, beyond geometry-only, appearance-only, recency, pose/FoV, confidence, and generic gate baselines at equal compute.
3. The effect survives source-ID and support/pose/edge-density-matched placebos.
4. A simple pre-future policy (for example, abstain or route appearance only when geometry residual is low) improves future geometry at matched acceptance and cost, while preserving or improving the ghosting metric.
5. The complete consumer path is recomputed for interventions, and exact-replay noise is materially smaller than the observed effect.

If these conditions are met, the possible contribution is a *mechanism-conditioned memory arbitration policy* with a future-state evaluation contract. The 2x2 decomposition remains the paper's diagnosis and does not itself constitute the algorithmic novelty.

## Kill criteria

Stop or downgrade this direction to a benchmark/negative result if any one of the following is observed:

- the interaction confidence interval includes zero across held-out scenes;
- the sign changes across scenes or only one target drives the pooled effect;
- RGB MSE improves but depth AbsRel, pose/reprojection, and ghosting metrics do not;
- geometry-only or appearance-only controls explain the effect within the preregistered tolerance;
- support/pose/edge-density matched masks or source-ID permutation preserve the apparent gain;
- exact-replay variance is comparable to or larger than the interaction effect;
- the effect disappears when all downstream descendants of the intervened source are recomputed;
- the appearance operation accesses future answers, changes information/compute budget, or alters source count;
- gains occur only in one static scene, one corruption magnitude, or one horizon;
- thresholds or corruption strengths are chosen after held-out outcomes are inspected;
- no valid independent held-out RGB-D/pose scene is available.

## Decision

This rotation yields one useful, falsifiable contribution candidate: a cross-scene *geometry–appearance interaction benchmark* for diagnosing long-horizon ghosting under a fixed world-model consumer. It does not authorize training or a new method before Gate 0. After Gate 0, run the 2x2 diagnostic only if its data contract and appearance operation can be frozen without future leakage. If it fails the kill criteria, preserve the negative mechanism result and return to FGB-Future or SOCF-A only when their externally supplied, held-out future RGB-D/pose contracts are available.

## Evidence boundary

The literature claims above were checked against primary CVPR/PMLR/OpenReview records on 2026-09-16 using English queries. Search snippets and model summaries were not used as evidence. No future GT, held-out data, or formal GPU output was read in this rotation.
