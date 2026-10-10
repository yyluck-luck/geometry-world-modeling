# R263 — Rejection review of the S144 and S145 drafts

**Verdict: reject both drafts as execution-ready; retain both as bounded, repairable experiments. Run corrected S144 first if only one complete experiment fits.** Its primary is mathematically meaningful, but one archival replay does not remove implementation lineage from the factorial. S145's proposed target-only intervention is correct in principle, but answers a narrower question than “why B failed.” Neither experiment currently supports a new-method claim.

This review is entirely read-only except for this file. No GPU, model inference, training, weight/data downloads, cluster access, submissions, or external communication occurred. The CPU checks below establish inventories, arithmetic, and synthetic control flow; they do not reproduce GPU results. No project ledger or protocol was edited. The idea-evaluator skill's baseline and falsifiability checks were applied to this protocol review, using the requested findings-table format.

The brief's “S141 running” statement is stale relative to CURRENT_STATUS.md:60–68 and S141/RESULT.md:7–21. Completed-run receipts and score summaries are local; the inspected S140/S141 results trees contain no prediction NPYs or adapter checkpoints (Appendix A). Thus actual adapter tensors, archived image bytes, and CUDA replay equality remain **UNVERIFIED in this review**. A checkpoint-check receipt is evidence of a previous check, not a fresh tensor inspection.

**Evidence notation.** All paths are relative to the repository root. S140 = work/S140_warp_guided; S141 = work/S141_finetune; V = data/S134_tacc/vmem_src; R262 = work/agents/CODEX_R262_IDEATION_AFTER_S141_RESULTS.md; D144/D145 = the corresponding PROTOCOL_DRAFT.md under work/S144_A_wgs and work/S145_B_diagnosis. Full source hashes and checkout identity are in Appendix A. Every proposed threshold, grid, sample count, and budget below is **ANALYTICAL**, unless marked **DERIVED** or **MEASURED**. “MEASURED, archived” means a repository receipt, not a new experiment.

## 1. S144 findings

| Issue | Severity | Evidence | Concrete change |
|---|---|---|---|
| An old F_C implementation is confounded with one factorial cell unless its equivalence is established. One exact cell proves that cell only. | MAJOR, execution blocker | D144:8–11; S140/gen_s140.py:139–180 versus the adapter insertion/loading path at S141/gen_s141.py:110–125. Existing S140 fidelity receipts test ref/none on one RGB-D window, not W2 in an A-capable generator: S140/results/dev/FIDELITY_SHA256.txt:1–4. | Generate F_C and F_R together from the same final post-Euler tensor. This costs an additional decode, not another denoising trajectory. Use old F_C as an archival fidelity reference. If reuse is retained, require the full identity contract in §3.2 and disclose the replay scope. |
| Skipping the terminal overwrite is possible, but “consume its RNG draw” is an incomplete implementation instruction. | MAJOR | S140/gen_s140.py:174–178; V/modeling/sampling.py:393–402 unconditionally draws full-state noise and computes sigma_hat = sigma*(gamma+1)+1e-6. | Preserve the internal Euler call and noise, every earlier replacement, and the terminal target replacement draw. Skip only the terminal assignment. Do not replace the last Euler result with a denoiser result or remove perturbation because gamma is zero. |
| The interaction does not isolate A's final denoiser skill. A changes the entire preceding trajectory. | MAJOR, claim boundary | S141/s141_common.py:109–115 changes attention projections; S140/gen_s140.py:172–175 uses that model at every step; R262:183 correctly acknowledges unequal A/F prefixes. | Name the estimand “whole-trajectory adapter × terminal-clamp interaction.” A terminal-only attribution would require a separate fixed-prefix endpoint swap, outside this minimal experiment. |
| Covered-latent clamping does not imply covered-RGB identity or local denoiser polishing. | MAJOR | Latent mask is pooled valid >=0.5 at S140/gen_s140.py:155,203; overwrite precedes decode at :174–179; scorer uses original pixel valid at S140/score_s140.py:35–38. VAE encoding/decoding is at V/modeling/modules/autoencoder.py:21–45. | State latent and pixel masks separately. Add the VAE-covered/B2-holes paste control. Report pixel-region effects without equating them to latent-region causation. |
| The listed controls are necessary but do not justify “strongest trivial” without a decoder-plus-paste control and equally tuned frozen/VAE alternatives. | MAJOR for added-value claims | D144:12–15; R262:185. The already required VAE/F_C/A_C outputs make these controls available without more denoiser calls. | Add VAE-covered/B2-holes; fit the same fixed global-alpha grid separately for VAE/B2, F_C/B2, A_C/B2. Freeze every coefficient and any named winning family on development. Keep raw B2 and all individual comparisons. |
| GPU-CUT3R monitor warps versus CPU-CUT3R case warps are a calibration shift, not target leakage. A badly transferred alpha is a weak deployment comparator. | MAJOR qualification | S141/warps_s141.py:27,79–96 uses CUDA; S141/PROTOCOL.md:27–31,94–97 records CPU case warps and a context-selection shift. | Prefer CPU monitor warps from the same geometry path as evaluation before any alpha fitting; use those warps in all S144 development arms. If GPU warps are deliberately retained, label the blend “GPU-monitor-calibrated transfer control”; failure does not rule out well-calibrated blending. Never refit on either case panel. |
| Monitor warp/ref format cannot be passed unchanged to the old generator/scorer. | MAJOR, implementation blocker | S141/warps_s141.py:7,87–97 stores one NPZ per clip with a target-frame dimension; S140/gen_s140.py:200–206 and score_s140.py:30–40 expect one NPZ per target and two-part refs. | Freeze a monitor plan/loader mapping from clip, scene, target index to the correct RGB/mask slice. Verify ordering, shapes, normalization, and equality to those slices. Re-encode a changed CPU warp; do not reuse GPU-derived latent caches. |
| Development go/no-go is not executable. The chess pair rule has no literal meaning for two monitor sequences. | MAJOR | D144:17–18,24–25; R262:160,197. | Separate engineering validity from the development performance screen; freeze both, including per-sequence criteria and the action after failure (§3.5). No improvised A_C continuation after inspecting development outcomes. |
| Alpha fitting/compositing and PSNR aggregation are underspecified. | MAJOR | D144:13–15; S140/score_s140.py:15–18,30–49 converts to uint8 and accumulates full-clip SSE. | Use one frozen conversion/compositing path; fit mean clip PSNR after seed averaging, with a deterministic tie rule. Recompute composite SSE; do not average covered/hole PSNRs or optimize pooled-pixel MSE while claiming the PSNR-optimal alpha. |
| A positive interaction alone can be caused by a particularly bad F_R; case windows are exposed and dependent. | MAJOR if the practical or exposure qualification is omitted | D144:18–23; R262:191–195; S141/RESULT.md:84–87; S141/analyze_s141.py:22–40. | Retain the separate A_R-versus-A_C and all-control requirements. Form a paired interaction within each window; preserve all four arms during bootstrap. Treat intervals as descriptive within this panel, not independent-room confidence. |
| The GPU cap is plausible, not established; development and references must be counted. W2 is a half-length schedule in calls, not necessarily in elapsed time. | MODERATE, timing gate | D144:25; S140/gen_s140.py:164–175; V/modeling/sampling.py:126–135; V/configs/inference/inference.yaml:20. Appendix A counts all cells and archived timing receipts. | Budget 25 calls per W2 trajectory. Share C/R endpoints; include both decodes, VAE controls, ordinary-A monitor references, replay, initialization, and preparation. Use a complete-cell timing pilot before committing the full cap. |
| Calling the local sampler simply “RePaint” invites an incorrect algorithm-equivalence claim. | MINOR | The local loop is monotonically decreasing with one replacement per step (S140/gen_s140.py:174–178). RePaint, arXiv:2201.09865, exact title and sections below, includes a resampling procedure. | Call it “S140 W2, RePaint-style latent replacement.” Preserve this exact recipe; this review does not request an algorithm change. |

The only literature attribution needed here is **arXiv:2201.09865, “RePaint: Inpainting using Denoising Diffusion Probabilistic Models,” §4.1, §4.2 and Algorithm 1**. The paper describes conditioning through known-region replacement and a separate forward/backward resampling procedure. The source-backed difference above prevents treating S140's simpler loop as a full reproduction. [Verified primary text](https://arxiv.org/html/2201.09865v4#S4). No novelty conclusion follows from this bounded literature check.

## 2. S145 findings

| Issue | Severity | Evidence | Concrete change |
|---|---|---|---|
| Context slots receive exactly the learned branch bias, because their extra inputs are zero. Whether that bias is materially nonzero or harmful is unverified. | MAJOR, hypothesis boundary | S141/s141_common.py:97–106,157–163. S141/results/tacc/eval/ADAPTER_CHECK_B.txt:1 records branch tensors but no bias norm; check_adapter_s141.py:8–13 reports LoRA up-norm. | Inspect branch weight/bias norms and activations as diagnostics before generation. Describe context-bias harm as a hypothesis, not a proven bug. Do not select a checkpoint from these diagnostics. |
| Multiplying branch inputs by the target indicator would leave context bias intact. The draft correctly specifies output gating; implementation must preserve that distinction. | MAJOR implementation gate | D145:6–7; S141/s141_common.py:102–106,157–163. | Multiply the entire extra-convolution output, including bias, before adding it to the unchanged base output. |
| The unconditional concat mask cannot identify target frames; packed CFG rows are grouped rather than interleaved. | MAJOR; wrong implementation invalidates every ablation | V/modeling/pipeline.py:1158–1172 zeros the uc indicator; V/modeling/sampling.py:265–276 packs uc then c. | Carry an explicit frame-identity mask. Repeat the complete eight-frame mask for CFG; never use repeat_interleave or “last half of rows.” Keep num_frames=8. |
| extend_concat cannot be applied unchanged after CFG packing. | MAJOR implementation gate | S141/s141_common.py:160–163 computes nctx from row counts; current correct calls are separately on c and uc at S141/gen_s141.py:145–151. V/modeling/network.py:226–230 concatenates noisy state with conditioning. | Extend each eight-row dictionary once, then pack. Assert extra shape (4,5,72,72), concat shape (8,12,72,72), and wrapped-conv input (16,16,72,72) for a single CFG clip. |
| B_off must preserve B's LoRA. B was separately trained; it is not A with a removable accessory. | MAJOR | S141/train_s141.py:42–48,89–94; S141/gen_s141.py:114–124. | Load the complete B checkpoint once, retain all LoRA tensors, and switch only the added branch contribution. A remains a practical comparator, not the branch-isolation control. |
| B_bias_only removes coverage as well as latent appearance. Its similarity to B_original cannot establish appearance independence. | MAJOR interpretation | S141/gen_s141.py:178–182 appends four latent channels plus coverage; WarpInConv acts on all five at common.py:102–106. | Retain the arm with its correct meaning: removal of all input-dependent branch terms. Add coverage-preserving zero-latent and spatial-mean-latent conditions to the cheap teacher-forced probe. |
| Permutation strata, channel coupling, random stream, and frame mapping are unspecified. | MAJOR | D145:8–10; fractional coverage at S141/gen_s141.py:180; sampler noise at V/utils/util.py:712–713 and V/modeling/sampling.py:393–396. | Freeze a per-target, four-channel-joint permutation within exact pooled-coverage strata, with a private CPU RNG and identical mapping in c/uc. Preserve coverage and original scoring masks; report moved-cell fractions. |
| B_target_only is the best targeted context-bias test, not the most diagnostic broad branch primary. | MAJOR, scope | D145:1,11–12; the source decomposition is S141/s141_common.py:97–106,157–163. | For “why B failed,” make B_off−B_original primary and target-only−original the key secondary. Alternatively retain the existing primary but rename the question to context-slot bias. Freeze this choice before new outcomes. |
| c/uc teacher-forced errors do not by themselves describe deployed CFG. Clean-latent MSE is a rescaling, not independent corroboration. | MAJOR interpretation | S141/train_s141.py:61–85; V/modeling/sampling.py:79–87,174–185,265–299. | Reuse the identical target/noise/sigma for every intervention; retain separate c/uc errors and combine them with the actual configured guider. Report sigma-squared scaling explicitly and include output sensitivity. |
| Monitor conditions and rollout conditions differ; teacher-forced results must not prune generation arms. | MODERATE | S141/train_s141.py:63–68,75–85 uses noisy ground-truth latents; S141/PROTOCOL.md:94–97 documents GPU/CPU warp and context-state differences. | Keep the probe diagnostic and complete all frozen generation arms. A monitor effect is not proof of the cause of a CPU-warp rollout failure. |
| Reused B_original/A need per-cell provenance, not merely “after a replay.” | MAJOR | D145:5–6; S141/gen_s141.py:134–155,195–198. | Match complete adapter hashes, plan/input/warp hashes, frame order, source/config and output receipts. Require intervention-disabled exact replay on the same backend. If provenance cannot establish the comparator, regenerate it or stop. |
| Neither a failed +0.20 dB repair nor a permutation drop proves branch irrelevance/usefulness. | MAJOR claim boundary | R262:225–233; S141/analyze_s141.py:2–5,33–40 explicitly avoids equivalence claims. | Report signed estimates and intervals. Use “no useful repair demonstrated,” “harmful branch contribution under fixed B LoRA,” or “sensitivity,” as appropriate. Do not infer alternative training history from an inference-time ablation. |

## 3. Corrected minimal S144 specification

### 3.1 Question, inputs and scope

Question: does the completed A adapter improve the effect of releasing the last covered-latent overwrite in the fixed S140 W2 trajectory, and does the resulting predictor beat cheap alternatives?

Freeze one generator and source/config hashes; base, VAE, CLIP and A weight hashes; the exact plans, input RGB/poses/intrinsics, warp RGB/masks; environment/precision; and output directory. The archived expected A checkpoint SHA-256 is **635e6e319d4dbf40d5db58d42498303c5f15fb32107f976e8c315d173de87818** (S141/results/tacc/eval/ADAPTER_CHECK_A.txt:1); recheck actual bytes at execution.

Use monitor clips c02000–c02031, seeds 3/4, followed only on a passed development gate by chess's fixed 24 windows and RGB-D's fixed 16 windows, seeds 3/4/5/6. Keep chess mem_vmem and RGB-D static contexts. S140/plan_confirm.json and the W2 strength-0.5 subset of S140/plan_dev.json define the case inputs; do not use the whole six-variant development plan (S140/build_plans_s140.py:9–20,23–30). Monitor IDs/counts and matching S140/S141 chess input fields are checked in Appendix A.

**Recommended frozen development choice:** CPU monitor warps made by the evaluation geometry path from the fixed contexts and target cameras. Use their RGB and masks for all development arms and re-encode through the same inference VAE. Their availability and CPU preparation time are unverified here; include them in the execution feasibility check. Retaining existing GPU monitor warps is a permissible explicitly amended transfer experiment, but does not establish the strongest CPU-deployment blend. There is also residual monitor-versus-case context-selection shift even after matching warp backend (S141/PROTOCOL.md:94–97).

Monitor target RGB may enter the separate scorer and scalar fitter. It must not enter warp generation, conditioning, or prediction. Case target RGB is scorer-only. Freeze coefficients and gate outcome before reading new case scores. Both case panels remain exposed; the monitors have already supported training diagnostics.

### 3.2 One implementation and an honest replay contract

Prefer fresh F_C/F_R/A_C/A_R from one generator. Per backbone, produce both endpoints from the same trajectory. This removes the need to mix an old script's F_C into the primary; it does not remove the need for an implementation-fidelity check.

A replay record must name the exact window, seed, context/target frame order, input bytes and warp bytes, config/schedule, base/VAE/CLIP bytes, A-disabled versus zero-initialized-wrapper state, GPU/library/backend/autocast settings, CPU and CUDA RNG states, and output-array hash. Reset RNG after adapter construction, as the sampling functions do (S141/gen_s141.py:116–117,135; S140/gen_s140.py:140). Require full decoded float-array equality and unchanged source inputs, not just equal PSNR or visually similar PNGs.

Specifically replay:
- Old S140 W2 against new F_C on a fixed chess cell and a fixed RGB-D cell with matching archived provenance.
- A-capable zero-initialized adapters against the adapter-disabled path, on the same inputs.
- For each new loader route, input-tensor/ref/mask mapping equality; monitor serialization needs this separate check.
- Same-backbone C/R equality through the last post-Euler state, identical consumed random tensors and final RNG states; uncovered latent cells and context slots must remain equal immediately before decode.

A one-cell match cannot prove identity of all archived cells. If someone insists on reusing the entire old F_C set, byte identity for that set requires all-cell replay; smaller replay plus all-cell provenance is supporting evidence with a stated scope, not universal proof. Since F_R already needs the base trajectory, fresh F_C is the cheaper scientific correction.

If the new consistent factorial cannot reproduce archival W2, diagnose before proceeding; do not silently label a changed recipe S140. Source/backend mismatch and scientific failure are different outcomes.

### 3.3 Exact terminal edit

Preserve S140's initialization, condition construction, W2 mask, sigma schedule and every sampler_step call (S140/gen_s140.py:139–178). The following is a **proposed** minimal control-flow change, not code installed by this review:

~~~python
for i in range(k, len(sigmas) - 1):
    x = sampler.sampler_step(
        s_in * sigmas[i], s_in * sigmas[i + 1],
        fn, x, CFG, c, uc, 0.0, **kw
    )  # preserve internal eps, sigma_hat, denoising, guidance and Euler expression
    nz = torch.randn_like(x[4:])  # always, including the final iteration
    if i == len(sigmas) - 2:
        x_R = x.clone()
        x_C = x.clone()
        x_C[4:] = m2 * (zw.to(x.dtype) + sigmas[i + 1] * nz) + (1 - m2) * x_C[4:]
    else:
        x[4:] = m2 * (zw.to(x.dtype) + sigmas[i + 1] * nz) + (1 - m2) * x[4:]
# Decode x_C and x_R separately, with original decode precision/chunking.
~~~

Do not alias x_R to x and then overwrite it. A separate-trajectory implementation can instead guard only the final assignment, while still drawing nz; it must pass the same trace checks.

**DERIVED:** with 50 configured steps, strength 0.5 gives k=25 and indices 25…49. Each backbone/cell uses 25 denoiser calls, 25 full-state Euler draws and 25 target replacement draws, plus the initial CPU normal tensor transferred to CUDA. These counts follow S140/gen_s140.py:163–178 and V/modeling/sampling.py:126–135,393–402. Gamma zero does not justify removing eps or the 1e-6 sigma_hat increment. The final Euler arithmetic is preserved even though its ideal real-number endpoint simplifies to a denoised prediction; floating-point identity is a separate issue.

**DERIVED latent relation:** at the endpoint, z_C = M_lat*z_w + (1-M_lat)*z_R on target slots. Thus C/R uncovered latent cells match, while decoded uncovered pixels need not. No denoiser runs after the overwrite; a covered-region RGB change is not automatically learned post-clamp refinement. A/F prefixes also differ, so the interaction estimates the stated full-trajectory policy effect.

Appendix B verifies the terminal edit's source-derived control flow with synthetic CPU arithmetic. It is not a PyTorch/CUDA numerical-equivalence test.

### 3.4 Controls and conversion

Mandatory controls: B2; V = D(E(B2)); P_V, P_FC, P_AC where P_G = M_pixel*G + (1-M_pixel)*B2; and three global blends alpha_G*G+(1-alpha_G)*B2 for G in {V,F_C,A_C}. Include ordinary A and the reverse A_C paste M_pixel*B2+(1-M_pixel)*A_C, the latter preventing a vague hole-filling attribution. All are fixed recipes, not per-window oracle choices.

Use the actual VAE posterior mean and scale factor, chunk size one and matched encode/decode precision, not posterior samples (V/modeling/modules/autoencoder.py:7,21–45; V/utils/util.py:657–668; S140/gen_s140.py:160,179,204–206). VAE reconstruction needs one result per warp, not one independent computation per sampling seed.

Convert each decoded output with the existing pred_u8 function; raw B2 is already uint8. Cast these canonical image arrays to float for blending, clip and truncate to uint8 once after blending. Never send a uint8-domain composite through pred_u8 again. Binary pastes select canonical uint8 pixels directly. The source conversion's range heuristic is frozen for comparability; any correction to it requires uniformly rescoring every arm/reference (S140/score_s140.py:15–18).

For each blend family independently, choose alpha from {0,0.05,…,1} by maximum development mean clip PSNR, first averaging seeds within clip; ties choose smaller alpha. If naming one strongest family, ties use the fixed order V, F_C, A_C. Retain and compare all families on cases; do not choose a new alpha/family for a case window or panel. Three one-dimensional searches add CPU scoring, not denoiser calls.

Use original input pixel masks throughout scoring. PSNR is computed from SSE pooled across the four target frames, then seed-averaged within each clip/window; SSIM is the existing frame mean (S140/score_s140.py:30–49). Blended PSNR must be evaluated from the blend itself. Empty regions must be reported as absent, not turned into reassuring regional scores via a fabricated denominator.

This is a strong bounded cheap-control set, not a proof that every conceivable smoother, calibration or blending rule has been exhausted. If the candidate loses to one of these controls, reject added predictive value.

### 3.5 Development gate and case decisions

Freeze these rules before monitor predictions:

1. **Engineering GO:** identities/loading/replay pass; the full planned development cell set exists, is finite and correctly shaped; C/R trace invariants hold; plan/scorer mappings are exact; and a complete-cell timing pilot projects the remaining mandatory work within the cap. Otherwise stop with an invalid/blocked assay, not a scientific negative.
2. Fit and freeze all blend coefficients.
3. **Performance GO, proposed explicit interpretation of R262's kill criterion:** development mean I >= +0.20 dB; A_R exceeds A_C and every mandatory practical control by >= +0.20 dB; each corresponding mean SSIM difference is >= -0.01. Require nonnegative means of I and of each required PSNR gain within **both** monitor sequences. Do not require bootstrap significance on this small, dependent development panel.
4. If performance GO fails, stop S144 and report the failed screen. No release-time sweep, checkpoint replacement, selective arm dropping, or automatic A_C-only continuation. A separate future simpler-recipe study would require a new protocol. This deliberately makes R262:197's otherwise ambiguous stop executable.

Appendix C finds **MEASURED manifest counts:** 32 monitor clips, 128 target slots but 105 distinct target frames, with overlapping targets across clips. The monitor screen is development selection, not independent evidence of generalization.

For the case primary, compute per seed:
I_ws = (P_AR,ws-P_AC,ws) - (P_FR,ws-P_FC,ws);
average within window, then bootstrap the resulting paired window contrasts with 10,000 resamples, RNG 0. Do not combine four separately bootstrapped intervals. Apply mean >= +0.20 dB, lower descriptive 95% bound >0, and nonnegative mean in at least two of three chess pairs. Apply the same PSNR rule to A_R−A_C and A_R minus each mandatory practical control; require mean SSIM loss no worse than -0.01 against each. Report all pair means and SSIM intervals.

A positive I without these quality gains fails. If development passes but the case interaction fails while A_C−F_C and A_C−B2 succeed, report only the predeclared secondary composition result; do not promote it to a passed release primary. RGB-D, covered/uncovered metrics and SSIM remain secondary. No claim of memory benefit follows without a matched static-context comparison; no frame-metric result establishes temporal video quality.

### 3.6 Budget

**DERIVED from the proposed plan:** 256 development outputs plus 640 case outputs = 896 WGS outputs. Independent execution would use 22,400 denoiser calls. Shared C/R endpoints reduce this to 448 trajectories and 11,200 calls, with two endpoint decodes per trajectory. Ordinary A on monitors adds 64 full trajectories unless verified identical outputs already exist.

**MEASURED, archived:** the direct S141 evaluation receipt subset contains 512 timings with median 40.94 s (Appendix A2, S141/results/tacc/eval/*/RUNS_*.jsonl). These timers cover sample calls, not full process initialization or all preprocessing (S141/gen_s141.py:173–190,195–197). **DERIVED conservative proxy:** 896*40.94/3600 = 10.1895 GPU-hours if each WGS output were charged at that old full-trajectory rate; 448*40.94/3600 = 5.0948 for shared trajectories before extra decodes and controls. Neither is a measured WGS runtime or a rigorous upper bound.

A 12 GPU-hour cap is reasonable to pilot, not guaranteed. Include new CPU warp preparation in wall-clock feasibility, and all occupied GPU time in the GPU cap. Time complete backbone-paired cells and ordinary-A references, including setup/decoding, then project the complete remaining denominator. Do not consume the budget on a subset and retrospectively drop the difficult panel.

## 4. Corrected minimal S145 specification

### 4.1 Question and primary

Use the broad question: under B's completed, fixed LoRA, is the added branch harmful at inference, and which part accounts for that effect? **Primary: B_off−B_original. Key secondary: B_target_only−B_original.** This is a proposed amendment to D145:11, made before new results. Keeping target-only primary is defensible only with the narrower context-bias title/question.

Use the same fixed chess plan, CPU warps and seeds 3–6. The expected full B checkpoint hash is **0dd40c86ea928b74abfa992ba0738f61950bd97d5d26aaa3d0bc494487de1c56** (S141/results/tacc/eval/ADAPTER_CHECK_B.txt:1); inspect actual bytes before execution. Retain B's own LoRA in every branch arm. Require the S144-style identity checks for reused B_original and A; no new A checkpoint or training.

### 4.2 Exact branch algebra and layout

Let e be the five added channels; W(e) is the bias-free convolution term, b its learned bias, and g the explicit target-frame indicator. Keep the original base-convolution term and every B LoRA weight unchanged.

| Arm | Added contribution | What it isolates |
|---|---|---|
| B_original | W(e)+b | Existing recipe |
| B_target_only | g*(W(e)+b) | Removal of context-slot bias only at this layer |
| B_off | 0 | Entire branch contribution under B's fixed learned backbone |
| B_bias_only | b | Removal of both appearance- and coverage-dependent terms |
| B_permuted | W([perm(z_w),cov])+b | Sensitivity to spatial arrangement under the fixed corruption |

This decomposition follows S141/s141_common.py:97–106,157–163. On context slots e=0, so the original extra output is b. The target-only target-branch output is unchanged for the same layer input, but downstream activations and later sampling states must evolve naturally; freezing those would change the intervention.

For one clip use g=[0,0,0,0,1,1,1,1]. For packed CFG use the entire vector twice:
[0,0,0,0,1,1,1,1, 0,0,0,0,1,1,1,1].
Reshape to (rows,1,1,1), cast to the branch output dtype/device, and multiply **after** convolution. For separate c/uc probes, rows=8; for packed generation rows=16. The grouping remains num_frames=8. Derive g = ~cond['input_masks'] before CFG repetition: input_masks is true for contexts, whereas g is true for targets. Never derive it from the uc concat/replace channels, coverage, or image values (V/modeling/pipeline.py:1154–1172; V/modeling/sampling.py:265–276).

Call extend_concat once on c and once on uc **before** packing. In this layout concat contains seven original plus five added channels; VMemWrapper adds four noisy channels, so the wrapped convolution sees sixteen total (S141/s141_common.py:157–163; V/modeling/network.py:226–230). Calling the original helper on sixteen packed rows with only four warp rows would instead invent twelve context rows. Assert shapes and the exact rowwise equality of the added c/uc inputs.

B_off should bypass the contribution while retaining loaded B tensors; zeroing only inputs implements bias-only, not off. B_bias_only may use the unchanged convolution on an all-zero five-channel input. Avoid in-place changes to shared c/uc dictionaries, the checkpoint, or cached original warp tensors. Verify off/bias-only identities and row-gating on synthetic tensors before GPU generation.

### 4.3 Permutation and monitor probe

For each target frame, define coverage strata by k=round(64*cov), assert cov equals k/64, and permute spatial indices within each k stratum. This preserves the exact fractional-coverage category, not merely the >=0.5 WGS bin; coverage comes from pooling a binary mask over 8×8 cells (S141/gen_s141.py:180). Move the four-channel latent vectors together, do not permute channels independently, do not cross targets, and leave coverage/scoring masks fixed.

Use a private CPU NumPy Generator/PCG64 seeded by the first eight bytes, little-endian, of SHA-256 of the UTF-8 string "S145|145|window_id|target_ref", with the actual identifiers substituted. Generate one mapping per target, independent of generation seed. Freeze/store the mapping identity; use it identically in c/uc. Empty/singleton strata remain unchanged; report moved-cell fractions, since a nearly identity permutation is a weak sensitivity probe. This corruption is deliberately artificial, not an equal-quality alternative warp.

Teacher-forced probe: all fixed monitor clips, original GPU monitor warps for continuity with B's training diagnostics, sigma indices [50,200,400,600,800,950], and the original fixed noise convention seed=1000*clip_index+sigma_position (S141/train_s141.py:75–85). Probe:
- correct warp;
- all five extra input channels zero;
- zero latent with original coverage;
- per-target/per-exact-coverage-stratum mean latent, with original coverage;
- the fixed permutation.

Keep target, noise, sigma, conditioning and precision identical within each comparison. The mean control preserves coarse latent content within coverage groups while removing spatial detail; it is not another generated arm. Compute c and uc separately, then their actual configured guided prediction using the source guider and camera/mask inputs, rather than assuming one global CFG multiplier (V/modeling/sampling.py:194–220,265–299; V/configs/inference/inference.yaml:21–23).

At each sigma report target-only epsilon-MSE, output sensitivity versus the correct input, and **DERIVED** clean-latent MSE = sigma²*epsilon-MSE, using the actual discrete sigma and z_hat=x-sigma*epsilon_hat. This identity follows the noisy-target construction at S141/train_s141.py:61–68 and EpsScaling at V/modeling/sampling.py:79–87; it applies to this teacher-forced state, not to a rollout state with an unrelated original epsilon label. Report the rescaling as one metric in different units, not two independent confirmations.

The archived monitor prediction uses bf16 autocast (S141/train_s141.py:66), while generation uses the sampling path's autocast (V/utils/util.py:701). Freeze and record probe precision; do not interpret precision or GPU-monitor/CPU-case differences as ablation effects. Probe findings cannot select, delete or retune generation arms.

### 4.4 Decisions, budget and stop

Use paired seed means within the fixed windows, the same descriptive bootstrap, pair reporting and practical thresholds as §3.5. A positive primary shows that removing the total branch improves this particular B backbone. A positive target-only contrast supports harmful context bias in this trained recipe; it does not establish the sole cause of B's deficit. Compare any proposed useful repair with each distinct comparator among B_off, A and raw B2, with SSIM and region scores; B_off is not required to beat itself. A/B2 are practical references, not causal branch controls.

B_original better than B_permuted establishes sensitivity only. Bias-only near original does not prove ignored appearance, and a failed threshold does not prove equivalence. Removing B's branch cannot tell how its LoRA would have trained without that branch; an A-anchored retraining experiment is outside S145.

**DERIVED:** four new arms × 24 windows × four seeds = 384 full trajectories; the archived 40.94 s proxy gives 4.3669 GPU-hours before overhead. The corrected five-condition monitor probe needs 32×6×5×2 = 1,920 single-branch forwards; guided combinations can reuse those outputs. This is not 1,920 full rollouts. Replay, setup and scoring remain extra. If all B_original outputs must be regenerated, add 96 full trajectories to the projection. A six GPU-hour cap is plausible only after that accounting and a timing pilot; it is not a guaranteed fit.

Complete the frozen diagnosis once, regardless of monitor signs. Stop on invalid identities/nonfinite/missing cells or a projected budget overrun before the full run. Do not retrain, sweep branch strengths, change checkpoints, expand capacity or relabel missing cells as negative results.

## 5. Priority and conditions that would destroy interpretability

**Choose S144 first.** This is a research-priority judgment: it directly tests predictive value from the completed A adapter and the fixed geometry-guided recipe; S145 explains a failed B recipe and is not a prerequisite. The distinction is also explicit in R262:166–197,201–235. If S144 fails its frozen engineering/development gate, stop it. A separately complete S145 may then be a reasonable bounded use of remaining resources; an incomplete S144 factorial is not a substitute.

Neither experiment is interpretable if archival cells are paired by labels without verified inputs/weights; any branch changes sampler RNG unintentionally; CFG/frame masks are wrong; development alpha or masks are retuned on cases; monitor targets enter generation; missing cells are dropped selectively; or multiple implementations remain entangled with intervention labels. Correct pairing and a complete denominator matter more than a favorable mean.

A valid negative ends the tested hypothesis. A positive exposed-panel result remains a local recipe/diagnostic result and does not establish novel methods, memory benefit, fresh-scene generalization or temporal video quality. **new_method_validated=false; novelty_authorization=NONE.**

**Changed file:** work/agents/CODEX_R263_S144_S145_REJECTION.md only. **Next execution session:** implement/freeze corrected S144, verify actual remote asset identities and timing under that session's authorization, then run or stop by its gates; retain S145 as the specified bounded diagnosis. No repository test suite or linter was run because no executable project code was changed. The CPU checks below are explicitly narrower than model tests.

## Appendix A — Exact root CPU verification commands and complete outputs

All commands ran from the repository root, read-only. The broad receipt inventory includes nested archived copies; it is not a count of independent generations. A2 deliberately selects the direct evaluation subset used for the timing proxy. Current-file hashes, not historical summaries, ground this review.

### A1. Snapshot, inventory and budget arithmetic

~~~bash
python3 -B - <<'PY'
import json, hashlib, statistics, subprocess
from pathlib import Path
from collections import Counter
print('HEAD',subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
files = ['work/S144_A_wgs/PROTOCOL_DRAFT.md','work/S145_B_diagnosis/PROTOCOL_DRAFT.md','work/agents/CODEX_R262_IDEATION_AFTER_S141_RESULTS.md','work/S140_warp_guided/gen_s140.py','work/S141_finetune/gen_s141.py','work/S141_finetune/s141_common.py','work/S141_finetune/warps_s141.py','data/S134_tacc/vmem_src/modeling/sampling.py']
for f in files:
 print('SHA256',hashlib.sha256(Path(f).read_bytes()).hexdigest(),f)
for stage in ['S140_warp_guided','S141_finetune']:
 p=Path('work')/stage/'results'
 rows=[]
 for f in sorted(p.rglob('RUNS_*.jsonl')):
  for line in f.read_text().splitlines():
   x=json.loads(line); rows.append((str(f),x))
 print(stage,'receipts',len(rows),'prediction_npy',len(list(p.rglob('*.npy'))),'adapter_pt',len(list(p.rglob('adapter*.pt'))))
 groups={}
 for f,r in rows:
  label=(r.get('mode',r.get('variant','?')),r.get('strength'))
  groups.setdefault(str(label),[]).append(float(r['seconds']))
 for k,v in sorted(groups.items()): print('TIMING',stage,k,'n',len(v),'median',round(statistics.median(v),3),'max',max(v))
clips=json.loads(Path('work/S141_finetune/clips_s141.json').read_text())['clips']
v=[c for c in clips if c['split']=='val']
print('MONITOR',len(v),'first',v[0]['id'],'last',v[-1]['id'],'scene_counts',dict(Counter(c['scene'] for c in v)),'kind_counts',dict(Counter(c['kind'] for c in v)))
for f in ['work/S140_warp_guided/plan_confirm.json','work/S140_warp_guided/plan_dev.json','work/S141_finetune/plan_eval_B.json','work/S141_finetune/plan_eval_A.json']:
 c=json.loads(Path(f).read_text())['contexts']
 print('PLAN',f,'contexts',len(c),'windows',len({x['window_id'] for x in c}),'modes',dict(Counter(x['mode'] for x in c)))
full=40.94
for name,n in [('S144_dev_outputs',32*2*4),('S144_case_outputs',40*4*4),('S144_all_independent',32*2*4+40*4*4),('S144_rerun_without_chess_FC',32*2*4+40*4*4-24*4),('S144_shared_C_R_trajectories',2*(32*2+40*4)),('S145_new_generation',4*24*4)]:
 print('BUDGET',name,'n',n,'hours_at_40.94s',round(n*full/3600,4))
print('S145_probe_forwards',32*6*3*2,'50_step_CFG_full_equivalents',(32*6*3*2)/(50*2))
PY
~~~

Complete output (exit 0):

~~~text
HEAD 043edd3f7ae5d804d68bc59dfbc0530a0deb4214
SHA256 1cf803b9b9ed152a1371675b737aabdd587fe7cf99efefe5bc7e04096950160c work/S144_A_wgs/PROTOCOL_DRAFT.md
SHA256 78a498ce76540b3f1d313bac39886a9f08792f51023705ac0ffd8ba7112476c6 work/S145_B_diagnosis/PROTOCOL_DRAFT.md
SHA256 2fdfe437d72a231b1a3f82095c03238d8a8687296318d67233924040c8b7ecc5 work/agents/CODEX_R262_IDEATION_AFTER_S141_RESULTS.md
SHA256 119904b368eefe4f7bd99e1aed0ba91d7a9250aad5e97a0fb298d7007c0a46c9 work/S140_warp_guided/gen_s140.py
SHA256 c903be28ffea8c359c79d927ebdcf782e1d9ac21b81d0b159439e1566fac8121 work/S141_finetune/gen_s141.py
SHA256 459549706fb3a965fc4f7c5021f4d49cc626158e94a7c9cdc94cf8784cccb6cc work/S141_finetune/s141_common.py
SHA256 72d8f66fb4439ef3cf626d973a594b182bf30b04d89cb0af221c1208fb048470 work/S141_finetune/warps_s141.py
SHA256 dc07ca0ba571ba5fb48f9856515d2cb7dea25254008a6f8b315538817f352b24 data/S134_tacc/vmem_src/modeling/sampling.py
S140_warp_guided receipts 0 prediction_npy 0 adapter_pt 0
S141_finetune receipts 802 prediction_npy 0 adapter_pt 0
TIMING S141_finetune ('A', None) n 449 median 41.14 max 44.33
TIMING S141_finetune ('B', None) n 353 median 38.42 max 42.13
MONITOR 32 first c02000 last c02031 scene_counts {'office': 16, 'redkitchen': 16} kind_counts {'memory': 23, 'static': 9}
PLAN work/S140_warp_guided/plan_confirm.json contexts 24 windows 24 modes {'W2': 24}
PLAN work/S140_warp_guided/plan_dev.json contexts 98 windows 16 modes {'W1': 48, 'W2': 32, 'W3': 16, 'ref': 1, 'none': 1}
PLAN work/S141_finetune/plan_eval_B.json contexts 24 windows 24 modes {'B_mem': 24}
PLAN work/S141_finetune/plan_eval_A.json contexts 48 windows 24 modes {'A_static': 24, 'A_mem': 24}
BUDGET S144_dev_outputs n 256 hours_at_40.94s 2.9113
BUDGET S144_case_outputs n 640 hours_at_40.94s 7.2782
BUDGET S144_all_independent n 896 hours_at_40.94s 10.1895
BUDGET S144_rerun_without_chess_FC n 800 hours_at_40.94s 9.0978
BUDGET S144_shared_C_R_trajectories n 448 hours_at_40.94s 5.0948
BUDGET S145_new_generation n 384 hours_at_40.94s 4.3669
S145_probe_forwards 1152 50_step_CFG_full_equivalents 11.52
~~~

### A2. Exact timing subset, adapter receipt and plan/input inventory

~~~bash
python3 -B - <<'PY'
import json, statistics, hashlib
from pathlib import Path
p=Path('work/S141_finetune/results/tacc/eval')
rows=[json.loads(l) for f in sorted(p.glob('*/RUNS_*.jsonl')) for l in f.read_text().splitlines()]
print('S141_eval_timing_receipts',len(rows),'median_seconds',statistics.median(r['seconds'] for r in rows))
for f in sorted(Path('work/S141_finetune/results').rglob('ADAPTER_CHECK_B.txt')):
 print('B_CHECK',str(f),f.read_text().strip())
J=lambda f: json.loads(Path(f).read_text())['contexts']
fields=('scene_dir','convention','ctx_refs','target_refs','warp_files')
s140={c['window_id']:c for c in J('work/S140_warp_guided/plan_confirm.json')}
s141={c['window_id']:c for c in J('work/S141_finetune/plan_eval_B.json')}
diff=[(w,k) for w in sorted(s140) for k in fields if s140[w].get(k)!=s141[w].get(k)]
print('chess_S140_S141_B_same_inputs',len(s140)==len(s141)==24 and not diff,'diff',diff)
root=Path('data')
for pat in ('S140*','S141*'):
 for d in sorted(root.glob(pat)):
  print('LOCAL_ASSET',str(d),'npz',len(list(d.rglob('*.npz'))),'pt',len(list(d.rglob('*.pt'))))
s=J('work/S140_warp_guided/plan_dev.json')
print('S140_dev_W2_half_contexts',sum(c['mode']=='W2' and c['strength']==0.5 for c in s))
print('S140_confirm_seeds', sorted({r['seed'] for r in json.loads(Path('work/S140_warp_guided/results/confirm_tacc/S140_SCORES_confirm_tacc.json').read_text())['runs'].values()}))
PY
~~~

Complete output (exit 0):

~~~text
S141_eval_timing_receipts 512 median_seconds 40.94
B_CHECK work/S141_finetune/results/tacc/eval/ADAPTER_CHECK_B.txt adapter /mnt/gluster_dcpu/yiyangliu/gwm_s141/runs/B/adapter_final.pt variant B step 10000 lora_tensors 512 warp_tensors 2 up_norm 17.1854 sha256 0dd40c86ea928b74abfa992ba0738f61950bd97d5d26aaa3d0bc494487de1c56 -> OK
chess_S140_S141_B_same_inputs True diff []
LOCAL_ASSET data/S140_warps_chess npz 96 pt 0
LOCAL_ASSET data/S140_warps_dev npz 64 pt 0
LOCAL_ASSET data/S141_warps_chess_static npz 96 pt 0
S140_dev_W2_half_contexts 16
S140_confirm_seeds [3, 4, 5, 6]
~~~

## Appendix B — Delegated read-only synthetic sampler probe

The sampler-audit sub-agent executed this exact command from the same checkout and returned the complete output below. It extracts the actual Euler step and WGS loop, but substitutes scalar fake tensors, a synthetic sigma schedule and Python RNG. It checks control flow and arithmetic only; it does not exercise actual conditioning, CUDA RNG streams, VAE decoding or model kernels.

~~~bash
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import ast, copy, math, random
from pathlib import Path
root=Path('.')
class V:
    dtype='float'
    def __init__(self,x): self.v=list(x)
    def __getitem__(self,k): return V(self.v[k]) if isinstance(k,slice) else self.v[k]
    def __setitem__(self,k,v): self.v[k]=v.v if isinstance(v,V) else v
    def op(self,o,f): return V(f(a,b) for a,b in zip(self.v,o.v if isinstance(o,V) else [o]*len(self.v)))
    def __add__(self,o): return self.op(o,lambda a,b:a+b)
    __radd__=__add__
    def __sub__(self,o): return self.op(o,lambda a,b:a-b)
    def __rsub__(self,o): return self.op(o,lambda a,b:b-a)
    def __mul__(self,o): return self.op(o,lambda a,b:a*b)
    __rmul__=__mul__
    def __truediv__(self,o): return self.op(o,lambda a,b:a/b)
    def to(self,dtype): return self
    @property
    def ndim(self): return 1
class T:
    def __init__(self): self.r=random.Random(3); self.draws=[]
    def randn_like(self,x):
        self.draws.append(len(x.v)); return V(self.r.gauss(0,1) for _ in x.v)
class G:
    def prepare_inputs(self,x,s,c,uc): return x,s,c
    def __call__(self,d,s,scale,**kw): return d
src=ast.parse((root/'data/S134_tacc/vmem_src/modeling/sampling.py').read_text())
cls=next(n for n in src.body if isinstance(n,ast.ClassDef) and n.name=='EulerEDMSampler')
step=copy.deepcopy(next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='sampler_step'))
for a in step.args.args+step.args.kwonlyargs: a.annotation=None
step.returns=None
body=ast.parse((root/'work/S140_warp_guided/gen_s140.py').read_text())
sample=next(n for n in body.body if isinstance(n,ast.FunctionDef) and n.name=='sample_wgs')
loop=copy.deepcopy(next(n for n in ast.walk(sample) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='i'))
released=copy.deepcopy(loop)
assignment=released.body[1].body[1]
released.body[1].body[1]=ast.If(test=ast.parse('i != len(sigmas) - 2',mode='eval').body,body=[assignment],orelse=[])
def run(release):
    torch=T(); trace=[]
    ns={'torch':torch,'append_dims':lambda x,n:x,'to_d':lambda x,s,d:(x-d)/s}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[step],type_ignores=[])),'source_sampler_step','exec'),ns)
    class S:
        s_noise=1.; guider=G()
        def sampler_step(self,*a,**kw):
            out=ns['sampler_step'](self,*a,**kw); trace.append(out.v[:]); return out
    sigmas=[(50-i)/50 for i in range(51)] # synthetic schedule; actual loop/step source
    x=torch.randn_like(V([0.]*8))*sigmas[25]; zw=V([.2,.3,.4,.5]); x[4:]=x[4:]+zw
    ns.update(x=x,zw=zw,m2=V([1.,0.,1.,0.]),sigmas=sigmas,k=25,s_in=1.,sampler=S(),fn=lambda x,s,c:x*.6+.07,CFG=2.,c={},uc={},kw={},mode='W2')
    exec(compile(ast.fix_missing_locations(ast.Module(body=[released if release else loop],type_ignores=[])),'source_wgs_loop','exec'),ns)
    return ns['x'].v,trace,torch.draws,torch.r.getstate()
C,tc,dc,rc=run(False); R,tr,dr,rr=run(True)
print('CPU arithmetic/control-flow probe; stdlib fake tensors/RNG, not Torch/CUDA fidelity')
print('denoiser_calls_each',len(tc),'step_indices',list(range(25,50)))
print('draw_shapes_each',dc)
print('identical_pre_overwrite_sampler_outputs',tc==tr)
print('identical_draws_and_final_rng_state',dc==dr and rc==rr)
print('contexts_and_uncovered_targets_identical',all(C[i]==R[i] for i in [0,1,2,3,5,7]))
print('covered_targets_clamped_exactly',C[4]==.2 and C[6]==.4)
print('covered_targets_released_differ',R[4]!=C[4] and R[6]!=C[6])
print('gamma_zero_sigma_hat_delta_at_sigma_0.02',(0.02*(0.0+1.0)+1e-6)-0.02)
PY
~~~

Complete output:

~~~text
CPU arithmetic/control-flow probe; stdlib fake tensors/RNG, not Torch/CUDA fidelity
denoiser_calls_each 25 step_indices [25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49]
draw_shapes_each [8, 8, 4, 8, 4, 8, 4, 8, 4, 8, 4, 8, 4, 8, 4, 8, 4, 8, 4, 8, 4, 8, 4, 8, 4, 8, 4, 8, 4, 8, 4, 8, 4, 8, 4, 8, 4, 8, 4, 8, 4, 8, 4, 8, 4, 8, 4, 8, 4, 8, 4]
identical_pre_overwrite_sampler_outputs True
identical_draws_and_final_rng_state True
contexts_and_uncovered_targets_identical True
covered_targets_clamped_exactly True
covered_targets_released_differ True
gamma_zero_sigma_hat_delta_at_sigma_0.02 1.000000000001e-06
~~~

## Appendix C — Delegated read-only monitor overlap inventory

The controls-audit sub-agent executed this command from the same checkout. This is manifest evidence, not an assertion about unseen remote data.

~~~bash
python3 - <<'PY'
import json, collections
from pathlib import Path
p=Path('work/S141_finetune/clips_s141.json')
c=json.loads(p.read_text())['clips']
t=[x for x in c if x['split']=='train']; v=[x for x in c if x['split']=='val']
train_refs={r for x in t for r in x['ctx']+x['tgt']}
vt=[r for x in v for r in x['tgt']]
vc=[r for x in v for r in x['ctx']]
print('monitor_count',len(v))
print('monitor_ids',v[0]['id'],v[-1]['id'])
print('monitor_sequences',dict(sorted(collections.Counter(x['scene']+'/'+x['C'] for x in v).items())))
print('monitor_kinds',dict(sorted(collections.Counter(x['kind'] for x in v).items())))
print('unique_target_frames',len(set(vt)),'target_slots',len(vt))
print('monitor_targets_in_any_training_slot',len(set(vt)&train_refs))
print('monitor_context_refs_in_training',len(set(vc)&train_refs),'unique_context_refs',len(set(vc)))
print('exact_duplicate_clip_inputs',len(v)-len({tuple(x['ctx']+x['tgt']) for x in v}))
print('shared_target_clip_pairs',sum(bool(set(a['tgt'])&set(b['tgt'])) for i,a in enumerate(v) for b in v[i+1:]))
for pp in ['work/S140_warp_guided/plan_confirm.json','work/S140_warp_guided/plan_dev.json']:
 d=json.loads(Path(pp).read_text())['contexts']; wins={x['window_id']:x for x in d}; rr=[r for x in wins.values() for r in [x['scene_dir']+'/'+r for r in x['target_refs']]]
 print(pp,'contexts',len(d),'windows',len(wins),'unique_target_frames',len(set(rr)),'target_slots',len(rr))
PY
~~~

Complete output:

~~~text
monitor_count 32
monitor_ids c02000 c02031
monitor_sequences {'office/seq-10': 16, 'redkitchen/seq-14': 16}
monitor_kinds {'memory': 23, 'static': 9}
unique_target_frames 105 target_slots 128
monitor_targets_in_any_training_slot 0
monitor_context_refs_in_training 59 unique_context_refs 113
exact_duplicate_clip_inputs 0
shared_target_clip_pairs 12
work/S140_warp_guided/plan_confirm.json contexts 24 windows 24 unique_target_frames 96 target_slots 96
work/S140_warp_guided/plan_dev.json contexts 98 windows 16 unique_target_frames 64 target_slots 64
~~~

## Appendix D — Final document/source integrity check

This check ran after the substantive corrections and before appending this receipt. It verifies citation path/range existence, unchanged inspected sources, English-only text, balanced fences and the concurrent checkout state; it does not validate scientific outcomes. Pre-existing untracked files were left untouched.

~~~bash
python3 -B - <<'PY'
from pathlib import Path
import re, hashlib, subprocess
p=Path('work/agents/CODEX_R263_S144_S145_REJECTION.md')
t=p.read_text()
aliases={'S140':'work/S140_warp_guided','S141':'work/S141_finetune','V':'data/S134_tacc/vmem_src'}
bad=[]
refs=re.findall(r'\b(S140|S141|V)/([A-Za-z0-9_./-]+):(\d+)(?:[–-](\d+))?',t)
for a,f,lo,hi in refs:
 q=Path(aliases[a])/f
 if not q.exists() or int(hi or lo)>len(q.read_text().splitlines()):
  bad.append((str(q),lo,hi))
expected={
'work/S144_A_wgs/PROTOCOL_DRAFT.md':'1cf803b9b9ed152a1371675b737aabdd587fe7cf99efefe5bc7e04096950160c',
'work/S145_B_diagnosis/PROTOCOL_DRAFT.md':'78a498ce76540b3f1d313bac39886a9f08792f51023705ac0ffd8ba7112476c6',
'work/agents/CODEX_R262_IDEATION_AFTER_S141_RESULTS.md':'2fdfe437d72a231b1a3f82095c03238d8a8687296318d67233924040c8b7ecc5',
'work/S140_warp_guided/gen_s140.py':'119904b368eefe4f7bd99e1aed0ba91d7a9250aad5e97a0fb298d7007c0a46c9',
'work/S141_finetune/gen_s141.py':'c903be28ffea8c359c79d927ebdcf782e1d9ac21b81d0b159439e1566fac8121',
'work/S141_finetune/s141_common.py':'459549706fb3a965fc4f7c5021f4d49cc626158e94a7c9cdc94cf8784cccb6cc',
'work/S141_finetune/warps_s141.py':'72d8f66fb4439ef3cf626d973a594b182bf30b04d89cb0af221c1208fb048470',
'data/S134_tacc/vmem_src/modeling/sampling.py':'dc07ca0ba571ba5fb48f9856515d2cb7dea25254008a6f8b315538817f352b24'}
print('output_exists',p.exists())
print('source_file_line_citations_checked',len(refs))
print('invalid_citation_paths_or_ranges',bad)
print('source_hash_drift',[f for f,h in expected.items() if hashlib.sha256(Path(f).read_bytes()).hexdigest()!=h])
print('fences_balanced',len(re.findall(r'^~~~',t,re.M))%2==0)
print('cjk_characters',len(re.findall(r'[\u4e00-\u9fff]',t)))
print('tracked_diff_paths',subprocess.check_output(['git','diff','--name-only'],text=True).splitlines())
print('git_status_begin')
print(subprocess.check_output(['git','status','--short'],text=True),end='')
print('git_status_end')
PY
~~~

Complete output (exit 0):

~~~text
output_exists True
source_file_line_citations_checked 71
invalid_citation_paths_or_ranges []
source_hash_drift []
fences_balanced True
cjk_characters 0
tracked_diff_paths []
git_status_begin
?? work/S144_A_wgs/
?? work/S145_B_diagnosis/
?? work/agents/CODEX_R262_IDEATION_AFTER_S141_RESULTS.md
?? work/agents/CODEX_R263_S144_S145_REJECTION.md
?? work/agents/prompts/R262_FULL.md
?? work/agents/prompts/R263_FULL.md
?? work/agents/prompts/R263_PROMPT.md
git_status_end
~~~
