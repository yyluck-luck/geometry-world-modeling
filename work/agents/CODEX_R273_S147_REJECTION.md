# R273 — S147 Anchor-A protocol rejection review

Workspace: local Mac, read-only repository inspection and CPU analysis. Review date: 2026-10-11. Observed HEAD: 565770bc99f9f6ebfe0a6b99099b6d15a29d2b7d. Source and input hashes, the exact numerical inspection command, and its complete output are in Appendix A.

**Verdict: REJECT THE DRAFT AS FREEZE-READY; ACCEPT A REVISED, BOUNDED MECHANISM DIAGNOSTIC.** Do not run S147 unchanged. The experiment is technically possible and can be informative. There is no evidence that frozen A makes branch learning impossible, and no evidence that the practical threshold is mathematically unattainable. There is also no evidence yet that Anchor-A will work.

The most serious defects are incomplete initialization/resume/serialization semantics, an insufficiently identified mechanism claim, undefined development geometry fallback, an incompletely specified blend comparator, and a budget that omits essential work. These are repairable without a new architecture search. If the sole objective is a likely novel competitive method, I would not spend this budget on S147. If the objective is to resolve whether retaining A permits a small input branch to add useful appearance evidence, a single capped comparison is defensible.

This review applies the fatal-flaw and feasibility portions of the local idea-evaluator skill. It does not assign speculative novelty scores. S147 is an ablation of an established conditioning family, not an established novel method. S145 motivates a training-time question; it does not identify the cause of B's training failure. Its own limitation explicitly says inference-time ablations cannot identify training-time causes (work/S145_B_diagnosis/RESULT.md:43–58,74–76). No S146 generation outcome is assumed or used.

All quantitative observations below are marked DERIVED from archived outputs or MEASURED (archived). Thresholds, budgets, and counterfactual reasoning are ANALYTICAL proposals. Large remote adapters, latent files, frames, environment versions and office1 storage history were not independently inspected. No GPU, training, SSH, Slurm, downloads of weights/data, or contact with anyone occurred. Only the requested review file is authored. The pre-existing untracked work/agents/prompts/R273_FULL.md is left alone; ledgers and source files are not modified.

## 1. Can the four arms be implemented exactly?

**Yes, with a dedicated S147 trainer and loader. No, not by changing the variant argument to the existing scripts.**

### 1.1 Frozen A does not block activation gradients

The branch is an ordinary convolution added to the base input convolution (work/S141_finetune/s141_common.py:97–106). The checkpointed forward explicitly uses non-reentrant checkpointing and propagates through every input, middle and output block (same file:129–142); the ordinary forward and wrapper also contain the normal differentiable path (data/S134_tacc/vmem_src/modeling/network.py:178–218,226–235). Freezing parameter gradients does not remove the derivative of the loss with respect to the branch output.

The local source therefore supports feasibility, not a runtime certification. PyTorch's official checkpoint documentation also distinguishes the non-reentrant path from the reentrant requirement for gradient-bearing inputs: [torch.utils.checkpoint, non-reentrant note](https://docs.pytorch.org/docs/2.14/checkpoint.html). The cluster's installed version and kernels remain unverified here.

Do not wrap the frozen downstream UNet in no_grad or inference_mode, and do not detach its input to save memory. S141 currently uses no_grad only for constructing conditioning, while the loss forward retains autograd under bf16 autocast (train_s141.py:54–68,119–121). A frozen backbone still needs downstream activation derivatives; a small trainable parameter count does not guarantee cheap training.

Required future evidence: nonzero finite branch gradients on a valid training clip, an actual branch update, unchanged frozen tensors, and checkpointed versus ordinary forward/loss/branch-gradient agreement. A compile check or requires_grad flag is insufficient. No such S147 test was performed in this review.

### 1.2 Concrete reuse hazards

| Finding | Evidence | Required correction |
|---|---|---|
| The trainer accepts only A/B and initializes fresh adapters; it does not initialize from trained A. | work/S141_finetune/train_s141.py:18–22,42–49 | Add a distinct A warm-start path. All four arms start from the same final A LoRA tensor state and a fresh optimizer. |
| add_adapters freezes the base, then creates trainable LoRA and branch modules. It does not freeze the new A LoRA. | work/S141_finetune/s141_common.py:109–122 | Load A, freeze all parameters, enable only an exact arm-specific name allowlist, then construct the optimizer. F arms train only the branch weight and bias. |
| A final adapter is not a resumable training checkpoint. Resume requires optimizer, scheduler and RNG state absent from adapter_final.pt. | train_s141.py:88–100,135–136 | Separate initialization from same-arm S147 resume. Do not inherit S141 optimizer moments or its completed step counter. |
| A→B loading is rejected by the inference variant check and missing-branch check. | work/S144_A_wgs/gen_s144.py:121–130 | Keep architecture variant A/B, add scientific arm_id and schema. Only the explicit A warm-start conversion may omit exactly the two newly zeroed branch tensors. Do not broadly disable strict adapter-key checks. |
| An ordinary prototype buffer is not retained by adapter_state. | s141_common.py:125–126 | Store the prototype explicitly in the checkpoint with its construction, dtype, membership and validity hashes. Verify it at resume and inference. |
| Existing B inference always supplies the real warp latent. | gen_s144.py:263–272,289–290 | Implement F_null's stored-prototype substitution at inference too, preserving the current example's coverage. |
| Zeroing branch inputs is bias_only, not off. Context zeros still receive the learned branch bias. | s141_common.py:102–106,157–163; gen_s144.py:140–152 | True bypass returns the base convolution before evaluating the branch, including for nonfinite warp inputs. Keep the drafted context-bias and c/uc policy identical across F/J arms. |
| S144 A plans include W2CR and ordinary entries; its scorer selects W2CR and expects its own endpoint arms. | build_plans_s144.py:20–27; score_s144.py:15,54–67; gen_s144.py:283–290 | Make S147 ordinary-sampler plans and a dedicated arm-map scorer. Reuse metric functions, not the S144 driver unchanged. |
| Existing generation skips by output filename alone. | gen_s144.py:250–254 | Use fresh arm/configuration directories; authenticate completed files with matching plan, adapter, source and output hashes before any resume reuse. |
| The current adapter checker cannot check frozen-A preservation, prototype identity or attempted/valid clocks. | work/S141_finetune/check_adapter_s141.py:6–13 | Add S147-specific validation. Architecture counts alone cannot distinguish F_geo from an accidentally trained J_geo. |

Posttraining F_geo and F_null can have exact-A bypass. Posttraining J_geo cannot promise that: its LoRA has changed. Its bypass means its current joint-trained backbone without the branch. At step zero, all four arms should reproduce A. Verify both F arms at the final checkpoint, not just F_geo.

Preserve the latent definition: the VAE encodes the posterior mean multiplied by its scale factor, not a sampled posterior (data/S134_tacc/vmem_src/modeling/modules/autoencoder.py:21–25). Branch representation, target order, coverage pooling, sampler precision and training precision need separate receipts. Flash Attention is explicitly selected in the inspected transformer (data/S134_tacc/vmem_src/modeling/modules/transformer.py:60–72); algebra alone cannot guarantee byte replay across changed software/hardware.

### 1.3 Scheduled attempts, RNG and resume

The present step indexes permutations, counts updates, terminates the loop and controls saving (train_s141.py:110–136). A naive continue on an invalid clip can repeat that clip forever or silently change the schedule. Separate attempted_steps and valid_updates. Invalid attempts must advance the former while leaving optimizer and scheduler untouched. Specify warm-up in valid optimizer updates.

**DERIVED:** the local warp logs contain exactly the asserted invalid set: 47 of 2,032 unique clips, 46 train and c02028 monitor; nonfinite reprojection and nonfinite-focal sets agree. With five complete passes through the unchanged 2,000-entry training list, the proposed 10,000 attempts produce **9,770 valid updates**, not 10,000 updates. Appendix A gives all invalid IDs and the calculation. Sources: work/S141_finetune/results/tacc/logs/WARP_LOG_*.jsonl and clips_s141.json.

Consume CFG, sigma and full-shaped noise draws before the skip decision in every arm; a skipped clip must not enter any model forward, backward, optimizer or scheduler step. Save the actual permutation/cursor or its reconstructible generator state, both clocks, optimizer/scheduler and Python/NumPy/CPU/CUDA RNG states. Verify cross-arm digests and interrupted/uninterrupted replay across an invalid attempt and an epoch boundary.

Do not invent an existing RNG bug: S141's clip permutation has a separate NumPy generator, CFG uses Python random, training sigma/noise use CUDA and validation uses its own CUDA generator (train_s141.py:77–83,110–118). New LoRA/convolution modules are initially constructed on CPU and moved afterward (s141_common.py:87–89,102,119–120). Different architecture initialization therefore does not by itself establish that archived A/B used different CUDA training noise. Explicitly isolated S147 streams are still preferable.

A short timing/gradient pilot must be discarded or resumed with its complete exact state according to a predeclared rule. Resetting weights while retaining pilot optimizer/RNG state is a different experiment.

## 2. Is F_null fair, and what does a positive result identify?

**Keep the four-scalar training prototype, but rename its meaning precisely: no instance-specific warp appearance, conditional on the actual estimated coverage and ordinary context.** It is not no-content, no-geometry or no-memory: context RGB still supplies content and the coverage map varies with the scene and target pose.

The convolution is linear with a bias and zero padding (s141_common.py:97–106). **ANALYTICAL:** constant latent channels primarily provide a target-slot offset, with additional boundary patterns from padding. They have much less effective input variation than real latent channels despite identical parameter counts and tensor shapes. Thus F_geo−F_null compares two learned recipes differing in information and optimization, not just read-time access to a latent.

Define the prototype as a float64 accumulation over all four target-warp latents and all spatial positions of each valid training clip, divided by the total element count for each channel, then cast once to the frozen stored dtype. Use context-derived warp latents, never clean target latents. No monitor, chess, S146 or office1 example enters that mean. Do not recompute it per batch, scene, evaluation clip or resumed process.

Alternative controls answer different questions:

- A global training spatial mean map contains a fixed layout prior. It avoids direct evaluation-target leakage if constructed only from training warps, but is a stronger structured prior, not a neutral replacement for the four-scalar null.
- A per-clip spatial average removes layout but retains instance appearance statistics; it is useful for an appearance-versus-layout contrast, not content-free.
- A warp from another training clip preserves donor image structure but contradicts the current cameras/coverage. It tests wrong-content conditioning and may be out of distribution. It is not a strictly superior null.
- A donor from another evaluation clip can introduce current-target content through overlapping windows or contexts. A source-only label on the donor does not prove source-only relative to the recipient. Reject such donors without a recipient-level disjointness proof.

Add cheap-in-design but explicitly budgeted **fixed-checkpoint** diagnostics: F_geo with prototype latent and F_geo with coverage-stratified latent permutation, keeping its checkpoint, coverage, poses, context, slots and sampling noise fixed. The latter is already implementable using gen_s144.py:224–235. Freeze its seed mapping and report moved fractions; do not cherry-pick corruptions. These diagnose appearance and alignment sensitivity. Corruption damage alone is not proof of correct use, as S145 itself states (RESULT.md:49–51). Combine them with absolute improvement over A and the trained-null comparison.

If F_geo beats a damaged F_null but remains below A, it has not added useful accuracy to A. If F_geo and J_geo tie, anchoring necessity is not established. With one training seed, even a positive F_geo−J_geo contrast is conditional evidence for this frozen-versus-joint recipe, not a universal explanation of co-adaptation.

## 3. Development gate and S144 comparators

**DERIVED from work/S144_A_wgs/results/SCORES_dev.json; exact command/output in Appendix A.** All values below use the complete existing panel.

| Comparator | Mean PSNR, dB | Mean SSIM |
|---|---:|---:|
| A_none | 11.187286294 | 0.560022306 |
| B2 | 13.190760458 | 0.573130307 |
| V | 13.263184172 | 0.586958300 |
| BL_FC | 13.583318284 | 0.590848704 |
| BL_AC | 13.607907420 | 0.592365212 |

The practical rule implies F_geo ≥ **13.807907420 dB**, or **+2.620621127 dB over A_none**, before accounting for A_cont. These are DERIVED thresholds, not predicted results. A substantial gap is appropriate for a competitive-refinement claim; it is an unsuitable sole definition of whether the branch learned anything useful. The records provide no attainable-performance upper bound, so calling failure predetermined would overstate the evidence.

**The blend definition is a binding omission.** BL_AC = 0.60 × A_C + 0.40 × B2, where A_C is A under the S144 W2CR C endpoint at strength 0.5. BL_FC analogously uses the frozen base's WGS C endpoint with coefficient 0.55. Neither means plain standard-sampler A blended with B2 (score_s144.py:4–6,54–67; build_plans_s144.py:12–14; gen_s144.py:188–222; results/ALPHA.json:3–7). Confirmation needs the corresponding WGS output and its compute allowance.

BL_AC is strongest of these blends globally, but BL_FC is slightly stronger on seq-10: **DERIVED 13.265094620 versus 13.261606681 dB**, same score file/Appendix A. Retaining BL_AC as the globally selected comparator is defensible; do not claim it is the strongest on each sequence or every future domain. Report BL_FC on development. A separately fitted ordinary-A/warp blend is a useful cheap scoring control, but must have a distinct name and a coefficient frozen before confirmation.

Two inexpensive controls from R271 are also missing: nearest-context copy and the ordinary-A/warp blend (CODEX_R271_IDEATION_AFTER_S145.md:137). Both reuse available source images or ordinary A outputs; neither needs another trained model. Include them in the practical set. Their S147-matched development scores have not been calculated here, so 13.807907420 dB is only a lower bound on the eventual required score.

The correct separation is:

1. PRIMARY_SCREEN: does training with the instance-specific warp outperform training with the prototype?
2. USEFUL_CONTENT_SCREEN: does it also improve A, with supportive fixed-checkpoint content diagnostics?
3. PRACTICAL_GO: does the candidate additionally clear the frozen simple estimators and continuation control?

Keep the practical threshold. Do not lower it after failure. Permit a mechanism-screen-positive/practical-negative report without relabeling it a method success. The minimal specification below keeps fresh confirmation conditional on practical GO; it does not silently authorize fresh-data spending for a weaker positive.

The single-run mechanism answer can justify the training cost only if this conditional diagnostic is itself the intended deliverable. S145 already established that B is sensitive to its input branch; repeating that sensitivity alone would not justify S147. The new information is the frozen-A versus jointly updated-A training comparison with identical start state and a content-poor trained control.

## 4. Leakage, exposure and validity boundary

### 4.1 The development panel is exposed and dependent

The monitor current sequences are excluded from training, while monitor histories may be training sequences (work/S141_finetune/build_clips_s141.py:44–64). S144 directly builds development from these same monitor IDs (build_plans_s144.py:8–14). S141 evaluates monitor loss repeatedly (train_s141.py:75–85,108–109,133–134).

**DERIVED from clips_s141.json, Appendix A:** no monitor target image occurs in the training context-or-target set; **59** unique monitor context images do occur there. The **128** monitor target slots contain **105** unique images, with maximum repetition **4**. Therefore this is a reasonable exposed development panel, not a new-scene evaluation or independent collection of image targets. A clip bootstrap is descriptive; neither repeated frames nor sampling seeds create independent environments.

S144 fits alpha on precisely the same development clips/seeds used to report the blends (analyze_s144.py:41–48; results/ALPHA.json:7). That is optimistic development fitting. It does not leak future office1 targets if inputs, coefficient and estimator identity are genuinely frozen now. The proposal and gate were themselves selected after seeing development outcomes, so no confirmatory interpretation belongs to the development gate.

Chess is exposed by construction in this brief and by S145 (RESULT.md:74–76). Fresh sampling seeds cannot make its images unexposed. Never use its new scores to adjust the recipe and still call office1 a confirmation of the original frozen recipe.

The inspected generator reads context RGB and target poses, not target RGB; target RGB enters the scorer (gen_s144.py:262–276; score_s144.py:48–49). The CPU warp builder uses context RGB and target poses (warps_monitor_s144.py:71–81). This is evidence about those code paths, not proof of the entire remote execution's provenance. office1 being absent from project use remains an owner/local-ledger claim to reverify before future staging; absence from foundation-model pretraining is unverified.

### 4.2 Geometry failure is not confined to training

The GPU-invalid monitor c02028 is explicitly logged with kps="OK" despite Infinity reprojection and a NaN focal (WARP_LOG_3of5.jsonl:400); its identity is clips_s141.json:44667–44687. Finite RGB outputs or an OK string are not valid-geometry evidence.

The proposed development inputs are CPU warps. The CPU builder writes a different construction receipt and does not check the KPS objective before saving (warps_monitor_s144.py:67–84). This review did not establish its per-clip validity. Do not declare c02028 CPU-invalid merely because its GPU construction failed, or declare it valid merely because S144 produced scores.

**MEASURED (archived):** CPU-versus-GPU monitor warp agreement has median PSNR **30.632779 dB**, minimum **18.769218 dB**, and mean coverage-mask agreement **0.946608**, from work/S144_A_wgs/results/MONITOR_WARP_CPU_VS_GPU.json:1. These are approximate pipelines, not byte-identical training/evaluation evidence. A negative result is conditional on that deployment shift; a teacher-forced GPU-warp result cannot explain a CPU-warp rollout difference by itself.

Before new generation, establish validity from each CPU artifact's own source-only receipt. Apply the same fallback policy on development, chess if retained, and confirmation. Retain every planned evaluation window. If a B2 input changes to nearest-copy fallback, recompute that cell's B2, V, WGS-derived blend and any region definitions; archived scores for the old artifact cannot remain the matched comparators.

“True coverage” should be “the unmodified source-derived estimated coverage.” Its mask is computed from forward-warp support and nearest fill, then average-pooled (warps_s141.py:44–66,86–97; gen_s144.py:263–265). It is not ground-truth visibility or certified disocclusion.

Do not inherit S146's whole protocol by shorthand. Its Amendment 3 withdrew KPS-R and removed geometry-dependent arms; it is an operational retrieval assay, not certification of usable per-package geometry (work/S146_fresh12/PROTOCOL.md:64–83). Import only the named metadata, coordinate and staging rules, and define S147's own per-package warp validation.

There is also a concrete new-dataset porting hazard: the training and monitor warpers hard-code the 7-Scenes intrinsics through C.K7 (work/S141_finetune/warps_s141.py:29; work/S144_A_wgs/warps_monitor_s144.py:26), whereas generation reads camera-intrinsics.txt (gen_s144.py:255–257). office1 warping must use its staged, resized intrinsics consistently; copying these warpers unchanged would disagree with the generator's cameras.

### 4.3 A nearest-4 advantage is not automatically long-range memory

The draft changes from pose-NMS mixed/static training to nearest-4 confirmation. R271 itself calls for distinguishing policies and slot order (CODEX_R271_IDEATION_AFTER_S145.md:166,172–176,217). Freeze nearest-4 and its order independently of pending S146 outcomes; do not opportunistically promote a policy after those scores arrive.

Nearest-4 can select recent frames. A nearest-4−static gain is a context-package effect, not necessarily history use. The draft's difference-of-differences versus A_cont can also increase because static quality fell. Report the two absolute package scores, history fractions and static guardrail. A long-range memory claim additionally needs a prospective matched historical-content intervention with the same selected slots/cameras and demonstrable history exposure. The minimal revision below deliberately limits the claim to context-package benefit.

## 5. Missing fidelity checks, scoring hazards and budget

### 5.1 Necessary checks

- Establish full checkpoint identity, exact trainable names and optimizer membership, complete frozen-A tensor equality, step-zero equivalence for every arm, and final true-bypass equality for both F arms.
- Check a valid c and uc loss/backward, including correct target-only loss slices. Test invalid-input bypass before computing the branch. Check save/load and resume parity, prototype integrity and shared RNG digests.
- Pin source/weights, preprocessing, precision, Flash Attention/CUDA/PyTorch versions, sampler configuration and ordered input manifests. Adapter/source hash prefixes in prose are not enough.
- For replay, one archived output is a necessary smoke test, not whole-panel validation. Reused cells must have matching contexts, target IDs, seeds, conventions, warp hashes and scorer version.
- Preserve full-frame PSNR pooling over the four target images before log conversion, then seed/clip means; retain frame-mean SSIM (score_s144.py:33–40). Do not substitute mean per-frame PSNR.
- Validate shapes, finiteness and exact array lengths before uint8 conversion or zip operations (score_s144.py:23–26,35–43). Empty covered/hole regions may have undefined regional PSNR; record null with pixel count, not a fake score or automatic failure of the full-frame panel.
- Assert the complete expected set of unique (arm, package, clip, seed) IDs. S144's equal-count check operates only on observed windows and does not require the expected seed/ID set (analyze_s144.py:14–20); its dictionary insertion can overwrite duplicate keys (score_s144.py:68). Missing whole windows or equally incomplete seed panels must fail completeness.

### 5.2 What the receipts actually support

**DERIVED from archived S141 logs, Appendix A:**

| Historical run | Median seconds/update | Peak allocated GiB | Sum of logged intervals, hours |
|---|---:|---:|---:|
| A | 1.400270373 | 8.709976673 | 4.530769320 |
| B | 1.324506354 | 8.765493870 | 4.088272081 |

An illustrative two-A-plus-two-B estimate is **17.238082803 GPU-hours**. It is not an S147 measurement. Those intervals start after initial validation and include preceding periodic validation/checkpoint work, but omit startup and the final validation (train_s141.py:108–112,123–136). The default periodic interval is 500 steps, so the proposed 100-step pilot alone misses that work (same file:22,129–134). Measure a validation/checkpoint cycle separately or omit monitor validation prospectively when only the final checkpoint matters.

**DERIVED cell counts and ANALYTICAL timing projections**, using the archived chess-generation medians **38.43–41.14 seconds** from results/tacc/eval/{chess_A,chess_B}/RUNS*.jsonl:

| Draft stage | Ordinary sampled cells | Sampler-receipt hours at those medians |
|---|---:|---:|
| Development | 256 | 2.733–2.926 |
| Chess | 384 | 4.099–4.388 |
| Confirmation: five models, both packages | 1,280 | 13.664–14.628 |
| Confirmation plus one blend's WGS source on both packages, treating its cost as ordinary sampling for this illustration | 1,536 | 16.397–17.553 |

WGS has a different trajectory length; that last row is not a measured WGS forecast. Its point is the omitted source work. Prototype/permutation diagnostics add more cells. Moreover, generation receipt timing starts after context/warp loading and encoding, and excludes model initialization (gen_s144.py:260–278,292–294). Geometry preparation, VAE comparators, replays, saves and restarts need actual allocation accounting.

The draft's stage caps sum to **45 GPU-hours** against a total cap of **48**, leaving only **3** unspecified hours (DERIVED from PROTOCOL_DRAFT.md:72; Appendix A). Its mandatory chess sweep spends about four sampler-receipt hours on an already exposed panel and cannot alter GO. Remove that sweep from the minimal design. Historical B's deficit is useful context; closing that exact historical number is not an additional causal endpoint.

Use one training process per allocated RTX 3090, two waves, by default. Two processes are not intrinsically invalid for fixed-update quality comparisons, but adding per-process allocated-memory peaks does not establish total VRAM fit. Permit packing only after every arm fits including CUDA/reserved/workspace memory, aggregate throughput improves, and a declared single-versus-packed short replay matches. Freeze mapping before scores. Do not alter batch, precision or checkpointing by arm to fit. Count occupied physical GPU-hours once per device interval; report overlapping process-hours separately.

Equal attempts are equal exposure, not equal GPU compute. R271 asked for an additional timing-selected A_cont compute endpoint if throughput materially differs (CODEX_R271_IDEATION_AFTER_S145.md:149–160). For a minimal diagnostic, explicitly drop any equal-compute superiority claim. If such a claim is wanted, add that endpoint and its budget before training, without using quality to choose its step.

## 6. Verified prior-art boundary

This is a narrow positioning check, not an exhaustive novelty search. Search results were followed to the primary arXiv texts; the exact titles and relevant sections are:

- Jia Li et al. (2026), **I3DM: Implicit 3D-aware Memory Retrieval and Injection for Consistent Video Scene Generation**, [arXiv:2603.23413v2, §3.3 and §4.1](https://arxiv.org/html/2603.23413v2). It conditions generation with aligned memory latents and jointly trains NVS components and diffusion LoRA while freezing original diffusion weights. S147's distinction is a controlled freeze of already adapted A with only a small input convolution trained; aligned-memory conditioning itself is not new.
- Xuanchi Ren et al. (2025), **GEN3C: 3D-Informed World-Consistent Video Generation with Precise Camera Control**, [arXiv:2503.03751v1, §§4.2–4.4](https://arxiv.org/html/2503.03751v1). It encodes rendered 3D-cache views, uses masked latent conditioning and fine-tunes the generator. This is direct precedent for render-conditioned generation, though its fusion and training recipe differ from S147.
- Minjun Kang et al. (2026), **GeoNVS: Geometry Grounded Video Diffusion for Novel View Synthesis**, [arXiv:2603.14965v2, §§3.2–3.3](https://arxiv.org/html/2603.14965v2). It uses geometry-guided feature lifting, refinement and fusion. S147 uses an input-level warp branch and a different controlled training intervention; this does not establish superiority or novelty over feature-space adaptation.

These verified differences prevent a false claim of exact duplication. They equally prevent presenting any successful S147 warp-conditioning result alone as a novel method. No paper's reported performance is used to predict this experiment.

## 7. Corrected minimal specification — proposed binding replacement

The following text may be adopted verbatim. It is a proposed protocol, not authorization to execute during R273. All numerical rules in this section are ANALYTICAL design choices.

### A. Scope and frozen evidence

S147 is one four-arm training diagnostic of whether a small input branch adds useful instance-specific warp evidence while preserving S141 A. It is not a new-method validation or a long-range-memory claim. new_method_validated=false and novelty_authorization=NONE remain unchanged. Pending S146 outcomes do not change the chosen recipe, packages, thresholds or rooms.

Before any training, freeze full source, base/VAE/CLIP/CUT3R weight, source-A adapter, clip-manifest, latent, warp-construction, invalid-ID and prototype hashes. Verify remote artifacts against these hashes. Use only existing S141 training material. Record every later change as an amendment stating whether any S147 quality outputs had been observed.

### B. Arms, prototype and training

All arms initialize from exactly the same final S141 A tensors with fresh optimizer and scheduler state. F_geo and F_null freeze every base and A-LoRA tensor and train only the new WarpInConv weight and bias. J_geo trains A LoRA and the same branch. A_cont trains A LoRA only. The branch is zero-initialized, retains S141 B's context-bias behavior, and is appended to both conditional and unconditional conditioning. Optimizer parameter names must equal the arm's declared allowlist.

F_geo and J_geo receive real context-derived warp latent plus estimated coverage. F_null receives the same coverage and a fixed four-scalar prototype broadcast over the target latent grid. Compute the prototype once from all target-warp latent positions of valid training clips only, using float64 sums and a single float32 cast; store it explicitly in all required S147 checkpoint metadata. It must never depend on monitor or evaluation data. Context extras remain zero.

Training uses the unchanged eight-frame conditioning, four-target epsilon-MSE, bf16 autocast, non-reentrant checkpointing, AdamW at lr 1e-4, weight decay zero, gradient clipping 1.0, and CFG dropout probability 0.1. Warm-up spans 100 valid updates, then the learning rate is constant. Preserve rank/alpha and all sampler-independent model settings from the verified A source.

The common schedule has 10,000 attempted records: five permutations of the original 2,000 training clips, generated by an isolated seed-0 permutation stream. The fixed 46 invalid training clips consume their scheduled CFG, sigma and full-shaped noise draws but execute no model, optimizer or scheduler step. Every arm therefore has 9,770 valid updates. Unexpected nonfinite input/loss/gradient stops the experiment as invalid; do not add exclusions after training begins.

Use isolated shared training RNG streams, unaffected by initialization, validation, diagnostics or checkpoint serialization. Checkpoints include attempted/valid counts, permutation/cursor, all RNG states, complete adapters, optimizer/scheduler, prototype and provenance. A warm-start is never treated as resume. Select only the final scheduled checkpoint; monitor loss cannot select a checkpoint or stop a scientific arm for quality. These are equal-exposure arms; no equal-GPU-compute claim is made.

### C. Engineering gates

Before full training, verify: a finite nonzero branch gradient and parameter update on valid conditional and unconditional cases; exact unchanged base/A tensors in F arms; checkpointed-versus-ordinary loss and branch-gradient agreement at a frozen numerical tolerance; and interrupted-versus-uninterrupted replay across a scheduled invalid record and epoch transition. Freeze any numerical tolerance from engineering data before development outputs, never relax it after a failed check.

Step-zero F_geo, F_null, J_geo and A_cont must reproduce archived ordinary A under the same pinned runtime. After training, both F arms must retain exact A-LoRA tensors and reproduce A with a true branch bypass. True bypass skips the branch computation and its bias; multiplying a nonfinite branch output by zero is forbidden. Final J_geo bypass uses its changed joint backbone and is not called A. Resume/load checks reject wrong arm, rank, schema, keys, hashes, prototype or clocks.

Run the future timing/memory pilot with one process per GPU and include loading, a representative validation/checkpoint cycle if retained, and finalization in the projection. Packing is optional only after the declared parity/memory/throughput check; freeze it before quality scores. Failure of an engineering gate is INVALID_IMPLEMENTATION, not evidence against the hypothesis.

### D. Geometry policy and permitted data access

Freeze validity from each package's own source-only construction receipt: finite reprojection objective, finite positive scale/focals and finite required depth/latent arrays, with valid shapes and coverage in [0,1]. Record support and depth-pathology diagnostics; passing these necessary checks is not a claim of accurate geometry. Do not use target RGB/depth or target scores in validity decisions. Use original KPS; do not introduce KPS-R.

The GPU training-invalid list does not classify CPU evaluation warps. Verify every monitor CPU receipt before generation. Missing validity provenance blocks engineering completion. Any evaluation package failing the declared check stays in the panel: F_geo/F_null use true A bypass, J_geo uses its joint-backbone bypass, and A/A_cont remain their ordinary model. No gradient is requested through a frozen bypass.

For invalid packages, B2 becomes the selected context RGB closest to each target camera under the frozen pose-distance rule; ties follow the declared context order. The distance is the existing S141 geo function (work/S141_finetune/build_clips_s141.py:26–29): 0.1 times Euclidean camera-centre distance plus relative rotation angle in radians, with the same trace clamp. Coverage is zero. V is the same VAE round trip of that copy. The WGS source for BL_AC becomes ordinary frozen A on that invalid package, and BL_AC applies its unchanged coefficient to that source and the copy. Label this the operational fallback extension of the S144 estimator. Recompute all affected comparison cells; do not reuse archived scores of replaced warps. Report failure/fallback fractions and valid-only descriptive contrasts without dropping failed windows from the primary.

Generation reads permitted context RGB and cameras plus target cameras. Evaluation target RGB is opened only by the scorer after predictions/manifests are sealed. Use common reference coverage masks for within-package region contrasts; zero-support regional scores are null with pixel counts.

### E. Development outputs and gates

Use exactly the 32 S141/S144 monitor IDs and seeds 3,4. Generate ordinary-sampler F_geo, F_null, J_geo and A_cont. Additionally generate F_geo with the stored prototype and F_geo with the existing deterministic coverage-stratified permutation, preserving all other inputs and sampler noise. These are fixed-checkpoint diagnostics, named F_geo_proto and F_geo_perm, not additional training runs. Record permutation moved fractions.

Retain all provenance-matched A_none, B2 and V cells. Also score COPY on every package: for each target use the context RGB selected by the frozen nearest-pose rule in section D, with the same reference-grid transform. The mandatory existing blend is explicitly BL_AC = 0.60 A_C + 0.40 B2, with A_C the S144 strength-0.5 WGS C endpoint and the same float/blend/uint8 scoring path. Reuse only unchanged, verified cells. Report archived BL_FC descriptively as another globally fitted estimator; BL_AC is the globally selected mandatory blend, not a per-sequence oracle.

Add BL_A0 = alpha_plain A_none + (1-alpha_plain) B2 as a distinct comparator. Before any S147 training or candidate output, select its one global coefficient on the archived, validity-matched development panel from {0,0.05,...,1}, maximizing the same seed-then-clip mean PSNR; exact ties choose the smaller coefficient. Store the coefficient and input hashes before training and freeze them for confirmation. This is explicitly optimistic development fitting of a baseline, not a new candidate. It requires scoring, not another sampling run. Do not fit a new F_geo blend for this minimal experiment.

Score pooled four-target-frame PSNR per cell; average seeds within clip and clips within each sequence, then equally average the two sequence means. Retain S144 SSIM conversion and definition. Require exactly every expected unique cell with finite full-frame metrics. Report 10,000 paired clip-bootstrap replicates with RNG 0 descriptively, per-sequence effects, individual-seed means and full denominators; no population significance claim follows from the overlapping windows.

Define:
- PRIMARY_SCREEN_PASS iff F_geo−F_null mean PSNR is at least +0.20 dB, strictly positive in both sequences, and mean SSIM difference is at least −0.01.
- USEFUL_CONTENT_SCREEN_PASS iff PRIMARY_SCREEN_PASS, F_geo−A_none and F_geo−F_geo_proto each have mean PSNR at least +0.20 dB and strictly positive means in both sequences, SSIM is at least −0.01 for each, and F_geo−F_geo_perm has positive mean PSNR in both sequences. Permutation sensitivity alone does not certify correct geometry.
- PRACTICAL_PASS iff F_geo−X mean PSNR is at least +0.20 dB, neither sequence mean is negative, and mean SSIM is at least −0.01 for every X in {A_none, A_cont, COPY, B2, V, BL_A0, BL_AC}.
- GO iff all engineering/data/completeness gates, USEFUL_CONTENT_SCREEN_PASS and PRACTICAL_PASS pass.

F_geo−J_geo, J_geo−A_cont, F_null−A_cont, covered/hole results and memory/static training-clip categories are descriptive. They cannot rescue GO. F_geo−J_geo is the direct frozen-versus-joint comparison; no necessity claim follows from a tie, and lack of significance is not equivalence.

A failed development GO stops S147 after the complete development report. There is no mandatory new chess sweep. Chess remains historical exposed context and cannot rescue failure.

### F. Fresh confirmation and claim boundary

Only after GO, stage the entire designated office1 environment. Enumerate and freeze its four room identities from release metadata before RGB inspection; require both complete traversals in each room with the same stated pose checks. If the planned panel cannot be constructed, report CONFIRMATION_UNAVAILABLE; do not replace rooms after looking at geometry or scores.

Adopt the explicit S146 metadata/staging/coordinate rules, including resize/intrinsics mapping, H=sequence0, C=sequence1, the frozen window/bank formulas and bank-only convention checks, rather than its amended operational retrieval policy. Use eight windows per room and 32-frame banks. Use the staged office1 intrinsics consistently in projection and generation; never substitute the S141 warpers' hard-coded K7. No room, convention, window or ordering may be chosen from target scores.

Freeze nearest-4 as the primary package: select the four bank frames nearest to the last target camera under section D's distance, break distance ties by bank index, then present the selected set in bank order. Static is the declared four recent offsets. Do not change this choice in response to S146. Generate F_geo, F_null, J_geo, A_cont and A for both packages at seeds 42,7,1,2. On nearest-4 additionally generate F_geo_proto, F_geo_perm and the A_C source required for BL_AC. Score COPY, B2, V, BL_A0 and the unchanged BL_AC rule on nearest-4. Never refit either blend coefficient on office1.

The nearest-4 confirmation uses equal room weights, seed means within window and window means within room. PRIMARY requires F_geo−F_null ≥+0.20 dB overall, positive in every room and at least three of four seed panels, with SSIM ≥−0.01 overall. Require the same magnitude/room/seed rule for F_geo−A and F_geo−F_geo_proto, supportive positive room means for F_geo−F_geo_perm, and the practical +0.20 dB/SSIM guardrails against A, A_cont, COPY, B2, V, BL_A0 and BL_AC, with no negative room means. This is a finite-panel decision, not independent evidence from four environments.

Report nearest-4−static for F_geo and A_cont, absolute quality of both packages, and actual history fractions. A package-benefit label requires F_geo's gain ≥+0.20 dB, greater than A_cont's gain, and no static degradation beyond 0.20 dB PSNR or 0.01 SSIM versus A. It is not a long-range-memory claim; such a claim needs a separate matched historical-content protocol.

### G. Budget and outcome wording

Physical allocation cap: 48 RTX 3090 GPU-hours total, allocated prospectively as engineering/preparation at most 2, training at most 20, development at most 6, and conditional confirmation at most 20. Count startup, pilots, retained validation, encoding, saves, replays, geometry on GPU if any, comparator sources and retries. CPU preparation is separately logged. Before each stage, project its complete fixed cell list using measured end-to-end timing; do not launch a stage that cannot fit. These caps are ceilings, not runtime predictions.

The revised confirmation includes 1,280 ordinary main-arm cells, 256 nearest-4 prototype/permutation cells and 128 A_C WGS cells, plus VAE/geometry/replay work. If the measured projection exceeds its cap, stop as BUDGET_INFEASIBLE before fresh generation; do not remove hard cells, controls or seeds. No training retuning, extra layer, quality-selected checkpoint or second training seed is part of S147.

Use the following outcome language:
- Engineering/provenance/completeness failure or budget exhaustion: “S147 did not produce a valid complete test; no scientific negative is inferred.”
- PRIMARY failure: “The predeclared benefit of instance-specific warp-latent training over the prototype control was not demonstrated under this recipe and budget.” Do not say geometry is useless or the methods are equivalent.
- PRIMARY success but A/prototype diagnostic failure: “The content-bearing training recipe outperformed its trained null, but useful added content use by frozen A was not established.”
- USEFUL_CONTENT success but practical failure: “On the exposed development panel, the anchored branch added useful appearance-conditioned accuracy, but failed the practical advancement gate against the frozen comparator set.” Stop; no method-validation claim.
- Development GO followed by fresh failure: “The development-selected recipe did not replicate under the predeclared office1 gate.” No retuning or reinterpretation of development as confirmation.
- Complete fresh success: “One training run supports useful warp-conditioned refinement with a frozen adapted backbone on this project-fresh office1 panel, exceeding the predeclared comparators.” It remains one environment and one training seed, with pretraining exposure unverified.
- F_geo better than J_geo descriptively: “Anchoring was better than joint updating in this matched single-seed comparison.” Do not say co-adaptation generally causes failure.
- F_geo/J_geo tie or both succeed: “The experiment does not establish that anchoring is necessary.”
- A history/package effect without matched historical-content evidence: “Context-package benefit”; never “long-range memory validated.”

## 8. Delivery and remaining work

Only work/agents/CODEX_R273_S147_REJECTION.md is created by this review. No executable implementation changed; repository tests/linter and GPU fidelity tests were not run because this is a read-only audit plus one Markdown deliverable. CPU calculations inspect saved JSON/logs, not new image metrics or independently reproduced generations.

A later implementation session should create the dedicated S147 trainer/loader/scorer, pin the actual CPU validity receipts and full remote hashes, freeze the corrected protocol, and then perform its engineering pilot. None of those future actions or gates is claimed complete here. Keep both authorization flags unchanged.

## Appendix A — Exact CPU inspection command and complete output

Run from the repository root with python3; exit code 0. This reads archived JSON/JSONL, performs arithmetic and hashes files; it does not import model code or run training/inference. The duplicate score means use all archived cells; the manifest inspection confirms the expected panel size, and the paired analysis must additionally enforce exact cell identities as specified above.

```bash
python3 - <<'PY'
import collections, hashlib, json, math, statistics, subprocess
from pathlib import Path
P=Path('.')
def J(p): return json.loads((P/p).read_text())
def rows(pat): return [json.loads(s) for p in sorted(P.glob(pat)) for s in p.read_text().splitlines()]
print('HEAD',subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
for name in ['work/S147_anchor_a/PROTOCOL_DRAFT.md','work/agents/CODEX_R271_IDEATION_AFTER_S145.md','work/S141_finetune/train_s141.py','work/S141_finetune/s141_common.py','work/S141_finetune/clips_s141.json','work/S144_A_wgs/gen_s144.py','work/S144_A_wgs/score_s144.py','work/S144_A_wgs/analyze_s144.py','work/S144_A_wgs/build_plans_s144.py','data/S134_tacc/vmem_src/modeling/pipeline.py','work/S144_A_wgs/results/SCORES_dev.json','work/S144_A_wgs/results/DEV_GATE.json','work/S144_A_wgs/results/ALPHA.json']:
 print('SHA256',name,hashlib.sha256((P/name).read_bytes()).hexdigest())
cs=J('work/S141_finetune/clips_s141.json')['clips']; tr=[c for c in cs if c['split']=='train']; va=[c for c in cs if c['split']=='val']; ix={c['id']:c for c in cs}
print('CLIPS',len(tr),len(va),'monitor_groups',dict(collections.Counter(c['scene']+'/'+c['C'] for c in va)))
tref={r for c in tr for r in c['ctx']+c['tgt']}; vt=[r for c in va for r in c['tgt']]; vc={r for c in va for r in c['ctx']}
print('OVERLAP val_target_vs_train_any',len(set(vt)&tref),'val_context_vs_train_any',len(vc&tref),'val_target_slots',len(vt),'val_unique_targets',len(set(vt)),'max_target_repeat',max(collections.Counter(vt).values()))
wl=rows('work/S141_finetune/results/tacc/logs/WARP_LOG_*.jsonl')
bad={r['id'] for r in wl if any(not math.isfinite(k['median_reproj_px']) for k in r['kps'])}; bf={r['id'] for r in wl if any(not math.isfinite(f) for k in r['kps'] for f in k['focals'])}
print('WARP_LOG',len(wl),'unique',len({r['id'] for r in wl}),'bad',len(bad),'same_nonfinite_focals',bad==bf,'bad_splits',dict(collections.Counter(ix[c]['split'] for c in bad)))
print('INVALID_IDS',','.join(sorted(bad))); print('VALID_UPDATES_10000',5*sum(c['id'] not in bad for c in tr))
print('CPU_GPU_MONITOR',J('work/S144_A_wgs/results/MONITOR_WARP_CPU_VS_GPU.json'))
s=list(J('work/S144_A_wgs/results/SCORES_dev.json')['runs'].values()); arms=['A_none','B2','V','BL_FC','BL_AC']
print('DEV_CELLS',len(s),'unique_windows',len({r['window_id'] for r in s}),'seeds',sorted({r['seed'] for r in s}))
for a in arms:
 print('DEV',a,'PSNR',format(statistics.mean(r[a]['psnr_db'] for r in s),'.9f'),'SSIM',format(statistics.mean(r[a]['ssim'] for r in s),'.9f'))
for q in sorted({r['seq'] for r in s}):
 sr=[r for r in s if r['seq']==q]; print('DEV_SEQUENCE',q,'n',len(sr)//2,{a:round(statistics.mean(r[a]['psnr_db'] for r in sr),9) for a in arms})
print('ALPHA',J('work/S144_A_wgs/results/ALPHA.json')); dg=J('work/S144_A_wgs/results/DEV_GATE.json'); print('S144_GATE',dg['PERFORMANCE_GO'],dg['checks'])
bar=statistics.mean(r['BL_AC']['psnr_db'] for r in s)+.2; print('PRACTICAL_REQUIRED_PSNR',format(bar,'.9f'),'GAIN_VS_A',format(bar-statistics.mean(r['A_none']['psnr_db'] for r in s),'.9f'))
th=[]
for a in ['A','B']:
 tt=[r for r in rows('work/S141_finetune/results/tacc/runs/'+a+'/train_log.jsonl') if 'sec_per_step' in r]; h=sum(r['sec_per_step']*20 for r in tt)/3600; th.append(h)
 print('TRAIN',a,'records',len(tt),'last_step',tt[-1]['step'],'median_seconds',format(statistics.median(r['sec_per_step'] for r in tt),'.9f'),'max_allocated_GiB',format(max(r['max_mem_gb'] for r in tt),'.9f'),'recorded_interval_hours',format(h,'.9f'))
print('FOUR_RUN_INTERVAL_ESTIMATE',format(2*sum(th),'.9f'))
for a in ['chess_A','chess_B']:
 rr=rows('work/S141_finetune/results/tacc/eval/'+a+'/RUNS*.jsonl'); print('GEN',a,'n',len(rr),'median_seconds',statistics.median(r['seconds'] for r in rr))
for n,cells in [('draft_dev',4*32*2),('draft_chess',4*24*4),('draft_confirmation',5*4*8*2*4),('confirmation_plus_A_C',6*4*8*2*4)]:
 print('PLANNING',n,'cells',cells,'hours_at_38.43_to_41.14_seconds',round(cells*38.43/3600,6),round(cells*41.14/3600,6))
print('DRAFT_STAGE_CAP_SUM',20+4+5+16,'TOTAL_CAP',48)
PY
```

Complete stdout (no stderr):

```text
HEAD 565770bc99f9f6ebfe0a6b99099b6d15a29d2b7d
SHA256 work/S147_anchor_a/PROTOCOL_DRAFT.md 503cfb82d4777a80e07b1c0d3f136eee455f180550f8c669773b6943382d39f3
SHA256 work/agents/CODEX_R271_IDEATION_AFTER_S145.md 6026edf8bf29f17ca20e3984bb9543609750d9fe278c121f005eb5c861b97f34
SHA256 work/S141_finetune/train_s141.py 6ba0419e5ceb39406bbd1894ffae90398c27daedbc2eea56b18e537ba6187c0a
SHA256 work/S141_finetune/s141_common.py 459549706fb3a965fc4f7c5021f4d49cc626158e94a7c9cdc94cf8784cccb6cc
SHA256 work/S141_finetune/clips_s141.json c2fbdd49e87426d837aa5e90a8e694cddd9032864079cef53c29a66991740f36
SHA256 work/S144_A_wgs/gen_s144.py dfd8f253e4b965ffd5d3570144cf4c874e8191bdb5fa841bdad15b5301c39d43
SHA256 work/S144_A_wgs/score_s144.py a1cefd73571f8ce9ad34d5097d205a8ae5f8f376cefebc7ccdf0d57c34080085
SHA256 work/S144_A_wgs/analyze_s144.py 5ca643757399af1a3249192e18e9121a48b8f9c680980c8615c739f26312fdc0
SHA256 work/S144_A_wgs/build_plans_s144.py b4f55339f8094c247425d11ab656d785d7260a548d9f7a1a0355f1196a1347a4
SHA256 data/S134_tacc/vmem_src/modeling/pipeline.py 680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255
SHA256 work/S144_A_wgs/results/SCORES_dev.json a8a6f634166a7c68c89307141fc35ca752b04feaf523ae5081643ba4a732f963
SHA256 work/S144_A_wgs/results/DEV_GATE.json 677a559b6a6027cd41fd3ffbaab019b6feb7650e2184835735edeecafaeeee18
SHA256 work/S144_A_wgs/results/ALPHA.json 263a628fb0f125b07c3b69bbbb2e0cfcf3986d60839b6028fbeffd3978ca3c15
CLIPS 2000 32 monitor_groups {'office/seq-10': 16, 'redkitchen/seq-14': 16}
OVERLAP val_target_vs_train_any 0 val_context_vs_train_any 59 val_target_slots 128 val_unique_targets 105 max_target_repeat 4
WARP_LOG 2032 unique 2032 bad 47 same_nonfinite_focals True bad_splits {'train': 46, 'val': 1}
INVALID_IDS c00020,c00119,c00164,c00171,c00220,c00329,c00338,c00358,c00433,c00492,c00579,c00584,c00606,c00608,c00612,c00664,c00690,c00763,c00766,c00819,c00887,c00897,c00923,c00943,c01066,c01075,c01095,c01097,c01100,c01241,c01298,c01308,c01408,c01413,c01600,c01712,c01727,c01761,c01763,c01789,c01811,c01821,c01836,c01876,c01925,c01991,c02028
VALID_UPDATES_10000 9770
CPU_GPU_MONITOR {'n': 128, 'psnr_cpu_vs_gpu_median': 30.63277928059658, 'psnr_min': 18.769217598676914, 'valid_agreement_mean': 0.9466081784095293, 'coverage_cpu': 0.5108024455882886, 'coverage_gpu': 0.5107350996982905}
DEV_CELLS 64 unique_windows 32 seeds [3, 4]
DEV A_none PSNR 11.187286294 SSIM 0.560022306
DEV B2 PSNR 13.190760458 SSIM 0.573130307
DEV V PSNR 13.263184172 SSIM 0.586958300
DEV BL_FC PSNR 13.583318284 SSIM 0.590848704
DEV BL_AC PSNR 13.607907420 SSIM 0.592365212
DEV_SEQUENCE seq-10 n 16 {'A_none': 10.745977076, 'B2': 12.881879117, 'V': 12.939657482, 'BL_FC': 13.26509462, 'BL_AC': 13.261606681}
DEV_SEQUENCE seq-14 n 16 {'A_none': 11.628595512, 'B2': 13.499641798, 'V': 13.586710861, 'BL_FC': 13.901541947, 'BL_AC': 13.95420816}
ALPHA {'alpha': {'V': 0.75, 'FC': 0.55, 'AC': 0.6}, 'fitted_on': 'S144 development (32 monitor clips, seeds 3,4)'}
S144_GATE False {'means_ge_0.20': False, 'ssim_ge_-0.01': False, 'nonnegative_both_sequences': False}
PRACTICAL_REQUIRED_PSNR 13.807907420 GAIN_VS_A 2.620621127
TRAIN A records 500 last_step 10000 median_seconds 1.400270373 max_allocated_GiB 8.709976673 recorded_interval_hours 4.530769320
TRAIN B records 500 last_step 10000 median_seconds 1.324506354 max_allocated_GiB 8.765493870 recorded_interval_hours 4.088272081
FOUR_RUN_INTERVAL_ESTIMATE 17.238082803
GEN chess_A n 192 median_seconds 41.14
GEN chess_B n 96 median_seconds 38.43
PLANNING draft_dev cells 256 hours_at_38.43_to_41.14_seconds 2.7328 2.925511
PLANNING draft_chess cells 384 hours_at_38.43_to_41.14_seconds 4.0992 4.388267
PLANNING draft_confirmation cells 1280 hours_at_38.43_to_41.14_seconds 13.664 14.627556
PLANNING confirmation_plus_A_C cells 1536 hours_at_38.43_to_41.14_seconds 16.3968 17.553067
DRAFT_STAGE_CAP_SUM 45 TOTAL_CAP 48
```


## Appendix B — Concurrent-work boundary

A final source/input hash comparison found no change to the files pinned in Appendix A. Other processes created the untracked S147 implementation and plan files listed below while this review was in progress. They were neither modified nor reviewed here. The implementation findings are about the inspected S141/S144 reuse paths and the pinned draft, not a verdict on those concurrently created S147 files. This source check is a read-only provenance check, not an implementation test.

Exact command, repository root; exit code 0:

```bash
python3 - <<'PY'
import hashlib,json,subprocess
from pathlib import Path
pinned=json.loads("{\"work/S147_anchor_a/PROTOCOL_DRAFT.md\":\"503cfb82d4777a80e07b1c0d3f136eee455f180550f8c669773b6943382d39f3\",\"work/agents/CODEX_R271_IDEATION_AFTER_S145.md\":\"6026edf8bf29f17ca20e3984bb9543609750d9fe278c121f005eb5c861b97f34\",\"work/S141_finetune/train_s141.py\":\"6ba0419e5ceb39406bbd1894ffae90398c27daedbc2eea56b18e537ba6187c0a\",\"work/S141_finetune/s141_common.py\":\"459549706fb3a965fc4f7c5021f4d49cc626158e94a7c9cdc94cf8784cccb6cc\",\"work/S141_finetune/clips_s141.json\":\"c2fbdd49e87426d837aa5e90a8e694cddd9032864079cef53c29a66991740f36\",\"work/S144_A_wgs/gen_s144.py\":\"dfd8f253e4b965ffd5d3570144cf4c874e8191bdb5fa841bdad15b5301c39d43\",\"work/S144_A_wgs/score_s144.py\":\"a1cefd73571f8ce9ad34d5097d205a8ae5f8f376cefebc7ccdf0d57c34080085\",\"work/S144_A_wgs/analyze_s144.py\":\"5ca643757399af1a3249192e18e9121a48b8f9c680980c8615c739f26312fdc0\",\"work/S144_A_wgs/build_plans_s144.py\":\"b4f55339f8094c247425d11ab656d785d7260a548d9f7a1a0355f1196a1347a4\",\"data/S134_tacc/vmem_src/modeling/pipeline.py\":\"680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255\",\"work/S144_A_wgs/results/SCORES_dev.json\":\"a8a6f634166a7c68c89307141fc35ca752b04feaf523ae5081643ba4a732f963\",\"work/S144_A_wgs/results/DEV_GATE.json\":\"677a559b6a6027cd41fd3ffbaab019b6feb7650e2184835735edeecafaeeee18\",\"work/S144_A_wgs/results/ALPHA.json\":\"263a628fb0f125b07c3b69bbbb2e0cfcf3986d60839b6028fbeffd3978ca3c15\"}")
changed=[p for p,h in pinned.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
print('reviewed_source_or_input_hash_changes',changed)
print('git_status')
print(subprocess.check_output(['git','status','--short'],text=True),end='')
PY
```

Complete stdout (no stderr):

```text
reviewed_source_or_input_hash_changes []
git_status
?? work/S147_anchor_a/INVALID_GEOMETRY.json
?? work/S147_anchor_a/analyze_s147.py
?? work/S147_anchor_a/gen_s147.py
?? work/S147_anchor_a/make_inputs_s147.py
?? work/S147_anchor_a/plan_chess_s147.json
?? work/S147_anchor_a/plan_dev_s147.json
?? work/S147_anchor_a/plan_replay_s147.json
?? work/S147_anchor_a/plan_score_chess_s147.json
?? work/S147_anchor_a/s141_common.py
?? work/S147_anchor_a/s147_chain.sh
?? work/S147_anchor_a/score_s144_functions.py
?? work/S147_anchor_a/score_s147.py
?? work/S147_anchor_a/train_s147.py
?? work/agents/CODEX_R273_S147_REJECTION.md
?? work/agents/prompts/R273_FULL.md
```
