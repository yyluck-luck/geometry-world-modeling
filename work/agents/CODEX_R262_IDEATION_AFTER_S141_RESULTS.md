# R262 — Ideation after the actual S141 results

Workspace: local Mac checkout. Review date: 2026-10-10. Repository snapshot and exact CPU command outputs are recorded in Appendix A.

**Run E1 first: cross the successful A adapter with S140 warp guidance, and test whether releasing only the final warp overwrite permits a useful correction.** Include a VAE round trip and fixed pixel compositing. Then, if the development gate passes, train **one final-step correction on the actual frozen A+WGS states** (E3). Use E2 as a short, bounded diagnosis of B; do not start another full B training run merely because its SSIM is high.

This is a new experimental recommendation after observing S141, not a declaration of a new method. The strongest new question is: **does the adapted denoiser add useful correction to a geometric prediction when trained and evaluated on exactly the state where that correction must act?** Generic warp conditioning, regional release, residual fusion, condition-preference training, and sampled-state correction all have close prior art. Their names cannot carry a novelty claim.

The three experiments below use existing project assets and fit individual one-to-two-day implementation/run windows on the stipulated two RTX 3090s, subject to a short timing gate. Their initial results would be exploratory because the available evaluation panels are exposed. No GPU, training, model inference, weight/dataset download, SSH, Slurm submission, or external contact occurred in this review. Only this memo is authored. No protocol or ledger is changed; **new_method_validated=false; novelty_authorization=NONE**.

Evidence labels throughout: **MEASURED (archived)** means an existing recorded experiment, not a new reproduction; **DERIVED** means CPU arithmetic or inventory recorded in Appendix A; **ANALYTICAL** means a deduction, proposed threshold, design, or budget; **UNVERIFIED** means a hypothesis or unavailable evidence. All future constants and resource estimates are ANALYTICAL.

Path abbreviations in file:line citations: **S141/** = work/S141_finetune/; **S140/** = work/S140_warp_guided/; **V/** = data/S134_tacc/vmem_src/. Other paths are repository-relative.

## 1. What the completed results actually establish

### 1.1 Verified starting facts and corrections

The brief's analysis path is relative to the stage: the existing file is [S141/results/S141_ANALYSIS.json](../S141_finetune/results/S141_ANALYSIS.json), not root-level results/S141_ANALYSIS.json. CURRENT_STATUS.md has an older S133–S140 heading but includes completed S141 and ongoing S143 at lines 60–74. The opening operating instructions' “S141 running” sentence is superseded by the completed local records.

| Finding | Evidence and interpretation |
|---|---|
| **MEASURED (archived):** A_mem − base_mem **+0.330456 dB**, CI **[+0.078217,+0.584857]**; A_static − base_static **+0.447869 dB**. | S141/results/S141_ANALYSIS.json:26–49,76–99; [output](../S141_finetune/results/S141_ANALYSIS.json). Appendix A2 independently recomputes the primary from per-run score records. This supports useful adaptation under this recipe. It does not isolate training-domain mismatch from other effects of fine-tuning. |
| **MEASURED (archived):** A_static − base_static **+1.162 dB** on RGB-D Scenes v2. | S141/results/S141_ANALYSIS.json:546–563; [output](../S141_finetune/results/S141_ANALYSIS.json). Transfer to another dataset, but on exposed rooms. |
| **MEASURED (archived):** A_mem − A_static **−0.331743 dB**, CI **[−0.669355,+0.005715]**. | S141/results/S141_ANALYSIS.json:51–74; [output](../S141_finetune/results/S141_ANALYSIS.json). Negative mean, registered INCONCLUSIVE. Do not call statistically established PSNR worsening or equivalence. **DERIVED:** adaptation changes the memory-minus-static advantage by **−0.117413 dB**; Appendix A1. |
| **MEASURED (archived):** B_mem − warp **−3.557738 dB**, CI **[−3.912510,−3.201337]**. | S141/results/S141_ANALYSIS.json:101–124; [output](../S141_finetune/results/S141_ANALYSIS.json). Appendix A2 recomputes it. This rejects the tested B recipe as a PSNR improvement over its input warp. It does not prove the branch ignores the warp. |
| **Correction:** B_mem is not the highest-SSIM arm once exploratory B_static is included. **MEASURED (archived):** B_static **0.524761**, B_mem **0.505080**, A_static **0.493731**. | S141/results/S141_ANALYSIS.json:13–21; [output](../S141_finetune/results/S141_ANALYSIS.json). The brief and RESULT.md's broad “highest” wording omit B_static. B_mem leads the original main chess arms, not all evaluated chess arms. |
| **MEASURED (archived):** B_static − base_static on RGB-D is **−2.617 dB** and **−0.057 SSIM**. | S141/RESULT.md:45–50; S141/results/S141_ANALYSIS.json:546–642; [output](../S141_finetune/results/S141_ANALYSIS.json). High chess SSIM is not a general B quality improvement. |
| **MEASURED (archived):** S140 WGS − warp **+0.020 dB**, with covered/uncovered differences **+0.244/−0.241 dB**, on the original mixed-hardware panel. | S140/RESULT.md:20–29; [confirmation output](../S140_warp_guided/results/CONFIRM_ANALYSIS.json). These regions are defined by estimated warp coverage, not certified visibility/disocclusion. |
| **Crucial implementation correction:** B did **not** start from the completed A adapter. | S141/train_s141.py:42–48 creates fresh adapters on the base; :89–94 only resumes the same output directory. B's launcher uses its own run directory at S141/s141_chainB.sh:11. “B = A + branch” describes architecture, not sequential adaptation from successful A. |
| **Recorded execution, not verified live remote state:** final adapter checks, training logs and generation receipts are present, but local prediction arrays and final adapter tensors are absent under the inspected S141 results directory. | S141/RESULT.md:7–21; [adapter A receipt](../S141_finetune/results/tacc/eval/ADAPTER_CHECK_A.txt), [adapter B receipt](../S141_finetune/results/tacc/eval/ADAPTER_CHECK_B.txt); Appendix A1 inventory. Remote availability, GPU occupancy and free storage remain UNVERIFIED here. |

S141's one training seed per recipe, pose-only training contexts versus mem_vmem evaluation contexts, and GPU-training/CPU-evaluation warps limit attribution (S141/RESULT.md:70–73; S141/PROTOCOL.md:90–99). The existing GPU/CPU warp comparison claim is in S141/PROTOCOL.md:29–31 and comparison code exists at S141/warpcheck_compare.py:6–12; no retained raw comparison output was located in the focused inspection. Do not promote that protocol statement into a new verification.

### 1.2 A useful negative derived from the region scores

A better generator is not automatically a better hole filler. Appendix A1 combines the stored covered/hole MSEs using each run's hole fraction, then averages paired dB differences over seeds within windows. It does **not** add region PSNRs, synthesize images, or establish SSIM for the composite.

**DERIVED, exposed chess, RTX 3090 seeds 3–6:**

| Predictor used for the generated region | Generated covered / warp holes, minus warp | Warp covered / generated holes, minus warp |
|---|---:|---:|
| A_mem | **−2.025684 dB** | **−1.389320 dB** |
| B_mem | **−2.396404 dB** | **−1.838282 dB** |
| Frozen S140 WGS | **+0.122799 dB** | **−0.127439 dB** |

Sources: [A scores](../S141_finetune/results/tacc/eval/SCORES_chess_A.json), [B scores](../S141_finetune/results/tacc/eval/SCORES_chess_B.json), [WGS scores](../S140_warp_guided/results/confirm_tacc/S140_SCORES_confirm_tacc.json); complete arithmetic/output in Appendix A1. These are ideal hard RGB pastes under the stored masks, with no seam blending.

**Reject the specific “warp for covered pixels, ordinary A for holes” shortcut.** It is already contradicted on this panel. Continuous blends, learned corrections and A+WGS remain untested; the table is not a bound on them. R258's favorable reverse paste remains a mandatory cheap baseline, not a novel method.

### 1.3 The final WGS overwrite changes the interpretation of “polish”

S140 sets m = 1[cov >= 0.5], uses the default schedule ending at zero, and overwrites target latent cells after every sampler step:

    x_next = m * (z_w + sigma_next * noise) + (1-m) * x_next.

At the final step, **covered latent cells equal z_w exactly in the algebra**, regardless of whether the denoiser is base or A. Evidence: S140/gen_s140.py:155,164,174–179; V/modeling/sampling.py:126–135.

This is **ANALYTICAL covered-latent invariance**, not covered-pixel invariance. Decoding acts on the whole mixed latent (S140/gen_s140.py:179; V/modeling/modules/autoencoder.py:37–48). Latent coverage is pooled from a pixel mask (S140/gen_s140.py:202–206). No finite “unaffected pixel interior” is assumed.

Therefore:

- Compare against **D(E(warp))**, the same frozen VAE's reconstruction of the complete filled warp.
- Compare fixed RGB pastes using the same original pixel masks.
- Measure whether dropping only the final overwrite exposes a useful A prediction.
- Do not infer learned covered-region refinement from the covered PSNR gain alone.

This is the reason E1 precedes another training run.

### 1.4 “Flat validation loss” hides a scale-dependent signal

The recorded monitor loss is conditional epsilon-MSE on six noise indices, not sampled endpoint error (S141/train_s141.py:75–85). The implemented clean prediction is x − sigma * epsilon_pred, with the prescribed preconditioning (V/modeling/sampling.py:79–87,174–185). For the teacher-forced target states, clean-latent MSE is therefore sigma² times epsilon-MSE.

**DERIVED from the final validation logs, Appendix A2:** at index 950, A/B epsilon-MSE is **0.000176548/0.000460690**, corresponding to clean-latent MSE **0.715029/1.865816**; at index 200 B is slightly better (**0.154544 versus A 0.172915**). Sources: [A log](../S141_finetune/results/tacc/runs/A/train_log.jsonl), [B log](../S141_finetune/results/tacc/runs/B/train_log.jsonl).

This is a reexpression of existing teacher-forced measurements, using the source schedule in CPU float arithmetic. It is not a rollout diagnosis or evidence that high-noise error causes B's final failure. It makes per-sigma branch diagnostics preferable to another undifferentiated mean-loss plot.

## 2. What is inherited, and what is new in this round

- **R255** offered outcome-dependent warp sensitivity, warp-as-context training, and output fusion. Its A-improves/B-loses cell favored fusion (work/agents/CODEX_R255_IDEATION_AFTER_S141.md:37–44). The subsequently frozen **S142** branch table instead says write up when B WORSENS (work/S142_followup/PROTOCOL.md:9–17). R262 is a separately requested exploratory proposal; it does not rewrite or “pass” S142.
- **R257** proposed source-space correction inside sampling, attention-address changes, and reliability-dependent release (work/agents/CODEX_R257_IDEATION_MECHANISMS.md:30–51,93–140,180–211). Repeating those as newly invented would be wrong.
- **R258** proposed source-fitted frequency residuals, bank-specific LoRA, useful-memory margins, small residual restoration and VAE calibration (work/agents/CODEX_R258_IDEATION_FROM_FINDINGS.md:56–73). Its ideas remain candidates; actual A results now make their A-based versions concrete.
- **R259** proposed context ranking and conditioning-path interventions (work/agents/CODEX_R259_IDEATION_EVALUATION.md:40–62). **S143 already implements the ranking experiment**, and its fresh-seed extension is explicitly only seed-level replication (work/S143_context_ranking/PROTOCOL.md:13–29,60–74). Do not duplicate it or take its reported running state as a result.

**New emphasis after actual S141:** preserve the successful A state; separate B's branch effects from independently changed LoRA; evaluate A and the final sampling overwrite jointly; and train one terminal correction on an unchanged, fully specified prefix distribution. The last comparison is more specific than ordinary residual restoration or a generic short-unroll suggestion.

## 3. Divergence: sixteen distinct ideas

All rows are proposals, with effectiveness UNVERIFIED. “New here” means a new experiment or distinction relative to the earlier main shortlist, not verified literature novelty. The five starred families receive focused prior-art checks next.

| ID | Idea and concrete prediction | Cheapest falsifier / disposition |
|---|---|---|
| **1 ★** | **A × WGS × terminal release.** A may supply useful corrections that the original final overwrite erases. Cross backbone with final-clamp removal while holding the prefix/noise fixed. | VAE round trip, frozen-backbone release and fixed compositing explain the entire improvement. **E1, first.** |
| **2** | **Covered-only A+WGS polish.** Retain A+WGS's covered RGB and the warp's nearest-filled holes, reversing the usual inpainting assignment. | The simple frozen-WGS paste or VAE reconstruction matches it. A cheap E1 control; ordinary A holes are already rejected by §1.2. |
| **3 ★** | **A-anchored geometry branch.** Start from completed A, freeze its LoRA, then learn a zero-initialized, target-only warp branch. This tests an incremental improvement that independent B never tested. | Correct warp fails to beat branch-off and equally budgeted A continuation. **Diagnose with E2 first; do not authorize another full training run by default.** |
| **4** | **B branch interference.** Its learned bias may perturb clean source slots; its warp-dependent contribution may harm high-noise denoising. | Target-only gating, branch-off and bias-only controls show no material quality difference. E2 directly tests these possibilities. |
| **5 ★** | **Fixed-prefix endpoint repair.** Train the final denoising operation on actual frozen A+WGS states, keeping every preceding operation unchanged. | Same-noise-level Gaussian training or a small direct residual predictor matches it. **E3, preferred new training experiment.** |
| **6** | **Deployment-weighted denoising loss.** Train with the fixed sampler's sigma occupancy or endpoint-error weighting rather than a uniform discrete epsilon objective. | Equal-budget ordinary continuation matches final generation. Use as an objective-control principle in E3, not a simultaneous broad schedule sweep. |
| **7 ★** | **Natural paired-context benefit training.** For the same training target, compare recent and retrieved packages; improve the better-supported prediction without rewarding destruction of the other. | Equal-compute ordinary adaptation or CPO-style condition preference matches it. Promising data-construction question; crowded objective family. |
| **8** | **Match training retrieval to deployment.** Build training packages with the evaluation selector, rather than pose-only NMS, at fixed images/steps. | Matching packages changes no generated benefit. A documented conditioning-distribution hypothesis, but recomputing retrieval/warps increases preparation cost. |
| **9 ★** | **Source-fitted signed residual fusion.** Predict withheld bank views with A+WGS, fit which generated-minus-warp frequency corrections help, then apply that rule to targets. | A global scalar/frequency blend or smoothing matches per-bank fitting. R258 continuation; practical alternative if E3's development gate fails. |
| **10** | **Source-fitted photometric correction.** Estimate color/brightness adjustment from held-out source predictions, then test whether it explains A/B's metric gap. | Oracle target-fitted correction is the only version that helps, or a global training-set correction matches it. Diagnostic only; never fit to chess targets at inference. |
| **11** | **Preservation-constrained updates.** Restrict adaptation so predictions of permissible source views retain fidelity while target errors decrease. | Ordinary weight/teacher regularization matches a structured constraint. New parameter-space test, but a higher engineering risk than E3. |
| **12** | **Source-resolved robust observation correction.** Keep conflicting source projections separate and correct a clean prediction inside denoising. | Equal-cost final-only correction or deterministic robust rendering matches it. R257's useful mechanism test, deferred for geometry-metadata cost. |
| **13** | **Memory in temporary weights.** Replay allowed history into A with runtime context fixed. | Equal-step generic scene adaptation matches targeted replay. R258 continuation with direct prior-art collision; not the strongest next novelty bet. |
| **14** | **Explicit textured scene memory.** Fit a small persistent source-only appearance representation, render it, and require any diffusion suffix to beat that render. | Ordinary multiview rendering accounts for all gains. A different memory substrate; full implementation exceeds this short shortlist. |
| **15** | **Active evidence acquisition.** Under a fixed reveal budget, choose which next camera observation to acquire based on expected consumer benefit, not only coverage. | A pose/coverage acquisition policy matches it. A genuinely different task direction here, but no current acquisition benchmark; defer beyond the one-to-two-day trials. |
| **16** | **Separate observed memory from generated hypotheses.** During a rollout, promote generated content only after later real observations corroborate it. | Immutable observed-only memory or ordinary delayed writes matches it. Different write policy, but current short-clip evidence cannot validate a long-rollout claim. |

The immediate mechanisms are anchored in the code/result evidence of §1. In particular, sigma sampling is uniform at S141/train_s141.py:118–119; static/memory packages are drawn separately at S141/build_clips_s141.py:47–67; training/evaluation selector mismatch is disclosed at S141/PROTOCOL.md:94. The larger directions deliberately change the problem or representation and are not advertised as ready assets.

## 4. Prior-art check of the five most promising families

The titles, arXiv IDs and cited method sections below were checked against live primary text. This is a focused adversarial search, not an exhaustive novelty certificate. Distinctions are hypotheses about what an experiment could isolate.

### P1. Adapted backbone plus warp guidance and terminal release — retain for E1, reject generic novelty

**arXiv:2201.09865, “RePaint: Inpainting using Denoising Diffusion Probabilistic Models,” §§4.1–4.2, Algorithm 1** already injects noised known-region observations during denoising and uses resampling. **arXiv:2306.00950, “Differential Diffusion: Giving Each Pixel Its Strength,” §3.3, Algorithm 1** already uses spatial schedules for releasing locations from injected input. [RePaint](https://arxiv.org/html/2201.09865v2#S4), [Differential Diffusion](https://arxiv.org/html/2306.00950v2#S3.SS3).

Adding an adapted VMem backbone or a confidence mask does not invent either primitive. S140's implementation is a RePaint-style latent replacement adaptation; its loop does not implement every feature of the original paper (S140/gen_s140.py:164–179). The useful question here is the **interaction of A with the final overwrite**, with VAE and compositing controls. A positive answer would support this deployment recipe, not a new inpainting algorithm.

### P2. Protect A while adding warp conditioning — retain diagnosis, reject architectural novelty

**arXiv:2302.05543, “Adding Conditional Control to Text-to-Image Diffusion Models,” §§3.1–3.3** establishes freezing a capable model and connecting trainable spatial conditioning through zero-initialized convolutions. **arXiv:2406.18524, “MultiDiff: Consistent Novel View Synthesis from a Single Image,” §3** conditions diffusion on warped reference views and uses structured geometric noise. **arXiv:2603.14965, “GeoNVS: Geometry Grounded Video Diffusion for Novel View Synthesis,” §§3.2–3.3, Eqs. 8–9** includes geometry-derived feature transport and gated residual injection. [ControlNet](https://arxiv.org/html/2302.05543v3#S3), [MultiDiff](https://arxiv.org/html/2406.18524v1#S3), [GeoNVS](https://arxiv.org/html/2603.14965v1#S3).

The local distinction is sequencing and attribution: S141 did not test “successful trained A plus a branch.” B is also only an input convolution plus LoRA, not an implementation of full ControlNet (S141/s141_common.py:97–118). Freezing A guarantees equality only at zero branch initialization, not non-degradation after training. E2 first asks whether a cheap branch intervention explains any failure.

### P3. Source-calibrated multiscale residuals — keep as a fallback, no demonstrated novelty

**arXiv:2108.02938, “ILVR: Conditioning Method for Denoising Diffusion Probabilistic Models,” §3.1, Eq. 8** already separates reference low frequencies from generated content. GeoNVS, **arXiv:2603.14965, exact title above, §3.2**, already learns spatial residual fusion. **arXiv:2405.15364, “NVS-Solver: Video Diffusion Model as Zero-Shot Novel View Synthesizer,” §§4.1–4.3** combines warped-view information and video diffusion with changing guidance. [ILVR](https://arxiv.org/html/2108.02938v1#S3.SS1), [GeoNVS](https://arxiv.org/html/2603.14965v1#S3.SS2), [NVS-Solver](https://arxiv.org/html/2405.15364v2#S4).

The remaining distinction is using **permissible source-bank holdouts to estimate the signed benefit of a correction**, rather than assuming generated high frequencies are correct. It must beat a globally fitted estimator of equal expressivity. High SSIM alone does not justify this decomposition: the existing exploratory output diagnostic also records lower B high-frequency energy and lower low-pass PSNR than A (S141/results/tacc/eval/OUTPUT_DIAGNOSTICS.json:12–24). Its scorer averages frame PSNRs, so those diagnostic numbers must not replace the registered metric (S141/diag_outputs_s141.py:37–45).

### P4. Correct-versus-wrong memory objectives — direct collision; retain only a narrower data question

**arXiv:2511.04753, “CPO: Condition Preference Optimization for Controllable Image Generation,” §3.2, Eqs. 6–11** fixes the image/noisy state while comparing better and worse aligned conditions. **arXiv:2404.03653, “CoMat: Aligning Text-to-Image Diffusion Model with Image-to-Text Concept Matching,” §§4.1–4.2** addresses condition ignorance and fidelity preservation. **arXiv:2606.31734, “MemLearner: Learning to Query Context memory for Video World Models,” §§3.2,5.4, Appendix C.2** learns context querying through the generation backbone. The arXiv metadata spells “memory” lowercase; the HTML title capitalizes it. [CPO](https://arxiv.org/html/2511.04753v1#S3.SS2), [CoMat](https://arxiv.org/html/2404.03653v2#S4), [MemLearner](https://arxiv.org/html/2606.31734v1).

A “correct memory beats corrupted memory” loss is not a new objective. A potentially useful narrower comparison is **natural, pose/support-matched context alternatives versus synthetic corruption**, with actual training-target benefit deciding preference. Require improved correct-input outputs, not merely a larger gap created by damaging the losing condition. It is less direct than E3 under this deadline.

### P5. Fixed-prefix endpoint repair — strongest new local training comparison, close conceptual precedent

**arXiv:2604.12617, “SOAR: Self-Correction for Optimal Alignment and Refinement in Diffusion Models,” §§2.3.2–2.3.3** constructs model-induced states with a stop-gradient rollout and supervises correction toward a real clean endpoint. **arXiv:2301.11706, “Input Perturbation Reduces Exposure Bias in Diffusion Models,” §5.1** perturbs training inputs to address inference errors. **arXiv:2307.12348, “ResShift: Efficient Diffusion Model for Image Super-resolution by Residual Shifting,” §2.1** uses restoration-oriented states and clean-target prediction. [SOAR](https://arxiv.org/html/2604.12617v1#S2.SS3), [Input Perturbation](https://arxiv.org/html/2301.11706v3#S5.SS1), [ResShift](https://arxiv.org/html/2307.12348v1#S2.SS1).

Thus neither “train on generated states” nor “predict the clean residual” is new. The remaining experiment is particularly controlled: **an unchanged geometry-guided prefix, one learned terminal operation, and an identical-objective Gaussian-state control**. Unlike changing a multistep tail, this keeps the terminal input distribution independent of the newly learned parameters. It is fixed-prefix supervised repair, not online/on-policy adaptation or a new diffusion process.

An additional collision demotes idea 13: **arXiv:2605.18813, “Composition of Memory Experts for Diffusion World Models,” §§3.2–3.3 and Appendix B** explicitly uses weight adaptation for memory and composes multiple memory experts. [Primary text](https://arxiv.org/html/2605.18813v1#S3). Temporary bank LoRA is therefore especially weak as an unqualified novelty claim.

**Prior-art verdict:** none of the five currently clears a method-novelty gate. P1 and P5 have the cleanest decisive tests; P2 needs a bounded diagnosis; P3 is an established-family fallback; P4 needs more than a renamed contrastive loss.

## 5. Shared execution and decision contract for the retained experiments

These are **proposed** contracts, not executed protocols. A later implementation session should freeze one dated stage protocol before each experiment, preserve the original S141/S142 records, and use only the allocated GPUs after existing S143 work releases capacity.

**Inputs and leakage.** Use the existing training clips/warps and final A/B identities; current chess memory-context plans and RGB-D static plans; paired seeds 3,4,5,6 on RTX 3090. Reuse results only after source/config/adapter/input/seed/hardware and output-receipt matches. Evaluation target RGB is scorer-only; no target depth enters prediction. Source-based calibration may use allowed source RGB, but a held-out source must be removed from its reconstruction inputs. Training targets may supervise training, never evaluation. All arm-specific coverage diagnostics use the original input-derived B2 mask, not an altered output/error mask.

**Development.** Use the existing monitor sequences for engineering, baseline fitting and an explicit go/no-go gate. They are exposed development data. No chess-specific learning rate, release step, mask threshold or checkpoint choice. Fit any scalar blend on development only; freeze its coefficient before case-study scoring. Use final fixed-budget checkpoints, not the best chess checkpoint.

**Inference/scoring fidelity.** A-disabled and intervention-disabled paths must reproduce the corresponding same-backend references. Preserve conditional/unconditional ordering, whole-frame states, sampler random draws and the sigma_hat perturbation. The actual Euler implementation draws noise even with nominal gamma zero and uses sigma_hat = sigma + 1e-6 (V/modeling/sampling.py:393–402). This detail matters for shared-prefix caches. Require complete finite output cells, correct frame order and matching receipts; missing cells are an invalid assay, not a negative scientific result.

**Decision thresholds, ANALYTICAL.** Unless overridden below, a retained useful effect requires paired mean PSNR gain **at least +0.20 dB**, lower descriptive 95% window-bootstrap bound above zero, and nonnegative means in at least two of the three chess trajectory pairs. Report every pair separately. Window intervals do not represent independent scene-level confidence. Require mean SSIM loss no worse than **−0.01** versus the relevant practical comparator; report its interval and any trade-off. Report full-frame, covered and uncovered scores, plus failures. No frame-metric result is called “better video.”

For practical value, require the candidate to beat **each** specified simple control, not an oracle that selects different controls per test window. If a development-selected single strongest control is used as the named primary comparator, freeze that identity; retain all individual comparisons. Do not treat “not significantly worse” as equivalence.

**Compute basis, DERIVED/ANALYTICAL.** Appendix A1 finds a median **40.94 s** across the retained S141 generation receipts and training medians **1.400270 s/step for A**, **1.324506 for B**. These are archived rates, not live capacity or timings for new code. Use 41 s per full trajectory as a conservative planning unit; time new paths first. WGS is shorter but its speedup is not assumed. GPU-hours sum occupancy across cards; two cards do not halve preparation or I/O. If a small pilot predicts the cap cannot be met, stop or report the incomplete experiment without dropping unfavorable arms.

## 6. E1 — Does A make a released WGS endpoint useful? Run this first

**Hypothesis, UNVERIFIED.** A improves the denoiser's terminal correction, but the original final overwrite prevents some of that correction from reaching covered latent cells. A simple A+WGS combination may also improve holes. The factorial separates those explanations.

### Minimal implementation and arms

Proposed new files under work/R262_E1_A_wgs/: PROTOCOL.md, gen_factorial.py, score_controls.py, analyze.py. These paths are plans, not files created by this review.

Combine the verified A-loading logic (S141/gen_s141.py:110–125) with S140's sampling function (S140/gen_s140.py:139–180). Keep W2 strength 0.5, all initial states, masks and random draws unchanged. In the release variant, consume the normal final replacement RNG draw but **skip only the final assignment**. Keep every earlier overwrite, including nearest-filled hole initialization. This avoids changing hole initialization and release simultaneously.

| Arm | Backbone | Terminal behavior |
|---|---|---|
| F_C | Frozen base | Original W2 clamp |
| F_R | Frozen base | Skip terminal overwrite only |
| A_C | Completed A | Original W2 clamp |
| A_R | Completed A | Skip terminal overwrite only |

The same-backbone C/R pair shares the entire prefix. Do not claim that base/A prefixes are equal; their denoisers differ.

**Strongest trivial controls:** raw filled B2; VAE round trip D(E(B2)); fixed RGB paste of F_C on covered pixels/B2 in holes; the analogous A_C paste; and a development-fitted global convex blend of A_C and B2. Include ordinary A as a context-only reference, but it is not the strongest comparator. Fit the blend on the fixed grid alpha = 0,0.05,…,1 using development mean window PSNR, one alpha for all queries. Decode and score these controls with the same conversion and masks.

### Primary, interpretation, stop rule

**Primary mechanism contrast:**

    I = (PSNR(A_R) - PSNR(A_C)) - (PSNR(F_R) - PSNR(F_C)).

Require the shared +0.20 dB/positive-bound rule for I. This interaction cannot by itself establish quality: **A_R must also beat A_C and every named simple control by the practical rule.** A larger interaction caused by making F_R bad does not pass.

Report A_C − F_C separately. If A_C wins but the interaction fails, retain the simpler A+WGS composition as a local recipe result; reject the special release explanation. If VAE reconstruction or paste explains the apparent covered benefit, explicitly withdraw the denoiser-polish attribution. Do not infer memory usefulness without a separate matched static-context comparison.

**Kill criterion:** zero-init/replay failure; invalid shared prefixes; inability to beat simple controls on the development panel; or failure of the fixed exposed-panel primary/practical contrasts. One terminal release point only. Do not turn this into a release-time sweep on chess.

**GPU-hours, ANALYTICAL:** allow **8–12 RTX 3090 GPU-hours**, hard cap **12**, including development controls and both existing evaluation panels. The case-study block is four arms × (24 chess + 16 RGB-D) × four seeds = 640 full-trajectory equivalents, about 7.3 GPU-hours at the archived rate before reuse/shortened WGS; this is an upper planning proxy, not measured E1 throughput. Shard whole window-seed cells across the two cards. Expected implementation/run window: one day, with a second day reserved for scoring and failures.

## 7. E2 — Diagnose B without another full training run

**Hypothesis, UNVERIFIED.** B's failure may include source-slot bias contamination or a harmful warp-dependent contribution, rather than absence of warp sensitivity. The already recorded high-sigma loss pattern motivates looking at noise level and conditioning branch separately.

### Cheap teacher-forced probe, then fixed generation ablations

Proposed new files under work/R262_E2_B_diagnosis/: PROTOCOL.md, probe_sigma.py, gen_ablation.py, analyze.py. Reuse S141's model/conditioning, validation noise construction and evaluator; do not change stored adapters.

The implementation adds zero extra channels to context frames, but WarpInConv's learned bias still contributes there (S141/s141_common.py:97–106,157–163). The same warp enters both CFG dictionaries (S141/gen_s141.py:145–147). Therefore changing ordinary CFG scale is not an isolated warp-strength test.

On all monitor clips and the existing six validation indices, inspect correct/zero/permuted warp inputs under c and uc separately; report epsilon-MSE, derived clean-latent MSE and output sensitivity. Same target/noise per contrast. These are teacher-forced diagnostics, not surrogate success criteria.

Generation arms, all with B's own completed LoRA:

1. **B_original:** existing B.
2. **B_target_only:** multiply the entire extra-branch output, including its bias, by the source/target frame indicator; source contribution is zero, target contribution unchanged. Apply the repeated frame mask correctly in both CFG halves.
3. **B_off:** zero the whole added branch. This retains B's LoRA; it is not A.
4. **B_bias_only:** zero all extra input channels while retaining learned branch bias on all frames.
5. **B_permuted:** permute warp latent spatial cells within coverage strata using one fixed seed, preserve coverage channels and original scoring masks, and apply the same intervention in both CFG branches.

The permutation is an intentionally artificial sensitivity control, not a natural data distribution or proof of useful memory. A decrease under corruption is insufficient.

**Primary contrast:** B_target_only − B_original, with the shared rule. **Strongest trivial baselines:** B_off and unmodified A; for practical prediction, also B2 and the E1 development-selected control.

Interpretation is deliberately bounded:

- A primary gain supports a harmful context-slot contribution in this recipe; it does not establish that input bias is the sole cause.
- B_original worse than B_off implicates its added branch contribution under fixed B LoRA.
- B_bias_only close to B_original suggests appearance-dependent warp information adds little under that test; it is not formal equivalence.
- B_original better than B_permuted establishes sensitivity only. Require superiority to B_off/A before claiming useful warp consumption.
- Removing the branch does not identify whether B's LoRA co-adapted badly. A future A-anchored branch would answer a different question.

**Kill criterion:** finish this fixed diagnostic once, report the sign, and stop. If target-only gating fails the +0.20 dB rule, reject that repair as a useful explanation; do not escalate branch capacity or train longer under E2. A warm-start A branch remains candidate 3, not an automatic fourth retained experiment.

**GPU-hours, ANALYTICAL:** **4–6 RTX 3090 GPU-hours**, hard cap **6**, for monitor probes plus four new chess arms × 24 windows × four seeds. Use existing B/A only after receipt matching. RGB-D full generation is not added to this diagnostic budget; its monitor/sensitivity transfer can be a later explicitly frozen extension if needed. Feasible within one day. This is a diagnosis, not a promised improved method.

## 8. E3 — Train one endpoint correction on the actual frozen prefix

**Hypothesis, UNVERIFIED.** An A-initialized denoiser trained on structured errors from the deployed warp-guided prefix can correct its final prediction better than an equally trained denoiser seeing Gaussian-corrupted ground-truth latents. This tests the training-state distribution while holding the endpoint objective and deployment point fixed.

This is the preferred next **training** experiment after E1's engineering and baseline work. It is narrower than restarting B and cheaper than differentiating through a complete sampling trajectory.

### Exact minimal construction

Proposed new files under work/R262_E3_endpoint/: PROTOCOL.md, cache_prefix.py, train_endpoint.py, gen_endpoint.py, train_residual_baseline.py, analyze.py.

1. Select **256** S141 training clips deterministically, stratified by scene and static/memory kind, seed 262. Cache **two** fixed prefix-noise seeds per clip. Use the existing **32** monitor clips for development only. All inputs, target supervision and warps already belong to S141's asset family; the future run must verify actual remote cache/adapter identities.
2. Run frozen A with original W2 strength 0.5 through the prefix preceding the final denoiser call. Save the full eight-frame state **after the final sampler input perturbation**, sigma_hat, the quantized denoiser sigma, c/uc conditioning, cameras, masks and RNG provenance. Also save the original standard-normal target tensor before initial sigma scaling, and the untrained A_R clean endpoint. Cache training target latents separately as labels. Never inject them into the prefix. When replaying the post-perturbation cache, call the denoiser/guider directly and preserve the Euler expression; do not call an entry point that adds the sampler perturbation a second time.
3. Initialize a separate trainable rank-16 LoRA state from completed A. Keep base weights/VAE frozen. Only the **final denoising call** uses the new LoRA; all earlier calls always use original A. Skip the terminal warp overwrite.
4. Train using the **actual guided clean prediction** returned by the existing denoiser and guider, with target-frame latent MSE to the real training targets. Use both CFG branches and the exact configured guider, rather than replacing it with an assumed scalar formula. The relevant preparation/order/guide code is V/modeling/sampling.py:265–276,279–332,393–402. Use separate sequential branch forwards if needed for memory; preserve gradients and the same guided result.
5. Fix **2,000 updates**, AdamW **1e-5**, batch one clip, seed 262; take only the final checkpoint. These are exploratory budget choices, not tuned optima. No full-trajectory backward graph or VAE backward is needed.

**Avoid an invalid target:** a cached WGS state is not z_GT + sigma * the original Gaussian noise. Reusing the old sampled epsilon as its label would be wrong. Direct clean-latent regression avoids that error. If epsilon labels are used instead, they must be derived from the actual state and the denoiser's quantized sigma. The registered S141 epsilon implementation and sigma quantization are at S141/train_s141.py:61–68 and V/modeling/sampling.py:159–185.

At the final Euler update with next_sigma = 0, its algebra returns the guided clean prediction (up to floating-point arithmetic), before the optional overwrite (V/modeling/sampling.py:393–402). This is the exact endpoint that the new loss trains. Before training, the A-initialized terminal LoRA must reproduce E1's A_R endpoint; restoring the original A adapter state must restore that endpoint. Disabling the whole LoRA would remove A itself and is not this fidelity control.

### Matched controls and primary

| Arm | Training input / deployment |
|---|---|
| **T_state** | Actual cached frozen-prefix state; endpoint target loss; learned LoRA used only at the last call. |
| **T_gauss** | Same A initialization, examples, sigmas, loss, optimizer and updates; replace only target-frame noisy states by z_GT + quantized_sigma * epsilon, using the same cached original standard-normal target tensor rather than an independent draw. Keep cached context states and conditioning fixed. Deploy at the same final call on actual prefix states. This pairs exogenous noise identity; it does not make WGS errors Gaussian. |
| **H_residual** | A small two-layer spatial latent residual network with an identity skip around the frozen A_R clean endpoint. Per target, concatenate A_R endpoint (4 channels), cached terminal target state (4), warp latent (4), and coverage (1): 13→64→4 channels, 3×3 convolutions, ReLU between them, zero-initialized final layer. Train 2,000 updates with the same examples and endpoint loss, AdamW 1e-3 and seed 262. A_R already carries the frozen model's context/camera processing; there is no training through that backbone. At inference the head adds its residual to A_R. This tests whether cheap supervised postprocessing of the same frozen predictor suffices. |
| **A_R / A_C** | No further training: E1 released endpoint and original A+WGS. |
| **Simple output controls** | B2, VAE round trip, E1's fixed pastes and development-fitted global blend. |

The primary is **T_state − T_gauss**, requiring the shared +0.20 dB/positive-bound rule. A practical win additionally requires T_state to beat **A_R, A_C, H_residual and all simple controls** by that rule on exposed chess, with no negative transfer mean on the fixed RGB-D panel and the SSIM guardrail.

The T_state/T_gauss contrast isolates **target-state distribution under this cache**, not every possible sampling mismatch. The small head is a deliberately cheaper baseline, not parameter-count matched. If it matches T_state, choose the head and reject the need for a diffusion-based endpoint refiner.

Because only one terminal operation changes, the frozen prefix produces the same input distribution before and after training. Calling this “on-policy training” would be wrong. Extending to multiple learned tail steps would invalidate that simple distribution argument and require a separate protocol.

**Development gate and kill criterion:** stop before case-study generation unless T_state beats both T_gauss and H_residual by at least +0.20 dB on sampled monitor outputs without the SSIM violation. If all learned arms only beat the unclamped A_R but lose to the original clamped A_C or VAE/paste baseline, stop. After the fixed case-study run, failure of the primary or practical comparisons closes this recipe; no extra steps or checkpoint selection on chess.

**GPU-hours, ANALYTICAL:** allow **12–18 RTX 3090 GPU-hours**, hard cap **18**, including frozen-prefix caching, both LoRA controls, the small head and fixed two-panel scoring. At the archived A rate, 4,000 ordinary single-branch training steps alone are about 1.6 GPU-hours; guided endpoint training requires extra forwards and must be timed, so budget several times that plus caching. Share exact inference prefixes across endpoint arms where the cache fidelity gate passes, but do not count hypothetical reuse as measured speed. Train T_state/T_gauss on separate cards after caches are ready. Feasible in one to two days if assets and gradients fit the timing/memory pilot.

## 9. What fresh confirmation would actually require

**No certified untouched, unseen-room confirmation set was found among the inspected local assets.** Appendix A3 records the bounded inventory. This is not a claim that no other remote data exist; this run did not inspect any cluster.

| Candidate data | What can honestly be claimed |
|---|---|
| S141's six non-chess 7-Scenes rooms | Training-room evaluation. The builder enumerates all seq-* directories and excludes only the two monitor sequences; it does not honor official train/test split files (S141/build_clips_s141.py:15–19,43–58). Appendix A2 lists the actual training target sequences. Nominal “test sequence” names do not restore independence. |
| office/seq-10; redkitchen/seq-14 | Held out of training references in the inspected manifest, but used for monitor loss and now development. Not fresh confirmation. S141/PROTOCOL.md:24–26,90–92; Appendix A3. |
| Chess | Held out of A/B training, repeatedly exposed to research decisions. All six traversals appear in the original source/target pairs (work/S139_crossseq_revisit/PROTOCOL.md:17–22). Disjoint future windows could be new-target transfer inside an exposed room, not an untouched scene. |
| RGB-D Scenes v2 scenes 13/14 | Exposed cross-dataset transfer; already evaluated in S141 (S141/RESULT.md:45–50). |
| Local TUM fr1_xyz / fr2_desk | Already exposed in earlier project work (docs/S24_RESULTS.md:5–9; docs/S21_RESULTS.md:39). They are not a newly blind scene test. |
| Local Bonn static_close_far | Its source history is explicitly exposed adaptation data (docs/S15B_BONN_POSE_RESOLUTION.md:46–54). New target frames would still be within an exposed room; calibration and later-exposure status also need checking. |
| Other RGB-D Scenes v2 rooms | Candidate acquisition/availability checks only. The stored dataset README identifies the collection at work/S102_gate0_3dmatch/adapter_v1/sources/rgbd_scenes_v2_README.txt:1–7; Appendix A3 finds only scenes 13/14 locally. Other scene IDs are not verified available or untouched. |

**Proposed fresh confirmation, ANALYTICAL:** after freezing the winning recipe and its baselines, identify at least **three additional physical scenes** with usable RGB/cameras and repeated traversals, none used in adaptation, monitor selection, figures, diagnostics or any other concurrent experiment. Audit exposure across the full project and collaborators' manifests. A possible source is other RGB-D Scenes v2 scene IDs, but room independence and data availability must be checked before naming a final set.

Freeze room IDs, source banks, target-camera windows, preprocessing and exact input/output hashes before viewing target RGB or outcome-dependent selection. Allow poses and input-only coverage checks to define windows; do not choose targets by reconstruction quality. Keep target RGB/depth scorer-only. Evaluate the **one** frozen candidate and all prespecified simple controls on paired seeds, with per-scene means as the main generalization summary. Several windows within a scene increase precision within that room; they do not create more independent rooms. No pretrained-model dataset-exclusion claim is possible without its training provenance.

If acquisition is impossible within the remaining project window, use the existing panels for the bounded experiments and label them exploratory. New seeds, untouched pixels from a trained room, or a freshly written protocol cannot substitute for new-room confirmation. Do not train a candidate on all newly acquired rooms and then call their remaining frames unseen-scene data.

## 10. Execution order and honest stopping point

1. **E1 first.** It directly combines the component that worked with the nearly successful sampler, has no new training, and tests a source-derived ambiguity in the covered-region claim.
2. **E2 is a bounded side diagnosis**, schedulable on the second available card after S143; its goal is to identify or reject branch-level explanations. A failing B does not earn unlimited rescue training.
3. **E3 is the next training use**, only after the fixed-prefix cache/baselines exist and its development gate is specified. The comparison is more informative than another general LoRA duration/rank sweep.

These budgets do not assume that both cards are idle now. They require no H800 access. Positive exposed-panel outcomes justify a frozen fresh-scene test; they do not set the validation or novelty flags. Negative outcomes still close concrete hypotheses without another ideation loop.

**Changed file:** work/agents/CODEX_R262_IDEATION_AFTER_S141_RESULTS.md only. **Follow-ups for a separate execution session:** implement/freeze E1; retain E2's bounded diagnostic; conditionally implement E3; inventory genuinely fresh scenes. No code tests were run because this task changes a research memo only; the CPU verifications below are arithmetic/inventory checks, not GPU reproductions.

## Appendix A — Exact CPU verification commands and complete outputs

All commands below were run read-only from /Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling. They import no project GPU modules and write no files. File reading and live primary-source literature inspection support the other citations; the commands below are the numerical/inventory computations claimed by this memo. Existing source and ledger files were not edited.

### A1. Snapshot, archived results, region composites and throughput

```bash
python3 -B - <<'PY'
import json, statistics as st, math, hashlib, subprocess
from pathlib import Path
p=Path('work/S141_finetune/results')
J=lambda x: json.loads(Path(x).read_text())
a=J(p/'S141_ANALYSIS.json')
print('HEAD',subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
for f in ['CURRENT_STATUS.md','work/S141_finetune/RESULT.md',str(p/'S141_ANALYSIS.json'),'work/S141_finetune/train_s141.py','work/S141_finetune/s141_common.py','work/S140_warp_guided/gen_s140.py']:
 print('SHA256',hashlib.sha256(Path(f).read_bytes()).hexdigest(),f)
for n in ['PRIMARY_A: A_mem - base_mem','A_mem - A_static','PRIMARY_B: B_mem - B2_warp']:
 c=a['contrasts']['psnr_db'][n]; print(n,f"{c['mean']:.6f}", 'CI',*[f'{v:.6f}' for v in c['ci95']])
print('A_change_in_memory_advantage_dB',f"{a['contrasts']['psnr_db']['A_mem - A_static']['mean']-a['contrasts']['psnr_db']['base_mem - base_static (S139 replica, seeds 3-6)']['mean']:.6f}")
for n,s in a['means']['ssim'].items(): print('chess_ssim',n,f'{s:.6f}')
A=J(p/'tacc/eval/SCORES_chess_A.json')['runs']
B=J(p/'tacc/eval/SCORES_chess_B.json')['runs']
W=J('work/S140_warp_guided/results/confirm_tacc/S140_SCORES_confirm_tacc.json')['runs']
for name,rows in [('A_mem',[r for r in A.values() if r['mode']=='A_mem']),('B_mem',list(B.values())),('WGS',[r for r in W.values() if r['seed'] in (3,4,5,6)])]:
 out={}
 for r in rows:
  h=r['hole_fraction']; gc=10**(-r['psnr_covered']/10); gh=10**(-r['psnr_holes']/10); wc=10**(-r['warp_psnr_covered']/10); wh=10**(-r['warp_psnr_holes']/10)
  wm=(1-h)*wc+h*wh
  out.setdefault(r['window_id'],[]).append([r['psnr_covered']-r['warp_psnr_covered'],r['psnr_holes']-r['warp_psnr_holes'],10*math.log10(wm/((1-h)*gc+h*wh)),10*math.log10(wm/((1-h)*wc+h*gh))])
 m=[st.mean(st.mean(x[j] for x in v) for v in out.values()) for j in range(4)]
 print('regions_and_fixed_pastes',name,'windows',len(out),'runs',len(rows),'covered_delta,hole_delta,generated_covered_warp_holes,warp_covered_generated_holes',*[f'{x:.6f}' for x in m])
for arm in ['A','B']:
 log=[json.loads(x) for x in (p/f'tacc/runs/{arm}/train_log.jsonl').read_text().splitlines()]
 vals=[r for r in log if 'val' in r]; sec=[r['sec_per_step'] for r in log if 'sec_per_step' in r]
 print('train',arm,'monitor_first_last',vals[0]['val'],vals[-1]['val'],'median_sec_per_step',f'{st.median(sec):.6f}')
times=[]
for f in (p/'tacc/eval').glob('*/RUNS_*.jsonl'):
 times += [json.loads(x)['seconds'] for x in f.read_text().splitlines()]
print('generation_receipts',len(times),'median_seconds',f'{st.median(times):.6f}')
print('S141_local_prediction_npy',len(list(p.rglob('*.npy'))),'S141_local_adapter_pt',len(list(p.rglob('adapter*.pt'))))
PY
```

Complete output (exit 0):

```text
HEAD 3ce97f83d2238dcf406ddbd9d050e1f5b9bc702a
SHA256 739005cc2a5e60719eff32e36b6ab25c30730872fc18d765548efaf05448b031 CURRENT_STATUS.md
SHA256 9e86f2384e3d9e3d066339cf212f6ca6d7c9452e3e97e1e9cf495f05ad3fe6be work/S141_finetune/RESULT.md
SHA256 323848ff27da6d96b78d10506f3257849799a33802ff655781f87122c6e7a350 work/S141_finetune/results/S141_ANALYSIS.json
SHA256 6ba0419e5ceb39406bbd1894ffae90398c27daedbc2eea56b18e537ba6187c0a work/S141_finetune/train_s141.py
SHA256 459549706fb3a965fc4f7c5021f4d49cc626158e94a7c9cdc94cf8784cccb6cc work/S141_finetune/s141_common.py
SHA256 119904b368eefe4f7bd99e1aed0ba91d7a9250aad5e97a0fb298d7007c0a46c9 work/S140_warp_guided/gen_s140.py
PRIMARY_A: A_mem - base_mem 0.330456 CI 0.078217 0.584857
A_mem - A_static -0.331743 CI -0.669355 0.005715
PRIMARY_B: B_mem - B2_warp -3.557738 CI -3.912510 -3.201337
A_change_in_memory_advantage_dB -0.117413
chess_ssim A_static 0.493731
chess_ssim A_mem 0.486071
chess_ssim B_mem 0.505080
chess_ssim base_static 0.486963
chess_ssim base_mem 0.468223
chess_ssim B2_warp_mem 0.431766
chess_ssim B_static 0.524761
chess_ssim B2_warp_static 0.474218
regions_and_fixed_pastes A_mem windows 24 runs 96 covered_delta,hole_delta,generated_covered_warp_holes,warp_covered_generated_holes -3.136745 -2.716981 -2.025684 -1.389320
regions_and_fixed_pastes B_mem windows 24 runs 96 covered_delta,hole_delta,generated_covered_warp_holes,warp_covered_generated_holes -3.649125 -3.489385 -2.396404 -1.838282
regions_and_fixed_pastes WGS windows 24 runs 96 covered_delta,hole_delta,generated_covered_warp_holes,warp_covered_generated_holes 0.231158 -0.274957 0.122799 -0.127439
train A monitor_first_last 0.04791178031655363 0.049092766404100985 median_sec_per_step 1.400270
train B monitor_first_last 0.04791178031655363 0.049212190777325304 median_sec_per_step 1.324506
generation_receipts 512 median_seconds 40.940000
S141_local_prediction_npy 0 S141_local_adapter_pt 0
```

### A2. Raw-score recomputation, sigma-scaled monitor errors and training splits

```bash
python3 -B - <<'PY'
from pathlib import Path
import json, math, statistics as st
p=Path('work/S141_finetune/results'); load=lambda f:json.loads((p/f).read_text())
def wm(rs,pick):
 d={}
 for r in rs.values():
  if pick(r) and r['seed'] in (3,4,5,6): d.setdefault(r['window_id'],[]).append(r['psnr_db'])
 assert len(d)==24 and all(len(v)==4 for v in d.values())
 return {w:st.mean(v) for w,v in d.items()}
A=wm(load('tacc/eval/SCORES_chess_A.json')['runs'],lambda r:r['mode']=='A_mem')
b=load('tacc/eval/SCORES_chess_B.json'); B=wm(b['runs'],lambda r:r['mode']=='B_mem')
base=wm(load('audit_inputs/S139_ALL_SSIM_tacc.json')['runs'],lambda r:'mem_vmem' in r['arms'])
print('raw-score PRIMARY_A',f'{st.mean(A[w]-base[w] for w in A):.12f}')
print('raw-score PRIMARY_B',f"{st.mean(B[w]-b['warps'][w]['psnr'] for w in B):.12f}")
last={v:[r for l in (p/f'tacc/runs/{v}/train_log.jsonl').read_text().splitlines() if 'val' in (r:=json.loads(l))][-1]['val_by_sigma'] for v in 'AB'}
alpha=1.; sig=[]
for i in range(1000):
 beta=(math.sqrt(5e-6)+(math.sqrt(.012)-math.sqrt(5e-6))*i/999)**2
 alpha*=1-beta; sig.append(math.sqrt((1-alpha)/alpha)*math.exp(2.4))
print('index sigma A_epsMSE B_epsMSE A_derived_x0MSE B_derived_x0MSE')
for j,i in enumerate((50,200,400,600,800,950)):
 av,bv=last['A'][j],last['B'][j]
 print(i,f'{sig[i]:.6f}',f'{av:.9f}',f'{bv:.9f}',f'{sig[i]**2*av:.6f}',f'{sig[i]**2*bv:.6f}')
c=json.loads(Path('work/S141_finetune/clips_s141.json').read_text())['clips']
print('manifest',len([x for x in c if x['split']=='train']),'train',len([x for x in c if x['split']=='val']),'monitor')
for sc in sorted({x['scene'] for x in c}):
 print('train_target_sequences',sc,','.join(sorted({x['C'] for x in c if x['scene']==sc and x['split']=='train'})))
print('monitor_target_sequences',','.join(sorted({x['scene']+'/'+x['C'] for x in c if x['split']=='val'})))
PY
```

Complete output (exit 0):

```text
raw-score PRIMARY_A 0.330455947376
raw-score PRIMARY_B -3.557737552245
index sigma A_epsMSE B_epsMSE A_derived_x0MSE B_derived_x0MSE
50 0.407069 0.250054676 0.252915069 0.041435 0.041909
200 2.273756 0.033446010 0.029892624 0.172915 0.154544
400 6.365476 0.007886606 0.008381034 0.319560 0.339593
600 13.583746 0.002386681 0.002807125 0.440386 0.517966
800 30.115066 0.000606076 0.000816602 0.549661 0.740590
950 63.639968 0.000176548 0.000460690 0.715029 1.865816
manifest 2000 train 32 monitor
train_target_sequences fire seq-01,seq-02,seq-03,seq-04
train_target_sequences heads seq-01,seq-02
train_target_sequences office seq-01,seq-02,seq-03,seq-04,seq-05,seq-06,seq-07,seq-08,seq-09
train_target_sequences pumpkin seq-01,seq-02,seq-03,seq-06,seq-07,seq-08
train_target_sequences redkitchen seq-01,seq-02,seq-03,seq-04,seq-05,seq-06,seq-07,seq-08,seq-11,seq-12,seq-13
train_target_sequences stairs seq-01,seq-02,seq-03,seq-04,seq-05,seq-06
monitor_target_sequences office/seq-10,redkitchen/seq-14
```

### A3. Bounded local inventory and monitor exclusion

```bash
python3 -B - <<'PY'
import json
from pathlib import Path
j=json.loads(Path('work/S141_finetune/clips_s141.json').read_text())
t=[x for x in j['clips'] if x['split']=='train']
r={p for x in t for p in x['ctx']+x['tgt']}
print('monitor_train_refs',sum(p.startswith(('office/seq-10/','redkitchen/seq-14/')) for p in r))
print('local_split_files',len(list(Path('data').rglob('*Split.txt'))))
print('local_7scenes_rooms',','.join(sorted({p.parent.name for p in Path('data').glob('**/seq-*') if p.is_dir() and p.parent.name in {'chess','fire','heads','office','pumpkin','redkitchen','stairs'}})))
print('local_rgbd_v2_rooms',','.join(sorted({p.name for p in Path('data').glob('**/rgbd-scenes-v2-scene_*') if p.is_dir()})))
print('local_tum_sequences',','.join(sorted({p.name for p in Path('data/tum').glob('**/rgbd_dataset_*') if p.is_dir()})))
print('local_bonn_sequences',','.join(sorted({p.name for p in Path('data').glob('**/rgbd_bonn_*') if p.is_dir()})))
PY
```

Complete output (exit 0):

```text
monitor_train_refs 0
local_split_files 0
local_7scenes_rooms chess
local_rgbd_v2_rooms rgbd-scenes-v2-scene_13,rgbd-scenes-v2-scene_14
local_tum_sequences rgbd_dataset_freiburg1_xyz,rgbd_dataset_freiburg2_desk
local_bonn_sequences rgbd_bonn_static_close_far
```

### A4. Document integrity and concurrent-checkout check

This check was performed after the final substantive edits and before appending this receipt; its byte count excludes this appendix. The checkout HEAD advanced concurrently from the A1 snapshot, while the six inspected evidence hashes remained unchanged. Concurrent prompt/status changes were left untouched. This is document/link verification, not a code test or experimental reproduction.

```bash
python3 -B - <<'PY'
from pathlib import Path
import re, hashlib, subprocess
p=Path('work/agents/CODEX_R262_IDEATION_AFTER_S141_RESULTS.md'); t=p.read_text()
missing=[]
for target in re.findall(r'\]\(([^)]+)\)',t):
 if not target.startswith(('https://','http://')) and not (p.parent/target.split('#')[0]).exists(): missing.append(target)
print('memo_exists',p.exists())
print('utf8_bytes',len(t.encode()))
print('local_link_missing',missing)
print('divergence_rows',len(re.findall(r'^\| \*\*\d+(?: ★)?\*\* \|',t,re.M)))
print('focused_prior_art_sections',len(re.findall(r'^### P[1-5]\.',t,re.M)))
print('retained_experiment_sections',len(re.findall(r'^## [678]\. E[123] ',t,re.M)))
print('code_fences_balanced',t.count('```')%2==0)
print('cjk_characters',len(re.findall(r'[\u4e00-\u9fff]',t)))
checks={
 'CURRENT_STATUS.md':'739005cc2a5e60719eff32e36b6ab25c30730872fc18d765548efaf05448b031',
 'work/S141_finetune/RESULT.md':'9e86f2384e3d9e3d066339cf212f6ca6d7c9452e3e97e1e9cf495f05ad3fe6be',
 'work/S141_finetune/results/S141_ANALYSIS.json':'323848ff27da6d96b78d10506f3257849799a33802ff655781f87122c6e7a350',
 'work/S141_finetune/train_s141.py':'6ba0419e5ceb39406bbd1894ffae90398c27daedbc2eea56b18e537ba6187c0a',
 'work/S141_finetune/s141_common.py':'459549706fb3a965fc4f7c5021f4d49cc626158e94a7c9cdc94cf8784cccb6cc',
 'work/S140_warp_guided/gen_s140.py':'119904b368eefe4f7bd99e1aed0ba91d7a9250aad5e97a0fb298d7007c0a46c9'}
print('inspected_input_hashes_unchanged',all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in checks.items()))
print('current_HEAD',subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
print('status_begin')
print(subprocess.check_output(['git','status','--short'],text=True),end='')
print('status_end')
PY
```

Complete output (exit 0):

```text
memo_exists True
utf8_bytes 57782
local_link_missing []
divergence_rows 16
focused_prior_art_sections 5
retained_experiment_sections 3
code_fences_balanced True
cjk_characters 0
inspected_input_hashes_unchanged True
current_HEAD 043edd3f7ae5d804d68bc59dfbc0530a0deb4214
status_begin
?? work/agents/CODEX_R262_IDEATION_AFTER_S141_RESULTS.md
?? work/agents/prompts/R262_FULL.md
status_end
```
