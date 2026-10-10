# R257 — How a memory video world model could consume geometric evidence

Date: 2026-10-10. Workspace: local Mac checkout. Scope: generative ideation and read-only verification; S141 results remain pending and UNVERIFIED.

**Run source-resolved, robust clean-latent correction first.** At a few denoising steps, adjust the predicted clean target latent so its decoded image agrees with the actual source observations under fixed geometric correspondences. Compare it with the identical correction performed only after generation and with deterministic robust reprojection. This directly tests whether interleaving the generator with evidence adds anything beyond rendering or postprocessing. It needs no new weights or training and does not depend on S141 winning.

Keep two alternatives: an intervention that changes **where native attention reads history while preserving its instantaneous history weight at the patched operation**, and **source-reliability-dependent release of warped evidence during sampling**. These are new experiments for this checkout, not verified new inventions. The broad primitives already appear in the literature. The interesting contribution, if any, must come from the precise distinction and a positive result against the strongest simple control.

This document contains sixteen candidates, five focused prior-art checks, and three bounded experiments. It proposes no changes to S141 or S142 and launches none of them. The current brief explicitly requests new mechanisms; R255's preference for closing the search is not used to suppress that request. The frozen S142 branches remain historical/current experiment contracts, not authorization to silently add these arms (work/S142_followup/PROTOCOL.md:9–17,19–49).

**Evidence notation.** MEASURED (archived) means a stored earlier result; DERIVED means arithmetic from those records; ANALYTICAL means a deduction, proposed mechanism, decision threshold or budget; UNVERIFIED means unavailable evidence or a prediction. All future constants, thresholds, arm counts and resource estimates below are ANALYTICAL. No candidate has a measured gain. No GPU, training, weight/dataset download, SSH, Slurm submission or outside contact was performed. Only this file is written. The flags remain new_method_validated=false and novelty_authorization=NONE.

For compact file:line citations, V/ means data/S134_tacc/vmem_src/, S140/ means work/S140_warp_guided/, and S141/ means work/S141_finetune/. All other paths are repository-relative. Literature claims below cite verified arXiv IDs, exact titles and sections; paper claims are not reproductions of those systems.

## 1. What the evidence actually leaves open

| Verified starting point | Consequence for ideation |
|---|---|
| MEASURED (archived): S139 memory minus recent-context generation is −0.1805 dB, 95% window CI [−0.5177,+0.1447]. The same retrieved contexts improve the separate warp predictor by about +1.46 dB. [Generation output](../S139_crossseq_revisit/results/S139_ANALYSIS.json), [geometric comparison](../S139_crossseq_revisit/results/S139_BASELINE_CONTRASTS.json). | There is useful evidence available to a geometric predictor. This does not prove zero memory influence inside VMem. |
| MEASURED (archived): S140 WGS minus B2 is +0.0203 dB, CI [−0.0946,+0.1343], and +0.0251 SSIM. The warp-versus-VMem ordering reverses between PSNR and SSIM. [Output](../S140_warp_guided/results/CONFIRM_ANALYSIS.json). | A new method should beat reprojection and disclose perceptual/structural trade-offs. A PSNR-only improvement is not automatically better video. |
| S140 W2 uses one global start index and a fixed coverage threshold, followed by noised-warp replacement. At a nonzero start index it adds the encoded nearest-filled warp everywhere, including holes (S140/gen_s140.py:155–178,202–206). | Its negative primary does not test all spatial schedules, source observation losses, or hole initialization without nearest-fill content. This is a source-derived boundary, not an explanation established by an experiment. |
| The current S141 manifest has 2,000 training clips and 32 monitor clips, rather than 2,032 optimization clips. [Manifest](../S141_finetune/clips_s141.json); Appendix A extracts its summary. | Preserve the monitor distinction. A monitor subset used here becomes development data. |
| S141 B uses an added warp-latent/coverage convolution; S142 E2 replaces the original context representation with target-pose warps (S141/s141_common.py:97–118,157–164; work/S142_followup/PROTOCOL.md:34–38). | Neither is an internal source-addressing intervention or a source-space proximal correction. Do not relabel either as one of the new candidates. |
| S141 saves filled RGB, validity, warp latent and coverage; its warp cache does not save source identities, projected coordinates or source depth (S141/warps_s141.py:79–97). | Source-resolved mechanisms require additional geometry metadata. “Assets already exist” does not make that preprocessing free. Existing depth receipts/cache reuse must be verified; otherwise rerun only source geometry later. |

The report correctly limits the earlier findings to a configuration and exposed panels (docs/report/TECHNICAL_REPORT_20261010.md:184–192). RESEARCH_MEMORY.md:6 still says only fine-tuning remains and its heading retains an older optional-Codex policy. Those statements are stale/too broad relative to this brief and the report; they are not adopted or edited here. R253's older missing-B_static concern is superseded by S141 Amendment 1 (S141/PROTOCOL.md:85–99). R256's concerns about copying, correct guidance, and final-only controls remain relevant (work/agents/CODEX_R256_S142_DRAFT_REJECTION.md:125–173).

The user-reported frame-cache count, complete remote caches, final adapters, available GPU slots, and full-run training throughput are **UNVERIFIED in this review**. No S141 result is inferred from a protocol, current-status sentence, or adapter filename.

## 2. Divergence: sixteen mechanisms at different pipeline locations

Each row is a proposal, not a claim that it works. “Unchecked” means its exact novelty was not established in the focused search, not that it is new. Starred families receive the five deeper checks in Section 3.

| ID / intervention point | Concrete mechanism and falsifiable prediction | Principal failure or strongest cheap alternative |
|---|---|---|
| **1. Observation representation** | Preserve several source colors and geometric addresses per target location, rather than irreversibly choosing one z-buffer winner. A robust observation likelihood can retain disagreement until generation resolves it. | Under squared loss this can reduce algebraically to averaging. Deterministic robust fusion may provide the whole gain. This supplies experiment P, not a separate claimed contribution. |
| **2. Native attention addressing ★** | Redistribute an existing target query's history-attention mass among geometrically compatible source tokens; preserve total history mass and target-token contributions. Correct addresses should outperform same-coordinate addressing. | Geometry may be wrong, or history mass may already be negligible. Generic geometric attention is published. Retain as experiment A. |
| **3. Multi-scale hidden-feature transport ★** | Transport original source VAE/hidden features at multiple resolutions, preserving raw source slots, and inject them into decoder features. Test encoding-then-warping against warping-then-encoding. | VAE/hidden features are not equivariant point samples. A geometry-conditioned first-convolution branch may be sufficient. Close GeoNVS overlap; defer the full pyramid. |
| **4. Frequency-limited feature transport** | Inject only the spatial high-frequency component of an aligned source feature at one late decoder stage; let native features retain global layout. | Misalignment makes edges worse, and filtering alone may explain any gain. Compare low-pass-only and matched RGB sharpening. Exact variant unchecked. |
| **5. Positional-address transport** | Supply target-view positions of source tokens while keeping their visual content unwarped; let learned attention perform appearance transfer. | This may merely restate geometric positional encoding. PE-Field 4D is an explicit precedent, discussed below. More training/interface work than A. |
| **6. True spatial noise/time ★** | Give reliable observed regions lower sigma than unknown/conflicting regions and condition every affected block on the corresponding spatial time map. | A scalar-time pretrained model does not implement this automatically. WorldWarp already does region-specific time conditioning. Defer the full trained redesign. |
| **7. Evidence release ★** | Keep reliable warped evidence constrained later into sampling, but release uncertain regions earlier, using input-only source disagreement rather than coverage alone. | This is a Differential Diffusion adaptation. Removing nearest-filled hole initialization or using a constant release time may explain everything. Retain as experiment R. |
| **8. Geometry-correlated noise** | Give rays that refer to the same observed surface correlated noise, with independent noise for unsupported regions. | MultiDiff already uses warped shared noise. A frozen model was not necessarily trained for that covariance; variance normalization alone does not restore spatial independence. Defer as known-method transfer. |
| **9. Observation-space proximal correction ★** | Correct a detached clean-latent prediction through the VAE decoder against source RGB constraints, then resume denoising. | ReSample establishes this family. Final-only correction and robust reprojection are the decisive controls. Retain as experiment P. |
| **10. Generated-target agreement** | Use a graph of input-supported correspondences between the four targets; penalize disagreement only on surfaces also supported by observed sources. | Mutually wrong outputs can agree. Source-anchored pair consistency must beat the same loss without the source anchor, while reference quality is preserved. Exact variant unchecked. |
| **11. Source cross-validation at inference** | Generate a small fixed set of candidates, rank them by predicting an omitted source view using the other sources, then reuse the selected rule for the target. | Additional samples and selection can dominate the result; visibility to a held-out source need not predict target fidelity. Compare equal-budget random/mean selection. Exact variant unchecked. |
| **12. Alternating geometry and generation** | Alternate one target-generation step with a small source-geometry correction accepted only if it improves independently held-out source reprojection. Never let generated target depth serve as truth. | Circular self-confirmation and pose/depth gauge errors. A source-only geometry refinement may give the same gain. Too many coupled failure modes for the first trial. |
| **13. Residual denoising target** | Predict target-minus-render residuals with confidence-normalized scale, so small observed-region errors and large unknown-region errors need not share one effective scale. | This can be only an invertible reparameterization of warp conditioning; compare matched loss weighting and the same capacity. No novelty claim without a dedicated check. |
| **14. Correspondence auxiliary supervision** | On training clips, supervise agreement between source and target hidden features at reliable projected locations while retaining target denoising supervision. | Feature collapse, wrong correspondences and the absence of an RGB benefit. GeoNVS includes feature alignment; an auxiliary loss alone is not a new broad primitive. |
| **15. Counterfactual evidence-use training** | Pair correctly aligned evidence with matched corruption and train a localized denoising advantage where real training labels confirm evidence utility. | It can learn to recognize corruption or sabotage the wrong-input arm. Must improve correct-input quality over ordinary LoRA, not merely increase the good/bad gap. Exact image-generation version unchecked; do not start with a ranking loss alone. |
| **16. Source radiometric correction** | Estimate exposure/color correction from source-source overlaps before any warp or feature transport, so the generator receives geometrically aligned and photometrically compatible observations. | Ordinary color normalization may solve it. Useful strong baseline, not an internal consumption novelty claim. |

The distinction between rows 3 and S141 B is substantive: E(warp(RGB)), warp(E(RGB)), and warp(hidden_feature) are different operations. The current B uses the first (S141/gen_s141.py:178–182); E2 changes context slots, not that order of operations (work/S142_followup/PROTOCOL.md:34–38). Their inequality is an analytical possibility, not evidence that one is better.

## 3. Focused prior-art checks for the five most promising families

The five checked families are native attention addressing, internal feature transport, spatial noise/time, evidence release, and observation-space correction. This is bounded retrieval, not an exhaustive novelty certificate. Search axes included geometric token addressing, latent/hidden warping, spatial uncertainty/noise, differential regional denoising, and inverse-problem/reprojection correction.

| Candidate family | Closest verified primary work and occupied mechanism | Precise remaining difference; verdict |
|---|---|---|
| **Native history addressing** | **arXiv:2609.34722, “Geometry as Address: Routing Attention to Visual Memory for Long-Horizon Camera-Controlled Video Generation,” §§3.2–3.4, Eqs. 8–10.** GEAR uses geometric correspondence sets to gather historical hidden K/V and inject a sparse attention residual. [Paper](https://arxiv.org/html/2609.34722v1#S3.SS4). | A below redistributes the existing history contribution at one native VMem layer, with unchanged total history mass, rather than adding a learned residual memory module. This is a narrower intervention on addressing versus strength, not a new generic geometry-memory attention idea. **Keep as an adaptation/mechanism experiment.** |
| **Internal feature transport** | **arXiv:2603.14965, “GeoNVS: Geometry Grounded Video Diffusion for Novel View Synthesis,” §§3.2–3.3.** It projects reference diffusion features through 3D Gaussians, fuses multi-scale features, and injects geometry corrections into a diffusion decoder. [Paper](https://arxiv.org/html/2603.14965v1#S3.SS3). | A per-source CUT3R/KPS bank can preserve alternatives without Gaussian fusion, but transporting features instead of RGB is already published. Proving that source separation matters requires matched fusion controls. **Defer the full pyramid; no generic feature-warp novelty claim.** |
| **Spatially different noise levels** | **arXiv:2512.19678, “WorldWarp: Propagating 3D Geometry with Asynchronous Video Diffusion,” §4.1, Eqs. 5–7.** Warped and missing regions receive different noise levels; token-specific time embeddings support that distribution. [Paper](https://arxiv.org/html/2512.19678v1#S4.SS1). | CUT3R source-disagreement-driven levels would change the reliability input and backbone, not invent spatial diffusion. Making VMem genuinely time-map-aware requires training and interface changes. **Defer for deadline/attribution risk, not because S140 disproved it.** |
| **Training-free evidence release** | **arXiv:2306.00950, “Differential Diffusion: Giving Each Pixel Its Strength,” §3.3, Algorithm 1.** Spatial change maps determine nested masks that mix noised input with the denoising trajectory. [Paper](https://arxiv.org/html/2306.00950v2#S3.SS3). | R derives the map from multiple input views and compares it with matched constant/shuffled maps in a camera-conditioned memory model. This is a different map and application, not a new release algorithm. **Keep as a low-cost reliability test.** |
| **Clean-latent observation correction** | **arXiv:2307.08123, “Solving Inverse Problems with Latent Diffusion Models via Hard Data Consistency,” §3.1, Eq. 10 and Algorithm 1.** ReSample optimizes decoded clean latents for measurement consistency, then remaps them into sampling. [Paper](https://arxiv.org/html/2307.08123v3#S3.SS1). | P uses uncertain, source-resolved multiview RGB constraints and a robust loss, with an explicit internal-versus-final-only comparison in VMem. Its Euler insertion is a heuristic; it does not inherit ReSample's posterior claims. **Keep first, as a new local experiment using an established family.** |

Three additional boundaries matter:

- **arXiv:2607.15667, “PE-Field 4D: Video Generation Models as Canvas,” §3.2, Eqs. 1–4**, already uses aligned reference positions and shared target/reference attention projections. Merely reusing native projections is not a novelty rescue. [Paper](https://arxiv.org/html/2607.15667v1#S3.SS2).
- **arXiv:2406.18524, “MultiDiff: Consistent Novel View Synthesis from a Single Image,” §3, “Structured noise distribution,”** warps a common Gaussian realization into target views and fills invalid regions with independent noise. Row 8 is therefore known-method transfer. [Paper](https://arxiv.org/html/2406.18524v1#S3).
- **arXiv:2506.23518, “WAVE: Warp-Based View Guidance for Consistent Novel View Synthesis Using a Single Image,” §3.4, Algorithm 1**, mixes low-frequency warped-image information into initialization noise. Generic geometry-informed initialization is also occupied. [Paper](https://arxiv.org/html/2506.23518v1#S3.SS4).

No shortlisted primitive presently supports a “first” or CCF-A method claim. That is not a reason to run nothing: the following experiments can determine whether a more specific mechanism is useful, redundant, or wrong within the available assets.

## 4. Shared experiment contract

All three designs below are prospective, exploratory, independently falsifiable experiments. Implement at most the first initially. The other two are alternatives, not an automatic serial rescue sweep.

**Data and inputs.** Reuse the original context identities and cameras, fixed source-estimated geometry, and frozen VMem weights for the primary trials. Do not wait for S141 results or choose the base/adapter after seeing chess scores. S141 A/B, once valid receipts exist, can be secondary practical comparators; a later adapter-based version is a separate amendment. Evaluation target RGB/depth must never enter correspondence construction, confidence, guidance, candidate selection or generation. Training-scene labels can enter the declared pilot scorer only.

Use the eight already specified monitor clips c02006, c02016, c02000, c02003, c02001, c02002, c02009, c02010 with generation seed 3 for one pilot per chosen design; they are defined in work/S142_followup/PROTOCOL.md:39–42. Their use here is development reuse, not a new holdout. Full follow-up: the existing chess panel, generation seeds 3–6, one hardware type for every paired arm. RGB-D Scenes 13/14 can supply a prespecified secondary transfer block with the same seeds, if within the cap. Both panels are exposed to research decisions.

**Metrics.** Retain the existing scorer's pooled RGB SSE over four targets, followed by PSNR, and its SSIM calculation (S140/score_s140.py:20–24,30–45). Average generation seeds within window before contrasts. Report window bootstrap CI with 10,000 resamples, rng 0; also all trajectory-pair effects and descriptive pair-cluster uncertainty. Do not treat seeds, pixels, or overlapping windows as independent scenes. All region scoring uses original immutable B2 masks and warp RGB, never intervention outputs (S140/score_s140.py:35–50).

**Retention threshold.** For the named primary, require mean gain at least +0.2 dB, lower 95% window CI above zero, and no negative mean in two of three chess trajectory pairs. Each experiment also has mandatory baseline comparisons below; a primary pass cannot waive them. A material SSIM decline, mean at most −0.01 with upper CI below zero, makes a PSNR win a trade-off. Covered/uncovered PSNR, support counts and failure cases are mandatory diagnostics. No frame-metric result warrants a temporal-quality claim.

**One pilot, no rescue tuning.** Use the constants specified below. Before full-panel spending, require the primary pilot mean to be at least +0.2 dB, positive in at least five of eight clips, with mean SSIM difference greater than −0.01 and finite outputs. Apply the same pilot requirements to the listed mandatory utility baselines. Failure stops that implementation for this deadline; it does not disprove its whole mechanism family. Do not sweep after inspecting pilot or chess results.

**Fidelity and provenance.** A disabled intervention must reproduce a same-backend unmodified control; record the source/config/weight/input/output hashes, exact complete window-seed cells, failure counts and rerun command. Do not rely on filename-only reuse. In A, the changed attention backend itself requires a control. In P, preserve the stock random draws and sigma_hat detail even though nominal churn is zero (V/modeling/sampling.py:393–402). Proposed implementation files below belong in new stage directories; no existing protocol or source deliverable needs overwriting.

**Timing basis.** MEASURED (archived), DERIVED aggregation: the four [S139 RTX 3090 logs](../S139_crossseq_revisit/results/stepB_tacc/) contain 288 generations, averaging 36.1144 seconds each. A 96-generation arm is therefore 0.9631 baseline GPU-hours; this is not a measured speed for any new mechanism. Appendix A gives the exact command and complete values. Two cards reduce ideal wall time, not total GPU-hours. Source-map regeneration, decoder backward and changed attention kernels remain unmeasured.

## 5. Experiment P — source-resolved robust proximal correction

**Hypothesis, UNVERIFIED.** Keeping inconsistent source observations separate and interleaving their robust correction with denoising produces a better target than applying the same correction after generation. The generator can then respond to corrected evidence, rather than merely having pixels replaced at the end.

### Minimal implementation

Proposed new files: work/R257_probe_prox/build_observations.py, gen_prox.py, analyze_prox.py, and a dated PROTOCOL.md. These files are not created by R257. Reuse the coordinate transformations from S141/warps_s141.py:38–61 and the S140 generator/scorer; do not import its top-level executable as a library without refactoring in the new stage.

For each source pixel with valid estimated depth, backproject into world coordinates and project into each target camera. Store source ID, RGB, continuous target coordinates, projected depth and interpolation weights. Reuse original camera geometry, not the normalized camera tensors mutated by get_cond (V/modeling/pipeline.py:1129–1140). Admit only in-bounds, positive-depth points within a fixed 2% relative band of the frontmost source-derived projected depth. Exclude source depth discontinuities greater than 10% across a 3×3 neighborhood. These are proposed conservative filters, not certificates of true visibility.

Keep observations from each distinct source separately; normalize total constraint weight per target cell and then across target frames. Do not let a dense or duplicate source dominate by pixel count. Bilinear target-image gathering defines H_j. Its adjoint is the scatter with those same weights, not an independently coded reverse camera warp.

Let D map a latent to decoded RGB on the [0,1] scale, and let z0 be the guided clean-latent estimate. Use

    J(z; z0) =
        mean_weighted[ Huber_0.03(H_j D(z) - source_RGB_j) / 0.03 ]
        + mean[(z - z0)^2].

At zero-based sampler iterations 24, 34 and 44 of the original 50-step trajectory, detach the four target z0 tensors, take eight normalized-gradient steps of latent RMS size 0.01, and project each correction into an RMS radius 0.1 around that event's starting z0. Use epsilon 1e-8 in normalization; a zero gradient leaves the tensor unchanged. Freeze these constants before the pilot. Context latents remain unchanged.

Insert the corrected estimate after CFG combination and before Euler's drift calculation, at V/modeling/sampling.py:398–402:

    corrected_target = prox(detach(guided_denoised_target))
    d = (x - corrected_denoised) / sigma_hat
    x_next = x + (next_sigma - sigma_hat) * d.

Use the exact implementation's broadcasting, sigma_hat and random-number sequence, not a simplified replacement of the whole sampler. This is a heuristic proximal correction, not an exact posterior sampler.

The VAE is frozen but differentiable with respect to its input (V/modeling/modules/autoencoder.py:18,37–48). S140 encloses sampling in inference_mode (S140/gen_s140.py:160–179), so simply placing enable_grad inside it is insufficient. Execute the correction outside inference_mode on an ordinary cloned target latent; retain no U-Net backward graph. Decode one target at a time if needed and include that cost in timing.

**Equivalence trap, ANALYTICAL.** When observations share one target variable or an identical design row, sum_j w_j||x-y_j||² equals (sum_j w_j)||x-weighted_mean(y)||² plus a constant. Source IDs alone therefore add no information in that pointwise quadratic case. This identity does not reduce different bilinear rows to independent per-cell averages: the actual H_j couples neighboring target pixels. Robust residuals retain disagreement, but deterministic reconstruction with the identical H_j remains an essential competitor. If only one source survives almost everywhere, the claimed source-resolution distinction has little support; report its actual support fraction.

### Arms, primary and controls

- **P:** internal source-resolved correction as above, starting from the original full-noise sampler.
- **Ffull:** ordinary generation followed by 24 correction steps, grouped as three consecutive eight-step proximal events with the tether reset each event. This matches P's decoder-gradient count and per-event trust radius, but not its effective update magnitude.
- **Fscaled, primary comparator:** the same final-only groups, but multiply each group's proposed latent correction by a_e=(sigma_hat_e-next_sigma_e)/sigma_hat_e from P's corresponding event. An internal correction delta changes the immediate next state by a_e*delta, not delta. This extra control matches that immediate attenuation; later denoiser interactions remain part of the schedule comparison. Do not claim that gradient count alone isolates interleaving.
- **M:** first compute Wrobust below; replace each color observation y_j by H_j(Wrobust), retaining every original H_j, weight and validity entry. Use P's same events and loss. Thus geometry and sampling locations are fixed while conflicting colors are replaced by predictions from one consistent reconstruction. This tests retaining original measurement conflicts versus consolidating them, not source IDs in isolation.
- **Wrobust:** deterministic image-space reconstruction minimizing mean_weighted Huber(H_j I-y_j) with the identical H_j, masks and weights and RGB constrained to [0,1]. Use a fixed convex solver capped at 200 iterations with relative objective-change tolerance 1e-6, and report convergence/residuals. Freeze the solver implementation before scoring. Fill only truly unconstrained pixels with the same nearest-fill rule afterward. Keep per-cell robust splatting as an additional cheaper baseline, not an allegedly identical objective. Also score original B2, its VAE round trip, and a fixed coverage composite using original B2 on covered pixels and original VMem in holes.
- Original frozen VMem and archived S140 W2 are references; reuse only matching identities/hardware/seeds.

Primary: P−Fscaled. **Useful mechanism retention additionally requires P−Ffull, P−B2, P−Wrobust and P−the coverage composite to clear the shared +0.2 dB/CI/pair rule.** Every strong trivial alternative must be beaten, so no outcome-dependent baseline selection is hidden. If P passes those but not P−M, retain only an interleaved data-consistency result and explicitly drop the measurement-conflict explanation. That stronger explanation requires P−M to clear the same rule. Even then the claim is about these specified correction schedules, not a theorem about all interleaving policies.

**Kill criterion.** Stop for a failed pilot, nonfinite gradients, excessive memory, or lack of the primary/mandatory gains. Stop the source-resolution claim if P and M are indistinguishable at the practical bar. Decreasing source residual while worsening target quality is failure, not evidence of better geometry. Do not replace the target metric with the optimized guidance loss.

**Budget and implementation window.** No training. P and M need separate trajectories; Ffull and Fscaled share one ordinary trajectory and then perform separate final corrections. Thus chess requires 288 denoising trajectories, approximately 2.89 baseline GPU-hours, plus 384 sets of decoder corrections. Reuse is allowed only if the final latent is reproduced exactly; decoded RGB alone is insufficient. Allow 10–16 RTX 3090 GPU-hours including pilot, metadata, the deterministic solver and VAE backward; cap 24 with a prespecified full transfer block. These are allowances, not measured decoder timings. Stop before full evaluation if the pilot predicts that the cap or two-day window cannot fit. No H800 comparison is necessary.

**Genuinely interesting result.** Internal correction beats both equal-cost final correction and deterministic robust reprojection, preserves SSIM, and improves uncovered-region reference error without giving the method target evidence. That would show a useful interaction between a generative prior and observed evidence in this model. It would still be a ReSample-family adaptation on exposed panels, not proof of a new universal sampler.

## 6. Experiment A — change the address, preserve the amount of history

**Hypothesis, UNVERIFIED.** The generator can benefit from assigning its existing history contribution to the correct source locations without an explicit history-mass boost at the patched operation. Later hidden states and attention masses may change as consequences of that intervention.

### Minimal implementation

Proposed new files: work/R257_probe_attention/build_addresses.py, attention_patch.py, gen_attention.py, analyze_attention.py, PROTOCOL.md. Reuse P's source-only projection metadata if it exists. Patch only the first spatial attn1 in middle_ds8, whose grid is 9×9 for this input. VMem's configured cross-view stages are V/modeling/network.py:33–35; frame flattening is V/modeling/modules/transformer.py:237–241. Derivation: eight frames give 648 tokens here. This is a small single-stage experiment, not full-resolution attention.

At each target query, use the native softmax affinities a_ij and split keys into history H and target T. Let m_i=sum_(j in H) a_ij. Fix contributing source identities from geometry once, canonicalizing duplicate source frames to their first context slot. For each contributing source, take exactly nine distinct grid keys nearest its proposed center by squared Euclidean distance, breaking ties by row-major index over the entire 9×9 grid. This gives nine keys even near borders; it is deliberately not a clipped 3×3 stencil. Geo, same-coordinate and shuffled arms keep the same contributing sources and key counts. Let b_ij be native logits renormalized only over their union N(i). Set

    output'_i =
        sum_(j in T) a_ij V_j
        + m_i * sum_(j in N(i)) b_ij V_j.

For empty N(i), retain the unmodified output. Context queries remain unchanged. There is no learned gate, no extra capacity and no mass boost at this operation. The preserved m_i is the current arm's instantaneous native mass for its current features, not A0's mass across the trajectory. Recompute all downstream states normally; do not freeze mediators to enforce cross-arm equality. Apply only during the last half of the 50-step schedule, and only in the conditional CFG half; unconditional attention remains native. Record this choice explicitly, since it changes the conditional pathway under CFG.

Native q/k/v and output projections are exposed at V/modeling/modules/transformer.py:53–74. The target is attn1; attn2 consumes external conditioning (same file:107–110), and get_cond pools source CLIP into one repeated token (V/modeling/pipeline.py:1125,1150). Pixel addresses must not be applied to CLIP cross-attention.

The stock attention forces Flash with no mask argument (V/modeling/modules/transformer.py:71–72). Use explicit math attention only at this small stage, in all A arms including the baseline. Avoid adding a dense mask at the 36×36 stage. Preserve original attention elsewhere. Recompute native features at every denoising step: they participate in joint source/target transformations and are not a permanent source-only cache (same file:236–243).

### Arms, primary and controls

- **A0:** unmodified attention using the same explicit-math backend at the selected stage.
- **Ageo:** proposed geometric redistribution.
- **Asame:** identical redistribution/support/source counts, but use same-image-coordinate source neighborhoods.
- **Ashuffle:** fixed spatial permutation, seed 257, of source neighborhood centers within each source and support stratum; preserve candidate counts and total history mass.
- Original B2, Wrobust if already available, and the original frozen VMem outputs are output-quality references.

Primary: Ageo−Asame. Require Ageo−A0 also to clear the shared rule; a degradation caused by Asame cannot create a success. Ashuffle is a sensitivity diagnostic and must not outperform Ageo; a material shuffle advantage rejects geometric addressing. To call Ageo a practically useful consumer, also require Ageo−B2 to clear the shared rule. Otherwise report only a bounded mechanism signal, even if the native-attention comparison succeeds.

The strongest trivial attention baseline is Asame plus A0, not a destructive shuffle. Measure native m_i and the geometrically supported-query fraction without target labels. If m_i is negligible, this experiment has little intervention strength; failure cannot reject a separate “increase memory weight” mechanism.

**Kill criterion.** Fail the pilot, fail backend fidelity/tensor-order checks, or fail the primary and A0 comparison: stop. If only coarse texture changes or attention maps change without reference-quality gain, do not claim improved consumption. Do not add LoRA or more layers after a failure under the same experiment.

**Budget and implementation window.** No training. Four chess arms are 384 generations, about 3.85 baseline GPU-hours. Allow 6–10 RTX 3090 GPU-hours with math-attention overhead, address construction and pilot; cap 14 including a full transfer block. The two-day feasibility is conditional on that one-stage implementation and pilot timing. A full GEAR-style trained module is outside this trial.

**Genuinely interesting result.** Geometry beats same-coordinate reading and the same-backend model without explicitly increasing instantaneous history mass at the patched operation, then also beats reprojection. That supports useful addressing; downstream changes in attention strength remain possible mediators. A smaller win below the warp is mechanistic evidence only. Generic geometric attention remains prior art.

## 7. Experiment R — release unreliable evidence without inventing spatial-time support

**Hypothesis, UNVERIFIED.** Evidence should remain constrained according to how well independent source views support it, not merely whether one projected point landed there. The spatial reliability of release times should matter beyond total clamp strength.

### Minimal implementation

Proposed new files: work/R257_probe_release/build_reliability.py, gen_release.py, analyze_release.py, PROTOCOL.md. Reuse S140/gen_s140.py:139–180, and add source-resolved support metadata. No training and no spatial-sigma argument are needed.

Build a fixed source-only reliability q on the target grid. Start with the fraction of distinct sources agreeing in projected depth; multiply by exp(−d/0.03), where d is the median absolute RGB deviation from the source-color median in [0,1]. Use the same visibility filter as P. Unsupported pixels receive q=0; singleton support has at most q=0.25. A map like this is a reliability heuristic, not calibrated uncertainty. Pool conservatively into latent cells, excluding cells that straddle validity/depth boundaries.

Keep the original scalar sigma schedule and binary covered set cov>=0.5. Boundary exclusions set q=0 rather than removing cells from that fixed set. After step i, define u=(i-k+1)/(50-k), where k is the shared strength-0.5 start index; replace covered target latent cells at next_sigma only while u<q. Thus the final step has u=1 and no replacement. Low-confidence cells are released early; high-confidence cells remain constrained longer. Use the same saved random-noise field per corresponding replacement event across all compared arms; do not accidentally change subsequent sampler RNG draws.

This is a Differential Diffusion-style release policy, **not** a true per-pixel sigma model. VMem's sigma quantizer assumes vector-like sigma and the training path samples one index per clip (V/modeling/sampling.py:159–178; S141/train_s141.py:61–67,118). A genuine spatial-time design must modify preconditioning, embeddings and training; it is not smuggled into R.

### Arms, primary and controls

- **R0:** reproduce S140 W2 at strength 0.5 with its original hole initialization and fixed binary clamp.
- **Rclean, mandatory trivial control:** same schedule, mask, random draws and replacement as R0, but initialize holes with sigma_k * epsilon rather than zw + sigma_k * epsilon. In covered cells retain zw + sigma_k * epsilon. Match the sigma multiplier exactly. This removes direct nearest-fill latent signal from holes; VAE receptive-field contamination near boundaries can remain.
- **Runiform:** use Rclean initialization and a single covered-region release time equal to mean q over covered latent cells, computed from inputs alone.
- **Rgeo:** use Rclean initialization and the q-dependent release rule.
- **Rperm:** same as Rgeo with q spatially permuted within the fixed covered set, seed 257; preserve its histogram and thus total replacement count at every step. Unsupported cells remain unsupported.
- Original B2 and a deterministic q-weighted blend of B2 and original VMem are CPU baselines. The latter tests whether q is useful only for output compositing.

Primary: Rgeo−Rperm. **Mandatory practical controls:** Rgeo must also beat Rclean, Runiform, B2 and the deterministic blend by the shared rule. This conjunction prevents beating a bad permutation from being mistaken for a useful schedule. Rclean−R0 is separately reported: if it explains the gain, retain the simpler initialization fix and reject the reliability mechanism.

The strongest trivial baseline is Rclean/Runiform plus the deterministic blend; none may be omitted. The total spatial reliability effect is measured by Rgeo−Rperm, not by a comparison with frozen VMem alone. Region masks remain the original B2 masks in scoring.

**Kill criterion.** Fail the pilot or any mandatory practical comparison: stop this heuristic. A PSNR gain entirely explained by hole initialization is an initialization result. A q map that does not distinguish source disagreement on development inputs is insufficient evidence for uncertainty calibration, irrespective of final scores. Do not fit q against chess targets.

**Budget and implementation window.** No training. R0 may be reused after fidelity; the other four arms require 384 chess generations. Their shortened schedules should be timed rather than assumed to be twice as fast. Allow 6–10 RTX 3090 GPU-hours including source metadata, controls and pilot; cap 14 with the transfer block. Coding and evaluation should fit one to two days if geometry metadata is reusable.

**Genuinely interesting result.** A fixed source-only reliability map improves target fidelity beyond the same distribution of release times shuffled in space, a uniform schedule, and corrected hole initialization, while adding value over a non-generative blend. That would establish a useful reliability policy in this configuration. It would not establish a new regional diffusion algorithm or calibrated probabilities.

## 8. Ranking and what would change the recommendation

1. **P first: robust observation correction inside the sampling loop.** It has the cleanest distinction from S141/S142, needs no retraining, and has an unusually decisive equal-cost final-only control. It asks whether the generator adds useful processing between evidence corrections. The principal risk is that it becomes ordinary rendering or fits incorrect source geometry; the controls expose both.
2. **A second: native history-mass-preserving addressing.** It is the most direct internal-consumption test, but one coarse stage may be insufficient and attention backend changes need care. Its scientific value is separating address from amount; the attention primitive itself is already known.
3. **R third: reliability-dependent release.** It is inexpensive and prompted by a real untested S140 boundary, but its novelty ceiling is lowest because regional release is established and a simpler hole-initialization fix may explain its entire gain.

The first action in a subsequent implementation session should be to freeze P's short protocol and produce the source-observation cache for the fixed pilot—not launch all three. If source-depth/provenance reconstruction cannot fit the budget, Rclean is a cheap standalone control available from existing warp tensors; it is a narrower question, not a substitute claimed as the new source-resolved mechanism.

An interesting positive pilot warrants completing the fixed exposed-panel experiment. A negative pilot warrants a recorded negative, not repeated ideation disguised as progress. A positive final result would justify fresh scene-level confirmation in the remaining project window; it would not retroactively make chess untouched. No method-validation or novelty-authorization flag changes automatically.

## 9. Verification limits and session handoff

The required current status, report, S139/S140 results, S141/S142 protocols and R253/R255/R256 were inspected. Current ledger entries and research principles were consulted for continuity; this brief's one-file and no-compute/no-contact restrictions take precedence over routine ledger writes and external-app review workflows. Three parallel read-only reviews checked code feasibility and prior-art overlap; they supplied no GPU results.

The evidence receipt below extracts archived summaries and timing logs and hashes the consulted snapshot. It does not recompute images, validate remote adapters, reproduce papers, certify upstream byte identity or run model tests. No tests/linter were run because this task produces a research memo without implementation changes. Broad literature priority is unverified; paper metadata and cited passages were checked on arxiv.org during this review.

At initial inspection the checkout already contained untracked S141 fetch, S142 generation and R257–R259 prompt files. Later QA also observed AGENTS.md modified by another process. These files were left alone; the change is reported without attributing its cause or reverting it.

Changed file: work/agents/CODEX_R257_IDEATION_MECHANISMS.md only.

Follow-up worth a new session: implement and time P's fixed pilot, with its final-only and deterministic robust-rendering controls. S141 validation and S142 execution remain separate tasks.

## Appendix A — exact CPU verification command and complete output

This read-only Python command was executed locally. Its output is a receipt of archived values and arithmetic, not new model performance.

```sh
python3 -B - <<'PY'
import collections, hashlib, json, statistics, subprocess
from pathlib import Path
print('HEAD', subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
paths=['CURRENT_STATUS.md','RESEARCH_PRINCIPLES.md','RESEARCH_MEMORY.md','RESEARCH_LOG.md','docs/report/TECHNICAL_REPORT_20261010.md','work/S139_crossseq_revisit/RESULT.md','work/S140_warp_guided/RESULT.md','work/S141_finetune/PROTOCOL.md','work/S142_followup/PROTOCOL.md','work/agents/CODEX_R253_RETRIEVAL_S141.md','work/agents/CODEX_R255_IDEATION_AFTER_S141.md','work/agents/CODEX_R256_S142_DRAFT_REJECTION.md','work/S140_warp_guided/gen_s140.py','work/S141_finetune/gen_s141.py','work/S141_finetune/train_s141.py','work/S141_finetune/s141_common.py','work/S141_finetune/warps_s141.py','data/S134_tacc/vmem_src/modeling/network.py','data/S134_tacc/vmem_src/modeling/pipeline.py','data/S134_tacc/vmem_src/modeling/sampling.py','data/S134_tacc/vmem_src/modeling/modules/transformer.py','data/S134_tacc/vmem_src/modeling/modules/autoencoder.py','work/S141_finetune/clips_s141.json']
for p in paths: print('SHA256',hashlib.sha256(Path(p).read_bytes()).hexdigest(),p)
d=json.loads(Path(paths[-1]).read_text())
print('CLIP_SUMMARY',json.dumps(d['summary'],sort_keys=True))
a=json.loads(Path('work/S139_crossseq_revisit/results/S139_ANALYSIS.json').read_text())['contrasts']['PRIMARY_mem_vmem_vs_static_recent']
print('S139_PRIMARY',json.dumps({k:a[k] for k in ['mean_db','ci95_window','verdict']}))
b=json.loads(Path('work/S140_warp_guided/results/CONFIRM_ANALYSIS.json').read_text())
print('S140_KEYS',list(b))
for metric in ['psnr_db','ssim']:
 print('S140_'+metric,json.dumps(b[metric],sort_keys=True))
logs=sorted(Path('work/S139_crossseq_revisit/results/stepB_tacc').glob('RUNS_*.jsonl'))
rows=[json.loads(l) for p in logs for l in p.read_text().splitlines() if l.strip()]
for p in logs: print('TIMING_LOG',p)
s=[r['seconds'] for r in rows]
print('TIMING',len(s),statistics.mean(s),statistics.median(s),min(s),max(s),sorted({r['gpu'] for r in rows}))
for n in [8,64,96,192,288,384]: print('BASELINE_GPU_HOURS',n,n*statistics.mean(s)/3600)
print('OUTPUT_EXISTS',Path('work/agents/CODEX_R257_IDEATION_MECHANISMS.md').exists())
PY
```

Complete stdout/stderr; exit code 0:

```text
HEAD ddb6b6c56685b5650621be2fc57e1996fcfb7624
SHA256 60c4f4a245bbda05fd9be464c5fba81393904e666f1cb15f7aefb090428bb0fe CURRENT_STATUS.md
SHA256 a264de55418e1224623ec06e7000c5ab8e58f84a01819ac1a9cbec980a0248cd RESEARCH_PRINCIPLES.md
SHA256 d070491215e5d7e7b620af66c0d938fd0834c2ed73eca5a3afb17a7c9d51ef95 RESEARCH_MEMORY.md
SHA256 aaac719851bc50100d1f50afa4a30a360821726137089628beec032b1ffadb5c RESEARCH_LOG.md
SHA256 a9e437e9fd5619070cad5eb38c50f4157c88afcedb5c64c98f66bc405c90b16f docs/report/TECHNICAL_REPORT_20261010.md
SHA256 a09a20a359acc31755a511b8b81ad56747f6046a2c750c5287ef6ab07e4e0f05 work/S139_crossseq_revisit/RESULT.md
SHA256 2db2f7ed6d3184a5cdc5b39c369d98bd2c558e55f56e0513fc3f86292f58634c work/S140_warp_guided/RESULT.md
SHA256 0b5c3aab9809f851ee476b2a54eae781c7c286bbe1e047ac89388b40d3051fdc work/S141_finetune/PROTOCOL.md
SHA256 d4358e4acfc64d8bd9f1d2e29742a2f5facbb67bdecc33f5852dcc74d4a1b692 work/S142_followup/PROTOCOL.md
SHA256 7e17d1600d0b0ab8019ff38fc3ba928f2075f500e72181755fb8770e0ade31de work/agents/CODEX_R253_RETRIEVAL_S141.md
SHA256 62fc97aed343bde1f684140f70bba7cd1281522c34c86d8fe8589cc7965b2a2a work/agents/CODEX_R255_IDEATION_AFTER_S141.md
SHA256 c0bc379db9f9fe847c744c5c51baee85dc5bdbba27ae629632c9db1f92594d0b work/agents/CODEX_R256_S142_DRAFT_REJECTION.md
SHA256 119904b368eefe4f7bd99e1aed0ba91d7a9250aad5e97a0fb298d7007c0a46c9 work/S140_warp_guided/gen_s140.py
SHA256 c903be28ffea8c359c79d927ebdcf782e1d9ac21b81d0b159439e1566fac8121 work/S141_finetune/gen_s141.py
SHA256 6ba0419e5ceb39406bbd1894ffae90398c27daedbc2eea56b18e537ba6187c0a work/S141_finetune/train_s141.py
SHA256 459549706fb3a965fc4f7c5021f4d49cc626158e94a7c9cdc94cf8784cccb6cc work/S141_finetune/s141_common.py
SHA256 72d8f66fb4439ef3cf626d973a594b182bf30b04d89cb0af221c1208fb048470 work/S141_finetune/warps_s141.py
SHA256 9ed21c2d804734d7ca2d81b1e596858835ca70a4a04abb9b5540b872515d4c9b data/S134_tacc/vmem_src/modeling/network.py
SHA256 680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255 data/S134_tacc/vmem_src/modeling/pipeline.py
SHA256 dc07ca0ba571ba5fb48f9856515d2cb7dea25254008a6f8b315538817f352b24 data/S134_tacc/vmem_src/modeling/sampling.py
SHA256 5f0d152a2f6464076cb0ee5aca725b3445420a5f37ac571d3daa77e580e65764 data/S134_tacc/vmem_src/modeling/modules/transformer.py
SHA256 ccb94f107fd07302fa34593f7b840b3066f73548fe800e647eccfd66da473807 data/S134_tacc/vmem_src/modeling/modules/autoencoder.py
SHA256 c2fbdd49e87426d837aa5e90a8e694cddd9032864079cef53c29a66991740f36 work/S141_finetune/clips_s141.json
CLIP_SUMMARY {"kinds": {"memory": 1028, "static": 1004}, "mean_hist_frac_memory": 0.7290856031128404, "n_train": 2000, "n_val": 32, "scenes": {"fire": 210, "heads": 97, "office": 493, "pumpkin": 305, "redkitchen": 608, "stairs": 319}, "val_seqs": ["office/seq-10", "redkitchen/seq-14"]}
S139_PRIMARY {"mean_db": -0.18051140714214683, "ci95_window": [-0.5177184693492473, 0.14474936062757815], "verdict": "NO_MATERIAL_CHANGE"}
S140_KEYS ['psnr_db', 'ssim']
S140_psnr_db {"B2_minus_VMem": {"ci95": [2.8412112010956028, 3.5812008243596134], "history_favourable": {"ci95": [3.047623237484541, 3.8963180386484813], "mean": 3.4738261162364648, "n": 16, "wins": 16}, "mean": 3.208244637323745, "n": 24, "per_pair": {"seq-01->seq-02": 2.963834803941379, "seq-04->seq-03": 3.2025898382293576, "seq-06->seq-05": 3.4583092698004987}, "verdict": "IMPROVES", "wins": 24}, "WGS_minus_B2": {"ci95": [-0.09460827842278613, 0.134346219561331], "history_favourable": {"ci95": [-0.2153553515670188, 0.016469636999922724], "mean": -0.09564758263423934, "n": 16, "wins": 7}, "mean": 0.020282133890735892, "n": 24, "per_pair": {"seq-01->seq-02": -0.18549612066657817, "seq-04->seq-03": 0.1761144202845244, "seq-06->seq-05": 0.07022810205426144}, "verdict": "NO_MATERIAL_CHANGE", "wins": 14}, "WGS_minus_VMem": {"ci95": [2.8613294120528057, 3.5995389045083304], "history_favourable": {"ci95": [2.94447308401223, 3.8223260285952088], "mean": 3.3781785336022256, "n": 16, "wins": 16}, "mean": 3.228526771214481, "n": 24, "per_pair": {"seq-01->seq-02": 2.778338683274801, "seq-04->seq-03": 3.3787042585138822, "seq-06->seq-05": 3.5285373718547604}, "verdict": "IMPROVES", "wins": 24}, "means": {"B2": 14.57238774192119, "VMem": 11.364143104597446, "WGS": 14.592669875811927}, "seeds_complete_8": true}
S140_ssim {"B2_minus_VMem": {"ci95": [-0.06852788762868538, -0.008501490620741006], "history_favourable": {"ci95": [-0.03628812681272393, 0.023497773174312876], "mean": -0.005155191000085324, "n": 16, "wins": 7}, "mean": -0.03852873951351891, "n": 24, "per_pair": {"seq-01->seq-02": -0.022564440267160535, "seq-04->seq-03": -0.037743891356512904, "seq-06->seq-05": -0.05527788691688329}, "verdict": "WORSENS", "wins": 7}, "WGS_minus_B2": {"ci95": [0.014721126846173624, 0.03618809998685416], "history_favourable": {"ci95": [0.0038511253784236036, 0.022294362176035063], "mean": 0.013182241789763793, "n": 16, "wins": 11}, "mean": 0.0251469851937145, "n": 24, "per_pair": {"seq-01->seq-02": 0.00511049572378397, "seq-04->seq-03": 0.0326041235239245, "seq-06->seq-05": 0.03772633633343503}, "verdict": "IMPROVES", "wins": 19}, "WGS_minus_VMem": {"ci95": [-0.03849206399706115, 0.0113749484890528], "history_favourable": {"ci95": [-0.018034399160387692, 0.033261367354862126], "mean": 0.00802705078967847, "n": 16, "wins": 9}, "mean": -0.01338175431980441, "n": 24, "per_pair": {"seq-01->seq-02": -0.017453944543376565, "seq-04->seq-03": -0.005139767832588404, "seq-06->seq-05": -0.01755155058344826}, "verdict": "INCONCLUSIVE", "wins": 10}, "means": {"B2": 0.431765907133619, "VMem": 0.4702946466471379, "WGS": 0.4569128923273335}, "seeds_complete_8": true}
TIMING_LOG work/S139_crossseq_revisit/results/stepB_tacc/RUNS_gpu13_2110672.jsonl
TIMING_LOG work/S139_crossseq_revisit/results/stepB_tacc/RUNS_gpu13_2110673.jsonl
TIMING_LOG work/S139_crossseq_revisit/results/stepB_tacc/RUNS_gpu13_2218137.jsonl
TIMING_LOG work/S139_crossseq_revisit/results/stepB_tacc/RUNS_gpu13_2227306.jsonl
TIMING 288 36.11440972222222 35.56 34.46 37.75 ['NVIDIA GeForce RTX 3090']
BASELINE_GPU_HOURS 8 0.0802542438271605
BASELINE_GPU_HOURS 64 0.642033950617284
BASELINE_GPU_HOURS 96 0.9630509259259259
BASELINE_GPU_HOURS 192 1.9261018518518518
BASELINE_GPU_HOURS 288 2.8891527777777775
BASELINE_GPU_HOURS 384 3.8522037037037036
OUTPUT_EXISTS False
```


## Appendix B — document QA receipt

The following read-only document check was executed after the technical corrections. It checks citation range existence and snapshot stability, not the truth of each proposed mechanism. The byte count is before this appendix was appended. The status also shows concurrent changes, including another review file; none was edited by R257.

```sh
python3 -B - <<'PY'
import hashlib,re,subprocess
from pathlib import Path
p=Path('work/agents/CODEX_R257_IDEATION_MECHANISMS.md')
s=p.read_text(); main=s.split('## Appendix A')[0]
roots={'V/':'data/S134_tacc/vmem_src/','S140/':'work/S140_warp_guided/','S141/':'work/S141_finetune/'}
pat=r'(?<![\w/])((?:V/|S140/|S141/|work/|docs/)[\w/.-]+|RESEARCH_MEMORY\.md):(\d+)(?:[–-](\d+))?'
refs=list(re.finditer(pat,main)); bad=[]
for m in refs:
 name,lo,hi=m.groups(); path=name
 for pre,root in roots.items():
  if name.startswith(pre): path=root+name[len(pre):]
 f=Path(path); lo=int(lo); hi=int(hi or lo)
 if not f.is_file() or not 1<=lo<=hi<=len(f.read_text().splitlines()): bad.append(m.group())
print('memo_exists',p.is_file())
print('memo_bytes_before_qa_append',p.stat().st_size)
print('source_citations_checked',len(refs))
print('invalid_ranges',bad)
print('fences_balanced',s.count(chr(96)*3)%2==0)
print('replacement_characters',s.count(chr(65533)))
changed=[]
for h,name in re.findall(r'^SHA256 ([0-9a-f]{64}) (.+)$',s,re.M):
 if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=h: changed.append(name)
print('reviewed_inputs_changed_since_receipt',changed)
print('git_status_begin')
print(subprocess.check_output(['git','status','--short'],text=True),end='')
print('git_status_end')
assert not bad
PY
```

Complete stdout/stderr; exit code 0:

```text
memo_exists True
memo_bytes_before_qa_append 52865
source_citations_checked 28
invalid_ranges []
fences_balanced True
replacement_characters 0
reviewed_inputs_changed_since_receipt []
git_status_begin
 M AGENTS.md
?? work/S141_finetune/fetch_results_s141.sh
?? work/S142_followup/gen_s142.py
?? work/agents/CODEX_R257_IDEATION_MECHANISMS.md
?? work/agents/CODEX_R258_IDEATION_FROM_FINDINGS.md
?? work/agents/prompts/R257_FULL.md
?? work/agents/prompts/R257_PROMPT.md
?? work/agents/prompts/R258_FULL.md
?? work/agents/prompts/R258_PROMPT.md
?? work/agents/prompts/R259_FULL.md
?? work/agents/prompts/R259_PROMPT.md
git_status_end
```
