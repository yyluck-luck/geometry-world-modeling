# Round 34 — Predictive Method Invention for VMem

**Scope.** This is a generative methods memo, not a validation claim. The project state remains `new_method_validated=false` and `novelty_authorization=NONE`. No GPU, training, weight download, or dataset download was used in this round. All repository numbers below were read or recomputed on CPU from existing files.

## Part 1 — Does the evidence imply support scarcity?

It does not. The clues support a **support-scarcity hypothesis**, but they combine observations from different levels of the system:

- **One retrieval panel:** the saved GPU summary reports `frame_count_raw = [(11, 1)]`: one of the twelve bank frames had visible surfels from the four target cameras (`docs/S103_S109_GPU_EXPERIMENT_SUMMARY_20260917.md:43-48`). This establishes a severe failure on that panel, not a scene-independent rate. It also measures the renderer/map's visible support, not the amount of information the diffusion consumer could infer from a non-visible but correlated frame.
- **Position arm:** the fixed-(k=4) panel reports 11.259 dB for the earliest group and 16.882 dB for the recent group (`docs/S103_S109_GPU_EXPERIMENT_SUMMARY_20260917.md:50-60`). Their difference is 5.623 dB, which explains the document's rounded 5.6 dB. The full table also contains a wide-span arm at 17.265 dB, so the full displayed range is 6.007 dB. The contrast changes both temporal/pose position and scene content; it does not condition on visible support.
- **Slot-0 arm:** the same multiset produces a 0.55 dB difference for `{55,55,40,40}` and 0.87 dB for `{50,50,45,45}` (`docs/S103_S109_GPU_EXPERIMENT_SUMMARY_20260917.md:64-76`). This is a consumer-coordinate effect, not evidence that the scene has too little support.
- **Duplicate repair:** replacing one duplicate with the next candidate gives -0.016 dB over eight eligible windows against a predeclared +0.20 dB threshold (`docs/report/TECHNICAL_REPORT_20260918.md:27-41`, `:241-250`). That closes one repair intervention; it does not compare an actually absent support slot with a generated support slot. The report explicitly says that an absent-slot control was not performed (`docs/report/TECHNICAL_REPORT_20260918.md:301-306`).
- **Retrieval contrast:** the shipped memory arm is +0.242 dB over the fixed context with SD 1.270 over 14 windows (`docs/report/TECHNICAL_REPORT_20260918.md:202-211`). The wide interval and mixed signs do not show that selection has no headroom; they show that this particular selection intervention is unstable and small on this exposed panel.
- **Fusion algebra:** the 4.4e-16 identity check proves that the proposed covariance matrix is algebraically recoverable from individual errors and pairwise source differences under its assumptions (`docs/proposal_v2/NEW_PROPOSAL_DRAFT_20260919.md:176-201`). It rules out that reweighting construction as an information-creating mechanism. It says nothing about a model that predicts new target-view content, new geometry, or new latent features.
- **Code path:** the selector uses surfel counts only to construct a duplicated candidate multiset (`work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:638-661`), then sorts and filters entirely by pose distance (`work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:663-750`) and caps the context by candidate count (`work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:671`). This proves a membership/pose implementation fact; it does not identify whether the downstream error is caused by absent evidence, the wrong reference coordinate system, or the consumer's learned prior.

### The cheapest falsification test

The decisive CPU test is a window-level support-controlled analysis:

1. For every target window and every candidate frame, obtain the saved `surfel_index_map` (or an equivalent target-depth-consistent visibility map) before selection.
2. Compute, per window, (a) the union visible-surfel count, (b) the number of frames with nonzero support, (c) the target-ray support fraction, and (d) support overlap between the selected context and each target frame.
3. Fit the prespecified positional contrast with these quantities as covariates or stratify by support-count bins, while keeping slot 0 fixed. The falsification is: if the 5.623 dB earliest-to-recent contrast remains large inside narrow support-count/overlap strata, the claim that support scarcity is the dominant bottleneck is weakened. If the contrast collapses after support control, scarcity becomes a stronger explanation.
4. A stronger intervention is to render the same target poses after synthetically completing only the missing support pixels, holding the selected IDs, slot order, cameras, seed, and diffusion steps fixed. Improvement in a held-out target-view score would be direct evidence for manufactured support.

I performed the cheapest available CPU audit of `work/S106_context_arms/ARM_SCORES.json`, `work/S107_order_balanced/ARM_SCORES.json`, `docs/report/bundle/S113_SCORES.json`, and `docs/report/bundle/LEAK_REGIME_CENSUS.json`. The JSONs contain PSNR/MAE/MSE, frame IDs, poses, multiplicities, regimes, and slot-0 identity, but no per-window `surfel_index_map`, visible-surfel count, visible-frame count, target support fraction, or support-overlap field. The only `frame_count_raw` record is the single panel summary above. There are no `.npz`, `.npy`, `.pt`, `.pkl`, or `.csv` support maps under the S103/S106/S107/bundle paths. Therefore the requested support-controlled regression is **not identifiable from saved artifacts**; fabricating a proxy from frame age or unique-ID count would answer a different question.

The current synthesis should therefore be written as:

> The panel is consistent with a support-scarcity bottleneck, but the evidence does not distinguish scarcity from content distribution, camera-reference asymmetry, or consumer mismatch. The next cheapest measurement is to save target support maps and re-run the fixed positional panel with support-stratified contrasts.

## Part 2 — Ten methods that change prediction

Every proposal below changes the conditional distribution of the generated target views. None is a retrieval reranker, a write/merge/decay/rollback gate, a covariance reweighting scheme, or a renamed selection layer. Costs are approximate **H800 GPU-hours** for a first serious run, including ablations and held-out scoring, followed by an honest calendar estimate for one researcher.

### 1. CAGF: Context-to-Target Geometry/Appearance Field

**Mechanism.** Train a target-camera field that maps the available context latents, their camera matrices, intrinsics, and the target Plücker rays to a predicted target-view latent, depth/normal field, and calibrated support probability. The prediction is a new content-bearing condition rendered at the target rays; it is not another choice among stored frames. VMem denoises with this proposal as a separate control branch and can learn when the proposal is reliable.

**VMem insertion.** Add a `SupportField` module under `work/S17C_interface_preparation/isolated_vmem_source/modeling/modules/`; call it from `work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:get_cond` after the camera normalization and Plücker construction (`work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:1123-1140`), and inject its target latent/confidence through a zero-initialized control branch in `work/S17C_interface_preparation/isolated_vmem_source/modeling/network.py:178-235`. The target condition is assembled at the existing boundary `work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:1263-1267`.

**Claim.** For the same legal context and target camera, a predicted support field improves future-view appearance and cross-view geometry, especially when the renderer supplies zero or one visible source.

**Estimand.** Paired held-out change in target-view MSE/PSNR and depth/pose consistency, conditional on pre-intervention support fraction; report the conditional average treatment effect of adding the field, with source IDs, order, seed, and diffusion budget fixed.

**Single kill experiment.** On scene-disjoint windows binned by support fraction, compare baseline VMem with the field branch and a shuffled-target-camera field; kill the method if the real field does not beat the shuffled control by at least +0.20 dB and does not improve an independent geometric metric in the low-support bin.

**Cost.** 1,500 H800-hours; 6–8 weeks.

**Nearest published work and delta.** *ViewCrafter: Taming Video Diffusion Models for High-fidelity Novel View Synthesis*, arXiv:2409.02048, §§III-B–III-D, reconstructs a coarse point cloud and uses point-conditioned video diffusion plus iterative view synthesis. CAGF differs by learning a target-ray latent/depth proposal inside an existing VMem context contract, with support calibration and no new-view trajectory search at inference.

### 2. SD-VMem: Support-Dropout-Calibrated VMem

**Mechanism.** During training, randomly erase the renderer's visible pixels, entire context frames, and contiguous target-ray regions while exposing an explicit support/visibility map. The denoiser is trained to treat unsupported pixels as prediction problems, while supported pixels receive a reconstruction-preserving loss; a calibrated uncertainty head prevents the model from copying hallucinated evidence with high confidence.

**VMem insertion.** Extend `get_cond` (`work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:1142-1173`) with a support mask and support-density channel, and add the mask to the `concat` path consumed by `VMemWrapper` (`work/S17C_interface_preparation/isolated_vmem_source/modeling/network.py:221-235`). The training sampler and mask generator live beside `work/S17C_interface_preparation/isolated_vmem_source/modeling/modules/preprocessor.py`.

**Claim.** A generator trained to see the support regime will degrade gracefully under zero-support regions and will recover content after occlusion better than a model trained only on dense conditioning.

**Estimand.** Difference in conditional target error as a function of support fraction and occlusion gap, plus calibration error of the predicted uncertainty; the primary quantity is the slope of error versus support fraction on held-out scenes.

**Single kill experiment.** Evaluate baseline and SD-VMem on a support-dropout ladder with identical clean inputs; kill it if the curves overlap at low support or if the uncertainty head is uncalibrated on a held-out dropout pattern.

**Cost.** 800 H800-hours; 4–5 weeks.

**Nearest published work and delta.** *Spatia: Video Generation with Updatable Spatial Memory*, arXiv:2512.15716v1, §§3.1–3.2, uses an explicit persistent point-cloud memory and dynamic/static conditioning. SD-VMem keeps VMem's surfel memory but changes the denoiser's training distribution and support semantics; it is not an update rule.

### 3. RayLift: Learned Scene-Coordinate Feature Field

**Mechanism.** Convert each context image and camera into a set of scene-coordinate features, aggregate them into a continuous neural field, and query that field at every target Plücker ray. The field predicts a feature and a visibility/depth distribution, allowing the generator to use information that is not representable as one of the four stored RGB latents.

**VMem insertion.** Implement a `RayLiftEncoder` in `work/S17C_interface_preparation/isolated_vmem_source/modeling/modules/`; invoke it in `work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:get_cond` before `c_replace` (`work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:1153-1155`) and inject ray features through `dense_vector` (`work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:1172-1184`).

**Claim.** A continuous scene-coordinate feature field increases cross-view correspondence and reduces view-dependent geometry drift at fixed context IDs.

**Estimand.** Target-ray feature-to-ground-truth correspondence accuracy and paired RGB/depth loss conditional on the same selected multiset; this directly measures new information content rather than retrieval quality.

**Single kill experiment.** Freeze the selected IDs and compare RayLift against a pose-only dense vector and a randomly permuted field on unseen scenes; kill it if the real field does not improve both correspondence and target PSNR.

**Cost.** 1,200 H800-hours; 5–6 weeks.

**Nearest published work and delta.** *AnchorWeave: World-Consistent Video Generation with Retrieved Local Spatial Memories*, arXiv:2602.14941v1, §3.4, jointly attends to local anchor latents and pose-guided fusion. RayLift replaces anchor selection and fusion with a continuous target-ray field queried inside VMem, so the predicted target content can exist where no anchor has visible pixels.

### 4. MHC: Multi-Hypothesis Completion

**Mechanism.** From the same context, generate a small posterior of target-view geometry/appearance hypotheses, each with uncertainty and a shared latent scene code. The denoiser samples or marginalizes these hypotheses at the target view; the system is evaluated as a distribution over plausible futures rather than forced to copy one arbitrary completion.

**VMem insertion.** Add a stochastic `HypothesisField` before `get_cond` and pass (H) proposal features through a new hypothesis-attention block in `work/S17C_interface_preparation/isolated_vmem_source/modeling/network.py` after the existing `MultiviewTransformer` calls (`work/S17C_interface_preparation/isolated_vmem_source/modeling/network.py:78-169`). This changes the target conditional distribution while preserving the legal state lists.

**Claim.** Explicit multimodality reduces catastrophic wrong-side completions after occlusion without sacrificing fidelity on supported pixels.

**Estimand.** Negative log-likelihood or calibrated coverage of the ground-truth target under the hypothesis mixture, plus best-of-(H) and mean-of-(H) PSNR and cross-view consistency.

**Single kill experiment.** Use an occlusion-reappearance benchmark with two genuinely plausible hidden appearances; kill it if the hypothesis mixture has no better calibrated coverage than a single-sample baseline at equal compute.

**Cost.** 1,800 H800-hours; 6–7 weeks.

**Nearest published work and delta.** *Beyond Pixel Histories: World Models with Persistent 3D State*, arXiv:2603.03482v2, §3, introduces persistent 3D state for world-model prediction. MHC targets posterior uncertainty in the VMem target-view completion itself and measures calibrated hidden-content coverage, rather than replacing the memory with a persistent voxel state.

### 5. CRP: Canonical-Ray, Permutation-Stable Conditioning

**Mechanism.** Remove the arbitrary first-context-camera coordinate frame by expressing every context ray and camera pose in a target-centered or learned canonical frame. Train with random permutations and a consistency loss so the same multiset yields the same prediction, while retaining the actual camera geometry as a set of relative transforms.

**VMem insertion.** Replace the source choice `extrinsics_src=all_w2cs[:1]` in `work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:1135-1140` with a target-centered canonicalization, and add a permutation-consistency wrapper around `MultiviewTransformer` (`work/S17C_interface_preparation/isolated_vmem_source/modeling/modules/transformer.py:169-248`). This is a change in geometric conditioning, not a change in which frames are read.

**Claim.** Removing the reference-camera coordinate discontinuity eliminates slot-0-dependent predictions and frees the model to use complementary support rather than the first slot's coordinate basis.

**Estimand.** Same-multiset permutation variance of the target prediction and target-view error after controlling for support and camera poses; the primary effect is the reduction in order sensitivity at fixed information.

**Single kill experiment.** Evaluate six permutations of each fixed multiset on held-out windows with equal seeds; kill it if CRP fails to reduce permutation variance by 80% or loses more than 0.05 dB on the canonical order.

**Cost.** 600 H800-hours; 3–4 weeks.

**Nearest published work and delta.** *Set Transformer: A Framework for Attention-based Permutation-Invariant Neural Networks*, arXiv:1810.00825, §3, constructs attention modules for permutation-invariant set inputs. CRP adds the missing geometric quotient and target-ray canonicalization to VMem's camera-conditioned diffusion path; it is not a generic set-pooling replacement.

### 6. PTS: Per-Source Token Cross-Attention

**Mechanism.** Preserve each source's semantic embedding as a token tagged with its camera, support map, and age instead of taking one global mean. Cross-attention can then learn source-specific appearance and conflict patterns, while the target rays determine where each source token is useful.

**VMem insertion.** Replace `context_encoder_embeddings = torch.mean(encoder_embeddings, dim=0)` (`work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:1123-1125`) and the repeated global token (`work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:1149-1150`) with per-source tokens plus camera/support metadata. Add a source-token cross-attention module to `work/S17C_interface_preparation/isolated_vmem_source/modeling/modules/transformer.py:78-111`.

**Claim.** Retaining source identity improves appearance reappearance and reduces semantic dilution when visible support is sparse or contradictory.

**Estimand.** Conditional target error and source-local attribution under fixed latent/camera inputs; report whether a token's removal changes pixels in its projected support region more than a matched placebo.

**Single kill experiment.** Train global-mean, per-source-token, and shuffled-source-tag models at equal parameter count; kill it if per-source tokens do not improve source-local attribution and held-out PSNR.

**Cost.** 700 H800-hours; 3–4 weeks.

**Nearest published work and delta.** *Latent Spatial Memory for Video World Models*, arXiv:2606.09828v2, §3, stores spatial memory in latent tokens. PTS is a VMem-specific consumer change that keeps source-wise tokens and camera/support tags through `get_cond`; it does not merely move the same retrieval decision to another layer.

### 7. OLR: Occlusion-Layered Radiance State

**Mechanism.** Predict a small ordered set of front-surface, occluded-surface, and unknown-layer features with per-ray depth distributions. The target denoiser can re-use a back layer when a later camera reveals it, instead of treating the first visible RGB layer as the whole scene.

**VMem insertion.** Extend the surfel renderer output passed into `get_cond` with layered depth/feature planes and add a layer axis to `dense_vector` (`work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:1135-1173`); train a layer-aware attention block in `work/S17C_interface_preparation/isolated_vmem_source/modeling/modules/transformer.py:169-248`.

**Claim.** Explicit hidden-layer state improves content reappearance after occlusion at the same geometry and support budget.

**Estimand.** Reappearance PSNR/LPIPS and identity consistency after an occlusion gap, conditional on the same pre-gap context; also measure front/back layer depth error.

**Single kill experiment.** Hold out tracks containing a visible–occluded–visible pattern and compare OLR with a single-layer field; kill it if reappearance does not improve while pre-occlusion quality remains matched.

**Cost.** 2,000 H800-hours; 7–8 weeks.

**Nearest published work and delta.** *Novel View Synthesis with Diffusion Models* (3DiM), arXiv:2210.04628, §3, uses pose-conditioned diffusion and stochastic conditioning for consistent novel views. OLR adds explicit multi-depth occlusion state and trains on reappearance events; 3DiM does not provide VMem's persistent layered scene state.

### 8. GSD: Geometry-Supervised World-State Distillation

**Mechanism.** Distill many context frames into a compact scene token set trained with a geometry teacher, then decode target-view latent and depth features from those tokens. At inference the teacher is absent; the compact state is the information-bearing object, so the model predicts from a learned world representation rather than from the four raw slots alone.

**VMem insertion.** Add a `SceneStateEncoder` between `get_context_info` and `get_cond` (`work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:1249-1267`) and pass the state tokens through a new cross-attention path in `work/S17C_interface_preparation/isolated_vmem_source/modeling/network.py:178-235`. The stored legal state remains unchanged; only the consumer's learned representation changes.

**Claim.** Geometry-supervised state tokens retain scene structure when the visible RGB support is nearly empty and improve future camera prediction.

**Estimand.** Target RGB/depth error and state-to-target mutual-information proxy at fixed context budget, with and without the geometry teacher at inference.

**Single kill experiment.** On held-out scenes, compare GSD to a same-size RGB-only scene encoder and a frozen teacher feature; kill it if geometry supervision does not improve target depth and cross-view consistency.

**Cost.** 2,500 H800-hours; 8–10 weeks.

**Nearest published work and delta.** *Geometry-Aware Implicit Memory for Video World Models*, arXiv:2606.02436v1, §3, supervises an implicit memory with geometry features. GSD tests the same principle inside the exact VMem latent/Plücker consumer and requires a target-view causal gain under low support, rather than claiming that geometry supervision alone is a new memory mechanism.

### 9. TDB: Trajectory-Conditioned Latent Dynamics Bridge

**Mechanism.** Learn a short-horizon latent dynamics model over camera motion that predicts intermediate scene features and target-view appearance from the last trusted state and a future camera trajectory. It is trained on real trajectories with randomly removed intervals, so it learns how content should evolve under camera movement rather than simply preferring recent frames.

**VMem insertion.** Call the bridge in `_generate_frames_for_trajectory` immediately after target cameras are formed (`work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:1245-1267`) and inject its predicted intermediate features into `dense_vector`; train the bridge jointly with a LoRA on temporal-mixing blocks (`work/S17C_interface_preparation/isolated_vmem_source/modeling/modules/transformer.py:114-156`).

**Claim.** A learned camera-conditioned transition prior improves future-view prediction for long gaps even when the scene map has no visible surfels.

**Estimand.** Error as a function of camera-distance and gap length, with a held-out trajectory segment removed from conditioning; report the interaction between bridge use and gap length.

**Single kill experiment.** Mask random contiguous future segments in held-out trajectories and compare TDB to constant-latent persistence and ordinary VMem; kill it if the gap-length slope is not reduced at equal target camera error.

**Cost.** 2,200 H800-hours; 8 weeks.

**Nearest published work and delta.** *Beyond Pixel Histories: World Models with Persistent 3D State*, arXiv:2603.03482v2, §3, models persistent 3D world state. TDB is a camera-conditioned transition prior attached to VMem's diffusion target path, with a direct gap-length estimand rather than a general persistent-state replacement.

### 10. FVC: Free-View Curriculum for the VMem Consumer

**Mechanism.** Use reconstructed scenes to generate carefully screened virtual target views during training, then train VMem to predict those views from sparse context and explicit support maps. The generated views are supervision and exposure to rare camera gaps, not extra context frames selected at inference.

**VMem insertion.** Add a virtual-view training dataset and support-map augmentation to `work/S17C_interface_preparation/isolated_vmem_source/modeling/modules/preprocessor.py`; no retrieval code changes are required. The consumer changes through the denoising objective in `work/S17C_interface_preparation/isolated_vmem_source/modeling/network.py:178-218`, with target support channels assembled at `work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:1169-1173`.

**Claim.** Exposure to geometrically valid but previously unseen target views increases generalization to large camera gaps and sparse support.

**Estimand.** Held-out target-view PSNR/SSIM/depth consistency versus real-only training at equal number of optimizer steps and real-image budget; separately estimate gains on large camera motion.

**Single kill experiment.** Train real-only and FVC models with the same real windows and compute; kill it if FVC does not improve a scene-disjoint large-motion split or if improvement disappears when the virtual-view geometry is randomized.

**Cost.** 1,000 H800-hours; 4–5 weeks.

**Nearest published work and delta.** *FreeScale: Scaling 3D Scenes via Certainty-Aware Free-View Generation*, arXiv:2604.10512v1, §§4.1–4.2, generates certainty-aware free views and uses them to scale novel-view models. FVC transfers the data-generation idea to VMem's support-conditioned target consumer and tests causal benefit under fixed real-data and compute budgets.

## Part 3 — Strongest proposal: CAGF in depth

I would start with CAGF because it changes the missing information term directly and has a clean counterfactual: the selected context, state lists, slot order, camera poses, random seed, sampler, and diffusion budget remain identical; only a learned target-ray content proposal is added. It can still help if the scarcity hypothesis is false, because the same field can correct a consumer that fails to use visible support.

### Concrete architecture changes

1. **Support-field module.** Create `work/S17C_interface_preparation/isolated_vmem_source/modeling/modules/support_field.py` with a context encoder, camera/Plücker encoder, cross-view attention, and two decoders: a target latent proposal \hat{z}_q and a target geometry proposal \hat{g}_q containing depth, normal, and a calibrated support probability (p_q). Inputs are the existing `context_latents`, `context_c2ws`, `context_Ks`, `context_time_indices`, and target camera tensors.
2. **Pipeline boundary.** In `work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:get_cond`, retain the existing pose normalization and Plücker construction (`work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:1128-1140`), then call the support field before padding and `c_replace` (`work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:1142-1155`). For supported target rays, concatenate the renderer feature and the predicted proposal; for unsupported rays, provide the proposal plus a low-support indicator. This is a target condition, not a new context slot.
3. **Zero-initialized control path.** In `work/S17C_interface_preparation/isolated_vmem_source/modeling/network.py`, add a ControlNet-style `support_control` branch parallel to the existing `concat` path (`work/S17C_interface_preparation/isolated_vmem_source/modeling/network.py:221-235`) and add its residual at the first and middle multiview blocks (`work/S17C_interface_preparation/isolated_vmem_source/modeling/network.py:56-133`). Zero initialization preserves the shipped model at step zero; only the branch and selected LoRA parameters are trained first.
4. **Slot-0 guard.** During the first implementation, canonicalize rays target-centrically so the bridge is not trained to exploit the known first-slot coordinate bug. Keep a separate CRP ablation; do not silently mix slot canonicalization into the main CAGF claim.

### Training data and protocol

Use scene-disjoint windows from RealEstate10K/DL3DV-style calibrated sequences plus the project's permitted RGB-D/trajectory sources. Each training example contains observed frames, cameras, a target camera, the target RGB/depth answer used only for loss, and a renderer-derived support map. Sample support dropout in four independent ways: pixel erasure, frame erasure, target-region erasure, and complete zero-support targets. The held-out evaluation scenes and target answers are never available to the selector or field at inference.

The first stage trains only the field and a small camera/feature encoder. The second stage freezes the field and trains the zero-initialized support control branch plus LoRA on the VMem denoiser. The final stage jointly fine-tunes the field and control branch with a low learning rate; the original VMem backbone is retained as a capacity-matched baseline.

### Objective

For target latent (z_q), target geometry (g_q), support probability (p_q), noisy latent (z_t), and denoiser noise ε, use

\[
\mathcal{L} = \lambda_\epsilon\|\epsilon_\theta(z_t,t,C,\hat z_q,\hat g_q,p_q)-\epsilon\|_2^2
+\lambda_z\|\hat z_q-z_q\|_{1,\,\text{target}}
+\lambda_g\operatorname{Huber}(\hat g_q-g_q)\\
+\lambda_{\rm cyc}\mathcal{L}_{\rm reproj}(\hat g_q,\text{observed context})
+\lambda_{\rm cal}\operatorname{Brier}(p_q,\mathbf{1}[\text{proposal error}<\tau]).
\]

The reprojection term uses only observed context and known cameras; the target RGB/depth answer appears only in the training loss and never in the runtime proposal. Weight the latent and geometry losses by the sampled support mask so the field cannot win by copying already-supported pixels. Include a no-proposal and shuffled-camera control in every validation checkpoint.

### First 1–2 week decision milestone

- **Days 1–3:** build a CPU-only contract test that feeds saved S106/S107 context tensors and synthetic target cameras through a shape-correct field stub; verify that the baseline path is byte-identical when the zero-initialized branch is disabled, and verify that the target support map is not read from future files.
- **Days 4–7:** prepare scene-disjoint training manifests and generate support masks from the calibrated sequences; freeze train/validation/test identities before reading test answers.
- **Days 8–14:** train the field and control branch on a small H800 pilot (about 150–250 GPU-hours), evaluate on at least 20 held-out scenes and a support ladder. Continue only if (i) the field's held-out depth/latent error beats a pose-only predictor, (ii) the VMem branch gives at least +0.20 dB on low-support targets against the exact same contexts, and (iii) no more than 5% degradation occurs on high-support targets. Otherwise stop CAGF before scaling.

### Final held-out evaluation

Use a scene-disjoint, trajectory-disjoint panel with at least four target offsets per scene and a predeclared low/medium/high support stratification. Compare original VMem, CAGF, support-dropout training, a pose-only field, and a shuffled-camera field. Primary metrics are pooled target PSNR/SSIM/LPIPS and depth/normal consistency; secondary metrics are camera obedience, occlusion reappearance accuracy, support-calibration Brier score, and failure rate. Report paired window effects with confidence intervals, per-support-bin effects, and exact replay variance. Preserve all negative windows and do not call development scenes held out.

### Why it is difficult to scoop in the next 12 months

Sparse-view completion, point-conditioned diffusion, persistent spatial memory, and free-view data generation already have strong precedents: ViewCrafter (arXiv:2409.02048, §§III-B–III-D), Spatia (arXiv:2512.15716v1, §3), AnchorWeave (arXiv:2602.14941v1, §3.4), and FreeScale (arXiv:2604.10512v1, §§4.1–4.2). The defensible contribution is therefore not “we hallucinate missing views.” It is the combination of (a) an explicit support-conditioned target proposal, (b) a causal low-support estimand under the exact VMem state protocol, (c) slot-0 canonicalization and support calibration, and (d) scene-disjoint evaluation that separates manufactured support from selection and consumer-coordinate effects. Reproducing this requires the VMem fork, the sealed protocol, the support-map instrumentation, a training corpus, and the held-out panel; a generic paper can imitate the architecture but cannot quickly reproduce the same causal evidence.

## Part 4 — What slot 0 reveals about the consumer

The slot-0 effect is a mechanistic clue, not merely a nuisance statistic.

1. **The first context camera defines the ray coordinate system.** `get_cond` calls `get_plucker_coordinates` with `extrinsics_src=all_w2cs[:1]` (`work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:1135-1140`). Because `all_c2ws` is built by concatenating context cameras before target cameras (`work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:1263`), the first selected context frame supplies the source coordinate frame for every Plücker ray. Swapping the first context frame changes the numerical dense condition even when the multiset is unchanged.
2. **Latent content remains slotwise.** The context latents are padded and inserted into `c_replace[input_masks]` in their existing order (`work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:1142-1155`). The model therefore receives a sequence of slot-specific latent images, not a pooled latent.
3. **Semantic content is globally pooled.** The encoder embeddings are averaged at `work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:1123-1125`, then repeated as the same cross-attention token for every camera (`work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py:1149-1150`). This path cannot tell which source supplied which semantic feature, even though the latent path can.
4. **The transformer treats the sequence as temporal.** `MultiviewTransformer` takes the first timestep as `time_context_first_timestep`, reshapes tokens with `t=num_frames`, and performs temporal mixing (`work/S17C_interface_preparation/isolated_vmem_source/modeling/modules/transformer.py:216-243`). There is no learned `nn.Embedding` or explicit slot-ID table in the inspected VMem transformer. The observed asymmetry is thus explained by the first-frame ray reference plus temporal ordering, rather than by a declared learned slot embedding.
5. **The asymmetry is actionable.** A model can either (a) canonicalize all rays to the target camera and enforce permutation consistency (CRP), or (b) deliberately learn a canonical “anchor” slot whose content is optimized for geometric conditioning. The first option is safer scientifically because it removes a protocol artifact before testing support-manufacturing gains. Any future context experiment must keep slot 0 fixed or include slot 0 as a registered factor.

The strongest immediate mechanistic prediction is: after target-centered canonicalization, the same-multiset permutation effect should collapse while the low-support error remains. If canonicalization removes the 0.55/0.87 dB effect but does not improve low-support target accuracy, the original asymmetry was a coordinate artifact rather than evidence for a support-manufacturing method.

## Verification and provenance notes

- The three pinned VMem pipeline copies are byte-identical at SHA-256 `90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e`; the checked anchors are in `work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py` and identical copies listed in the brief.
- Repository evidence was checked directly at the cited paths and line numbers. The CPU JSON audit was read-only and produced no repository artifact.
- Public literature identifiers were checked against arXiv pages where available: ViewCrafter (`2409.02048`, §§III-B–III-D), 3DiM (`2210.04628`, §3), Set Transformer (`1810.00825`, §3), Spatia (`2512.15716v1`, §3), AnchorWeave (`2602.14941v1`, §3.4), and FreeScale (`2604.10512v1`, §§4.1–4.2). The additional nearby-work IDs GIM-World (`2606.02436v1`), LSM-World (`2606.09828v2`), and PERSIST (`2603.03482v2`) match the repository's citation audit in `docs/LITERATURE_SYNTHESIS_V2_CITATION_AUDIT.json`; their claims here are limited to the mechanisms recorded there.
- The mandated external Astra review command was attempted in the repository with network enabled but returned HTTP 401 (missing API bearer) before producing a review. No Astra output is used as evidence. The local ChatGPT Pro UI channel was unavailable to the computer-use surface, so no Pro verdict is represented; the method decisions above are based on directly checked repository code, saved artifacts, and the cited primary papers.
