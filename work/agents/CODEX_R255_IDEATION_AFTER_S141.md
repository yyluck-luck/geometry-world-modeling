# R255 — What to do after S141: conditional experiments and self-rejection

Date: 2026-10-10. Workspace: local Mac checkout. Review type: ideation with adversarial self-review, not experimental validation.

**Recommendation:** finish the S133–S140 diagnostic manuscript now, let S141 finish under its existing protocol, then execute at most one outcome-selected follow-up. If B beats the warp, test whether its improvement depends on aligned evidence. If B does not beat the warp, allow one small, explicitly bounded alternative consumption mechanism, not an architecture search. If both A and B fail, stopping has higher expected project value than another method; the table nevertheless specifies the single experiment I would choose if the owner prioritizes one last test.

Only this review file is a deliverable of R255. There were no GPU runs, training, model/data downloads, cluster connections, submissions, or outside contacts in this review. S141 outcomes and remote artifact integrity remain **UNVERIFIED**. The current source snapshot is not proof of what the remote jobs executed. `new_method_validated=false` and `novelty_authorization=NONE` remain unchanged.

Evidence notation: **MEASURED (archived)** means a prior run's stored measurements, not a new run; **DERIVED** means arithmetic on those records; **ANALYTICAL** means a proposed design, threshold, or resource calculation; **UNVERIFIED** means unavailable evidence or an untested explanation. All future thresholds and budgets below are ANALYTICAL, not observed performance. Appendix A provides exact CPU verification commands and their complete outputs. Repository citations are relative to the checkout root. For compact repeated citations, bare S141 script names resolve under `work/S141_finetune/`; `pipeline.py`, `network.py`, `modeling/sampling.py`, and `transformer.py` resolve respectively to `data/S134_tacc/vmem_src/modeling/pipeline.py`, `data/S134_tacc/vmem_src/modeling/network.py`, `data/S134_tacc/vmem_src/modeling/sampling.py`, and `data/S134_tacc/vmem_src/modeling/modules/transformer.py`. The report filename resolves under `docs/report/`.

## (i) Outcome-conditional plan

### Read the S141 outcomes correctly

A's registered primary is `A_mem - base_mem`; B's is `B_mem - B2_warp`. The separate contrasts `A_mem - A_static` and `B_mem - A_mem` answer different questions; the latter is explicitly exploratory in the implementation (`work/S141_finetune/PROTOCOL.md:51-64`; `work/S141_finetune/analyze_s141.py:35-50`).

- **A improves:** mean primary PSNR difference at least +0.2 dB and lower 95% CI above zero. **A not:** no such positive verdict; distinguish worsening from inconclusive.
- **B beats / ties / loses:** respectively `IMPROVES`, `NO_MATERIAL_CHANGE`, and `WORSENS` under the implemented rule. Worsening requires mean at most −0.2 dB and upper CI below zero; the code's tie requires absolute mean below 0.2 dB and a CI spanning zero. Everything else is **INCONCLUSIVE**, a fourth outcome, not a tie (`analyze_s141.py:24-30`). A genuine practical-equivalence claim would need an interval wholly inside the equivalence band.
- A positive A result establishes useful adaptation under this recipe. It does not uniquely identify domain mismatch as the cause: there is no same-budget alternative-domain training control. A positive B result establishes added PSNR over this warp; it does not by itself establish the benefit of the warp branch over A, memory use, or better temporal/perceptual quality.
- B's warp is present in both CFG dictionaries. Lowering CFG or dropping the usual image conditioning therefore does not remove it (`train_s141.py:71-72,115-119`; `gen_s141.py:134-148`).
- If fidelity, checkpoint completion, or scoring is invalid, classify the result as an **execution failure**, outside the scientific outcome table. If B is inconclusive, complete only missing registered cells first; if complete, report uncertainty and select no winner. Do not append seeds until significance appears.

**Source anomalies to resolve from S141 artifacts, without rewriting its protocol retrospectively:** `s141_chainB.sh:6-11` prints hashes but does not compare them before training; `self_audit_s141.py:22-34,50-52` records final steps and observed/expected counts but its failure list only catches Boolean false values. The trainer defaults to 3,000 steps (`train_s141.py:21`), whereas the B chain explicitly exports 10,000 (`s141_chainB.sh:11`); the inspected wrapper does not establish A's launch environment (`tacc_s141.sh:13-15`). Existing predictions are skipped by filename (`gen_s141.py:164-165`). Thus check actual final-adapter step, hashes, complete planned cells, and prediction provenance. These are possible interpretation hazards, not findings that the remote runs failed. Leave concurrent files untouched.

### Shared contract for the proposed follow-up

Use the same four-frame targets, deterministic context identities, cameras, scorer, final S141 adapters, and paired generation seeds 3, 4, 5, 6 on RTX 3090. Average seeds within each window. Use one stated primary contrast, a fixed 95% window bootstrap for compatibility, and also show all three trajectory-pair means; shared history makes these windows dependent. A narrow window CI is not population-level evidence across scenes (`work/agents/SELF_AUDIT_S139.md:30-35`). Require the primary threshold and no PSNR reversal in two of the three pairs before promoting a candidate within this case study.

Chess is excluded from S141 training, but is already exposed to project decisions. S140 explicitly reused targets previously scored in S139 (`work/S140_warp_guided/PROTOCOL.md:29-32`). A method chosen after seeing S141 and scored on the same chess windows is an **exposed-panel follow-up**, even with a new preregistration. Existing RGB-D Scenes 13/14 supply transfer evidence, also exposed. Do not call either an untouched new confirmation set. No fresh dataset download is necessary for the decision experiments below; a general method paper would need fresh scene-level confirmation later.

For any new predictor, report full-frame PSNR, SSIM, covered/hole PSNR, and per-pair effects. Freeze coverage from input geometry, not target error. A +0.2 dB PSNR success accompanied by a material SSIM decline (mean ≤−0.01 with upper CI below zero) is only a reconstruction trade-off, not a general image-quality win. Evaluate temporal behavior separately before using the phrase “better video”; frame PSNR/SSIM cannot establish it.

### Six outcome combinations

E1, E2, and E3 are specified immediately below. Repeated entries intentionally reuse one decisive experiment instead of manufacturing a different method for each cell.

| S141 outcome | Single most informative next experiment; hypothesis and minimal change | One preregisterable primary contrast and decision threshold | Kill criterion | Data needed; additional storage | Estimated compute on the available hardware |
|---|---|---|---|---|---|
| **A improves; B beats warp** | **E1: aligned-evidence intervention on final B.** Hypothesis: B benefits from spatially correct warp evidence, beyond A's adaptation. Keep raw contexts, poses, weights, masks and seeds fixed; spatially derange only warp appearance within the fixed coverage classes. | Window-mean PSNR `B(correct) - B(deranged)` ≥+0.2 dB, lower CI >0. B−A is a prespecified supporting comparison, not a replacement primary. | Below threshold: reject the alignment-dependence claim; do not discard B's measured predictor gain. A positive perturbation effect alone is insufficient to claim useful causal memory use. Finish the report. | Existing 24 chess windows, 96 correct outputs, warp/mask caches. No download. One new arm: approximately 1.42 GiB float32 outputs; reserve 3 GiB. | **1–2 RTX 3090 GPU-h** for the new arm, approximately 0.5–1 h ideal wall time across two cards, plus setup. H800 may run the complete fixed RGB-D transfer comparison separately; budget 2–4 h provisionally, not a measured speedup. |
| **A not; B beats warp** | **E1 again.** Hypothesis: the geometry-conditioned package depends on aligned content even though generic adaptation did not improve. The same minimal intervention is more informative than another A learning-rate/rank sweep. | Same E1 primary and +0.2 dB/positive-CI threshold. Inspect B−A, but do not retroactively promote S141's exploratory comparison to its original primary. | Same E1 kill; if insensitive to alignment, retain only “B is a better predictor than B2 under this recipe,” with the mechanism unresolved. | Same existing data; zero download; approximately 1.42 GiB new outputs, 3 GiB reserve. | Same **1–2 RTX GPU-h**; optional H800 transfer 2–4 h planning allowance with all controls generated on that site. |
| **A improves; B ties warp** | **E2: train target-pose warps as clean context slots.** Hypothesis: pretrained context consumption is easier to adapt than B's new input branch. Replace the four context RGB/latent/pose slots by the four input-derived target-pose warps; keep targets noisy and trainable. | `C_replace - B2` PSNR ≥+0.2 dB, lower CI >0. Require C not to be materially worse than A or B before retaining it as a practical predictor. | One fixed training budget, then one evaluation. No primary gain, or gain merely matching warp copying: reject C. Preserve A's adaptation result; write up. | Reuse 2,000 training +32 monitor clips and their four warps. New download 0 bytes. Cached warp latent+coverage arrays are approximately 0.785 GiB total if fp32; CLIP warp embeddings require a small new cache. Reserve 5 GiB extra including predictions/checkpoints, not duplicating all raw data. | **5–8 RTX GPU-h** training C plus **1–2 GPU-h** evaluation. Second 3090: fixed seed-1 training replication if C passes the train-only gate, another 5–8 h; not a different method. H800: complete fixed transfer block, provisional 2–4 h. |
| **A not; B ties warp** | **E2 again.** Hypothesis: channel placement, rather than merely more adaptation, limits the tested recipe. This is the last consumption-route trial, conditional on valid completed S141 training. | Same `C_replace - B2` primary and threshold; separately compare against B and report covered/hole effects. | Train-only learning gate fails or final primary fails: end the learned-consumer search for this deadline. No rank, loss-weight, or architecture rescue sweep. | Same 2,032 existing clips; no download; approximately 0.785 GiB existing warp-array payload, 5 GiB new reserve. | **6–10 RTX GPU-h** including inference; optional seed replication on the second card 5–8 h. H800 transfer only if it answers the fixed transfer question. |
| **A improves; B loses warp** | **E3: learned pixel-space reliability fusion of A and warp.** Hypothesis: A supplies locally useful content, but making a generator overwrite reliable geometry loses too much. Freeze A; learn a tiny gate from training scenes to blend it with the warp. | `F_gate - B2` PSNR ≥+0.2 dB, lower CI >0. Also require F to exceed a prespecified constant-blend control and not materially worsen A; otherwise attribute the gain to ordinary averaging or keep A. | Train-only oracle bound shows <+0.2 dB headroom, monitor gate fails to beat constant blend, or final primary fails: stop. Never estimate inference gates from chess target error. | 256 fixed S141 training clips +32 monitor clips, A predictions, their warps, training RGB labels; existing chess outputs for final scoring. No download. About 4.27 GiB for 288 float32 four-frame A predictions; reserve 12 GiB with warp/features/outputs. | **3–6 RTX GPU-h** to produce train/monitor predictions, **≤2 GPU-h planning allowance** for the tiny gate, **≤1 h CPU/GPU** compositing/scoring. Cards can shard prediction generation; H800 may generate a complete separate transfer block. |
| **A not; B loses warp** | **E2 is the sole defensible last experiment if one more trial is required.** Hypothesis: a pretrained clean-context route can rescue a failed side-branch recipe. **My preferred decision is stop/write**; broad scaling or full-resolution attention is worse value. | Same `C_replace - B2` primary, +0.2 dB/positive-CI threshold, no SSIM harm. This is not a prediction that C will succeed. | Abort on the train-only gate; otherwise one final adapter/evaluation, then stop regardless of sign. No second rescue mechanism. | Same cached 2,032 clips, zero new download, 5 GiB extra reserve. | **6–10 RTX GPU-h maximum planned trial**, plus seed replication only if its prespecified train-only gate passes. Stop/write itself requires **0 new GPU-h**. |

All storage estimates are array arithmetic, not inspected remote free space. No H800 training throughput is established here. The H800 budget is an explicit scheduling allowance subject to a small runtime calibration, not a performance prediction.

### E1 — Test dependence, without confusing sabotage with benefit

Use a fixed within-frame permutation of warp RGB pixels separately inside covered and uncovered pixel sets, seed 255, before VAE encoding. Keep the coverage bitmap unchanged and leave raw retrieved contexts, their CLIP embeddings, cameras, ordering, adapters, and diffusion noise untouched. This preserves region-level color histograms and the mask while destroying spatial alignment. Apply the changed warp to **both** CFG branches. Define the permutation before scoring and include every window. Correct-arm outputs can be reused only when source, adapter, output, sampler, and seed identities match.

This intervention is deliberately cheap and deliberately limited. A drop establishes dependence on the supplied warp's spatial content; the deranged input is out of distribution. It does **not** alone show that naturally better retrieval helps, that attention is geometrically correct, or that B is novel. The positive utility evidence remains B(correct)−warp and the comparison with A. Thus use E1 as a stringent check on the explanation of an existing success, not as a new model contribution. Repeated target-slot permutations would often be too weak for nearby poses; moving the coverage mask as well would confound content with availability.

If the report needs the stronger claim that learning makes *retrieved history* useful, the missing experiment is a source-coherent memory-versus-static comparison: change raw contexts and recompute their warps together, then compare `(B_mem-B_static)-(A_mem-A_static)`. That is a distinct future experiment, not silently added to this one-experiment budget. A warp-only perturbation is a path intervention, not the total effect of changing memory.

### E2 — A trained context-route challenger, with an honest attribution boundary

Call the challenger C, not a named new method. For each clip compute four warps from exactly its allowed original context frames and the four target poses. Use their VAE latents as the four clean context slots and their actual target poses as context poses. Compute CLIP conditioning from those warped images. Use the four real target latents only as supervised training targets; at evaluation only the scorer sees target RGB. Leave target `replace` masks at zero. Keep LoRA rank, seed, optimizer, step budget, and sampler identical to S141 A; remove the extra B input convolution.

This follows an existing interface: `get_cond` builds clean context latents with mask one and target placeholders with mask zero (`data/S134_tacc/vmem_src/modeling/pipeline.py:1143-1185`); sampling substitutes the masked clean values (`modeling/sampling.py:174-185`). S141's training objective predicts target ε after substituting clean contexts (`work/S141_finetune/train_s141.py:61-68,115-121`).

**Do not put the warp into clean target slots and retain ε-MSE there unchanged.** That removes the target's sampled noise from those inputs while still asking for that noise. The resulting objective would not be the proposed ordinary conditional denoising problem. Likewise, do not treat unknown warp pixels as ground truth: nearest fill is an imperfect condition, not a target label.

The smallest C changes the representation and loses access to the original high-resolution source pixels; it is **not** a clean causal comparison of replace versus concat. Changed context poses also alter conditioning normalization and the reference camera in the current implementation (`pipeline.py:1090-1141`). A success supports this complete input representation; a failure does not prove the replace channel intrinsically inadequate. Preserving both sets of frames or holding the original camera gauge fixed is a different, larger design. Do not smuggle that expansion into this trial.

**Train-only gate and stop:** on eight predetermined training clips, run a separate disposable 500-step learning check with fixed noise/sigma evaluation. Require finite gradients/loss and at least a 10% decrease in the same fixed target ε-MSE before spending on the full run. This threshold is an engineering decision, not a scientific effect size. Discard the disposable adapter, restart from the base for the fixed 10,000-step run, and evaluate only the final adapter. A failed gate is a failed implementation/recipe, not evidence that geometry cannot help. Budget this gate within the stated allowance. Freeze any corrections before the full trial, not after chess scoring.

C must beat the raw warp, not merely beat frozen VMem. Its strongest likely failure is simply learning an identity-like copy: the frozen same-pose experiment already matched the warp and copied grey holes (`work/S137_geometry_baselines/RESULT.md:40-55`). Training may alter that behavior, but the burden is on C to show added value. Report the untrained C output as a descriptive copying control on the fixed monitor subset, not another tuned contender.

### E3 — A cheap fusion baseline, not evidence that VMem learned to consume memory

Let `F = g(f) * W + (1-g(f)) * A`, clipped to the output range, with one scalar gate per pixel shared across RGB. W is the warp; A is the fixed final A prediction. Inputs f may contain fixed coverage, distance to its boundary, local warp gradients, and warp–A disagreement. Fit a small fixed-capacity sigmoid gate on the specified training clips using RGB MSE; no target-derived feature is available at inference. Use the existing monitor clips once to check the frozen design against a constant blend whose coefficient is fitted only on training data. The monitor set becomes development data for this follow-up and cannot also be called untouched validation.

Before fitting, estimate the attainable **convex-blend upper bound on training/monitor data only**. For each pixel, the best scalar blend is
`g* = clip(((Y-A) dot (W-A)) / ||W-A||^2, 0, 1)`
(with g=1 when the denominator is zero). This is a target-using oracle and can never be deployed or scored as a method. If even this permissive bound provides less than +0.2 dB mean headroom over W, kill E3 immediately. A large oracle gap does not establish that the available features predict the right gate.

The uniform “warp covered / generation in holes” rule is already a negative result on the exposed development panel (`work/S137_geometry_baselines/RESULT.md:44-54`). The only reason to revisit fusion after A improves is that the generator has changed and local errors may now be complementary. If the fitted gate does not beat the constant-blend control, keep the simpler baseline. Even a successful gate improves the **composite predictor**, not the internal memory use of A. No calibration claim follows from naming g “confidence”; calibration would require a separate held-out reliability test.

### Compute basis and a bounded schedule

**MEASURED (archived), DERIVED aggregation:** the local S139 RTX 3090 logs contain 288 generations with mean 36.1144 seconds and median 35.56 seconds each. One 24-window ×4-seed arm therefore has a baseline cost of 0.9631 GPU-h. **UNVERIFIED training extrapolation:** S141's protocol reports a short smoke at 1.38 seconds/step, not a full-run measurement; 10,000 steps extrapolate to 3.8333 GPU-h before validation, checkpointing, contention, or changes to the representation (`work/S141_finetune/PROTOCOL.md:43-49`). Hence the wider training budget above. Exact arithmetic and source hashes appear in Appendix A.

A realistic use of the owner's resources is two parallel, independently seeded instances of the **same accepted trial** on the 3090s, or paired-control inference split across them, while the one H800 job processes a fixed transfer comparison with all its own controls. Do not confound methods with hardware or present two cards as pooled memory. Do not run every rejected idea merely to fill the cards.

Planning allocation: finish S141 artifacts and choose one branch during the first working day; allow up to three further days for implementation, fixed-budget training, scoring, and one independent training-seed check; freeze methods by the end of day four. Reserve the remaining time in the stated one-to-two-week window for analysis, figures, artifact cleanup by the main agent, and writing. Queue delay or failed engineering shrinks experiments, not writing time. These are proposed allocations, not claims of time already spent.

## (ii) Candidate ideas and strongest rejection

The candidates act at different points: conditioning representation, attention geometry, training robustness, attention capacity, objective, retrieval, and output fusion. Distinct mechanisms do not imply distinct publishable contributions. The Idea Evaluator skill's fatal-flaw lens was used for prior-art overlap and deadline fit; its generic scoring format was not used.

| Candidate | Hypothesis and minimal scientific test | Strongest rejection, including verified prior art where applicable | Verdict |
|---|---|---|---|
| **1. Trained warp-as-context through clean replace slots** | Aligned evidence can exploit a pretrained context path more readily than a new branch. E2 changes the conditioning representation and tests added value over the identical warp. | Rendering memory into diffusion conditioning is already established by **arXiv:2409.02048, “ViewCrafter: Taming Video Diffusion Models for High-fidelity Novel View Synthesis,” §III-C**, and **arXiv:2503.03751, “GEN3C: 3D-Informed World-Consistent Video Generation with Precise Camera Control,” §§4.3–4.4**. The exact VMem route differs; broad novelty does not. C may just copy the warp and discard useful unwarped evidence; S137c makes this a concrete failure mode. [ViewCrafter](https://arxiv.org/html/2409.02048v1#S3.SS3), [GEN3C](https://arxiv.org/html/2503.03751v1#S4.SS3) | **KEEP conditionally**, as one bounded adaptation experiment; not a new-method claim. |
| **2. Epipolar or depth-band attention bias** | Bias target/source attention toward geometrically plausible correspondences, preferably with a soft fallback outside the reliable depth band. Compare otherwise identical trained attention with and without the bias. | **arXiv:2303.17598, “Consistent View Synthesis with Pose-Guided Diffusion Models,” §3.2 and Appendix A.3**, already modulates cross-view attention using epipolar geometry. A depth band is not identical, but wrong CUT3R depth can confidently suppress the correct source. New kernels, masks, and fine-tuning create too many moving parts for this deadline. [Primary paper](https://arxiv.org/html/2303.17598v1) | **REJECT for this project window**; no generic epipolar novelty claim. |
| **3. Training-time warp/depth corruption augmentation** | Train B with fixed synthetic misalignment, dropout and depth-scale perturbations; compare with a schedule-matched clean-training B on both untouched and corrupted evidence. This targets robustness, not raw capacity. | If clean B cannot use correct geometry, adding corruption can teach it to ignore geometry. The corruption distribution may not match real visibility/depth error. No exact prior-art duplication is asserted from this search; “not verified as duplicated” is not novelty. Evidence currently supports a failed or successful clean interface only after S141, not an identified corruption failure. | **REJECT as the next experiment.** Reopen only in a later project after a clean trained interface works and a specific natural robustness failure is measured. |
| **4. Full-resolution cross-view attention** | Add spatial cross-view mixing at the largest latent scale instead of relying on coarse mixing for displaced details. | VMem already has cross-view mixing, so “introduce cross-view attention” is false: configured unflatten stages are `network.py:26-35`, with cross-frame flattening at `transformer.py:229-242` and same-position TimeMix at `transformer.py:146-155`. **arXiv:2405.17251, “GenWarp: Single Image to Novel Views with Semantic-Preserving Generative Warping,” §3.2**, already combines source cross-view and target self-attention with warped coordinate guidance. Full resolution is not an exact duplicate, but increases optimization and memory risk without a demonstrated resolution bottleneck. Doubling both spatial dimensions multiplies a global attention score matrix by 16, analytically; efficient kernels reduce materialization, not the need for computation. [GenWarp](https://arxiv.org/html/2405.17251v2#S3.SS2) | **REJECT.** Too expensive in engineering and interpretation, even if it fits on H800. |
| **5. Consistency distillation from the warp** | Add a covered-region decoded or latent consistency loss to teach copying trustworthy geometry; contrast against the same training without the loss. | The teacher is the imperfect baseline the model must beat. A dominating consistency loss reproduces its errors; an uncovered-region loss has no valid teacher. “Covered” does not mean correct depth or color. This is an analytical objection, not an unsupported claim of exact published duplication. A teacher cannot supply missing scene content by relabeling it supervision. | **REJECT the simple form.** Needs an independently justified reliability signal and a separate mechanism for improvement; those would become another project. |
| **6. Retrieve by reprojection coverage instead of pose distance** | Select four frames by marginal union coverage of the target cameras, rather than merely closeness; compare with actual VMem and pose-NMS at equal bank/slot budgets. | **arXiv:2506.18903, “VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory,” §3.1**, already uses rendered visible-surface support to select candidate views, followed by diversity control. Marginal joint coverage could differ, but “geometric coverage retrieval” is not new. On S139 the existing retrieved set already improves the geometric predictor while failing to improve generation; selector work therefore attacks an upstream stage with existing useful evidence (`S139/RESULT.md:31-51`). [VMem](https://arxiv.org/html/2506.18903v1#S3.SS1) | **REJECT as the next method.** A coverage baseline could be useful later; do not reopen generic selector tuning now. |
| **7. Uncertainty-aware fusion of warp and generation in pixel space** | Preserve geometry when locally reliable; use adapted generation only where errors are complementary. E3 fits a small gate and tests it against warp and constant blending. | Naive mask fusion already lost in S137c. **arXiv:2603.14965, “GeoNVS: Geometry Grounded Video Diffusion for Novel View Synthesis,” §§3.2–3.3**, already uses a learned pixel-wise residual confidence gate to fuse geometry with diffusion features. That is **feature-space**, not an exact RGB blend or proof of calibrated uncertainty; nonetheless adaptive fusion is not a new broad contribution. E3 could improve PSNR by smoothing, without improving video consistency or memory consumption. [GeoNVS](https://arxiv.org/html/2603.14965v1#S3.SS2) | **KEEP only as a low-cost baseline after A improves and B loses**, with oracle/constant-blend kills. |
| **8. Stop experimenting and write up** | Consolidate the repaired baseline, useful-evidence/generated-benefit separation, failed intervention, and S141 result into one reproducible case study. No new mechanism is needed to test whether the current claims are accurately supported. | It sacrifices the chance of a positive new-method result. One frozen consumer and one held-out room are insufficient for broad field conclusions; careful writing cannot manufacture novelty or external validity. | **KEEP.** Highest-confidence project deliverable and preferred choice if A and B both fail. |

Only candidates **1, 7, and 8** survive, and they are mutually conditional choices rather than a three-method sweep. E1 is validation of an existing positive S141 result, not an additional retained method.

The literature search verifies the mechanisms and metadata cited above; it is not an exhaustive novelty proof. In particular, it does not establish that warp corruption or calibrated RGB fusion has no prior art. It also does not establish superiority over ViewCrafter, GEN3C, GenWarp or GeoNVS; none was run in this review.

## (iii) Final ranked shortlist, maximum three

1. **Write the diagnostic study now; close it after S141 plus at most one selected follow-up.** This ranks first for expected value under the actual deadline. It yields an evidence-backed independent-project deliverable even if training is negative. If B succeeds, E1 is the most informative final addition, not a reason to launch more methods. If A and B both fail, writing wins outright over speculative architecture work.
2. **One trained warp-context challenger, E2, when B ties or loses and a final mechanism test is worth the bounded cost.** It directly tests a route supported by the observed same-pose behavior and uses existing data/caches. A success would be a useful, constrained adaptation result. Its overlap with published rendered-conditioning methods and its representation/pose confounds prevent calling it a novel causal channel discovery. A failure ends this direction for the deadline.
3. **A tiny learned pixel fusion baseline, E3, only when A improves but B loses.** It has a calculable oracle headroom check and a simple control, so it can fail cheaply. It ranks below E2 scientifically because postprocessing does not make the generator use memory. In its designated outcome cell, however, it outranks E2 as the practical experiment because it tests whether already improved A outputs complement the strong warp.

These ranks are not estimates of acceptance probability. None of the retained ideas currently supports a CCF-A method claim. Full GPU utilization is useful only while the jobs answer a frozen question; training replicas, complete baselines, and fixed transfer evaluation are better uses than parallel hyperparameter fishing.

## (iv) The stop-and-write option

### Strongest paper-shaped claim already supported

Suggested title, not a literature citation: **“When useful retrieved views fail to improve generation: a controlled VMem case study.”**

A defensible central claim is:

> In the tested frozen VMem configuration, after repairing geometry and memory-construction problems and correcting the camera convention, retrieved revisit views improve a geometric predictor but do not produce a detected PSNR improvement in generated frames over recent static contexts; generated-frame SSIM becomes worse on the tested chess panel. A selected training-free warp-guidance intervention improves development PSNR but does not exceed the warp on the primary chess confirmation metric.

This is a **configuration-specific diagnostic disconnect between evidence quality and generated-frame benefit**. It is not proof that retrieval is optimal, that the generator never uses memory, or that its attention architecture is the cause.

| Evidence in the existing record | Quantitative result and provenance | Supported scope |
|---|---|---|
| Positive control: convention correction | **MEASURED (archived):** +0.890 dB, CI [+0.248,+1.469], `work/S136_repaired_memory/results/S136_ANALYSIS.json:3-16`. | The configured static predictor responds to a consequential input correction. |
| Repaired memory versus static | **MEASURED (archived):** −0.059 dB, CI [−1.153,+0.942], `work/S136_repaired_memory/results/S136_ANALYSIS.json:57-70`. | No detected aggregate gain; interval is much too wide to establish equivalence. |
| Scale repair reaches a downstream predictor | **MEASURED (archived):** KPS warp−threshold-fixed warp +1.752 dB, CI [+0.846,+2.821] rounded, `work/S137_geometry_baselines/SUMMARY_s136ref_v2map.json:14-23`. | Practical repair evidence; not established novelty of scale estimation. |
| Revisit contexts contain useful geometric evidence | **MEASURED (archived):** warp(memory)−warp(static) +1.46 dB, CI [+0.91,+2.05], `work/S139_crossseq_revisit/RESULT.md:31-38`, backed by `results/S139_BASELINE_CONTRASTS.json:2-4`. | Same selected views are useful to that geometric predictor. |
| That advantage does not become generated-frame PSNR benefit | **DERIVED from archived scores:** memory−static −0.180511 dB, 10/24 positive windows; archived CI [−0.517718,+0.144749], `work/S139_crossseq_revisit/results/S139_ANALYSIS.json:4-21`; Appendix A recomputation. | Limited-panel negative result, not an absence-of-influence result. |
| A second frame metric agrees on memory versus static | **MEASURED (archived):** SSIM −0.018989, CI [−0.032331,−0.006068], `work/S140_warp_guided/results/s139_ssim/S139_SSIM_ANALYSIS.json:15-25`. | Supports the specific generated-frame comparison. |
| Sampling intervention does not replicate its PSNR gain | **DERIVED:** WGS−warp +0.020282 dB; archived CI [−0.094608,+0.134346], `work/S140_warp_guided/results/CONFIRM_ANALYSIS.json:9-26`. SSIM improves by +0.025147, `CONFIRM_ANALYSIS.json:89-106`. | Failed primary confirmation, with a genuine metric-dependent secondary benefit. |
| Geometry does not dominate under all metrics | **MEASURED (archived):** warp−VMem SSIM −0.038529, CI [−0.068528,−0.008501], `work/S140_warp_guided/results/CONFIRM_ANALYSIS.json:137-154`. | “Warp beats generation” must specify PSNR on chess. |

### Weakest link a reviewer would attack

**The mechanism and generality claims outrun the experimental unit.** One consumer, one chess room, three trajectory pairs with shared history, and reconstruction metrics do not establish a general memory-consumption bottleneck or a cause inside the architecture. The evidence also comes from posed observed-view prediction rather than a demonstrated long autonomous rollout. The report itself acknowledges limited scenes, seed/hardware confounding, approximate intrinsics, and unverified pretraining exposure (`docs/report/TECHNICAL_REPORT_20261010.md:181-185`).

The sharpest corrections are:

- Replace “the generator does not use it” by “the retrieved-view advantage does not become a detected generated-frame benefit under these metrics.” Influence and improvement are different estimands.
- Keep the hole-content explanation **UNVERIFIED**. Covered versus hole effects were measured, but “crop bands visible in context versus truly unseen disocclusions” remains a hypothesis (`work/S140_warp_guided/RESULT.md:34-37`; `work/agents/SELF_AUDIT_S140.md:14-16`). The report's assertion at `TECHNICAL_REPORT_20261010.md:178-179` is too strong.
- Do not describe all defects as upstream VMem bugs: the priming holes came from this project's construction schedule (`work/S135_scale_init/RESULT.md:53-57`; `TECHNICAL_REPORT_20261010.md:75-79`).
- Shared intrinsics across arms do not prove calibration errors cancel: different source viewpoints and consumers can respond differently. Treat the nominal calibration as a common assumption, not an immunity argument.
- Do not call the frozen-consumer search exhaustive. S140 rejects the selected intervention in the tested setting; it does not prove only fine-tuning can help. Likewise, S141 failure would reject these training recipes, not all trainable geometry conditioning.
- Do not let adaptation on six scenes erase the need for external validity. Chess remains held out from training but has been repeatedly examined by the project.

### Honest comparison with more experiments

For CSIT6910, the strongest deliverable is a reproducible case study with corrected claims, explicit negative results, and a compact final adaptation section. Stopping is a scientific choice when another experiment would add an established component without resolving the core uncertainty. It is not proof that the broader research problem is exhausted.

For a method paper, the missing evidence is harder: gains over strong geometric and adapted-generator controls, scene-level transfer beyond the exposed panels, useful evidence dependence rather than mere copying/sabotage sensitivity, and perceptual/temporal evaluation. One additional small adapter cannot be promised to supply all of that. A positive S141 result should narrow the missing experiment; a negative one should narrow the claim.

**Changed file for this review:** `work/agents/CODEX_R255_IDEATION_AFTER_S141.md` only. **Follow-up for the main research session:** validate S141's actual artifact completeness, apply the relevant outcome cell once, and revise the manuscript's overstated mechanism/equivalence language. No ledger, source, protocol, or concurrent artifact was edited here.

## Appendix A — Exact CPU verification commands and complete output

These are read-only CPU calculations, not new image generation or training. The first was performed by the evidence-review sub-agent; it independently recomputed aggregates from archived score records, not from unavailable remote RGB outputs. The second was performed by the main reviewer and records the inspected snapshot and resource arithmetic. Working directory for both: `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling`.

### A1. Archived S139/S140 arithmetic

```bash
python3 -B - <<'PY'
import json, math, statistics as st
from pathlib import Path
root=Path('.')
def load(p): return json.loads((root/p).read_text())
runs={}
for site in ('superpod','tacc'):
 runs.update(load(f'work/S139_crossseq_revisit/results/stepB_{site}/S139_SCORES_{site}.json')['runs'])
err=0.0; by={}
for r in runs.values():
 mse=sum(f['squared_integer_sum'] for f in r['frames'])/(sum(f['channel_value_count'] for f in r['frames'])*255**2)
 err=max(err,abs(-10*math.log10(mse)-r['aggregate']['psnr_db']))
 for a in r['arms']: by.setdefault((r['window_id'],a),{})[r['seed']]=r['aggregate']['psnr_db']
wins=sorted({w for w,a in by})
d=[st.mean(by[(w,'mem_vmem')][s]-by[(w,'static_recent')][s] for s in by[(w,'mem_vmem')]) for w in wins]
print(f'S139 scored_runs={len(runs)} windows={len(wins)} seeds_per_cell={sorted({len(x) for x in by.values()})} aggregate_max_error_from_integer_SSE={err:.3g}')
print(f'S139 mem_vmem-static mean={st.mean(d):.12f} positive_windows={sum(x>0 for x in d)}/{len(d)}')
wgs={}; warps={}
for sub,f in [('confirm_superpod','S140_SCORES_confirm.json'),('confirm_tacc','S140_SCORES_confirm_tacc.json')]:
 j=load(f'work/S140_warp_guided/results/{sub}/{f}'); wgs.update(j['runs']); warps.update(j['warps'])
for metric,wk in [('psnr_db','psnr'),('ssim','ssim')]:
 by={}
 for r in wgs.values(): by.setdefault(r['window_id'],[]).append(r[metric])
 ds=[st.mean(x)-warps[w][wk] for w,x in sorted(by.items())]
 print(f'S140 WGS-B2 {metric} mean={st.mean(ds):.12f} positive_windows={sum(x>0 for x in ds)}/{len(ds)}')
for metric,base in [('psnr_covered','warp_psnr_covered'),('psnr_holes','warp_psnr_holes')]:
 by={}
 for r in wgs.values(): by.setdefault(r['window_id'],[]).append(r[metric]-r[base])
 ds=[st.mean(x) for x in by.values()]
 print(f'S140 WGS-B2 {metric} mean={st.mean(ds):.12f} positive_windows={sum(x>0 for x in ds)}/{len(ds)}')
print(f'S140 scored_runs={len(wgs)} windows={len(warps)}')
PY
```

```text
S139 scored_runs=576 windows=24 seeds_per_cell=[8] aggregate_max_error_from_integer_SSE=3.55e-15
S139 mem_vmem-static mean=-0.180511407142 positive_windows=10/24
S140 WGS-B2 psnr_db mean=0.020282133891 positive_windows=14/24
S140 WGS-B2 ssim mean=0.025146985194 positive_windows=19/24
S140 WGS-B2 psnr_covered mean=0.243982956563 positive_windows=23/24
S140 WGS-B2 psnr_holes mean=-0.240847771221 positive_windows=8/24
S140 scored_runs=192 windows=24
```

### A2. Local plan, timing, size, and source snapshot

```bash
python3 -B - <<'PY'
import json, statistics as st, hashlib
from pathlib import Path
p=Path('work/S141_finetune/clips_s141.json')
j=json.loads(p.read_text())
print('clips_sha256='+hashlib.sha256(p.read_bytes()).hexdigest())
print('clips_summary='+json.dumps(j['summary'],sort_keys=True))
rows=[]
for p in sorted(Path('work/S139_crossseq_revisit/results/stepB_tacc').glob('RUNS_*.jsonl')):
 rows.extend(json.loads(s) for s in p.read_text().splitlines() if s.strip())
secs=[r['seconds'] for r in rows]
print(f'baseline_3090_runs={len(rows)} median_sec={st.median(secs):.4f} mean_sec={st.mean(secs):.4f} min_sec={min(secs):.2f} max_sec={max(secs):.2f}')
print(f'96_generations_baseline_gpu_hours={96*st.mean(secs)/3600:.4f}')
print(f'10000_steps_at_reported_1.38_sec_gpu_hours={10000*1.38/3600:.4f}')
print(f'2032_warp_latent_and_coverage_fp32_GiB={2032*4*5*72*72*4/2**30:.4f}')
print(f'96_saved_4_frame_float32_rgb_GiB={96*4*3*576*576*4/2**30:.4f}')
for name in ['S139_crossseq_revisit','S140_warp_guided']:
 print(name+'_result_sha256='+hashlib.sha256(Path('work',name,'RESULT.md').read_bytes()).hexdigest())
for name in ['PROTOCOL.md','train_s141.py','s141_common.py','analyze_s141.py','s141_chainB.sh']:
 print('S141_'+name+'_sha256='+hashlib.sha256(Path('work/S141_finetune',name).read_bytes()).hexdigest())
print('r255_output_already_exists='+str(Path('work/agents/CODEX_R255_IDEATION_AFTER_S141.md').exists()))
PY
```

```text
clips_sha256=c2fbdd49e87426d837aa5e90a8e694cddd9032864079cef53c29a66991740f36
clips_summary={"kinds": {"memory": 1028, "static": 1004}, "mean_hist_frac_memory": 0.7290856031128404, "n_train": 2000, "n_val": 32, "scenes": {"fire": 210, "heads": 97, "office": 493, "pumpkin": 305, "redkitchen": 608, "stairs": 319}, "val_seqs": ["office/seq-10", "redkitchen/seq-14"]}
baseline_3090_runs=288 median_sec=35.5600 mean_sec=36.1144 min_sec=34.46 max_sec=37.75
96_generations_baseline_gpu_hours=0.9631
10000_steps_at_reported_1.38_sec_gpu_hours=3.8333
2032_warp_latent_and_coverage_fp32_GiB=0.7848
96_saved_4_frame_float32_rgb_GiB=1.4238
S139_crossseq_revisit_result_sha256=a09a20a359acc31755a511b8b81ad56747f6046a2c750c5287ef6ab07e4e0f05
S140_warp_guided_result_sha256=2db2f7ed6d3184a5cdc5b39c369d98bd2c558e55f56e0513fc3f86292f58634c
S141_PROTOCOL.md_sha256=5833bd1177ae2e0f776de84c903e0919d09b2f1977d114ddd3013ea63b7f20a2
S141_train_s141.py_sha256=6ba0419e5ceb39406bbd1894ffae90398c27daedbc2eea56b18e537ba6187c0a
S141_s141_common.py_sha256=459549706fb3a965fc4f7c5021f4d49cc626158e94a7c9cdc94cf8784cccb6cc
S141_analyze_s141.py_sha256=df8e360a036bc82969ecfcbaa0c8deefa94e140b45342c5801470b2d9161a90a
S141_s141_chainB.sh_sha256=484ada5b07bfcbd260f56d158d6da0c6e3f860838e0294e08eec64646e83ee68
r255_output_already_exists=False
```

The `r255_output_already_exists=False` line records the pre-write check. Raw source/result hashes identify this inspected snapshot only. Archive/weight hashes stated in the S141 protocol and remote runtime state were not independently checked here. No new numerical experiment, test suite, or linter run is claimed; this deliverable changes prose only.
