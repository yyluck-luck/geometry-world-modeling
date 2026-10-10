# R254 — Hostile review of S141 before evaluation

| issue | severity | evidence file:line | fix | fixable before evaluation without a protocol change? |
|---|---|---|---|---|
| F1. Fidelity hashes are printed, never compared; evaluation does not depend on a fidelity pass. | blocker | `work/S141_finetune/s141_chainB.sh:6-11`; `work/S141_finetune/s141_chainEval.sh:5-8`; required by `work/S141_finetune/PROTOCOL.md:38-39` | Require actual base/A/B byte equality and a checked receipt before either evaluation starts. | yes |
| F2. Final-checkpoint existence is mistaken for completion; the stored training step is unchecked. | blocker | `work/S141_finetune/train_s141.py:135-136`; `work/S141_finetune/s141_chainEval.sh:5-8`; `work/S141_finetune/gen_s141.py:119-124` | Publish atomically or require a completion receipt; verify step 10000, variant/rank, finite tensors and digest. | yes |
| F3. Outer chains mask failures; resumable generation can silently reuse stale predictions. | major | `work/S141_finetune/s141_chainB.sh:1-11`; `work/S141_finetune/s141_chainEval.sh:1-13`; `work/S141_finetune/gen_s141.py:164-165,192-195` | Propagate subprocess/pipeline failures and preserve full logs. Validate existing output bytes and receipts against the final adapter, source, configuration and plan before skipping. | yes |
| F4. Nonfinite model output can become finite black pixels and receive ordinary scores. | blocker | `work/S141_finetune/gen_s141.py:190-195`; `work/S140_warp_guided/score_s140.py:15-18,30-45`; Appendix B | Assert expected shape, finite values and declared image range before saving and before scoring. Preserve numerical failures as failures. | yes |
| F5. Analyzer pairing and self-audit completeness checks are insufficient. | major | `work/S141_finetune/analyze_s141.py:18-25,42`; `work/S141_finetune/self_audit_s141.py:20-34,50-52`; Appendix B | Require exact unique plan/arm/window/seed cells, identical paired keys, finite metrics, and explicit step/count checks; exit nonzero on any failure. | yes |
| F6. `NO_MATERIAL_CHANGE` is not equivalence; its CI can allow large effects. | major | `work/S141_finetune/analyze_s141.py:28-29`; `work/S141_finetune/PROTOCOL.md:59,64`; Appendix B | Preserve the registered rule but qualify its interpretation. Replacing it with an equivalence rule requires an amendment. | no |
| F7. Training matches denoiser wiring, not the evolving unconditional context-state distribution; context scores have no direct training loss. | major | `work/S141_finetune/train_s141.py:58,61-68,117-119`; `data/S134_tacc/vmem_src/modeling/sampling.py:174-185,393-402` | Disclose the limitation and collect non-intervening state diagnostics. Adding context loss or reclamping states changes the method. | no |
| F8. bf16 training does not establish fp16 stability; algebraic zero initialization does not establish GPU byte equality. | major | `work/S141_finetune/train_s141.py:66-67`; `data/S134_tacc/vmem_src/utils/util.py:701-733`; `work/S141_finetune/s141_common.py:82-106`; Appendices C–D | Enforce the existing GPU fidelity gate and check final-adapter/output finiteness. Do not silently change inference precision or relax equality. | yes |
| F9. Training memory selection is S139 `mem_pose`, while primary evaluation uses `mem_vmem`. | major | `work/S141_finetune/build_clips_s141.py:26-40,57-63`; `work/S139_crossseq_revisit/pose_arms_s139.py:25-51`; `work/S139_crossseq_revisit/build_plan_s139.py:11-13`; `work/S141_finetune/build_eval_plan_s141.py:11-24` | Report the mismatch. Matching the training retrieval producer requires retraining; an added mem_pose evaluation is exploratory. | no |
| F10. GPU-training/CPU-evaluation warp agreement is not established by three rounded comparisons from one pair. | major | `work/S141_finetune/PROTOCOL.md:27-31`; `work/S141_finetune/warpcheck_clips.json:8,32,56`; `work/S141_finetune/warpcheck_compare.py:7-12` | Preserve frozen CPU evaluation warps; archive exact masks, pixel/latent discrepancies and producer provenance. Removing the incurred training mismatch requires another run. | no |
| F11. Historical base comparison needs artifact/runtime parity, which local launch receipts do not establish. | major | `work/S141_finetune/tacc_s141.sh:13,17-19`; `work/S141_finetune/gen_s141.py:192-194`; `work/S139_crossseq_revisit/gen_s139.py:109-127,161-165` | Verify base/VAE/CLIP/source/config/data/warp/output hashes and runtime, enforce fidelity, and use the same scorer. Mark unavailable historical provenance as unavailable. | yes |
| F12. Window bootstrap and previously exposed chess do not support untouched, independent scene-level confirmation. | major | `work/S139_crossseq_revisit/PROTOCOL.md:17-22,41-42`; `work/S141_finetune/PROTOCOL.md:8-20,51-59` | Keep registered window analysis; report pair effects and descriptive sensitivity. New independent confirmation needs a new panel/protocol. | no |
| F13. Positive A/B results do not isolate domain gap, learned memory use, geometric reasoning or novelty. | major | `work/S141_finetune/PROTOCOL.md:12-15,54-64`; `work/S141_finetune/analyze_s141.py:45-51` | Restrict claims to the tested adaptation/pipeline. Mechanism-isolating and matched-capacity controls need separately labeled experiments. | no |
| F14. B's “unconditional” branch retains image-derived warp evidence; a learned convolution bias also affects context slots. | minor | `work/S141_finetune/s141_common.py:97-106,157-164`; `work/S141_finetune/train_s141.py:71-72,117`; `work/S141_finetune/gen_s141.py:145-147` | Describe actual CFG conditioning; do not claim warp cancellation or a target-only learned branch. Changing dropout/guidance/bias now changes the method. | no |
| F15. Neither nominal steps nor conditional monitor loss establishes an adequately optimized scientific negative. | major | `work/S141_finetune/train_s141.py:21,75-85,110-136`; `work/S141_finetune/PROTOCOL.md:43-49,64,69-70` | Verify actual completion and health, report sigma-resolved curves and one-run scope. Stronger adequacy/capacity conclusions need new controls. | no |
| F16. RGB-D secondary plans/scoring exist, but this analyzer does not implement their contrasts. | major | `work/S141_finetune/build_rgbd_plan_s141.py:13-23`; `work/S141_finetune/s141_chainEval.sh:9-12`; `work/S141_finetune/analyze_s141.py:35-65` | Complete the already specified secondary analysis with matched baseline scoring and exposed-panel labeling before inspecting results. | yes |
| F17. Clip digest prefix, distinct-example accounting and monitor-input scope need correction. | minor | `work/S141_finetune/PROTOCOL.md:24-26`; `work/S141_finetune/build_clips_s141.py:43-71`; Appendices A–B | Record the full correct digest, duplicate entries and held-out-target-sequence scope; retain the frozen list. | yes |

“yes” means the stated engineering safeguard or reporting completion preserves the frozen scientific comparison. “no” means removing the underlying limitation or establishing the stronger claim requires an amendment/new experiment. Disclosure is always possible. No implementation fixes were made in this review.

## Verdict and evidence boundary

**Do not release a confirmatory S141 verdict through the current evaluation chain.** Enforce F1–F5 and establish F11 first. The recipe remains a useful, narrowly scoped adaptation experiment; the strong causal interpretations in its Decision section are not identified by this design.

The evidence does **not** support rejecting S141 for a wrong epsilon sign, an omitted log-SNR shift, a reversed channel order, missed named attention adapters, or chess/RGB-D frames in the supplied training manifest. Those accusations would be incorrect. The strongest objections concern unenforced evaluation contracts, unsafe scoring, statistical interpretation, and training/evaluation/claim mismatches.

The local protocol bytes match commit `7cefe20ede81597b32517b49a9f0bbdf35278b10` [MEASURED, Appendix A]. This verifies the local frozen text, not remote training start time or executed bytes. Training progress, final adapter contents, GPU fidelity, actual GPU warpcheck arrays, and remote runtime provenance remain **UNVERIFIED here**. No GPU work, training job, weight/dataset download, SSH, Slurm submission or external communication was performed. CPU checks used source-function extraction or reduced random models without model weights; exact commands and complete outputs appear below.

The working tree contained concurrent changes, including the modified TACC wrapper and untracked chain/RGB-D/self-audit files. These were reviewed as local working-tree evidence, not assumed to belong to the frozen commit. They were left untouched. Snapshot digests identify central reviewed files in Appendix A. Only this report was authored; research ledgers and status flags were not modified.

## 1. Objective versus sampler

### Correct parameterization and conditioning

Training forms `x = z + sigma * eps`, replaces conditional context slots, scales the result and minimizes epsilon MSE on targets (`work/S141_finetune/train_s141.py:61-68,117-119`). The pinned denoiser has `c_skip=1`, `c_out=-sigma`, `c_in=1/sqrt(1+sigma**2)`, and passes a discrete index after sigma quantization (`data/S134_tacc/vmem_src/modeling/sampling.py:79-87,154-185`). Therefore, for target slots,

\[
D_\theta=x-\sigma\widehat\epsilon,\qquad D_\theta-z=\sigma(\epsilon-\widehat\epsilon).
\]

**ANALYTICAL:** the epsilon target and sign are correct; epsilon MSE is denoised-latent squared error weighted by `1/sigma**2`. It is not image-space PSNR optimization. Training manually reconstructs the denoiser input instead of literally calling `den(...)` in `eps_pred`; “compatible with the pinned inference parameterization” is more accurate than claiming the original VMem training objective has been reproduced.

`get_cond` creates conditional replacement as four clean context latents with a mask and zero target replacements, with zero replacement for uc. Concat is **input mask, six Plücker channels**; conditional cross-attention is mean context CLIP embedding repeated across cameras, while uc cross-attention is zero; dense conditioning is Plücker in both branches (`data/S134_tacc/vmem_src/modeling/pipeline.py:1124-1185`). Training calls this same function through `build_cond` (`work/S141_finetune/s141_common.py:146-154`). The wrapper prepends the scaled latent, giving **latent(4), mask(1), Plücker(6)**, and forwards cross/dense conditioning (`data/S134_tacc/vmem_src/modeling/network.py:226-235`). B appends **warp latent(4), coverage(1)** afterward (`work/S141_finetune/s141_common.py:157-164`).

Training passes `num_frames=8` (`work/S141_finetune/train_s141.py:58,67`). CFG batches **uc then c**, retaining eight-frame grouping rather than mixing a single sixteen-frame sequence (`data/S134_tacc/vmem_src/modeling/sampling.py:265-276`; `data/S134_tacc/vmem_src/utils/util.py:703-722`; grouping at `data/S134_tacc/vmem_src/modeling/modules/transformer.py:146-155`). Separate training passes versus batched inference are semantically compatible, not necessarily bit-identical kernel executions.

### Context state: matching replacement is not matching the entire trajectory

Conditional contexts are replaced before scaling, so “clean” does not mean unscaled. Unconditional contexts in training are freshly drawn as real `z_ctx + sigma * eps` (`work/S141_finetune/train_s141.py:58,63-67`). Sampling instead feeds the persistent context state of its Euler trajectory, initialized from noise and updated repeatedly (`data/S134_tacc/vmem_src/modeling/sampling.py:359-368,393-402,422-438`). It never resets that state to a fresh forward-noised real context.

Let `X` be a context slot's persistent state and `sigma_q` its quantized denoiser sigma. The code implies

\[
D_c=z_{ctx}-\sigma_q e_c,\quad D_u=X-\sigma_q e_u,
\]
\[
D_g=gz_{ctx}+(1-g)X-\sigma_q[ge_c+(1-g)e_u].
\]

This is derived from replacement and CFG (`data/S134_tacc/vmem_src/modeling/sampling.py:174-185,238-247,295-298`). The context self-match normally uses the configured minimum guidance of 1.2 (`data/S134_tacc/vmem_src/modeling/sampling.py:205-218`; `data/S134_tacc/vmem_src/configs/inference/inference.yaml:20-23`). Its guided score changes persistent context state, which later uc passes consume.

S141 directly supervises only target outputs (`work/S141_finetune/train_s141.py:119`). Shared adapters can thus alter context scores without direct context-output loss. This is a plausible adaptation/trajectory limitation, **not a measured failure** and not proof that ordinary forward-noise training is invalid. It prevents treating a null result as a clean architecture-capacity test. Adding context loss or clamping states at evaluation would change the frozen method; retain the current recipe and disclose the limitation.

### Sigma schedule: no missing shift

Both paths instantiate the same default `DDPMDiscretization()` (`work/S141_finetune/train_s141.py:47`; `work/S141_finetune/gen_s141.py:148-150`). Its `log_snr_shift=2.4` is implemented by multiplying sigma by `exp(2.4)` (`data/S134_tacc/vmem_src/modeling/sampling.py:90-123`). Do not substitute an assumed log-SNR formula for that implementation.

Uniform training indices over the dense table and inference visiting a fifty-point timestep subset differ in sampling/weighting, but belong to the same shifted sigma family (`work/S141_finetune/train_s141.py:118`; `data/S134_tacc/vmem_src/modeling/sampling.py:73-76,110-123`). Appendix C confirms the nominal inference sigmas are exact table entries [MEASURED CPU]. Euler adds a small offset before denoiser quantization (`data/S134_tacc/vmem_src/modeling/sampling.py:393-398`). There is no evidence here that uniform-index sampling is itself an error or a demonstrated cause of failure. The original pretrained model's training distribution was not established by these inference files.

## 2. Numerics, checkpointing and adapters

`ckpt_forward` preserves time embedding, block order, skip concatenation, dense/cross conditioning, frame count and final cast (`work/S141_finetune/s141_common.py:129-142` versus `data/S134_tacc/vmem_src/modeling/network.py:178-218`). The non-reentrant checkpoint arguments match `TimestepEmbedSequential.forward` (`data/S134_tacc/vmem_src/modeling/modules/layers.py:67-84`). Reduced-model CPU outputs and adapter gradients matched exactly in Appendix C [MEASURED]; this does not validate the full weighted CUDA execution.

Every instantiated pinned `Attention` receives q/k/v/output LoRA, including ordinary and TimeMix attention (`work/S141_finetune/s141_common.py:109-122`; `data/S134_tacc/vmem_src/modeling/modules/transformer.py:53-57,88-102,127-141`). This is not adaptation of every linear/convolutional layer or of the VAE/geometry producer. Default network and attention dropout are zero; not toggling validation to eval is not an observed dropout bug under these defaults (`data/S134_tacc/vmem_src/modeling/network.py:32`; `data/S134_tacc/vmem_src/modeling/modules/transformer.py:45,85,121,179`).

LoRA up matrices and B convolution weights/bias begin at zero (`work/S141_finetune/s141_common.py:82-106`). They are algebraically null for finite inputs. That does not promise byte equality across changed layouts/freezing/kernel dispatch. Appendices C–D demonstrate small CPU differences for a reduced baseline whose parameters remain trainable versus the frozen/adapted version, disappearing when the baseline is also frozen [MEASURED synthetic]. This is **not** proof the RTX 3090 gate fails or a diagnosis of its CUDA kernels. It establishes why the actual prescribed gate must run.

Training explicitly uses bf16 autocast, whereas `do_sample` invokes CUDA autocast without a dtype, ordinarily fp16, and decodes within it (`work/S141_finetune/train_s141.py:66-67`; `data/S134_tacc/vmem_src/utils/util.py:701-733`). Log the actual runtime dtype. Finite bf16 losses do not establish finite fp16 sampling. The current scorer can hide nonfinite predictions through uint8 casting [MEASURED, Appendix B]. Enforce finite checks rather than changing precision after observing bad scores.

The fidelity check covers zero adaptation and the inference refactor. It does not establish backward correctness, actual trained-adapter loading, final-step identity, or learned B stability. Its plans contain one memory context, and the chain uses seed 3 (`work/S141_finetune/build_eval_plan_s141.py:25-26`; `work/S141_finetune/s141_chainB.sh:7`). Keep that required sentinel and add representative static/memory numerical checks if feasible. Do not silently relax the frozen byte-equality requirement after a mismatch.

## 3. Variant B and warp mismatch

For target slots, where replacement is absent, B's guided epsilon is

\[
e_g=e_u(x,pose,w)+s[e_c(x,RGBctx,pose,w)-e_u(x,pose,w)].
\]

An exactly shared additive warp response survives with coefficient one; nonlinear warp/context interactions may enter the difference. The warp neither cancels nor is necessarily amplified wholesale by two. Training and evaluation consistently retain it in c and uc (`work/S141_finetune/train_s141.py:71-72,117`; `work/S141_finetune/gen_s141.py:145-147`; combination at `data/S134_tacc/vmem_src/modeling/sampling.py:247`). “Unconditional” means RGB-context-dropped **given warp and pose**. It changes the information being guided relative to A, but does not invalidate B-versus-B2 as a full-predictor comparison.

The distinction has a direct precedent: **arXiv:2302.05543, “Adding Conditional Control to Text-to-Image Diffusion Models,” §3.4**, discusses conditioning both CFG branches versus only the conditional branch. Its no-text example does not imply all S141 guidance cancels: S141 still differs in replacement, masks and CLIP. [Verified primary source](https://arxiv.org/html/2302.05543v3#S3.SS4).

B's added convolution has a trainable bias. Zero context extra channels can still produce a learned context feature offset (`work/S141_finetune/s141_common.py:102-106,161-163`; synthetic demonstration in Appendix D). This obeys the literal promise of zero context **inputs**, but B is not a strictly target-only learned modification. Do not remove its bias at evaluation.

Warp production reads context RGB and target poses, not target RGB (`work/S141_finetune/warps_s141.py:79-90`). It uses corrected depth mapping, nearest-filled splats, VAE encoding and pooled coverage (`work/S141_finetune/warps_s141.py:38-66,89-97`); evaluation encodes the saved filled images/masks equivalently (`work/S141_finetune/gen_s141.py:177-182`). VAE encoding uses the posterior mean, not a random posterior sample (`data/S134_tacc/vmem_src/modeling/modules/autoencoder.py:21-35`), so caching is not inherently a frozen-random-sample problem.

The real 28–42 dB GPU/CPU comparison remains **UNVERIFIED here**, asserted by `work/S141_finetune/PROTOCOL.md:29-31`. The checker prints four-decimal mask agreement without asserting equality, and all check windows belong to the same sequence pair (`work/S141_finetune/warpcheck_compare.py:7-12`; `work/S141_finetune/warpcheck_clips.json:8,32,56`). Rounded 1.0000 alone cannot prove identical masks. Pixel closeness cannot bound downstream nonlinear latent/model response.

There is also a producer precision difference: S141 rounds poses to float32 before float64 splatting, whereas S139's splat reloads float64 poses (`work/S141_finetune/s141_common.py:64-65`; `work/S141_finetune/warps_s141.py:80,84-88`; `work/S139_crossseq_revisit/baselines_s139.py:22-24,54-60`). Thus this is an implementation/backend comparison, not an isolated device-only experiment. Preserve the frozen CPU evaluation warps. An alternative GPU-warp arm is a labeled sensitivity check, not a replacement primary chosen from observed scores.

## 4. Splits and memory construction

**MEASURED manifest checks, Appendix B:** training references contain only the six specified scenes; neither monitor sequence appears in training inputs/targets; monitor targets have no training-reference overlap; no clip has identical context and target references. The optimizer selects train-split clips (`work/S141_finetune/train_s141.py:27,110-119`). Precomputation restricts scenes but also encodes monitor sequences (`work/S141_finetune/prep_latents_s141.py:11-23`); mere presence in a GPU tensor is not evidence of gradient training. Remote tensors/receipts still require verification.

The monitor holds out current/target sequences, not every context image: memory history may come from training sequences (`work/S141_finetune/build_clips_s141.py:44-45,57`). Appendix B finds 59 of 113 distinct monitor context references among training references [MEASURED]. This is compatible with the specified construction; it is not an unseen-scene validation set.

Pose-distance computation, sorting, NMS relaxation, threshold construction and target rotation normalization match S139's **pose-only** selector (`work/S141_finetune/build_clips_s141.py:26-40,57-63`; `work/S139_crossseq_revisit/pose_arms_s139.py:25-51`). The problem is selector identity: `mem_vmem` comes from the surfel retrieval receipt, not that function (`work/S139_crossseq_revisit/build_plan_s139.py:11-13`). Appendix B finds no ordered equality across the evaluation panel; S139's saved plan also reports no set equality (`work/S139_crossseq_revisit/plan.json:7-8`). Training is not an exact reproduction of evaluated VMem retrieval.

The manifest contains 2000 training entries but 1911 distinct ordered context/target clips [MEASURED, Appendix B]. The builder samples with replacement and does not deduplicate (`work/S141_finetune/build_clips_s141.py:43-67`). Five passes over entries is accurate; five passes over 2000 distinct examples is not. The displayed 1004/1028 static/memory counts include validation; training-only counts are 995/1005 [MEASURED, Appendix B; combined-count construction at `work/S141_finetune/build_clips_s141.py:68-71`]. Retain the frozen list.

The actual clip digest is `c2fbdd49e87426d837aa5e90a8e694cddd9032864079cef53c29a66991740f36` [MEASURED, Appendix A]. The protocol's `c2fbdd49e877…` prefix is wrong (`work/S141_finetune/PROTOCOL.md:26`). Record a factual correction and compare against the remote receipt; the typo is not itself evidence of contaminated training.

## 5. Evaluation and statistical analysis

### What the plans and historical comparator get right

**MEASURED, Appendix B:** chess A/B/base-region/fidelity plans match S139 contexts, targets and convention and S140 confirmation warp filenames. RGB-D A/B/base plans match S140 development references and filenames. This verifies metadata, not remote bytes.

A's plan carries mem_vmem warp filenames even for A-static to support the reused region scorer (`work/S141_finetune/build_eval_plan_s141.py:9,16-24`). A does not consume them (`work/S141_finetune/gen_s141.py:177-182`); this is not a secretly warp-conditioned A. Any A-static regional analysis would use memory-warp coverage and must be labeled accordingly. Primary B takes its warp scores from B's plan (`work/S141_finetune/analyze_s141.py:41,47`).

Earlier base generation is legitimate in principle: sampler/preprocessing structure corresponds between S139 and S141 zero adaptation (`work/S139_crossseq_revisit/gen_s139.py:96-127`; `work/S141_finetune/gen_s141.py:75-86,134-155`). Historical scoring uses the same helpers and four-target SSE aggregation (`work/S140_warp_guided/score_ssim_plan.py:11-24`; `work/S140_warp_guided/score_s140.py:10-24,30-45`). Same seed plus a 3090 label does not establish identical weights, VAE/CLIP, runtime, source or data. Do not pool H800 seeds into this registered comparison.

### Required engineering repairs

1. `sha256sum | tee` is not comparison (`work/S141_finetune/s141_chainB.sh:10`). Bind a passing byte comparison to actual base/A/B files, zero-init settings and sentinel plan before evaluation.
2. Final save is non-atomic, unlike resumable checkpoint save (`work/S141_finetune/train_s141.py:97-101,135-136`). A watcher can see a partial file. Enforce stored step 10000; the script default is 3000, and only B's supplied chain visibly overrides it (`work/S141_finetune/train_s141.py:21`; `work/S141_finetune/s141_chainB.sh:11`). A's remote invocation is unverified.
3. The wrapper has strict shell options, but the outer chains do not, and pipes can mask producer errors (`work/S141_finetune/tacc_s141.sh:6`; `work/S141_finetune/s141_chainEval.sh:1-13`; `work/S141_finetune/s141_chainB.sh:1-11`). DONE is not evidence of success.
4. Existing output names are skipped without adapter/receipt checks (`work/S141_finetune/gen_s141.py:164-165`). Validate the arrays being scored, not just log entries.
5. Self-audit trusts the first three hash strings; records step/count integers without comparing them to requirements; only literal false enters FAILED, and failure is only printed (`work/S141_finetune/self_audit_s141.py:20-34,50-52`). Its primary recomputation also lacks the main analyzer's A/B seed filter (`work/S141_finetune/self_audit_s141.py:38-46`). Enforce exact cells, steps, artifact identity and failure exits.
6. Require prediction shape `(4,3,576,576)`, finite values and explicit decoder range before scoring. `pred_u8` uses a sign heuristic and uint8 cast, not a numerical-validity check (`work/S140_warp_guided/score_s140.py:15-18`). Appendix B shows NaNs becoming black pixels. Do not drop failed cells to obtain a complete-looking panel.
7. RGB-D scoring exists but its contrast analysis is absent from the supplied chess-only analyzer (`work/S141_finetune/s141_chainEval.sh:9-12`; `work/S141_finetune/analyze_s141.py:10-13,35-65`). Complete the frozen secondary outcomes and their baseline scores before reading results.

These safeguards preserve the existing protocol. They do not authorize changing seeds, adapters, warps, sampler, precision, primary metrics or window selection.

### Estimand, pairing and verdict

The analyzer implements primary A-mem minus base-mem and B-mem minus B2, means over seeds 3–6, per-window differences, 10000 percentile bootstrap resamples with RNG 0, and the inherited S140 threshold rule (`work/S141_finetune/analyze_s141.py:13-30,35-52`; `work/S140_warp_guided/analyze_confirm_s140.py:34-35`). The scorer pools target-image SSE per seed before PSNR, then the analyzer averages seed PSNRs; this is not PSNR from pooled seed SSE (`work/S140_warp_guided/score_s140.py:30-45`; `work/S141_finetune/analyze_s141.py:16-21`). Preserve that definition.

Equal lengths do not prove equal window sets. `summ` intersects keys and `wm` overwrites duplicate seeds (`work/S141_finetune/analyze_s141.py:18-25,42`). Appendix B demonstrates different 24-window sets silently yielding 23 paired windows, and a duplicate cell altering its mean [MEASURED synthetic failures]. Enforce exact planned keys before aggregation.

The `NO_MATERIAL_CHANGE` rule asks for a small point estimate and a CI crossing zero, not a CI contained within ±0.2 dB (`work/S141_finetune/analyze_s141.py:28-29`). Appendix B produces mean zero and CI approximately [-2.08,+2.08] dB with that label [MEASURED synthetic]. It cannot justify the protocol's “LoRA is insufficient” conclusion. Conversely, `IMPROVES` requires the lower CI above zero, not above the materiality threshold. Report effect, interval and literal decision rule; do not silently substitute a new equivalence rule.

The windows share one room and a history bank within each of three sequence pairs (`work/S139_crossseq_revisit/PROTOCOL.md:17-22`). Distinct target frames do not imply independent errors. Window bootstrap does not provide independent scene replication. Keep the registered analysis, show pair effects already implemented at `work/S141_finetune/analyze_s141.py:50`, and add descriptive leave-one-pair-out sensitivity if desired. Three pairs cannot manufacture a large population sample. Sampling seeds quantify variation conditional on one trained checkpoint, not independent training replications.

Chess is training-scene-held-out, but belongs to the same dataset/acquisition domain and its earlier results explicitly motivate S141 (`work/S141_finetune/PROTOCOL.md:8-20`). “Untouched by design decisions” would be false. RGB-D is explicitly exposed (`work/S141_finetune/PROTOCOL.md:57-58`). Pretraining exposure remains unverified. Present the two registered primaries separately; an “either wins” omnibus claim is not established by unadjusted individual intervals.

## 6. Outcome interpretation and adequacy of the negative

| Outcome after valid evaluation | Claim supported | Claim not supported / alternative explanation |
|---|---|---|
| A-mem beats base-mem | This adapter recipe improves the registered metric on this training-held-out chess panel. | A unique diagnosis of domain gap; memory use improved. Task adaptation, priors and reconstruction changes remain alternatives. |
| A-mem also beats A-static | These selected historical contexts help this adapted generator relative to these recent contexts. | Surfel indexing is necessary or a particular geometric mechanism caused the gain. |
| B-mem beats B2 | The complete trained warp-conditioned predictor improves over this exact CUT3R+KPS nearest-filled warp under the registered metrics. | Novel memory/geometric reasoning, hidden-surface correctness or temporal/world consistency. Copying and cleaning splat cracks, nearest-fill repair, VAE effects and learned indoor priors remain explanations. |
| B beats A | The exploratory comparison favors B's recipe (`work/S141_finetune/analyze_s141.py:48`). | A capacity-matched causal effect of warp input; B adds trainable parameters and changes effective uc conditioning. |
| B improves only covered pixels or only SSIM | A benefit confined to that region/metric. | Hole completion or overall PSNR improvement. |
| RGB-D improves | Descriptive transfer on the exposed static-context panel. | Untouched confirmation or memory-selection transfer (`work/S141_finetune/build_rgbd_plan_s141.py:13-20`). |
| Both have small effects and wide CIs | This run did not establish improvement at the available precision. | Equivalence, that more steps will help, or that geometry conditioning/LoRA cannot work. |
| Both have tight CIs inside materiality bounds | A narrowly bounded small effect for this recipe/panel, under an explicitly declared equivalence interpretation. | General failure of LoRA, full fine-tuning, alternative objectives or other domains/training seeds. |
| Quality worsens versus numerical failure | Respectively a negative recipe result versus an engineering failure. | Scientific rejection based on NaN-cast images or missing cells. |

Coverage holes mean no valid splat under the computed mask, not independently certified never-observed surfaces (`work/S141_finetune/warps_s141.py:62-66,90`; `work/S140_warp_guided/score_s140.py:35-49`). Even hole-PSNR gains can be ordinary interpolation or restoration.

This is a fixed-budget test, not a validated test of optimization sufficiency. One training seed, a fixed clip list, final-checkpoint selection and conditional-only monitoring at six sigma indices leave optimization/capacity/objective/power explanations unresolved (`work/S141_finetune/train_s141.py:24,75-85,110-136`; `work/S141_finetune/PROTOCOL.md:43-49,69-70`). A decreasing epsilon loss does not prove good unconditional CFG behavior or convergence in generated-image PSNR. Five nominal passes is not an adequacy theorem. Verify finite losses, gradients, checkpoint parameters and intended data before reporting even the narrow negative. Preserve the final-checkpoint stop rule; intermediate adapters remain exploratory, not a rescue of the primary.

Nor does a positive result establish novelty. **arXiv:2106.09685, “LoRA: Low-Rank Adaptation of Large Language Models,” §4.1**, describes low-rank additive adaptation with a zero-initialized factor. **arXiv:2302.05543, “Adding Conditional Control to Text-to-Image Diffusion Models,” §3.1**, describes learned spatial conditioning through zero-initialized connections. S141 is not literally the full ControlNet architecture, but this combination plus a gain is not proof of a new mechanism. [LoRA primary source](https://arxiv.org/html/2106.09685v2#S4.SS1), [ControlNet primary source](https://arxiv.org/html/2302.05543v3#S3.SS1).

The general epsilon-loss/dropout interpretation is supported by **arXiv:2207.12598, “Classifier-Free Diffusion Guidance,” §2 and §3.2, Algorithms 1–2**. This supports the construction, not exact reproduction of VMem's original training or harmlessness of target-only context adaptation. [Verified primary source](https://arxiv.org/html/2207.12598v1#S3.SS2).

## 7. Release and follow-up boundary

Before scoring, enforce fidelity, completed final-adapter identity, finite arrays, exact planned cells and receipt-to-array integrity; verify historical base/warp provenance. Complete the promised RGB-D analysis and qualify the registered verdict wording. Preserve trained adapters and failures. No evaluation-driven tuning is needed for these safeguards.

A subsequent protocol could isolate warp restoration, VAE round-trip effects, branch capacity, context dependence, actual mem_vmem training selection, context-state supervision, warp producer matching or training-seed sensitivity. Those experiments must not be folded retroactively into S141's confirmatory claim.

Changed file: `work/agents/CODEX_R254_S141_HOSTILE_REVIEW.md` only. Follow-up belongs to the main agent: implement the evaluation safeguards, collect remote evidence when authorized, then report frozen results within this scope. `new_method_validated=false` and `novelty_authorization=NONE` remain unchanged.

## Appendix A — Local freeze and identity probe

Commands below were executed from the repository root during this review session. Their outputs are complete. MEASURED means local CPU/software evidence, not GPU experimental performance. This appendix records the review-time snapshot; concurrent processes may subsequently change files. The `output_exists False` line predates creation of this report.

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-cut3r/bin/python - <<'PY'
from pathlib import Path
import hashlib, subprocess
files = ['work/S141_finetune/PROTOCOL.md','work/S141_finetune/clips_s141.json','work/S141_finetune/s141_common.py','work/S141_finetune/train_s141.py','work/S141_finetune/gen_s141.py','work/S141_finetune/s141_chainB.sh','work/S141_finetune/s141_chainEval.sh','data/S134_tacc/vmem_src/modeling/sampling.py','data/S134_tacc/vmem_src/modeling/network.py','data/S134_tacc/vmem_src/modeling/pipeline.py','data/S134_tacc/vmem_src/modeling/modules/transformer.py','data/S134_tacc/vmem_src/utils/util.py']
print('HEAD', subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
p=Path(files[0]); old=subprocess.check_output(['git','show','7cefe20e:'+str(p)])
print('protocol_matches_freeze',p.read_bytes()==old)
for f in files: print(hashlib.sha256(Path(f).read_bytes()).hexdigest(), f)
print('output_exists',Path('work/agents/CODEX_R254_S141_HOSTILE_REVIEW.md').exists())
PY
```

```text
HEAD 7cefe20ede81597b32517b49a9f0bbdf35278b10
protocol_matches_freeze True
5833bd1177ae2e0f776de84c903e0919d09b2f1977d114ddd3013ea63b7f20a2 work/S141_finetune/PROTOCOL.md
c2fbdd49e87426d837aa5e90a8e694cddd9032864079cef53c29a66991740f36 work/S141_finetune/clips_s141.json
459549706fb3a965fc4f7c5021f4d49cc626158e94a7c9cdc94cf8784cccb6cc work/S141_finetune/s141_common.py
6ba0419e5ceb39406bbd1894ffae90398c27daedbc2eea56b18e537ba6187c0a work/S141_finetune/train_s141.py
c29d991a3c7ddc0eb36bdbd9869b4a82226f19ad56b44f39cff8973408fb75e0 work/S141_finetune/gen_s141.py
484ada5b07bfcbd260f56d158d6da0c6e3f860838e0294e08eec64646e83ee68 work/S141_finetune/s141_chainB.sh
c58e4edc6c3cef07d7576c486fdd7e6ed03d432c718893278472568d7ebd7ccc work/S141_finetune/s141_chainEval.sh
dc07ca0ba571ba5fb48f9856515d2cb7dea25254008a6f8b315538817f352b24 data/S134_tacc/vmem_src/modeling/sampling.py
9ed21c2d804734d7ca2d81b1e596858835ca70a4a04abb9b5540b872515d4c9b data/S134_tacc/vmem_src/modeling/network.py
680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255 data/S134_tacc/vmem_src/modeling/pipeline.py
5f0d152a2f6464076cb0ee5aca725b3445420a5f37ac571d3daa77e580e65764 data/S134_tacc/vmem_src/modeling/modules/transformer.py
30a97451f7a895e99ab881e97249f564e6b97eca2b5ea4d8f83953c26c4cf65e data/S134_tacc/vmem_src/utils/util.py
output_exists False
```

## Appendix B — Analyzer, scoring, plans and splits

This probe extracts functions rather than executing scripts that write score files. It independently checks supplied JSON manifests and produces synthetic failure examples, not model-evaluation results.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=work/S17C_environment/site-packages .venv-cut3r/bin/python - <<'PY'
import ast, json, warnings
from collections import Counter
from pathlib import Path
import numpy as np
S=Path('work/S141_finetune'); W=Path('work')
def J(p): return json.loads(Path(p).read_text())
def functions(p,names,ns):
 t=ast.parse(Path(p).read_text()); exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),str(p),'exec'),ns)
ns={'np':np,'SEEDS':(3,4,5,6)}; functions(S/'analyze_s141.py',{'summ','wm'},ns)
a={f'w{i:02}':(-5. if i<12 else 5.) for i in range(24)}; b={k:0. for k in a}
print('wide_CI',ns['summ'](a,b,.2))
a={f'w{i:02}':1. for i in range(24)}; b={f'w{i:02}':0. for i in range(1,25)}
print('unequal_24_window_sets',ns['summ'](a,b,.2))
r={str(s):{'window_id':'w0','seed':s,'x':0.} for s in (3,4,5,6)}; r['duplicate']={'window_id':'w0','seed':3,'x':4.}
print('duplicate_cell',ns['wm'](r,lambda r:True,'x'))
functions(W/'S140_warp_guided/score_s140.py',{'pred_u8'},ns)
with warnings.catch_warnings(record=True) as ws:
 warnings.simplefilter('always'); y=ns['pred_u8'](np.full((3,2,2),np.nan,dtype=np.float32))
 print('NaN_cast',y.tolist(),str(y.dtype),[str(w.message) for w in ws])
p139=J(W/'S139_crossseq_revisit/plan.json')['contexts']; p140=J(W/'S140_warp_guided/plan_confirm.json')['contexts']
base={(c['window_id'],a):c for c in p139 for a in c['arms']}; warps={c['window_id']:c for c in p140}
for name in ('plan_eval_A','plan_eval_B','plan_base_regions','plan_fid_A','plan_fid_B'):
 cs=J(S/(name+'.json'))['contexts']; errors=[]
 for c in cs:
  b=base[c['window_id'],c['arm']]
  for k in ('ctx_refs','target_refs','convention'):
   if c[k]!=b.get(k,'gl'): errors.append((c['ctx_key'],k))
  if c['warp_files']!=warps[c['window_id']]['warp_files']: errors.append((c['ctx_key'],'warp_files'))
 print(name,'n',len(cs),'errors',errors,'duplicate_keys',len(cs)-len({c['ctx_key'] for c in cs}))
dev={c['window_id']:c for c in J(W/'S140_warp_guided/plan_dev.json')['contexts'] if c['mode'] not in ('ref','none')}
for name in ('plan_rgbd_A','plan_rgbd_B','plan_rgbd_base'):
 cs=J(S/(name+'.json'))['contexts']; errors=[(c['ctx_key'],k) for c in cs for k in ('ctx_refs','target_refs','warp_files','scene_dir') if c[k]!=dev[c['window_id']][k]]
 print(name,'n',len(cs),'errors',errors)
clips=J(S/'clips_s141.json')['clips']; tr=[c for c in clips if c['split']=='train']; va=[c for c in clips if c['split']=='val']
refs=lambda cs,key:set(r for c in cs for r in c[key]); trrefs=refs(tr,'ctx')|refs(tr,'tgt'); valctx=refs(va,'ctx'); valtgt=refs(va,'tgt')
print('clips_train_val',len(tr),len(va),'train_scenes',sorted({r.split('/')[0] for r in trrefs}))
print('train_monitor_refs',sum('/'.join(r.split('/')[:2]) in {'office/seq-10','redkitchen/seq-14'} for r in trrefs),'val_target_train_overlap',len(valtgt&trrefs),'val_ctx_train_overlap',len(valctx&trrefs),'unique_val_ctx',len(valctx))
print('unique_full_train_clips',len({(tuple(c['ctx']),tuple(c['tgt'])) for c in tr}),'within_clip_ctx_target_overlap',sum(bool(set(c['ctx'])&set(c['tgt'])) for c in clips))
print('train_kind_counts',dict(Counter(c['kind'] for c in tr)),'val_kind_counts',dict(Counter(c['kind'] for c in va)))
print('vmem_pose_equal_contexts',sum(base[w,'mem_vmem']['ctx_refs']==base[w,'mem_pose']['ctx_refs'] for w in warps),'of',len(warps))
print('warpcheck_windows',[c['id'] for c in J(S/'warpcheck_clips.json')['clips']])
print('pairs',dict(Counter(c['pair'] for c in J(W/'S139_crossseq_revisit/POSE_ARMS.json')['rows'])))
PY
```

```text
wide_CI {'n': 24, 'mean': 0.0, 'ci95': [-2.0833333333333335, 2.0833333333333335], 'wins': 12, 'verdict': 'NO_MATERIAL_CHANGE'}
unequal_24_window_sets {'n': 23, 'mean': 1.0, 'ci95': [1.0, 1.0], 'wins': 23, 'verdict': 'IMPROVES'}
duplicate_cell {'w0': 1.0}
NaN_cast [[[0, 0, 0], [0, 0, 0]], [[0, 0, 0], [0, 0, 0]]] uint8 ['invalid value encountered in cast']
plan_eval_A n 48 errors [] duplicate_keys 0
plan_eval_B n 24 errors [] duplicate_keys 0
plan_base_regions n 24 errors [] duplicate_keys 0
plan_fid_A n 1 errors [] duplicate_keys 0
plan_fid_B n 1 errors [] duplicate_keys 0
plan_rgbd_A n 16 errors []
plan_rgbd_B n 16 errors []
plan_rgbd_base n 16 errors []
clips_train_val 2000 32 train_scenes ['fire', 'heads', 'office', 'pumpkin', 'redkitchen', 'stairs']
train_monitor_refs 0 val_target_train_overlap 0 val_ctx_train_overlap 59 unique_val_ctx 113
unique_full_train_clips 1911 within_clip_ctx_target_overlap 0
train_kind_counts {'static': 995, 'memory': 1005} val_kind_counts {'memory': 23, 'static': 9}
vmem_pose_equal_contexts 0 of 24
warpcheck_windows ['chk0', 'chk1', 'chk2']
pairs {'seq-01->seq-02': 8, 'seq-04->seq-03': 8, 'seq-06->seq-05': 8}
```

## Appendix C — CPU objective, schedule and checkpoint check

A delegated reviewer executed this exact command in this session. It uses a reduced random source model, not pretrained VMem weights. Backward checks do not perform optimizer steps or training jobs. The zero-init discrepancy is a CPU execution observation, not a CUDA failure claim.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=work/S17C_environment/site-packages .venv-cut3r/bin/python - <<'PY'
import ast, math, sys, copy, types
from pathlib import Path
import torch
import torch.nn as nn
pkg=types.ModuleType('modeling'); pkg.__path__=['data/S134_tacc/vmem_src/modeling']; sys.modules['modeling']=pkg
from modeling.network import VMemModel, VMemModelParams
from modeling.modules.layers import timestep_embedding
from modeling.modules.transformer import Attention
from modeling.sampling import DDPMDiscretization, DiscreteDenoiser
ns=dict(torch=torch,nn=nn,math=math,Attention=Attention,timestep_embedding=timestep_embedding)
tree=ast.parse(Path('work/S141_finetune/s141_common.py').read_text())
names={'LoRALinear','WarpInConv','add_adapters','ckpt_forward'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names],type_ignores=[]),'<s141 definitions>','exec'),ns)
torch.set_num_threads(1); torch.manual_seed(123)
den=DiscreteDenoiser(DDPMDiscretization(),device='cpu')
s=DDPMDiscretization()(50,device='cpu')[:-1]; ids=den.sigma_to_idx(s)
print('torch',torch.__version__)
print('sampling_indices',ids.tolist())
print('sampling_sigma_exact_discrete',torch.equal(s,den.sigmas[ids]))
print('sigma_min_max',den.sigmas[0].item(),den.sigmas[-1].item())
z=torch.randn(8,4,4,4); eps=torch.randn_like(z); idx=torch.tensor([400]); sig=den.sigmas[idx]
rep=torch.zeros(8,5,4,4); rep[:4,:4]=z[:4]; rep[:4,4]=1
cond={'replace':rep}; seen={}
def capture(x,t,c,**kw):
    seen.update(x=x,t=t,kw=kw)
    return eps
out=den(capture,z+sig*eps,sig.repeat(8),cond,num_frames=8)
m=rep[:,4:]; inp=(z+sig*eps)*(1-m)+rep[:,:4]*m
train_input=inp/torch.sqrt(sig**2+1)
print('input_divide_vs_sampler_multiply_max_abs',float((train_input-seen['x']).abs().max()))
print('discrete_timestep_equal',torch.equal(seen['t'],idx.repeat(8)))
print('num_frames',seen['kw'])
print('epsilon_target_reconstructs_target_max_abs',float((out[4:]-z[4:]).abs().max()))
p=VMemModelParams(model_channels=32,num_res_blocks=1,attention_resolutions=[1,2],channel_mult=[1,1],num_head_channels=16,transformer_depth=[1,1],context_dim=16,unflatten_names=['middle_ds2','output_ds2'])
base=VMemModel(p).eval()
x=torch.randn(8,11,8,8); t=torch.arange(8); y=torch.randn(8,1,16); dense=torch.randn(8,6,8,8)
a=copy.deepcopy(base); n,params=ns['add_adapters'](a,r=2,alpha=2,warp=False)
b=copy.deepcopy(base); nb,pb=ns['add_adapters'](b,r=2,alpha=2,warp=True)
with torch.no_grad():
    ob=base(x,t,y,dense,8); oa=a(x,t,y,dense,8); ow=b(torch.cat([x,torch.randn(8,5,8,8)],1),t,y,dense,8)
print('tiny_model_attention_count',n,nb)
print('zero_init_A_equal',torch.equal(ob,oa),'max_abs',float((ob-oa).abs().max()))
print('zero_init_B_equal',torch.equal(ob,ow),'max_abs',float((ob-ow).abs().max()))
a.train()
for m in a.modules():
    if isinstance(m,ns['LoRALinear']): nn.init.normal_(m.up.weight,std=.01)
bck=copy.deepcopy(a)
one=a(x,t,y,dense,8); two=ns['ckpt_forward'](bck,x,t,y,dense,8)
one.square().mean().backward(); two.square().mean().backward()
pairs=[(p,q) for p,q in zip(a.parameters(),bck.parameters()) if p.requires_grad]
print('checkpoint_forward_equal',torch.equal(one,two),'max_abs',float((one-two).abs().max()))
print('checkpoint_adapter_gradient_max_abs',max(float((p.grad-q.grad).abs().max()) for p,q in pairs))
print('checkpoint_all_adapter_gradients_present',all(p.grad is not None and q.grad is not None for p,q in pairs))
print('scope','CPU float32 reduced random model only; no weights, CUDA, optimizer step, or files written')
PY
```

```text
torch 2.7.0
sampling_indices [999, 979, 959, 939, 919, 899, 879, 859, 839, 819, 799, 779, 759, 739, 719, 699, 679, 659, 639, 619, 599, 579, 559, 539, 519, 499, 479, 459, 439, 419, 399, 379, 359, 339, 319, 299, 279, 259, 239, 219, 199, 179, 159, 139, 119, 99, 79, 59, 39, 19]
sampling_sigma_exact_discrete True
sigma_min_max 0.02464863285422325 84.91632843017578
input_divide_vs_sampler_multiply_max_abs 2.384185791015625e-07
discrete_timestep_equal True
num_frames {'num_frames': 8}
epsilon_target_reconstructs_target_max_abs 8.344650268554688e-07
tiny_model_attention_count 28 28
zero_init_A_equal False max_abs 1.0728836059570312e-06
zero_init_B_equal False max_abs 1.0728836059570312e-06
checkpoint_forward_equal True max_abs 0.0
checkpoint_adapter_gradient_max_abs 0.0
checkpoint_all_adapter_gradients_present True
scope CPU float32 reduced random model only; no weights, CUDA, optimizer step, or files written
```

## Appendix D — CPU zero-init execution dependence and branch bias

This follow-up was executed by the same delegated reviewer. It narrows the interpretation of Appendix C: freezing the baseline eliminates the discrepancy in this CPU example. It does not prove a CUDA mechanism or authorize changing the fidelity criterion.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=work/S17C_environment/site-packages .venv-cut3r/bin/python - <<'PY'
import ast,math,sys,copy,types
from pathlib import Path
import torch
import torch.nn as nn
pkg=types.ModuleType('modeling');pkg.__path__=['data/S134_tacc/vmem_src/modeling'];sys.modules['modeling']=pkg
from modeling.network import VMemModel,VMemModelParams
from modeling.modules.transformer import Attention
ns=dict(torch=torch,nn=nn,math=math,Attention=Attention)
tree=ast.parse(Path('work/S141_finetune/s141_common.py').read_text());names={'LoRALinear','WarpInConv','add_adapters'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names],type_ignores=[]),'<s141>','exec'),ns)
torch.set_num_threads(1);torch.manual_seed(123)
p=VMemModelParams(model_channels=32,num_res_blocks=1,attention_resolutions=[1,2],channel_mult=[1,1],num_head_channels=16,transformer_depth=[1,1],context_dim=16,unflatten_names=['middle_ds2','output_ds2'])
base=VMemModel(p).eval();a=copy.deepcopy(base);b=copy.deepcopy(base)
ns['add_adapters'](a,r=2,alpha=2,warp=False);ns['add_adapters'](b,r=2,alpha=2,warp=True)
x=torch.randn(8,11,8,8);xb=torch.cat([x,torch.randn(8,5,8,8)],1);t=torch.arange(8);y=torch.randn(8,1,16);d=torch.randn(8,6,8,8)
print('B_base_slice_contiguous',xb[:,:11].is_contiguous())
for label,context in [('no_grad',torch.no_grad),('inference_mode',torch.inference_mode)]:
    with context():
        ref=base(x,t,y,d,8);aa=a(x,t,y,d,8);bb=b(xb,t,y,d,8)
    print(label,'A_equal',torch.equal(ref,aa),'A_max_abs',float((ref-aa).abs().max()),'B_equal',torch.equal(ref,bb),'B_max_abs',float((ref-bb).abs().max()))
base.requires_grad_(False)
with torch.inference_mode():
    ref=base(x,t,y,d,8);aa=a(x,t,y,d,8);bb=b(xb,t,y,d,8)
print('frozen_base_inference_mode','A_equal',torch.equal(ref,aa),'B_equal',torch.equal(ref,bb))
branch=b.input_blocks[0][0];branch.warp.bias.data.fill_(0.25)
with torch.no_grad():
    zero=torch.zeros(8,5,8,8);delta=branch(torch.cat([x,zero],1))-branch.base(x)
print('zero_warp_input_learned_bias_delta_mean',float(delta.mean()))
PY
```

```text
B_base_slice_contiguous False
no_grad A_equal False A_max_abs 8.344650268554688e-07 B_equal False B_max_abs 8.344650268554688e-07
inference_mode A_equal False A_max_abs 8.344650268554688e-07 B_equal False B_max_abs 8.344650268554688e-07
frozen_base_inference_mode A_equal True B_equal True
zero_warp_input_learned_bias_delta_mean 0.25
```

These are CPU synthetic checks. Full model-weight/CUDA/bf16-to-fp16 checks and actual evaluation were deliberately not run under this brief's restrictions. No code changes were made, so no repository-wide implementation test/linter run is claimed.
