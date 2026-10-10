# R259 — New evaluation and analysis angles for memory world models

Date: 2026-10-10. Workspace: local Mac checkout. Scope: ideation, source inspection, public-literature/release verification, and CPU analysis of archived artifacts. S141 outcomes remain pending for this review; none was inspected or awaited.

**Run the finite-candidate evidence-versus-consumer ranking experiment first.** Its strongest question is not whether memory is ignored, but whether the contexts that are best for geometric reconstruction are also best for the actual generator. Pair it with a controlled input-path sensitivity experiment and a metric/visibility audit. These are three bounded evaluation experiments, not three proposed generators.

There is already a useful new lead in the archived results: a target-informed, split-seed consumer selector beats the warp-informed selector by approximately **0.31 dB** on the existing three context sets. This is **DERIVED, exploratory, and unattainable as a deployed selector**; it is not a new method result. It makes a ranking-mismatch study more promising than merely restating the mean S139 negative. Exact commands and complete outputs are in Appendix A.

The plausible paper contribution is a reproducible diagnostic that separates **evidence utility, conditioning influence, and reference-quality benefit**, with a finding that survives appropriate controls and another consumer. None of those concepts alone is new. A generic revisit benchmark, a claim that memory can be ignored, or a consumer-aware retriever would overlap substantially with verified prior art.

Only this file is authored in this review. No GPU/model inference, training, weight or dataset download, SSH, scheduler submission, external contact, or change to existing files was performed. The specific one-file instruction supersedes routine ledger updates. **new_method_validated=false; novelty_authorization=NONE.**

## 1. Evidence boundary and corrections to the brief

Evidence labels throughout:

- **MEASURED (archived):** measurements stored by earlier runs; not regenerated here.
- **DERIVED:** arithmetic or inventory computed in this review, with command/output receipts below.
- **ANALYTICAL:** proposed definitions, thresholds, experiment counts, or planning estimates.
- **UNVERIFIED:** remote state, untested mechanisms, runtime compatibility, or missing evidence.

All future numerical thresholds are ANALYTICAL decisions, not observed gains. Source citations are repository-relative. For compact citations, S139/ means work/S139_crossseq_revisit/, S140/ means work/S140_warp_guided/, S141/ means work/S141_finetune/, S137/ means work/S137_geometry_baselines/, and V/ means data/S134_tacc/vmem_src/. Public code links pin their own commits; those are not asserted identical to the transported GPU source.

The required context was reviewed: CURRENT_STATUS.md; the S133–S140 technical report; S139/S140 RESULT files; S141 and S142 protocols; and R253/R255/R256. The older memory registry was used only to locate continuity; current files supersede it. In particular:

| Verified boundary | Evidence and consequence |
|---|---|
| S139 already demonstrates different geometric and generated utility. | **MEASURED (archived):** warp(mem)−warp(static) +1.46 dB; generation(mem)−generation(static) −0.181 dB, with the latter CI spanning zero. S139/RESULT.md:17–42; underlying files S139/results/S139_ANALYSIS.json and S139/results/S139_BASELINE_CONTRASTS.json. Repeating that scatter plot alone is not a new contribution. |
| S140's ordering depends on the metric. | **MEASURED (archived):** chess means WGS/B2/VMem are 14.59/14.57/11.36 dB but SSIM 0.457/0.432/0.470. S140/RESULT.md:20–29; S140/results/CONFIRM_ANALYSIS.json. The existing evidence does not say the warp is universally better. |
| There are 2,000 training clips plus 32 monitor clips, not 2,032 training clips. | **DERIVED:** manifest count in Appendix B. The builder and trainer distinguish splits: S141/build_clips_s141.py:14,43–70; S141/train_s141.py:26–38. |
| The six other 7-Scenes scenes are training scenes for A/B. | S141/PROTOCOL.md:17–26,90–99. More windows there can broaden a frozen-base audit; they cannot establish A/B scene generalization. The stated 7,400-frame cache and completed remote adapter artifacts were not independently inventoried here. |
| Chess is no longer untouched research confirmation data. | docs/report/TECHNICAL_REPORT_20261010.md:184–192; S141/PROTOCOL.md:97–99. New seeds or a newly written protocol do not make these windows unseen. |
| The other panel is RGB-D Scenes v2 scenes 13/14 in 3DMatch packaging. | docs/report/TECHNICAL_REPORT_20261010.md:56–58,221; S137/geometry_baselines.py:19–21. It is not a broad 3DMatch/ScanNet benchmark. |
| Scores and warps are locally available, but generation payloads are not. | **DERIVED:** Appendix B counts no prediction .npy files under the inspected S139/S140 result roots. LPIPS, intervention-output distances, and new pixel metrics require the existing predictions to be made available or scored at their storage location in a later run. |
| Sensor-depth coverage is incomplete. | **DERIVED:** no local chess depth or matching archive found under data; twelve RGB-D windows have all context and target depths. Appendix B gives exact paths and counts. Historical remote dataset paths at S139/s139_stepA.slurm:22,28–41 do not verify current remote availability. |
| S142 is an existing, separate contract. | work/S142_followup/PROTOCOL.md:9–32,34–54 fixes outcome-dependent E1/E2 and its stop rule. R259 proposes evaluation work; it neither changes that branch table nor launches another learned-consumer search. |

Some older wording is too strong. “Retrieval is not the bottleneck” does not establish optimal retrieval; “the generator does not use it” confuses influence with benefit. The current report's narrower wording is preferable (docs/report/TECHNICAL_REPORT_20261010.md:163–189). R253:119–125 already recommends the utility/benefit separation; R259 must add identifiable measurements and new empirical evidence, not rename that recommendation.

## 2. Divergence: fifteen distinct candidates

These are hypotheses, not novelty declarations. Five candidates receive the focused prior-art audit in §3; the rest are explicitly not cleared for novelty.

| # | Pipeline location and candidate | Falsifiable question / useful measurement | Decision for this deadline |
|---|---|---|---|
| **1** | **Retrieval-to-consumer interface: finite-set utility and ranking diagnostic** | Across the same fixed context sets, how often does geometric utility rank contexts differently from held-seed generated benefit? Quantify geometric headroom and consumer-selection shortfall separately. | **Retain; first experiment.** More informative than a single memory−static mean. |
| **2** | **Conditioning paths: localized source interventions** | Does a modest source-appearance intervention propagate through clean context latents, averaged CLIP, or both; is the response concentrated on projected source support? | **Retain.** Separates influence from beneficial consumption. |
| **3** | **Rendering/evaluation: audit what “uncovered” means** | Are holes missing scene evidence, discarded crop support, raster gaps, or unreliable geometry? Does this explain a metric ordering reversal? | **Retain as supporting analysis.** True visibility labels need independent depth. |
| **4** | **Data construction: real RGB-D finite-bank revisit testbed** | Can a frozen bank, target poses, actual consumed contexts, and finite-set oracle make retrieval/consumer failures reproducible? | **Fold into #1.** Useful artifact; a small new benchmark is not automatically a paper. |
| **5** | **Utility/temporal state: consumer-specific recall and stale-memory choice** | Does the same geometric view support the wrong scene state; does a consumer prefer a different history than overlap predicts? | **Reject as standalone novelty.** FAR is close prior art; existing static-room assets also lack verified state-change labels. |
| 6 | Camera interface: world-coordinate gauge sensitivity | Apply a common rigid world transform to all cameras, preserving physical rays. Does normalization/numerical handling create output changes? | Cheap harness control, not an independent memory method; novelty unchecked. |
| 7 | Slot allocation: order versus set identity | With the same images and physical cameras, does permutation of slots change generation more than replacing an image? | Diagnostic appendix if needed. Preserve a canonical order in #1; slot-0 effects are already documented locally. |
| 8 | Memory capacity: marginal utility versus redundancy | Does adding a distinct view improve geometric support without improving generation compared with duplicate or pose-nearest slots? | Interesting budget curve, but changing frame counts can leave the pretrained operating regime. Defer unless fixed-slot replacements suffice. |
| 9 | Temporal policy: age versus geometry | At matched pose/coverage, do older and newer observations have different influence or benefit? | Worth a later natural-history study. These cross-traversal data do not provide a clean causal age intervention. |
| 10 | Geometry estimator: graceful degradation | At fixed images, vary a prespecified depth-scale/noise corruption and compare the degradation of warp and consumer. | Robustness diagnostic; partly overlaps GenRec (§3). Do not turn it into a new corruption-trained generator. |
| 11 | Denoising: when evidence enters | Restrict a context intervention to early or late denoising steps and measure persistence of its output response. | Potentially mechanistic, but downstream trajectories must be recomputed; not a substitute for useful input evidence. Defer until #2 shows a signal. |
| 12 | Rollout feedback: observed versus self-generated history | Under the same poses, how quickly does replacing real historical RGB with previous generated RGB erase evidence utility? | Strong longer-term question. Four-target clips do not yet establish long-rollout behavior; sequence plumbing risks the deadline. |
| 13 | Numerical execution: retrieval discontinuities | Does tiny floating-point variation change selected contexts, and does it materially change generation? | Useful reproducibility appendix, not a new central idea: TF32/NMS effects are already in CURRENT_STATUS.md:18–21. |
| 14 | Memory storage: distortion versus useful evidence | Compress/resize the stored RGB at fixed camera/slot budget; compare utility and consumer-benefit curves against bytes and latency. | Systems/evaluation angle distinct from a generator. Prior-art review still needed; no bandwidth/storage bottleneck has been measured here. |
| 15 | Output geometry: consistency versus correctness | Can a repeated frame or mutually wrong generated pair beat a geometrically correct predictor on a consistency metric? | Mandatory metric negative control in #3, not a new “3D consistency” metric by itself. |

The useful direction is an **evaluation study with a construction pipeline**, not a new generator and not an assertion that a new metric is intrinsically better. Generic selector tuning remains low value unless the new diagnostic identifies a concrete, recoverable failure.

## 3. Focused prior-art audit of the five most promising angles

All titles below were checked on arxiv.org during this run. Public preprints count as prior art; their presence does not certify peer review. The search included memory utility/predictive relevance, counterfactual interventions, revisit benchmarks, geometric consistency, metric rank reversal, and released implementations. “No exact match located” is bounded retrieval evidence, not a firstness claim.

### A. Same-context evidence utility versus consumer benefit — candidate 1

Closest work: **arXiv:2609.34677, “Learning What to Recall: Adaptive Multi-Cue Episodic Memory for World Models,” §§3.1–3.3**. FAR already defines consumer-dependent predictive utility and trains retrieval using realized-future likelihood approximated through diffusion prediction loss. Thus “learn which memory is useful to the generator” is published. [Verified record](https://arxiv.org/abs/2609.34677), [method](https://arxiv.org/html/2609.34677v1#S3).

Two other overlaps matter. **arXiv:2606.31734, “MemLearner: Learning to Query Context memory for Video World Models,” §5.4 and Appendix C.2**, reports an unsuccessful separate query-conditioning design. **arXiv:2512.15716, “Spatia: Video Generation with Updatable Spatial Memory,” §4.2/Table 4**, separates reference and projection conditioning experimentally. Ignored conditioning and projection/reference ablations are therefore not new observations in general. [MemLearner](https://arxiv.org/html/2606.31734v1), [Spatia](https://arxiv.org/html/2512.15716v1).

**Precise proposed difference:** an external geometric predictor and a sampled generator are both evaluated on identical, explicitly enumerated context sets; their target-informed rankings and held-seed selection shortfall are compared. Neither a likelihood-trained retriever nor a component ablation measures exactly this. The contribution would be the controlled diagnostic and replicated finding, not the concept of utility. No exact duplicate of that full design was located in the inspected works.

Counterevidence must remain visible: **arXiv:2506.18903, “VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory,” §4.4/Table 4**, reports positive retrieval ablations on its cycle trajectories. A new real-revisit result must explain its task/configuration scope instead of declaring that VMem universally fails. [Paper](https://arxiv.org/html/2506.18903v3).

### B. Counterfactual post-retrieval conditioning interventions — candidate 2

Closest framework: **arXiv:2608.08982, “Twin Rollouts: Noise-Coupled Counterfactual Branching in Interactive Video World Models,” §2**, already formalizes shared-noise branches and spatial locality; the inspected version is a framework note with large-scale experiments deferred. **arXiv:2609.36843, “RolloutFaith: Auditing Persistent Internal Interventions in Visual World Model,” §§3.3–3.4 and §5**, audits internal edits and component restoration under controlled rollout conditions. Its abstract title is singular “Model”; the HTML title uses “Models.” [Twin Rollouts](https://arxiv.org/abs/2608.08982), [framework](https://arxiv.org/html/2608.08982v1#S2), [RolloutFaith](https://arxiv.org/abs/2609.36843).

**Precise proposed difference:** intervene after retrieval on source RGB-derived latent conditioning versus source CLIP, while keeping camera geometry fixed; measure response relative to source-projected support. This is an **input-path sensitivity assay**, not an action counterfactual, a physical-world causal intervention, or activation editing. Shared seeds, locality, and restoring a path are established techniques. Without an informative localization/benefit finding, this is an ablation appendix.

### C. Hole taxonomy and metric ordering — candidate 3

Closest region precedent: **arXiv:2608.17832, “GenRec: Knowing Where to Reconstruct and Where to Generate,” §4 and Appendix B** already evaluates observed/unobserved regions and studies depth/mask errors. Geometry-consistency evaluation is also established by **arXiv:2501.06336, “MEt3R: Measuring Multi-View Consistency in Generated Images,” §§3 and 5.4**. **arXiv:2511.12675, “Appreciate the View: A Task-Aware Evaluation Framework for Novel View Synthesis,” §§4.2, 4.4, 4.6**, studies task/pose sensitivity of common image metrics. [GenRec](https://arxiv.org/abs/2608.17832), [inspected v1](https://arxiv.org/html/2608.17832v1), [MEt3R](https://arxiv.org/html/2501.06336v1), [task-aware evaluation](https://arxiv.org/html/2511.12675v1).

**Precise proposed difference:** independently audit whether this pipeline's nominal holes actually lack observed scene evidence, then test whether those categories and deterministic filling explain a warp/generator ranking reversal. Region scoring or adding LPIPS alone is not novel.

A learned geometry evaluator is not independent ground truth. **arXiv:2605.18754, “Can These Views Be One Scene? Evaluating Multiview 3D Consistency when 3D Foundation Models Hallucinate,” §§3–5**, examines misleading geometric agreement from reconstruction models. This motivates a sensor-depth audit and an explicit unknown category. [Paper](https://arxiv.org/html/2605.18754v1).

### D. Small real-revisit benchmark with a geometric oracle — candidate 4

Closest benchmark: **arXiv:2608.27328, “R2M-Bench: Evaluating Revisit Memory via Relative Consistency in Interactive Video World Models,” §§3–4**, calibrates revisit similarity against same-rollout temporal controls. **arXiv:2602.08025, “MIND: Benchmarking Memory Consistency and Action Control in World Models,” §§3.1, 3.4–3.5**, evaluates constructed revisit trajectories. **arXiv:2606.00793, “MBench: A Comprehensive Benchmark on Memory Capability for Video World Models,” §§2–3**, already uses real-captured videos. Real trajectories, revisit consistency, and multiple metric families are not unoccupied contribution space. [R2M-Bench](https://arxiv.org/html/2608.27328v1), [MIND](https://arxiv.org/html/2602.08025v1), [MBench](https://arxiv.org/html/2606.00793v1).

**Precise proposed difference:** a posed historical RGB-D bank, fixed candidate context sets, actual consumed evidence, and target-only geometric/consumer oracle diagnostics. This supports a small mechanistic testbed. It does not justify “comprehensive world-model benchmark”; the existing four-target windows do not constitute autonomous closed-loop video rollouts.

### E. Consumer-specific utility / stale-memory evaluation — candidate 5

FAR's **arXiv:2609.34677, “Learning What to Recall: Adaptive Multi-Cue Episodic Memory for World Models,” §4.3/Fig. 7**, also studies stale states and different histories with the same current observation/action. [Experiment](https://arxiv.org/html/2609.34677v1#S4.SS3).

**Reject as a standalone new idea here.** The remaining opportunity is to use finite-set consumer regret as a measurement inside A, without training another retriever. Testing actual state changes would additionally require validated state-changing data; painting a patch in a static room is not a real stale-state benchmark.

## 4. Which other models are actually usable?

This is a release audit, not a runtime reproduction. Appendix C records live repository and checkpoint-manifest responses. A repository, a project page, a checkpoint file listing, and a successful task-specific run are different evidence levels.

| Model / verified arXiv identity | Code and weight status at inspection | Practical judgment |
|---|---|---|
| **WorldMem**, 2504.12369, **“WorldMem: Long-term Consistent World Simulation with Memory”**, §§3–4. [arXiv](https://arxiv.org/abs/2504.12369) | [xizaoqu/WorldMem](https://github.com/xizaoqu/WorldMem), commit c1cc91bdfb2dda52fe309280e5ed046b1faba448. [Checkpoint manifest](https://huggingface.co/api/models/zeqixiao/worldmem_checkpoints) lists diffusion/VAE/pose checkpoints, ungated. | Released inference wires those weights to Minecraft. A released RealEstate10K checkpoint was not verified. Not a cheap real-scene comparator merely because the paper also studies real scenes. |
| **Context as Memory**, 2506.03141, **“Context as Memory: Scene-Consistent Interactive Long Video Generation with Memory Retrieval”**, abstract. [arXiv](https://arxiv.org/abs/2506.03141) | [Official project](https://context-as-memory.github.io/) labels GitHub “Coming Soon”; linked [KwaiVGI/Context-as-Memory](https://github.com/KwaiVGI/Context-as-Memory) returns 404 in the API audit. | Neither runnable official inference nor released model weights verified. A dataset release does not fill that gap. |
| **Spatia**, 2512.15716, **“Spatia: Video Generation with Updatable Spatial Memory”**, §§3.1–3.2. [arXiv](https://arxiv.org/abs/2512.15716) | [ZhaoJingjing713/Spatia](https://github.com/ZhaoJingjing713/Spatia), f75b10c9bb5f6b0cd779ec8c41ab33dd8382dba3. [Checkpoint manifest](https://huggingface.co/api/models/Jinjing713/Spatia) lists control_weight_8500.safetensors and lora_weights_10000.safetensors. | Real inference code and weights exist. External fixed-memory wrapper needed; 3090 memory fit and runtime unverified. Plausible fallback consumer. |
| **MemLearner**, 2606.31734, **“MemLearner: Learning to Query Context memory for Video World Models”**, abstract. [arXiv](https://arxiv.org/abs/2606.31734) | [Official project](https://yujiwen.github.io/memlearner/) provides paper/demonstrations; no official runnable repository or weights verified in this bounded search. | Do not schedule as an available second model; do not assert global nonexistence. |
| **VMem**, 2506.18903, **“VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory”**, abstract. [arXiv](https://arxiv.org/abs/2506.18903) | [runjiali-rl/vmem](https://github.com/runjiali-rl/vmem), 39291e4f272f6b4f270691d930926ab5930f942e. [Checkpoint manifest](https://huggingface.co/api/models/liguang0115/vmem) lists vmem_weights.pth with automatic gating. | Existing first consumer. Audit the project's transported source/checkpoint, not an assumed equality with current upstream. |
| **GEN3C**, 2503.03751, **“GEN3C: 3D-Informed World-Consistent Video Generation with Precise Camera Control”**, §§4.1–4.3. [arXiv](https://arxiv.org/abs/2503.03751) | [nv-tlabs/GEN3C](https://github.com/nv-tlabs/GEN3C), db2ffe12ced12ddafcec5e0422ee46ce8520746b. [Checkpoint manifest](https://huggingface.co/api/models/nvidia/GEN3C-Cosmos-7B) lists model.pt, ungated. | Best conditional second consumer because its native multiview interface accepts posed RGB-D. Use the H800 path only after a bounded smoke test in a later run. |
| **LSM-World**, 2606.09828, **“Latent Spatial Memory for Video World Models”**, abstract. [arXiv](https://arxiv.org/abs/2606.09828) | [microsoft/LatentSpatialMemory](https://github.com/microsoft/LatentSpatialMemory), be530516a8b8c79ae5d5dff543b4d1640f59bd54, has substantive code; released trained checkpoint URLs were not verified. | Code existence is insufficient for a two-day consumer commitment. |

Implementation facts behind that judgment:

- WorldMem's [infer.sh:6–11](https://github.com/xizaoqu/WorldMem/blob/c1cc91bdfb2dda52fe309280e5ed046b1faba448/infer.sh#L6) loads the released checkpoints and Minecraft data. Its [df_video.py:203–214](https://github.com/xizaoqu/WorldMem/blob/c1cc91bdfb2dda52fe309280e5ed046b1faba448/algorithms/worldmem/df_video.py#L203) constructs centered K from a scalar focal length; [791–805,831–836](https://github.com/xizaoqu/WorldMem/blob/c1cc91bdfb2dda52fe309280e5ed046b1faba448/algorithms/worldmem/df_video.py#L791) implements action/pose-conditioned interaction. Porting Kinect scenes would confound domain and camera interface.
- Spatia's [inference.py:145–188](https://github.com/ZhaoJingjing713/Spatia/blob/f75b10c9bb5f6b0cd779ec8c41ab33dd8382dba3/inference.py#L145) loads the base/control/LoRA models and configures offloading; [565–584](https://github.com/ZhaoJingjing713/Spatia/blob/f75b10c9bb5f6b0cd779ec8c41ab33dd8382dba3/inference.py#L565) exposes input_video, control_video, control_score, ref_images. Supplying fixed external warps there evaluates an adapted consumer, not the native end-to-end Spatia memory system.
- GEN3C's [gen3c_multiview.py:179–188,226–249](https://github.com/nv-tlabs/GEN3C/blob/db2ffe12ced12ddafcec5e0422ee46ce8520746b/cosmos_predict1/diffusion/inference/gen3c_multiview.py#L179) accepts keyframe images/depth/masks/K/w2c and target trajectories, then passes rendered warps/masks to generation. **Its native maximum is two buffers**, set at [line 176](https://github.com/nv-tlabs/GEN3C/blob/db2ffe12ced12ddafcec5e0422ee46ce8520746b/cosmos_predict1/diffusion/inference/gen3c_multiview.py#L176). [cache_3d.py:373–411](https://github.com/nv-tlabs/GEN3C/blob/db2ffe12ced12ddafcec5e0422ee46ce8520746b/cosmos_predict1/diffusion/inference/cache_3d.py#L373) selects by overlap and further handles near-full masks. Log and score the final consumed rendering, not the union of all submitted views. Keyframe zero seeds generation ([line 243](https://github.com/nv-tlabs/GEN3C/blob/db2ffe12ced12ddafcec5e0422ee46ce8520746b/cosmos_predict1/diffusion/inference/gen3c_multiview.py#L243)).
- **MEASURED by upstream authors, not here:** GEN3C's [README:144–155](https://github.com/nv-tlabs/GEN3C/blob/db2ffe12ced12ddafcec5e0422ee46ce8520746b/README.md#L144) reports H100/A100 testing and roughly 43 GB observed with full offload. That supports an H800 feasibility hypothesis, not a 3090 promise or a measured H800 speed.

**Second-consumer plan, conditional:** allocate at most half a working day to a GEN3C NPZ adapter and one native smoke in a later authorized session. Keep its first source image fixed; vary only a second source with its matching depth/pose. Score exactly the warps it consumed, at its native preprocessing/resolution. A short panel can then repeat the utility-versus-benefit diagnostic under its two-buffer contract. Report per-model effects, not an unfair two-versus-four-context leaderboard. VMem VAE latents and CLIP caches cannot simply be reused as another backbone's representations.

Allow at most **12 H800 GPU-hours as a spending cap**, not a throughput estimate. If timing, weights/dependencies, output length, pose conversion, or the adapter cannot fit the cap after the smoke, stop the port and retain a one-family claim. Neither this model nor its dependencies were downloaded here. A/B are useful within-family probes when ready; they are not independent architectures.

## 5. New CPU evidence that changes the research question

### 5.1 Geometry is informative, but its preferred context is not always the consumer's

Appendix A joins the existing three candidate sets, all twenty-four chess windows, and only RTX 3090 seeds 3–6. This avoids pooling hardware-confounded seed blocks. E is warp(mem_vmem)−warp(static_recent); B is generation(mem_vmem)−generation(static_recent).

| Quantity | DERIVED from archived scores, exploratory |
|---|---:|
| Mean E | +1.458341 dB |
| Mean B, RTX-only | −0.214330 dB |
| Windows with E > 0 | 19/24 |
| Windows with E > 0 and B ≤ 0 | 9/24 |
| Spearman correlation between E and B across windows | 0.213913 |
| Best-of-three warp selection: static / pose / VMem | 1 / 12 / 11 windows |
| Best-of-three warp PSNR minus factual VMem-context warp | +0.287935 dB |
| Generated PSNR using the warp-selected context versus factual VMem context | +0.236053 dB |
| Consumer-selected minus warp-selected generated PSNR; choose on seeds 3,4, evaluate 5,6 | +0.329913 dB |
| Same contrast with seed folds exchanged | +0.291781 dB |
| Per-window consumer oracle minus seed-selected global rule; choose on seeds 3,4, evaluate 5,6 | +0.401579 dB |
| Same global-rule control with seed folds exchanged | +0.309596 dB |

Sources: S139/BASE_b2_static.json, BASE_b2_mem_pose.json, BASE_b2_mem_vmem.json; S139/plan_v2.json; S139/results/stepB_tacc/S139_SCORES_tacc.json. Full hashes and computation output: Appendix A.

**Interpretation:** the three-set geometric oracle has modest remaining geometric headroom, while a consumer-targeted hindsight choice retains an advantage across seed folds. This is evidence worth following up about **which contexts each predictor prefers**, not proof of total memory insensitivity. The approximately +0.31 dB summary is the mean of the two consumer-versus-warp seed-fold rows, +0.329913 and +0.291781 dB; Appendix A prints both components.

The consumer oracle uses target RGB scores even on its selection fold. Seed splitting addresses sampling-noise selection optimism; it does **not** make the selector deployable, remove target dependence, create a new scene, or establish a population CI. These statistics were chosen after exposure and are exploratory. The weak correlation is not a proof of independence. Pair-wise E/B means also differ (Appendix A). The added strongest-trivial control selects static_recent globally in one fold and mem_pose in the other; the per-window oracle still has descriptive headroom over those global choices (Appendix A2). That supports testing heterogeneous rankings, but does not validate them beyond this exposed panel.

### 5.2 Hole location differs, but its cause is not identified

**DERIVED, cached-mask analysis:** development/chess mean hole fractions are 0.337379/0.447649. Among hole pixels, the mean proportion lying in the top/bottom seventy-two-pixel bands is 0.559578/0.383322. Central-band hole rates are 0.213582/0.387648. Source: data/S140_warps_dev and data/S140_warps_chess; exact command/output in Appendix B.

This justifies a stratified audit. It does not identify crop-induced holes or disocclusion. The source zeroes depth outside the CUT3R crop, splats points, nearest-fills unsupported pixels, and thresholds coverage after resizing (S139/baselines_s139.py:45–48,59–67; S137/geometry_baselines.py:49–89). Several causes can therefore yield the same Boolean mask.

## 6. Convergence: three concrete experiments

These are proposed protocols to implement in fresh stage directories, not modifications made by R259. Each pilot fits one or two working days using the available model/assets, conditional on access to the already existing remote artifacts where stated. No pilot depends on S141 finishing.

### Experiment 1 — Finite-candidate evidence/consumer ranking audit

**Hypothesis.** Geometric reconstruction utility is an imperfect proxy for sampled consumer utility: among a fixed set of valid historical contexts, the context maximizing warp PSNR can leave a stable, practically meaningful generated-quality shortfall. This permits a positive, negative, or matching-rank result; it does not presume that memory is ignored.

**Minimal implementation and files.** Create a new stage with PROTOCOL.md, build_context_pool.py, gen_eval.py, score_eval.py, analyze_utility.py, and a frozen context manifest. Adapt the plan/warp interface in S139/baselines_s139.py:49–69, sampler entry in S140/gen_s140.py, and receipt/finite-output handling in S141/gen_s141.py:134–198. Preserve existing S139–S142 files. Canonical context ordering affects camera normalization, so regenerate this pilot instead of pretending old reordered predictions are reusable (V/modeling/pipeline.py:1099–1120,1136–1140).

**Panel and inputs.** All twenty-four exposed chess windows. Same thirty-two-frame historical bank, four source slots, four target cameras, gl convention, base weights, RTX 3090, seeds 3,4,5,6. Freeze six context-set construction rules before scoring:

1. Existing static_recent membership.
2. Existing mem_pose membership.
3. Existing mem_vmem membership.
4. Four distinct bank frames minimizing the mean existing pose-distance score to the target cameras, without NMS.
5. Four distinct bank frames selected greedily for estimated union coverage, using context-only geometry.
6. One uniform four-frame bank sample from a manifest-construction RNG fixed at 259.

Target poses are allowed query inputs; target RGB/depth are excluded from all six construction rules and generation. For rule 5, estimate bank geometry once using the existing pipeline before target scoring; log failures instead of replacing difficult windows. This is a known-style baseline, not a new selector. Sort each selected set by its position in the frozen bank manifest for a common deterministic slot policy. Deduplicate identical ordered sets and retain their multiple labels; do not replenish a duplicate with a favorable new candidate. Exact set counts become part of the receipt.

**Definitions.** For window w and context c:

- W(w,c) is the fixed CUT3R+KPS warp, including a fixed fill policy.
- Q_W(w,c) is its target PSNR.
- Q_G(w,c,F) is mean generated PSNR over seed fold F, with identical target/scoring grids.
- E(w,c)=Q_W(w,c)−Q_W(w,static).
- B(w,c,F)=Q_G(w,c,F)−Q_G(w,static,F).
- c_W(w)=argmax over the frozen pool of Q_W(w,c).
- c_G(w,F)=argmax over that pool of Q_G(w,c,F), with ties broken by manifest index.

The **primary shortfall** is the window mean of:

R(w) = 0.5 × {
 Q_G(w,c_G(w,{3,4}),{5,6}) − Q_G(w,c_W(w),{5,6})
 + Q_G(w,c_G(w,{5,6}),{3,4}) − Q_G(w,c_W(w),{3,4})
}.

Do not divide B by E: near-zero denominators and negative values would create misleading “efficiency.” Plot the two axes directly and report the actual ranking changes. A geometric maximum is optimal only for this finite pool, this predictor, and this metric. It is not the best of every four-frame subset, not an information bound, and not an upper bound on generation. R can be negative after seed splitting; do not clip it.

**Primary contrast and threshold.** R ≥ +0.20 dB, descriptive window-bootstrap lower bound > 0, and no negative pair mean in two of the three trajectory pairs. Also require the pool to provide a mean best-versus-worst geometric spread ≥1 dB; otherwise the evidence range is too narrow to stress the proxy. These are frozen practical thresholds, not acceptance probabilities.

**Controls, including strongest trivial baselines.**

- All six sets have the same slot budget and allowed historical bank. Show the nearest-four and pose-NMS baselines prominently.
- Score copy-nearest from each selected set, plus copy-nearest from the entire bank as a separately labeled larger-choice baseline. The existing copy-bank implementation selects by pose for each target (S139/baselines_s139.py:34–39).
- Add a seed-cross-fitted **global rule selector**: choose one of the six construction rules by its mean generated score across all windows in the selection fold, then evaluate that single rule on the held seed fold; exchange folds. It is also target-informed, not deployable. Report per-window oracle minus global-rule gain and rule frequencies. Require a mean gap of at least +0.20 dB with descriptive lower bound above zero before claiming useful window-specific ranking structure. If only the global rule wins, call the finding a globally biased geometric proxy and retain the simpler rule; R alone does not establish heterogeneous context utility.
- Score the raw warp itself and one fixed Gaussian-smoothed warp; retain full-frame PSNR/SSIM. LPIPS is secondary when prediction payloads and metric weights are available.
- One byte-identical unchanged sampler replay and complete paired cells. No target-based context filtering.
- Report all context-set Q_W/Q_G pairs, not only the oracle. Show E/B, all pair means, tie counts, and the seed-fold ranking stability.
- Because Q_W includes the estimator and fill, report common-support regional scores and the sensor-depth subset where feasible. Call it utility for that predictor, not absolute evidence content.
- Changes of source cameras also change the normalization package. The primary is an operational context-package comparison; it does not isolate source RGB causality. Experiment 2 supplies that distinct test.

**Kill criterion.** Abort for fidelity failures, missing cells, invalid context geometry, or target leakage. If the geometric spread gate fails, do not enlarge the pool until something works. If R misses the practical threshold, reject the proposed ranking-mismatch claim for this panel; report whether rankings agree or the interval remains uninformative. Do not relabel a wide CI as equivalence. Even a success does not justify a broad memory-model claim without a second consumer and additional scenes.

**Cost and timing.** Upper bound six sets × twenty-four windows × four seeds = **576 four-frame generations**, about **5.78 baseline-equivalent RTX 3090 GPU-hours**, DERIVED from the archived 36.114410 seconds/generation in Appendix B. Provision **8 GPU-hours**, plus CPU/context preprocessing and one replay; recalibrate before exceeding the cap. Two cards may shard complete paired cells, but their availability is not verified here. Day 1: manifest/warps/fidelity; day 2: generation/scoring. No training.

**Genuinely interesting outcome.** A reproducible gap between geometry's preferred evidence and the consumer's preferred evidence, despite substantial valid geometric spread, that changes under an independently trained consumer or survives the GEN3C replication. Equally informative: geometric utility predicts a second consumer's gain while failing for VMem, locating a consumer-dependent boundary. The currently observed oracle gap is a reason to test, not the conclusion of that test.

### Experiment 2 — Localized conditioning-path response, with benefit reported separately

**Hypothesis.** Useful source information can measurably influence outputs through one conditioning path without yielding better target reconstruction. Separating the local latent path from global CLIP can distinguish geometrically localized response from global appearance sensitivity.

**Minimal implementation and files.** New make_interventions.py, gen_interventions.py, analyze_response.py, plus an input-only intervention manifest. Reuse S141/gen_s141.py:134–155 and its encoding/cache boundary at :170–184, initially with the frozen base. Add an explicit intervention identity to every cache key and output receipt. No trained adapter or S142 warp shift is required.

The source makes this feasible: mean CLIP is repeated across views, while clean source latents enter conditional replace and the unconditional source/CLIP paths are zero (V/modeling/pipeline.py:1124–1126,1143–1185). Replacement is applied at denoiser calls (V/modeling/sampling.py:174–185). Do not freeze attention, fused states, or target latents after an intervention; rerun all downstream computation.

**Fixed intervention.** Use the original mem_vmem ordering/cameras/K, four source slots, twenty-four windows, and seeds 3,4. Choose one non-anchor source slot using largest projected support, then a fixed-size interior source patch using only source geometry. Apply opposite signed, bounded color offsets to that same patch, clipped to the valid RGB range. Freeze patch size (64×64 on the model grid), magnitude (0.10 in [0,1]), channel direction, and deterministic tie-breaking before any generation. Preserve source geometry; this is an appearance-conditioning corruption, not a physically validated scene edit.

For each sign, generate three branches: changed source latent with original CLIP; original latent with changed CLIP; both changed. The factual branch uses neither edit. Define patch support using edited source pixels that **win the final target z-buffer against all four sources**, with fixed tie handling and source-pixel provenance. Use that unchanged support in every branch. Match the equal-area non-patch control within the same original warp-covered domain. If no eligible non-anchor patch has at least 256 winning projected pixels and a matched control region, mark localization undefined for that window, still retain its global response and report the denominator. Never select patches from target errors or output responses.

**Noise and camera controls.** Preserve all camera tensors, order, normalization, masks, guidance, and sampler draw sequence. Merely reusing initial noise is insufficient: the sampler draws noise within each step even at nominal zero churn (V/modeling/sampling.py:381–399). Encode interventions before resetting generation RNG as in S141/gen_s141.py:134–135; record per-step noise equality or deterministic draw-order equality. A no-op edit must exactly replay the factual output. Changing slot zero or recomputing different camera normalization would break this restricted-path interpretation.

**Primary contrast and threshold.** For the latent-only branch, compute squared output change from its paired factual output. Compare mean response inside the projected patch support with a deterministic equal-area control region outside it, matched for target-plane location and source-derived texture level without target RGB. Average the two signs and seeds within each window.

Require (i) support-region output RMS change ≥1/255, (ii) mean support/control response ratio ≥1.5 among eligible windows, (iii) lower descriptive window-bootstrap bound for support-minus-control response >0, and (iv) the same direction in at least two trajectory pairs. Require at least twelve eligible windows; otherwise report the assay as underpowered/undefined rather than adjusting patches. Ratio values with near-zero control energy must be shown alongside absolute differences; do not report infinities as strong evidence.

**Controls, including strongest trivial baseline.**

- Exact no-op replay; factual output; latent-only, CLIP-only, and joint branches.
- Direct warp of the same edited source with fixed geometry is the localization positive control. Evaluate its localization only on covered pixels, before nearest fill or with holes excluded: nearest fill can legitimately propagate edited colors outside direct patch support (S137/geometry_baselines.py:49–75). A nearest-copy predictor is a cheap competing transfer mechanism. Their response must be reported, not just the generator's.
- A projected-support mask is initially a CUT3R-derived hypothesis, not a causal-descendant or certified visibility mask. Repeat the localization check on the independently depth-valid RGB-D subset before a strong geometric-localization claim.
- Opposite edit signs reduce a one-sided color-preference explanation; CLIP-only response detects global semantic/appearance effects.
- Report intact-minus-corrupt target PSNR/SSIM separately as **quality sensitivity to corruption**. It does not establish benefit from a naturally better memory. Experiment 1's factual valid-context contrasts answer that separate question.
- If a source-coherent whole-view replacement is added in a later study, update RGB, CLIP, pose and all geometry together, and call it a total package intervention. Do not confuse it with this held-geometry path test.

**Kill criterion.** If the sham changes, noise differs, or the deterministic warp fails to localize, stop and repair the assay. If latent response fails the threshold, reject localized latent-path influence at this edit magnitude; no amplitude sweep. If only CLIP or only large unlocalized effects appear, report global appearance dependence. A nonzero response cannot rescue a quality-negative model into “uses memory effectively.”

**Cost and timing.** Six new branches × twenty-four windows × two seeds = **288 generations**, about **2.89 baseline GPU-hours**. Factual predictions can be reused only after receipts match; regenerating all forty-eight factual cells adds about **0.48 hours**. Provision **5 GPU-hours** plus CPU patch/support analysis and the single sham replay. One day for input/fidelity controls, one day for inference/analysis. Sensor-validated transfer is a bounded supporting block, not a prerequisite for reporting the limited source-projection assay.

**Genuinely interesting outcome.** A model responds mainly through global CLIP while another shows local appearance transfer; or localized sensitivity is strong despite no signed benefit from valid better evidence. Either separates a real mechanism from “ignores memory.” An isolated corrupt-input quality drop is not enough.

### Experiment 3 — Explain the PSNR/SSIM reversal through support, filling, and independent geometry

**Hypothesis.** A substantial part of the chess warp/generator ranking reversal is attributable to how unsupported pixels are filled and scored, rather than uniformly worse reconstruction on observed surfaces. The stronger crop-versus-disocclusion explanation remains unverified until independent visibility supports it.

**Minimal implementation and files.** New score_multimetric.py, audit_visibility.py, analyze_regions.py in a fresh stage. Reuse the exact original PSNR/SSIM conversion from S140/score_s140.py:10–24,30–49. Add float-RGB LPIPS as a separately versioned score; do not silently replace the legacy uint8 metric. Reuse cached filled/valid arrays and score existing base/WGS outputs once available. This is a postprocessing/evaluation pilot, with no generator training.

**Phase A: immediately feasible mask/fill audit.** On all existing chess and RGB-D windows, freeze original warp masks. Partition into covered interior, coverage boundary, nearby holes, distant holes, and the known image-border bands using only input masks. Define covered interior by erosion of at least six pixels for SSIM's local window; retain the boundary as its own stratum. Keep all pixels in the full-frame score. Measure distance to observed support, not “distance to true visibility.”

Compare existing warp, base, WGS, plus two fixed inexpensive alternatives: (a) Gaussian blur of the filled warp, sigma=1 pixel, no tuning; (b) preserve covered pixels and fill holes with the pose-nearest context image. Include an unchanged nearest-filled warp and VAE round-trip if its already available model can be used in the later run. A simple fill/smoothing control is the strongest trivial explanation to beat before attributing an improvement to generation.

**Primary contrast and threshold.** Define Δ as SSIM(warp)−SSIM(base) using the same original spatial SSIM map. The primary localization contrast is Δ on covered interior minus full-frame Δ. Require mean ≥0.02, a descriptive lower window-bootstrap bound >0, and covered-interior Δ≥0 in at least two of three chess pairs. This tests concentration of the rank reversal; it does not prove the cause of that concentration. Report the original full-frame ordering regardless of the result.

A fixed blur/fill eliminating the difference is an interesting **baseline/metric explanation**, not a learned-memory gain. If the sign reversal persists in independently supported interiors and survives the trivial controls, reject the hole-filling explanation and report the unresolved appearance/alignment trade-off.

**Phase B: independent visibility on the available depth subset.** First use the twelve RGB-D windows with complete source/target depth. For each valid target-depth surface point, project into each source camera and check source depth agreement under a fixed tolerance, proposed max(0.03 m, 0.02×depth), with a declared boundary erosion. Geometry calibration/resizing must be checked on real-to-real RGB/depth before judging generated images. Missing/invalid depth remains **unknown**, never unseen.

Cross the independent support label with the pipeline mask:

- Sensor-supported and warp-covered: reconstruction region.
- Sensor-supported and warp-uncovered: evidence existed but this renderer missed it; crop/support loss or raster failure are hypotheses to separate further.
- Every source comparison reliably classifies the target surface as occluded by a nearer source surface or outside calibrated source FoV, and the warp is uncovered: candidate unobserved region under the stated cameras/tolerance.
- Warp-covered but depth-inconsistent: suspicious projection/occlusion region.
- Incomplete/ambiguous sensor evidence: unknown.

A source depth closer than the projected target surface by more than tolerance indicates occlusion. A farther source depth is a free-space contradiction or calibration/geometry inconsistency, not evidence of invisibility; assign it to unknown/inconsistent. Any unresolved relevant comparison prevents an unobserved label. Report the counts of each classification before interpreting region-quality differences.

Target depth is evaluator-only privileged information. Do not supply these target-derived masks to inference, context selection, or a fusion gate. For chess, this phase is conditional on later verification of the retained sensor data; it is not promised from nonexistent local depth files.

**Metrics beyond PSNR/SSIM, and their limits.**

| Metric | What it adds / exact proposed use | Essential safeguard |
|---|---|---|
| LPIPS | Full-frame reference perceptual distance, one fixed official backbone/version. **arXiv:1801.03924, “The Unreasonable Effectiveness of Deep Features as a Perceptual Metric,” §§3–4.** [Paper](https://arxiv.org/abs/1801.03924) | Not geometric truth or evidence of memory. Do not black out arbitrary holes before LPIPS; use full images or prespecified valid crops with sufficient feature support, and disclose crop selection. No LPIPS result was computed here. |
| Generated/generated reprojection residual | On fixed sensor-supported correspondences, symmetric RGB residual between two generated target views. Report the equivalent real/real residual as the acquisition/calibration floor. | Correspondences come from reference scene geometry, so label the measure accordingly. Repeated-frame and constant-color controls can be consistent but wrong; always pair with target fidelity and motion/viewpoint checks. |
| Generated-depth accuracy/consistency | If using existing CUT3R on generated images, compare estimated depth/point geometry against valid sensor depth after one declared input-only scale calibration; also compare cross-view depth residual. | Evaluates the generator-plus-estimator chain. No per-output target-depth scale fit in a primary metric; no estimator self-agreement as ground truth. Report validity/failure rate. Optional if it fits the cap. |
| MEt3R | An established learned multiview comparator, using its stated protocol, if weights/dependencies are already available later. | Distinguish learned consistency from correctness; independent-depth audit and negative controls remain necessary. It is optional, not a new metric to rename. |

PSNR penalizes squared aligned pixel errors. The repository's SSIM computes local luminance structure and averages over valid convolution centers (S140/score_s140.py:19–24). Thus splat cracks, stretched nearest fill, modest misregistration, VAE smoothing, and hallucinated but smooth structure can affect their ordering differently. Which mechanism dominates here is **UNVERIFIED**; the controls above discriminate them. **arXiv:1711.06077, “The Perception-Distortion Tradeoff,” §§II–III**, distinguishes reference distortion and distributional perceptual quality; it does not prove this particular PSNR/SSIM reversal. [Paper](https://arxiv.org/abs/1711.06077).

**Controls and kill criterion.** Preserve per-window seeds and masks across predictors; retain all sixteen RGB-D windows for the original full-frame panel and label the twelve-depth subset separately. Do not turn missing depth into silent sample exclusion. Stop the causal hole explanation if the primary localization test fails or independent support disagrees with it. Do not swap the primary to LPIPS after a favorable result. No single aggregate “quality” score combining unrelated units.

**Cost and timing.** Existing-output scoring needs **zero new diffusion generations**. Provision one working day for implementation/calibration and one for scoring/analysis, with **≤2 GPU-hours** as a cap for optional VAE/perceptual/depth calculations, not measured runtime. CPU metrics are feasible but wall time and local metric-weight availability are unverified. Access to existing prediction payloads is a concrete prerequisite. The mask inventory already completed here does not constitute completion of this experiment.

**Genuinely interesting outcome.** A widely used coverage mask is shown to mix observed-but-dropped evidence with genuinely unsupported surfaces, and that mixture explains a reproducible ranking reversal or changes which refinement actually helps. Simply reporting one more metric would be weak.

## 7. Statistical, leakage, and reporting contract shared by the pilots

1. Freeze source/checkpoint/config hashes, context manifest/order, target poses, seeds, all primary contrasts, missing-data rules, and stopping rules before new runs. The existing S141/S142 protocols are left intact.
2. Unit of analysis is a window averaged over seeds; four frames and millions of pixels are not independent samples. Show all three chess pair means and acknowledge shared banks. The existing pair bootstrap is descriptive with only three pairs (S139/analyze_s139.py:3–4,21–39). Report scene-level claims only after scene-level evidence exists.
3. Retain all prespecified arms, failed windows and undefined region scores. Predeclare practical-equivalence claims only if the CI lies fully inside a stated equivalence interval; failure to detect a gain is not equivalence.
4. In Experiment 1, candidate pools are generated without targets. All oracle choices are scorer-side privileged analyses, explicitly ineligible for a deployed leaderboard. A consumer oracle does not train or choose a model.
5. In Experiment 2, the intervention occurs after retrieval. All descendants within the tested path are recomputed; held-fixed CLIP/geometry define a restricted-path effect. No physical-world counterfactual correctness claim follows.
6. In Experiment 3, target-depth geometry is evaluator-only. Score both correctness and consistency; ordinary still/copy/blur controls prevent a smooth/static output from winning by construction.
7. Hardware-matched contrasts are mandatory. An H800 model output cannot be paired with a reused 3090 control as if only the model differed. Estimates below are summed GPU-hours, not wall time across cards.
8. Reuse outputs only with matching source/model/context/order/camera/preprocessing/sampler/seed receipts. The current generator skips existing filenames and caches by context group (S141/gen_s141.py:164–184), so fresh intervention-aware namespaces are necessary.
9. None of these protocols can turn old chess exposures into untouched confirmation. No pending S141 metric may retroactively select a more favorable R259 primary.

## 8. Paper value, scope, and one-to-two-week allocation

The benchmark-paper-template skill was applied in targeted evaluation-design mode: gap, construction, evaluation framework, empirical findings, and optional companion method. A companion generator is unnecessary here.

| Pillar | Current strength | What would make it paper-worthy |
|---|---|---|
| Evaluation gap | Plausible after distinguishing FAR, R2M-Bench/MIND/MBench, and region-metric work. | Explicit same-evidence comparison and falsifiable separation of utility, influence, benefit. |
| Construction | Existing posed real-image banks and deterministic sampler are useful. | Releasable manifests/adapter/scoring code, exact consumed-evidence receipts, independent visibility audit, no target-informed deployment. |
| Evaluation framework | Three complementary assays specified above. | Negative controls prove that each axis detects the intended failure rather than generic image degradation. |
| Findings | Existing S139/S140 results plus new exploratory ranking evidence. | A stable new finding beyond the old mean negative, ideally with another architecture and fresh scene-level tests. |
| Companion method | Not required. A/B may later provide within-family sensitivity analysis. | Do not delay the evaluation paper to invent a generator or rename a known selector. |

**ANALYTICAL schedule:** days 1–2, Experiment 1 and its quality gates; days 3–4, one mechanism follow-up (#2) and output scoring (#3) in parallel where independent. During that period, allow one bounded GEN3C interface smoke; expand only if it works within its cap. Use the remaining days for a fixed external-validity block, figures, independent arithmetic/source checks, and writing. Reserve the final several days for the artifact and manuscript; setup failures shrink the experiment list.

A sensible core GPU allowance is roughly **8 + 5 + 2 = 15 RTX 3090 GPU-hours**, plus at most the conditional **12 H800 GPU-hours** for the second consumer. These are caps/planning allowances, not measured consumption, and do not include pending S141/S142 work or assume devices are idle. No new training is needed.

Suggested paper framing: **“Useful Evidence, Different Consumers: Auditing Memory in Video World Models.”** This is a proposed title, not a publication claim. Figure 1 should show the same historical views producing different geometric/consumer rankings; Figure 2 the localized latent-versus-CLIP response; Figure 3 the metric ranking by independently audited support category. A positive cross-model difference would be as valuable as another negative VMem result.

**Single first action:** freeze and implement **Experiment 1**, beginning with the already demonstrated three-set CPU join and then its six-set controlled generation pilot. It offers a concrete new question supported by archived evidence, fits the existing sampler/budget, does not wait for S141, and can falsify the overly simple “retrieval solved; consumer ignores memory” account. Experiment 2 explains a response; Experiment 3 checks whether the response is being judged correctly. They support one study rather than three disconnected projects.

If all that survives is the old VMem mean negative on the same chess windows, the outcome remains a rigorous case study, not a general benchmark or a demonstrated CCF-A contribution. If the ranking assay identifies a reproducible consumer-dependent mismatch, localizes its conditioning route, and survives another model or independent visibility audit, the project has a substantially stronger empirical contribution without a new generator.

## 9. Delivery and unresolved items

Changed by this review: **work/agents/CODEX_R259_IDEATION_EVALUATION.md only**. No repository tests or linter were run because no executable implementation was changed; the CPU analyses and output-integrity checks below verify the calculations and document structure, not GPU behavior.

Concurrent state: S141/S142 scripts and R257–R259 prompts were already untracked; AGENTS.md became modified during inspection. These are other processes' work and were left alone. The source snapshot and hashes are recorded below.

Follow-up work belongs to the next implementation session: freeze one new evaluation protocol; make existing prediction payloads available; verify missing sensor depth; and, only if selected, try the bounded second-consumer port. Do not certify remote adapters, broaden novelty authorization, or change S142 from this document.

## Appendix A — Exact CPU analysis command and complete output

The following is exploratory analysis of existing score records. It performs no generation, reads no S141 outcome, and writes no file.

Exact command from the repository root:

~~~bash
python3 -B - <<'PY'
import json, math, statistics, hashlib
from pathlib import Path
root=Path('work/S139_crossseq_revisit')
plan=json.loads((root/'plan_v2.json').read_text())
runs=json.loads((root/'results/stepB_tacc/S139_SCORES_tacc.json').read_text())['runs']
pose={r['window_id']:r for r in json.loads((root/'POSE_ARMS.json').read_text())['rows']}
arms=['static_recent','mem_pose','mem_vmem']
base_files={'static_recent':'BASE_b2_static.json','mem_pose':'BASE_b2_mem_pose.json','mem_vmem':'BASE_b2_mem_vmem.json'}
W={a:{r['window_id']:r['psnr'] for r in json.loads((root/f).read_text())['rows']} for a,f in base_files.items()}
G={}
for c in plan['contexts']:
 for a in c['arms']:
  G[c['window_id'],a]={s:runs[c['ctx_key']+'__s'+str(s)]['aggregate']['psnr_db'] for s in [3,4,5,6]}
wins=sorted(pose)
def mean(x): return statistics.mean(x)
def score(w,a,seeds): return mean(G[w,a][s] for s in seeds)
def ranks(xs):
 return [sum(y<x for y in xs)+(sum(y==x for y in xs)+1)/2 for x in xs]
def corr(x,y):
 mx,my=mean(x),mean(y)
 return sum((a-mx)*(b-my) for a,b in zip(x,y))/math.sqrt(sum((a-mx)**2 for a in x)*sum((b-my)**2 for b in y))
E=[W['mem_vmem'][w]-W['static_recent'][w] for w in wins]
B=[score(w,'mem_vmem',[3,4,5,6])-score(w,'static_recent',[3,4,5,6]) for w in wins]
print('EXPLORE_ARCHIVED_3090_ONLY no_new_generation')
print('windows',len(wins),'seeds',[3,4,5,6],'candidate_sets',arms)
print('mean_E_db',format(mean(E),'.6f'),'mean_B_db',format(mean(B),'.6f'))
print('E_positive',sum(x>0 for x in E),'E_positive_and_B_nonpositive',sum(x>0 and y<=0 for x,y in zip(E,B)))
print('pearson_E_B',format(corr(E,B),'.6f'),'spearman_E_B',format(corr(ranks(E),ranks(B)),'.6f'))
O={w:max(arms,key=lambda a:W[a][w]) for w in wins}
print('warp_best_counts',{a:sum(O[w]==a for w in wins) for a in arms})
print('warp_oracle_minus_memwarp_db',format(mean(W[O[w]][w]-W['mem_vmem'][w] for w in wins),'.6f'))
print('generation_warpselected_minus_mem_db',format(mean(score(w,O[w],[3,4,5,6])-score(w,'mem_vmem',[3,4,5,6]) for w in wins),'.6f'))
for sel,ev in [([3,4],[5,6]),([5,6],[3,4])]:
 Q={w:max(arms,key=lambda a:score(w,a,sel)) for w in wins}
 print('selection_seeds',sel,'evaluation_seeds',ev,'consumer_best_counts',{a:sum(Q[w]==a for w in wins) for a in arms},'agreement_with_warp',sum(Q[w]==O[w] for w in wins),'eval_consumerselected_minus_warpselected_db',format(mean(score(w,Q[w],ev)-score(w,O[w],ev) for w in wins),'.6f'),'eval_consumerselected_minus_mem_db',format(mean(score(w,Q[w],ev)-score(w,'mem_vmem',ev) for w in wins),'.6f'))
for p in sorted({r['pair'] for r in pose.values()}):
 ids=[i for i,w in enumerate(wins) if pose[w]['pair']==p]
 print('pair',p,'n',len(ids),'E_db',format(mean(E[i] for i in ids),'.6f'),'B_db',format(mean(B[i] for i in ids),'.6f'))
for p in [root/'plan_v2.json',root/'POSE_ARMS.json',root/'results/stepB_tacc/S139_SCORES_tacc.json',*[root/f for f in base_files.values()]]:
 print('sha256',hashlib.sha256(p.read_bytes()).hexdigest(),str(p))
PY
~~~

Complete output; exit code 0:

~~~text
EXPLORE_ARCHIVED_3090_ONLY no_new_generation
windows 24 seeds [3, 4, 5, 6] candidate_sets ['static_recent', 'mem_pose', 'mem_vmem']
mean_E_db 1.458341 mean_B_db -0.214330
E_positive 19 E_positive_and_B_nonpositive 9
pearson_E_B 0.242618 spearman_E_B 0.213913
warp_best_counts {'static_recent': 1, 'mem_pose': 12, 'mem_vmem': 11}
warp_oracle_minus_memwarp_db 0.287935
generation_warpselected_minus_mem_db 0.236053
selection_seeds [3, 4] evaluation_seeds [5, 6] consumer_best_counts {'static_recent': 9, 'mem_pose': 10, 'mem_vmem': 5} agreement_with_warp 11 eval_consumerselected_minus_warpselected_db 0.329913 eval_consumerselected_minus_mem_db 0.583811
selection_seeds [5, 6] evaluation_seeds [3, 4] consumer_best_counts {'static_recent': 6, 'mem_pose': 14, 'mem_vmem': 4} agreement_with_warp 9 eval_consumerselected_minus_warpselected_db 0.291781 eval_consumerselected_minus_mem_db 0.509988
pair seq-01->seq-02 n 8 E_db 1.743304 B_db -0.204835
pair seq-04->seq-03 n 8 E_db 1.794257 B_db 0.056472
pair seq-06->seq-05 n 8 E_db 0.837462 B_db -0.494629
sha256 62c49eeb87b5e5934e38469fa53465b3fbe8fdb469b688130cd8efab3a83fb6b work/S139_crossseq_revisit/plan_v2.json
sha256 07fe2ebf8a67de04c2ecb928a330479215a0613c420cc03aa5154f965c1c155e work/S139_crossseq_revisit/POSE_ARMS.json
sha256 3c42e2c3658f1115bda23b5bb1ecef673a824bbc51166137bffe19a32340bd5f work/S139_crossseq_revisit/results/stepB_tacc/S139_SCORES_tacc.json
sha256 9c95977f93a923bb31a133aac8a0c9f443b9f0ff32c9e8f78d693ac81fdfe8cb work/S139_crossseq_revisit/BASE_b2_static.json
sha256 bfc7d4f4ffde5205743985880767160164cd01fd3556e755290ecfdc71ff64a1 work/S139_crossseq_revisit/BASE_b2_mem_pose.json
sha256 478407dd57883cebb255b3237424a15ef6eb0b505351433e256a8e56aeb3db4f work/S139_crossseq_revisit/BASE_b2_mem_vmem.json
~~~

### A2. Strongest trivial global-rule control

A separate read-only calculation chooses a single global construction rule on the selection seed fold, alongside the per-window oracle. Both remain target-informed.

~~~bash
python3 -B - <<'PY'
import json, statistics
from pathlib import Path
root=Path('work/S139_crossseq_revisit'); p=json.loads((root/'plan_v2.json').read_text())
r=json.loads((root/'results/stepB_tacc/S139_SCORES_tacc.json').read_text())['runs']
a=['static_recent','mem_pose','mem_vmem']; g={}
for c in p['contexts']:
 for x in c['arms']: g[c['window_id'],x]={s:r[c['ctx_key']+'__s'+str(s)]['aggregate']['psnr_db'] for s in [3,4,5,6]}
w=sorted({k[0] for k in g}); m=statistics.mean
q=lambda w,x,s:m(g[w,x][i] for i in s)
print('EXPLORE_GLOBAL_RULE_CONTROL target_informed seed_split_only')
for sel,ev in [([3,4],[5,6]),([5,6],[3,4])]:
 global_a=max(a,key=lambda x:m(q(v,x,sel) for v in w))
 local_a={v:max(a,key=lambda x:q(v,x,sel)) for v in w}
 print('selection_seeds',sel,'evaluation_seeds',ev,'global_rule',global_a,'global_minus_mem_db',format(m(q(v,global_a,ev)-q(v,'mem_vmem',ev) for v in w),'.6f'),'window_oracle_minus_global_db',format(m(q(v,local_a[v],ev)-q(v,global_a,ev) for v in w),'.6f'))
PY
~~~

Complete output; exit code 0:

~~~text
EXPLORE_GLOBAL_RULE_CONTROL target_informed seed_split_only
selection_seeds [3, 4] evaluation_seeds [5, 6] global_rule static_recent global_minus_mem_db 0.182232 window_oracle_minus_global_db 0.401579
selection_seeds [5, 6] evaluation_seeds [3, 4] global_rule mem_pose global_minus_mem_db 0.200392 window_oracle_minus_global_db 0.309596
~~~


## Appendix B — Asset inventory, archived timing, and cached-mask statistics

Read-only CPU calculation using the existing .venv-cut3r environment. This is not a model or GPU run.

Exact command from the repository root:

~~~bash
.venv-cut3r/bin/python -B - <<'PY'
import collections, hashlib, json, statistics
from pathlib import Path
import numpy as np
p=Path('work/S141_finetune/clips_s141.json'); clips=json.loads(p.read_text())['clips']
print('manifest_sha256',hashlib.sha256(p.read_bytes()).hexdigest())
print('clips_total',len(clips),'splits',dict(collections.Counter(c['split'] for c in clips)))
print('clip_kinds',{s:dict(collections.Counter(c['kind'] for c in clips if c['split']==s)) for s in ['train','val']})
logs=sorted(Path('work/S139_crossseq_revisit/results/stepB_tacc').glob('RUNS_*.jsonl'))
rows=[json.loads(l) for p in logs for l in p.read_text().splitlines() if l.strip()]; secs=[r['seconds'] for r in rows]
print('timing_sources',[str(p) for p in logs])
print('archived_generations',len(secs),'gpu',sorted({r['gpu'] for r in rows}),'mean_seconds',format(statistics.mean(secs),'.6f'),'median_seconds',statistics.median(secs))
for n in [48,96,192,288,576]: print('new_generations',n,'baseline_equivalent_gpu_hours',format(n*statistics.mean(secs)/3600,'.6f'))
for root in ['work/S139_crossseq_revisit/results/stepB_tacc','work/S140_warp_guided/results','work/S141_finetune/results']:
 print('local_prediction_npy_count',root,len(list(Path(root).rglob('*.npy'))))
print('local_chess_depth_png_count',len(list(Path('data/S139_chess').rglob('*.depth.png'))))
archives=[str(p) for p in Path('data').rglob('*') if p.is_file() and (p.suffix in ['.zip','.tgz'] or p.name.endswith('.tar.gz')) and any(s in str(p).lower() for s in ['chess','7scene','scene_13','scene_14'])]
print('local_matching_archives',archives)
for s in ['13','14']:
 root=Path('data/S133_scale_debug/datasets')/f'heldout_3dmatch_scene{s}/extracted/rgbd-scenes-v2-scene_{s}/seq-01'
 complete=[w for w in [0,50,100,150,200,250,300,350] if all((root/f'frame-{w+o:06d}.depth.png').is_file() for o in [0,15,30,45,60,75,90,105])]
 print('rgbd_scene',s,'depth_png_count',len(list(root.glob('*.depth.png'))),'windows_with_all_context_target_depths',complete)
for root in ['data/S140_warps_dev','data/S140_warps_chess']:
 files=sorted(Path(root).glob('*.npz')); rows=[]
 for p in files:
  with np.load(p) as z: v=z['valid'].astype(bool)
  assert v.shape==(576,576),v.shape
  border=np.zeros_like(v); border[:72,:]=True; border[-72:,:]=True
  rows.append([(~v).mean(),(~v&border).sum()/(~v).sum(),(~v)[border].mean(),(~v)[~border].mean()])
 a=np.array(rows)
 print('masks',root,'n',len(files),'mean_hole_fraction',format(a[:,0].mean(),'.6f'),'mean_fraction_holes_topbottom72',format(a[:,1].mean(),'.6f'),'mean_hole_rate_topbottom72',format(a[:,2].mean(),'.6f'),'mean_hole_rate_central432',format(a[:,3].mean(),'.6f'))
PY
~~~

Complete output; exit code 0:

~~~text
manifest_sha256 c2fbdd49e87426d837aa5e90a8e694cddd9032864079cef53c29a66991740f36
clips_total 2032 splits {'train': 2000, 'val': 32}
clip_kinds {'train': {'static': 995, 'memory': 1005}, 'val': {'memory': 23, 'static': 9}}
timing_sources ['work/S139_crossseq_revisit/results/stepB_tacc/RUNS_gpu13_2110672.jsonl', 'work/S139_crossseq_revisit/results/stepB_tacc/RUNS_gpu13_2110673.jsonl', 'work/S139_crossseq_revisit/results/stepB_tacc/RUNS_gpu13_2218137.jsonl', 'work/S139_crossseq_revisit/results/stepB_tacc/RUNS_gpu13_2227306.jsonl']
archived_generations 288 gpu ['NVIDIA GeForce RTX 3090'] mean_seconds 36.114410 median_seconds 35.56
new_generations 48 baseline_equivalent_gpu_hours 0.481525
new_generations 96 baseline_equivalent_gpu_hours 0.963051
new_generations 192 baseline_equivalent_gpu_hours 1.926102
new_generations 288 baseline_equivalent_gpu_hours 2.889153
new_generations 576 baseline_equivalent_gpu_hours 5.778306
local_prediction_npy_count work/S139_crossseq_revisit/results/stepB_tacc 0
local_prediction_npy_count work/S140_warp_guided/results 0
local_prediction_npy_count work/S141_finetune/results 0
local_chess_depth_png_count 0
local_matching_archives []
rgbd_scene 13 depth_png_count 72 windows_with_all_context_target_depths [50, 100, 150, 200, 250, 300]
rgbd_scene 14 depth_png_count 72 windows_with_all_context_target_depths [50, 100, 150, 200, 250, 300]
masks data/S140_warps_dev n 64 mean_hole_fraction 0.337379 mean_fraction_holes_topbottom72 0.559578 mean_hole_rate_topbottom72 0.708771 mean_hole_rate_central432 0.213582
masks data/S140_warps_chess n 96 mean_hole_fraction 0.447649 mean_fraction_holes_topbottom72 0.383322 mean_hole_rate_topbottom72 0.627650 mean_hole_rate_central432 0.387648
~~~

## Appendix C — Public code and checkpoint-manifest receipt

This requests only public metadata. No weight bytes or datasets are downloaded. The official-project-page checks for Context as Memory and MemLearner are linked in §4; absence claims remain bounded to those inspected releases.

Exact command from the repository root:

~~~bash
python3 -B - <<'PY'
import json, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
repos=['xizaoqu/WorldMem','KwaiVGI/Context-as-Memory','ZhaoJingjing713/Spatia','runjiali-rl/vmem','nv-tlabs/GEN3C','microsoft/LatentSpatialMemory']
models=['zeqixiao/worldmem_checkpoints','Jinjing713/Spatia','liguang0115/vmem','nvidia/GEN3C-Cosmos-7B']
def fetch(url):
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'R259-read-only-audit'}),timeout=30) as r: return json.load(r)
 except urllib.error.HTTPError as e:return {'http_error':e.code}
 except Exception as e:return {'error':type(e).__name__+': '+str(e)}
def repo(name):
 j=fetch('https://api.github.com/repos/'+name+'/commits?per_page=1')
 return ('repo',name,j[0]['sha'] if isinstance(j,list) else j)
def model(name):
 j=fetch('https://huggingface.co/api/models/'+name)
 return ('model',name,{'sha':j.get('sha'),'gated':j.get('gated'),'weight_files':[x['rfilename'] for x in j.get('siblings',[]) if x['rfilename'].endswith(('.ckpt','.pth','.pt','.safetensors'))],**({k:v for k,v in j.items() if k in ['http_error','error']})})
with ThreadPoolExecutor(max_workers=4) as ex:
 for row in ex.map(repo,repos): print(json.dumps(row))
 for row in ex.map(model,models): print(json.dumps(row))
PY
~~~

Complete output; exit code 0:

~~~text
["repo", "xizaoqu/WorldMem", "c1cc91bdfb2dda52fe309280e5ed046b1faba448"]
["repo", "KwaiVGI/Context-as-Memory", {"http_error": 404}]
["repo", "ZhaoJingjing713/Spatia", "f75b10c9bb5f6b0cd779ec8c41ab33dd8382dba3"]
["repo", "runjiali-rl/vmem", "39291e4f272f6b4f270691d930926ab5930f942e"]
["repo", "nv-tlabs/GEN3C", "db2ffe12ced12ddafcec5e0422ee46ce8520746b"]
["repo", "microsoft/LatentSpatialMemory", "be530516a8b8c79ae5d5dff543b4d1640f59bd54"]
["model", "zeqixiao/worldmem_checkpoints", {"sha": "a3ae4d1c3a89260f800ddeab01ca56b7e63b10e2", "gated": false, "weight_files": ["diffusion_only.ckpt", "pose_prediction_model_only.ckpt", "vae_only.ckpt"]}]
["model", "Jinjing713/Spatia", {"sha": "97dc39565d2dac4cd7bc4be697f45b5dae507549", "gated": false, "weight_files": ["control_weight_8500.safetensors", "lora_weights_10000.safetensors"]}]
["model", "liguang0115/vmem", {"sha": "ac5921080a57f5a634f4b9acbbc8f3db67c9d113", "gated": "auto", "weight_files": ["vmem_weights.pth"]}]
["model", "nvidia/GEN3C-Cosmos-7B", {"sha": "9bcfdb4f3924f41376daeadf6200826c12a3bf8e", "gated": false, "weight_files": ["model.pt"]}]
~~~

## Appendix D — Inspected input snapshot

This snapshot was taken before authoring the report. Untracked/modified items in the output belong to concurrent work; R259 leaves them untouched. SHA-256 values identify local inputs, not remote training execution.

Exact command from the repository root:

~~~bash
python3 -B - <<'PY'
import hashlib, subprocess
from pathlib import Path
print('head',subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
print('git_status_begin')
print(subprocess.check_output(['git','status','--short'],text=True),end='')
print('git_status_end')
paths=['CURRENT_STATUS.md','docs/report/TECHNICAL_REPORT_20261010.md','work/S139_crossseq_revisit/RESULT.md','work/S140_warp_guided/RESULT.md','work/S141_finetune/PROTOCOL.md','work/S142_followup/PROTOCOL.md','work/agents/CODEX_R253_RETRIEVAL_S141.md','work/agents/CODEX_R255_IDEATION_AFTER_S141.md','work/agents/CODEX_R256_S142_DRAFT_REJECTION.md','work/S139_crossseq_revisit/baselines_s139.py','work/S140_warp_guided/gen_s140.py','work/S140_warp_guided/score_s140.py','work/S141_finetune/gen_s141.py','work/S141_finetune/train_s141.py','work/S141_finetune/s141_common.py','data/S134_tacc/vmem_src/modeling/pipeline.py','data/S134_tacc/vmem_src/modeling/sampling.py']
for name in paths:
 p=Path(name);print(hashlib.sha256(p.read_bytes()).hexdigest(),name)
print('requested_output_exists',Path('work/agents/CODEX_R259_IDEATION_EVALUATION.md').exists())
PY
~~~

Complete output; exit code 0:

~~~text
head ddb6b6c56685b5650621be2fc57e1996fcfb7624
git_status_begin
 M AGENTS.md
?? work/S141_finetune/fetch_results_s141.sh
?? work/S142_followup/gen_s142.py
?? work/agents/prompts/R257_FULL.md
?? work/agents/prompts/R257_PROMPT.md
?? work/agents/prompts/R258_FULL.md
?? work/agents/prompts/R258_PROMPT.md
?? work/agents/prompts/R259_FULL.md
?? work/agents/prompts/R259_PROMPT.md
git_status_end
60c4f4a245bbda05fd9be464c5fba81393904e666f1cb15f7aefb090428bb0fe CURRENT_STATUS.md
a9e437e9fd5619070cad5eb38c50f4157c88afcedb5c64c98f66bc405c90b16f docs/report/TECHNICAL_REPORT_20261010.md
a09a20a359acc31755a511b8b81ad56747f6046a2c750c5287ef6ab07e4e0f05 work/S139_crossseq_revisit/RESULT.md
2db2f7ed6d3184a5cdc5b39c369d98bd2c558e55f56e0513fc3f86292f58634c work/S140_warp_guided/RESULT.md
0b5c3aab9809f851ee476b2a54eae781c7c286bbe1e047ac89388b40d3051fdc work/S141_finetune/PROTOCOL.md
d4358e4acfc64d8bd9f1d2e29742a2f5facbb67bdecc33f5852dcc74d4a1b692 work/S142_followup/PROTOCOL.md
7e17d1600d0b0ab8019ff38fc3ba928f2075f500e72181755fb8770e0ade31de work/agents/CODEX_R253_RETRIEVAL_S141.md
62fc97aed343bde1f684140f70bba7cd1281522c34c86d8fe8589cc7965b2a2a work/agents/CODEX_R255_IDEATION_AFTER_S141.md
c0bc379db9f9fe847c744c5c51baee85dc5bdbba27ae629632c9db1f92594d0b work/agents/CODEX_R256_S142_DRAFT_REJECTION.md
791068ee1410449143be7a3bd4a1c823efc5abe4e16ea1c7d523aa59c5cb7173 work/S139_crossseq_revisit/baselines_s139.py
119904b368eefe4f7bd99e1aed0ba91d7a9250aad5e97a0fb298d7007c0a46c9 work/S140_warp_guided/gen_s140.py
61f093cb2e40eeec2d862562dc6e28e98076447cde5819a2384536937cb00a79 work/S140_warp_guided/score_s140.py
c903be28ffea8c359c79d927ebdcf782e1d9ac21b81d0b159439e1566fac8121 work/S141_finetune/gen_s141.py
6ba0419e5ceb39406bbd1894ffae90398c27daedbc2eea56b18e537ba6187c0a work/S141_finetune/train_s141.py
459549706fb3a965fc4f7c5021f4d49cc626158e94a7c9cdc94cf8784cccb6cc work/S141_finetune/s141_common.py
680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255 data/S134_tacc/vmem_src/modeling/pipeline.py
dc07ca0ba571ba5fb48f9856515d2cb7dea25254008a6f8b315538817f352b24 data/S134_tacc/vmem_src/modeling/sampling.py
requested_output_exists False
~~~

## Appendix E — Document integrity receipt

This checks document structure, referenced local line ranges, and unchanged hashed inputs. It does not certify interpretations or runtime behavior. The byte count predates this appendix. The later R257/R258 output files in git status appeared concurrently and were not read or modified for R259.

Exact command:

~~~bash
python3 -B - <<'PY'
import hashlib, re, subprocess
from pathlib import Path
p=Path('work/agents/CODEX_R259_IDEATION_EVALUATION.md'); text=p.read_text(); body=text.split('## Appendix A')[0]
roots={'S139/':'work/S139_crossseq_revisit/','S140/':'work/S140_warp_guided/','S141/':'work/S141_finetune/','S137/':'work/S137_geometry_baselines/','V/':'data/S134_tacc/vmem_src/'}
pat=r'(?<![\w/])((?:S139/|S140/|S141/|S137/|V/|work/|docs/)[\w/.-]+\.(?:py|md|json|slurm)):(\d+(?:[–-]\d+)?(?:,\d+(?:[–-]\d+)?)*)'
refs=list(re.finditer(pat,body)); bad=[]
for match in refs:
 name,ranges=match.groups(); path=name
 for prefix,root in roots.items():
  if name.startswith(prefix):path=root+name[len(prefix):];break
 q=Path(path); n=len(q.read_text().splitlines()) if q.is_file() else 0
 for part in ranges.split(','):
  a=re.split('[–-]',part); lo=int(a[0]); hi=int(a[-1])
  if not 1<=lo<=hi<=n:bad.append(match.group())
changed=[]
for h,name in re.findall(r'^([0-9a-f]{64}) ((?:CURRENT_STATUS|docs/|work/|data/)[^\n]+)$',text,re.M):
 q=Path(name)
 if not q.is_file() or hashlib.sha256(q.read_bytes()).hexdigest()!=h:changed.append(name)
print('report_exists',p.is_file())
print('report_bytes_before_qa_append',p.stat().st_size)
print('divergent_candidate_rows',len(re.findall(r'^\| (?:\*\*)?\d+(?:\*\*)? \|',body,re.M)))
print('focused_prior_art_sections',len(re.findall(r'^### [A-E]\. ',body,re.M)))
print('converged_experiments',len(re.findall(r'^### Experiment [1-3] ',body,re.M)))
print('source_citations_checked',len(refs),'invalid_ranges',bad)
print('changed_hashed_inputs',changed)
print('markdown_fences_balanced',text.count('~~~')%2==0)
print('replacement_characters',text.count(chr(65533)))
print('git_status_begin')
print(subprocess.check_output(['git','status','--short'],text=True),end='')
print('git_status_end')
assert not bad and not changed and text.count('~~~')%2==0
PY
~~~

Complete output; exit code 0:

~~~text
report_exists True
report_bytes_before_qa_append 76418
divergent_candidate_rows 15
focused_prior_art_sections 5
converged_experiments 3
source_citations_checked 28 invalid_ranges []
changed_hashed_inputs []
markdown_fences_balanced True
replacement_characters 0
git_status_begin
 M AGENTS.md
?? work/S141_finetune/fetch_results_s141.sh
?? work/S142_followup/gen_s142.py
?? work/agents/CODEX_R257_IDEATION_MECHANISMS.md
?? work/agents/CODEX_R258_IDEATION_FROM_FINDINGS.md
?? work/agents/CODEX_R259_IDEATION_EVALUATION.md
?? work/agents/prompts/R257_FULL.md
?? work/agents/prompts/R257_PROMPT.md
?? work/agents/prompts/R258_FULL.md
?? work/agents/prompts/R258_PROMPT.md
?? work/agents/prompts/R259_FULL.md
?? work/agents/prompts/R259_PROMPT.md
git_status_end
~~~
