# Research Report Synchronization — 2026-09-16

**Purpose.** This file is a synchronized, beginner-readable handoff. It combines the proposal-aligned plan with the newest evidence from the H800 runs and the pre-Gate innovation diagnostics. It is an English research-plan artifact with a Chinese explanation for the student. It does not replace the append-only ledger, sealed experiment records, or historical reports.

**Scientific status at this snapshot.** `new_method_validated=false`; `novelty_authorization=NONE`; `NO_METHOD_SELECTED`. The project has real infrastructure and component evidence, but it has not yet completed a legal held-out VMem baseline, a fair same-pool selector comparison, or a cross-scene method confirmation.

## 1. Proposal translated into an executable research question

The proposal asks whether a world model can preserve 3-D geometry when the camera leaves a place, observes other content, and later revisits it. The observable chain is:

`past RGB-D/pose observations → geometric memory → memory selection/update → VMem consumer → future RGB-D/pose prediction`.

The central testable hypothesis is:

> Under the same candidate history and the same computation budget, a history item with lower *past geometric risk* should reduce *future held-out geometric error*.

This is a hypothesis, not a result. A result can only be claimed after the selector is frozen before future answers are opened, externally supplied, held-out future RGB-D/pose reference is held out from selection decisions, and strong controls are run.

The original GRC-Memory idea is currently a **candidate**, not an accepted contribution. Recent-neighbour auditing indicates that geometry-aware selection, long-term memory, and future-aware conditioning already exist in nearby work. The defensible distinction must therefore be a measurable future-state evaluation contract and a mechanism that survives the controls below.

## 2. Historical experiment identifiers with explicit names

The `S` identifiers are retained for provenance. The parenthesized names are the concrete experiment names to use in an advisor report. “Real run” means an actual model/data execution; “saved-data reanalysis” means no new model forward; “pre-Gate” means development or synthetic evidence that cannot validate the method.

| Identifier | Concrete experiment name (parentheses) | Evidence class and current interpretation |
|---|---|---|
| S0 (memory geometry correction stress test) | Real synthetic program run; checks whether later observations update an already written surfel. Not a video or new method. |
| S1 (geometry perturbation and reference-frame selection) | Real synthetic program run; final reference selection response to position/depth perturbations. |
| S2 (real RGB-D interface qualification) | Real-data interface audit; no CUT3R/VMem generation. |
| S3 (simple surfel position-update comparison) | Real TUM measured-data component run; no full VMem consumer. |
| S4 (two-frame CUT3R measured-depth diagnostic) | Real model forward on RGB only with held-out second-frame depth scoring under its original protocol; component diagnostic. |
| S5 (three-block CUT3R sequence geometry diagnostic) | Real model forward on RGB sequence; depth used only for frozen scale scoring, not selector input. Not a retrieval experiment. |
| S6 (CUT3R geometry-to-memory bridge) | Real component run; tests predicted geometry entering a memory bridge. Not full VMem generation. |
| S7 (fixed-identity event replay) | Saved-array/event replay; separates position, association, and selection explanations under one seen environment. |
| S8 (external TUM scene mechanism check) | Real-data mechanism check on a second TUM scene; not an independent blind benchmark. |
| S9 (seen-query component timing profile) | Saved-buffer timing diagnostic; no model forward or quality claim. |
| S10 (renderer comparison and edge audit) | Real/saved renderer comparison and independent visual/edge checks; not geometry ground truth. |
| S11 (renderer regression verification) | Regression recheck; preserves previous renderer outcomes. |
| S12 (matched-budget selection protocol) | Protocol and fairness preparation for equal candidate and compute budgets. |
| S13 (new-scene identity and data-source audit) | Data/scene identity audit; not a method result. |
| S14 (feature extraction and ray-only geometry diagnostics) | Real component and geometry-feature diagnostics; not end-to-end VMem. |
| S15 (native history and consumer preparation) | Real-data history/consumer interface preparation and controlled checks. |
| S16 (interference and mechanism separation) | Saved-data/controlled interference analysis; limited support, not an independent method result. |
| S17 (DPT two-frame and embedded geometry) | Real CUT3R/VMem geometry-component work; no complete video claim. |
| S18 (minimal VMem map and renderer bridge) | Real component execution on saved geometry; map/renderer bridge only. |
| S19 (ray-difference and near-work rejection audit) | Literature/source audit and mathematical rejection; no new method validated. |
| S20 (software and generation-path preparation) | Engineering preparation; no complete video or innovation result. |
| S21 (300-frame CUT3R trajectory baseline) | Real model run; position RMSE baseline for an existing method. |
| S22 (300-frame FILT3R/TTT3R trajectory baseline) | Real model run; existing-method trajectory baseline and precision-compatibility check. |
| S23 (geometry diagnostic and depth-tail analysis) | Real/saved geometry diagnostics; failure characterization only. |
| S24 (baseline expansion and horizon diagnostic) | Real/saved horizon and baseline comparisons; no new method. |
| S25 (consumer preparation and saved-state controls) | Preparation/control work; not a method result. |
| S26 (consumer execution and scoring) | Real consumer execution/scoring on the declared variant; scope is constrained by its data and VAE identity. |
| S27 (saved-scale preparation) | Saved-data scale/geometry preparation; no new forward. |
| S28 (gradient-control renderer check) | Renderer gradient-control diagnostic. |
| S29 (state and memory handoff preparation) | Handoff/provenance preparation. |
| S30 (trajectory and endpoint report) | Reported trajectory/endpoint measurements from existing runs. |
| S31 (data and source qualification) | Data/source audit. |
| S32 (window AbsRel diagnostic) | Saved-data window error diagnostic; not held-out method validation. |
| S33 (four-condition geometry/appearance diagnostic) | Controlled geometry/appearance comparison; diagnostic only. |
| S34 (resource and renderer depth audit) | Resource and renderer/depth audit. |
| S35 (model/checkpoint access audit) | Weight/source access and provenance audit. |
| S36 (dependency and environment recovery) | Dependency recovery; no scientific result. |
| S37 (VMem component access audit) | Model/component interface audit. |
| S38 (checkpoint and VAE identity audit) | Checkpoint/VAE identity audit; declared-variant limitations retained. |
| S39 (component variant execution preparation) | Variant-run preparation. |
| S40 (declared VMem variant generation and readback) | Real local generation/readback for the declared variant; not exact external reproduction while VAE identity is unknown. |
| S41 (VMem checkpoint transfer recovery) | Transfer attempt/recovery; no scientific result. |
| S42 (baseline failure preregistration and statistics) | Failure preregistration and statistical protocol. |
| S43 (interface and source integrity audit) | Source/interface audit. |
| S44 (C1 confirmation generation) | Real/local confirmation-generation attempt with preserved failures. |
| S45 (C1 numeric camera guard) | Numeric camera-guard implementation and failed/repair attempts. |
| S46 (blind scoring wrapper) | Scoring-wrapper preparation; no claim of blind validation until the seal is respected. |
| S47 (C2 confirmation generation) | C2 generation attempt; retained failures and incomplete paths. |
| S48 (geocausal memory contract) | Research-contract/design work; no accepted method. |
| S49 (causal memory implementation preparation) | Implementation preparation. |
| S50 (causal memory control audit) | Control/audit work. |
| S51 (generation-source provenance audit) | Source provenance audit. |
| S52 (history/cache interface audit) | History/cache interface audit. |
| S53 (consumer-path audit) | Consumer-path audit. |
| S54 (memory-source identity audit) | Source-identity audit. |
| S55 (long-horizon failure classification) | Failure-classification preparation. |
| S56 (camera and pose contract audit) | Camera/pose contract audit. |
| S57 (camera-observer calibration and erratum) | Real/saved observer calibration; old y/z-flip interpretation withdrawn where invalid. |
| S58 (C2 result readback) | Saved C2 readback and result audit. |
| S59 (consumer integration preparation) | Integration preparation. |
| S60 (renderer unit replay) | Unit/replay diagnostic, no full model claim. |
| S61 (unit-consistent retrieval) | Retrieval unit consistency check. |
| S62 (B0 context integration) | B0 integration check. |
| S63 (C2 context integration) | C2 integration check. |
| S64 (unit-repaired generation) | Declared engineering variant; not a new method. |
| S65 (generation-output audit) | Output audit. |
| S66 (camera scoring and nine-frame control) | Real scoring/control on the declared variant; metric is not comparable to unrelated S70 metrics. |
| S67 (translated-query diagnostic) | Fixed-set translated-query diagnostic. |
| S68 (TUM VMem cache bridge) | Real CPU encoding/cache bridge on TUM data. |
| S69 (TUM camera conditioning) | Camera-conditioning interface test. |
| S70 (fixed-context three-arm VMem generation) | Real 50-step generation for three arms; low pixel error did not prove geometry benefit; declared SD2.1 VAE identity remains unknown. |
| S71 (generation framing and matching diagnosis) | Saved-output/matching diagnosis; target 23 has insufficient reliable pairs. |
| S72 (real control with measured-depth reprojection) | Real measured-depth/reprojection control with approximate camera constraints; not full 3-D truth. |
| S73 (generation matching observer) | Saved generation/matching observer; content/camera/coverage confounds remain. |
| S74 (wrong-pose camera-label sensitivity) | Saved matching control; wrong labels produce larger residuals in this set, not method evidence. |
| S75 (five-history VAE round-trip) | Real VAE decode/readback; weakens a broad decode-distortion explanation, but does not prove latent compatibility. |
| S76 (relative-camera response) | Real 50-step one-arm camera-response generation; finite matched subset only, not camera correctness or innovation. |
| S77 (generated wrong-pose control) | Saved/controlled wrong-pose check; no new method. |
| S78 (match-visual preflight) | Manual visual preflight; disagreement is preserved and is not accuracy. |
| S79 (conservative-prefix and workflow audit) | Saved-state/workflow audit plus innovation rejection; no new dynamic method. |
| S80 (LightGlue observer and fixed-feature matching) | Real component matching observer; increased accepted matches did not increase ≤10 px acceptance. |
| S81 (anchor-depth reprojection scoring) | Real measured-depth scoring under asynchronous/approximate-K limits; no new method. |
| S82 (history geometry guidance preparation) | Geometry-guidance preparation; no new generation accepted in this snapshot. |
| S83 (history-geometry guidance baseline) | Local/declared-variant guidance diagnostic; not independent held-out VMem. |
| S84 (fixed-camera/geometry projection consumer) | Local projection-consumer diagnostic. |
| S85 (fixed-geometry warp consumer) | Saved/local warp consumer; projection consistency is not physical truth. |
| S86 (single-scene four-target geometry-conditioned baseline) | Real local 50-step generation. Lower RGB MSE coexisted with ghosting/smearing; no 3-D accuracy claim. |
| S87 (terminal guidance-strength and multi-step necessity control) | Real local control at strengths 0.5/0.75/1; a local counterexample to “multi-step is necessary,” not GRC evidence. |
| S88 (RTMV camera metadata and static-projection qualification) | Metadata/static qualification; no complete dynamic independent sequence. |
| S89 (RTMV TLS/range continuation failure audit) | Real transport attempts with zero new image payload; failure preserved. |
| S90 (RTMV archive indexing and protocol review) | Archive/index/licence review; no independent RGB-D/pose test set. |
| S91 (formal GRC-Memory pilot) | **Blocked**. Development-source identity mixing prevents a valid formal claim. |
| S92 (tail-risk decomposition) | Saved-data tail-risk decomposition; descriptive/diagnostic only. |
| S93 (alternative TUM-01 qualification) | Data qualification route; not a method result. |
| S94 (alternative 3RScan-01 qualification) | Data qualification route; not a method result. |
| S95 (evaluation-contract and mathematical semantics audit) | Contract/kernel mathematical audit; no model result. |
| S96 (GIM saved-pose audit) | Saved-pose audit and nearest-work comparison; no method validation. |
| S97 (development RGB-D pair audit) | Development pair audit; source identity is not a held-out guarantee. |
| S98 (development-window feasibility) | Window feasibility audit; no future answer score. |
| S99 (fixed-budget geometry update comparison) | Saved-data same-block update comparison; low inconsistency did not stably beat confidence, so that claim is stopped. |
| S100 (context-matched equal-amplitude swap diagnostic) | Saved-data consumer re-render diagnostic, 144 swaps; mean benefit near zero and background-dependent sign. |
| S101 (SuperPOD SSH/Slurm environment and run-contract qualification) | **Real H800 infrastructure run**: SSH, Slurm, environment, source/checkpoint transfer and resource probes. Infrastructure only. |
| S102 (Gate 0 held-out RGB-D/pose qualification) | **Pre-Gate/data qualification only; TUM metadata audit job 588524 completed** (2,488/2,585 RGB-D pairs within 20 ms). Future-GT isolation and independent held-out scene remain unfrozen, so overall Gate 0 is not passed. |
| S103 (H800 VMem no-data model-load smoke) | **Real H800 run, no data/GT/forward**. All declared VMem components loaded successfully in 24.60 s; this is model-load evidence, not a baseline. |
| S104 (H800 CUT3R RGB-only component calibration forward) | **Real H800 model forward** on four RGB frames (IDs 1/31/61/91), 10.663 s forward, 3.642 GB peak; depth/pose/GT were not read and calibration scoring was not run. |

**Identifier disambiguation.** The repository also contains an earlier `S103` directory for the saved prediction-geometry-decomposition diagnostic. It is not the same run as `S103 (H800 VMem no-data model-load smoke)`. The full paths and receipts are therefore part of every citation; no historical identifier is renamed or overwritten. The same rule applies to any future package that reuses an `S` number.

## 3. Latest evidence and its exact limits

### 3.0 TUM metadata audit — S102 (Gate 0 held-out RGB-D/pose qualification)

The corrected H800 submission (job 588524, requiring `--gpus=1` because of the SuperPOD QoS) completed the metadata-only audit. The archive contains 2,585 RGB rows, 2,509 depth rows, and 8,710 ground-truth pose rows; 2,488 RGB-D pairs fall within the fixed 20 ms tolerance (96.25%). The sampled depth PNG is 640×480, `uint16`, with raw median 9,965. The archive SHA-256 is recorded in the receipt. This is **conditional data qualification only**: `future_gt_isolation=NOT_YET_FROZEN` and `independent_heldout_scene=NOT_YET_ACQUIRED`; no model inference or future scoring occurred. Therefore this audit does not pass the formal Gate 0 and does not unlock the VMem baseline.

### 3.1 H800 model-load smoke — S103 (H800 VMem no-data model-load smoke)

Job 588459 loaded `VMemModel`, `AutoEncoder`, `CLIPConditioner`, and `ARCroco3DStereo` from SHA-verified checkpoints. Load time was 24.598 s and peak memory was 7,883,764,736 bytes. `data_access=NONE`, `gt_access=false`, and `forward_completed=false`. Therefore this closes a software/model-construction preflight only.

### 3.2 H800 CUT3R component forward — S104 (H800 CUT3R RGB-only component calibration forward)

Job 586719 used four fixed RGB frames, IDs 1, 31, 61, and 91. The receipt reports `forward_completed=true`, 10.663 s synchronous inference, and 3,641,906,688 bytes peak memory on an NVIDIA H800. The CUT3R checkpoint SHA was verified. `depth_access=false`, `pose_access=false`, and `gt_access=false`; no calibration score was produced. This is evidence that one geometric component can execute remotely, not evidence of geometric accuracy, long-horizon consistency, or GRC benefit.

### 3.3 Pre-Gate SOCF-A source-conflict diagnostic

The runner read only sealed S100 low/conf prediction tensors. It produced 72 pair-target rows and 36 context-stability rows. Mean source identity-flip rates were 0.00109 (source 0), 0.00455 (source 1), and 0.00091 (source 3). The fraction of depth changes explained by source conflict was 0.973, 0.964, and 0.916. Mean absolute cross-background conflict-rate difference was 0.000870. These are descriptive signals from a saved consumer; they do not test future prediction benefit, calibrated risk, abstention benefit, causality, or novelty.

### 3.4 Pre-Gate ghosting mechanism diagnostic

The saved S86/S87 outputs from one already-seen scene were reanalysed without a new model forward. Mean RGB MSE was lowest for `Gterminal_l075` (0.05116758), while its high-frequency ratio was about 6.7826 times the reference. `Gpaste_l075` had MSE 0.05336067 but high-frequency ratio about 19.5367. `Gguide` had MSE 0.05242222 and high-frequency ratio about 2.5887. These image proxies support the warning that lower pixel error can coexist with edge instability, but they do not establish ghosting causality, geometry accuracy, or method effectiveness.

### 3.5 Pre-Gate CVaR and DLV implementation pilots

The synthetic CVaR fixture selected a different three-item set from the mean-risk selector and reduced fixture CVaR from 1.90 to 0.19 under equal cardinality budget. The DLV state machine correctly waited for two contradictions before invalidating and two consistent revisits before reactivation. These results verify code paths and tie rules only. They use no VMem forward, no RGB-D benchmark, no held-out manifest, and no future ground truth.

## 4. GPU experiment sequence after this snapshot

The following plan is written in English so it can be used by a remote runner. Every package has a name, a data contract, a success criterion, and a stop condition.

1. **P01 (Gate 0 TUM metadata qualification — metadata-only audit).** **Completed conditionally** in H800 job 588524: RGB/depth associations, timestamps, one depth sample, and archive hash were recorded. Future-GT isolation and independent held-out-scene status remain unresolved, so this is a data-gate result rather than model science. Stop formal baseline entry until the missing fields are frozen.
2. **P02 (Implementation freeze — S103 VMem execution contract).** Hash code, environment, checkpoints, precision, seed, input paths, candidate pool, allowed inputs, budget, and output seal. The output seal must precede opening future RGB/depth/pose answers.
3. **P03 (S103 VMem development baseline — RGB-D/pose development split).** Execute the complete VMem path on a development split only. Preserve all predictions, failures, memory, runtime, and logs. Do not label it held-out or use it to tune a method.
4. **P04 (Baseline scoring — image versus geometry endpoints).** Score RGB quality separately from geometry: depth AbsRel/RMSE, valid-pixel denominator, reprojection, pose/ATE/RPE where defined, coverage, collision/occlusion, and ghosting proxies. Never infer 3-D accuracy from RGB MSE.
5. **P05 (Natural-failure classification — mechanism audit).** Classify failures into camera/scale drift, stale memory, source conflict, visibility/occlusion, retrieval, and decoder/appearance. Pre-register the labels and preserve ambiguous cases.
6. **P06 (FGB-Future selector-free future-state test).** Under fixed history and budget, test whether extra history predicts externally supplied, held-out future RGB-D/pose reference. This is the safest problem/benchmark route if no method survives.
7. **P07 (Same-pool strong selector baselines — equal budget).** Compare recent, random, pose-distance, coverage, confidence, utility-only, persistent/event-anchor, and any declared baseline using identical candidate pools and total compute.
8. **P08 (SOCF-A correlated conflict plus abstention).** First test incremental prediction of future geometry beyond the strong baselines. Only then run abstention/fallback. Kill the method if conflict does not predict held-out future tail error or if static scenes regress.
9. **P09 (Source-level counterfactual intervention).** Delete/replace one selected source while holding prompt, camera, RNG/noise, non-target memory, and pre-intervention conditions fixed. Recompute all target-source descendants. Report influence, localization, and signed benefit separately.
10. **P10 (Ghosting 2×2 mechanism experiment — geometry × appearance).** Use a held-out split with fixed geometry and appearance factors; add RGB MSE, perceptual/edge measures, and geometry metrics. Treat this as a diagnosis, not proof of a selector.
11. **P11 (CVaR tail-risk selector).** Run only if the real baseline error distribution is heavy-tailed. Compare mean-risk and CVaR policies under equal budget, with tail confidence intervals and worst-case samples.
12. **P12 (DLV dynamic landmark invalidation).** Run only when legal data contains leave-change-return events. Compare one-conflict/two-conflict invalidation and recovery against fixed memory, with matched replacement counts.
13. **P13 (Calibration and threshold fitting).** Fit risk thresholds on development/calibration data only. Record the calibration population and exchangeability limitations; never tune on held-out future answers.
14. **P14 (Held-out confirmation).** Freeze the selected method and all thresholds, then unlock externally supplied, held-out future RGB-D/pose reference scores. Use paired bootstrap or an explicitly justified hierarchical analysis with complete denominators.
15. **P15 (Cross-scene confirmation).** Repeat on independent scenes/trajectories and report scene-level variance. Repeated windows from one scene are not independent scenes.
16. **P16 (Ablation and cost matrix).** Remove each component, match total candidates/slots/token/forward/GPU time, and report memory, latency, and tail cost.
17. **P17 (Independent readback).** Have a separate checker recompute hashes, metrics, split isolation, coordinate transforms, and claim scope from sealed artifacts.
18. **P18 (Final report and advisor briefing).** Update the Chinese beginner explanation from only accepted evidence; keep all protocol and scheduled-plan specifications in English.

## 5. Current decision gates

- **Gate 0:** not passed. The TUM metadata audit (S102 (Gate 0 held-out RGB-D/pose qualification)) is now complete but conditional: future-GT isolation and an independent held-out scene are still missing. ICL-NUIM has useful structure but is synthetic and its timestamp/depth semantics and exposure boundary remain limited. A data file not decoded is not automatically an unseen answer.
- **VMem baseline gate:** not passed. S103 (H800 VMem no-data model-load smoke) loaded components but did not run a forward. S104 (H800 CUT3R RGB-only component calibration forward) is not a VMem baseline.
- **GRC/SOCF method gate:** not passed. Pre-Gate diagnostics show implementable signals, not future benefit.
- **Innovation gate:** current ranking is SOCF-A conditional candidate, FGB-Future safest problem/benchmark route, counterfactual and ghosting as measurement/diagnostic, CVaR/DLV conditional. The original GRC headline remains rejected as a standalone novelty claim until a mechanism difference and future benefit survive strong controls.

## 6. 中文初学者同步摘要

**现在做到哪里：** 学校 H800 已经能真正运行代码。`S103（H800 VMem无数据模型加载烟测）`证明四个主要组件可以载入；`S104（H800 CUT3R只读RGB组件前向）`证明CUT3R可以对四张固定RGB图做一次GPU计算。但这两项都没有完成VMem长时程视频，也没有读取未来答案，所以还不算正式基线。

**已经发现什么：** 旧的S86/S87生成图中，RGB像素误差较低时仍可能出现重影和边缘不稳定。这个结论来自已保存图片的重新测量，只能作为下一轮诊断依据。SOCF-A的预Gate统计发现来源冲突在保存的消费者输出中是可测的；CVaR和DLV的合成小测试证明代码规则可运行，但不说明真实数据有效。

**创新现在是什么状态：** 还没有能诚实写成“方法有效”的创新。原来的GRC-Memory与已有几何选择和长期记忆工作存在近邻重叠，因此暂时退到候选。当前最重要的创新问题是：在固定预算下，历史几何风险或来源冲突能否在真正未见的未来RGB-D/位姿上预测并降低尾部误差；如果不能，就把论文改成有价值的评测/负结果工作，而不是硬保留方法名。

**下一步实际动作：** 先完成Gate 0的合法数据合同和实现冻结，再运行真正的VMem开发基线；之后用同一候选池、同一记忆槽位、同一计算预算比较最近帧、随机、位姿距离、覆盖率、confidence、utility和持久事件等强基线，最后才允许SOCF/GRC候选使用未来答案做一次封存后的评分。

**给老师的一句话：** “我已经在H800上完成了VMem组件加载和CUT3R的真实GPU前向，也保留了之前低MSE但重影明显的失败证据；现在我没有提前宣称创新，而是在冻结数据和防泄漏规则后，先完成完整VMem基线，再检验固定预算下历史几何风险是否真的能改善未见未来的几何误差。”

## 7. Evidence paths

- `work/S103_h800_model_load_smoke/remote_receipts_588459/RECEIPT.json`
- `work/S104_h800_cut3r_calibration/remote_receipts_586719/RECEIPT.json`
- `work/S102_gate0_tum/remote_receipts_588524/RECEIPT.json`
- `work/SOCF_pre_gate_20260916/run_01/AGGREGATES.json`
- `work/ghosting_diagnostic_pre_gate_20260916/REPORT.md`
- `work/cvar_dlv_prep_20260916/results.json`
- `work/agents/INNOVATION_SYNTHESIS_20260916.md`
- `docs/RESEARCH_PLANS_EN.md`
- `docs/GPU_EXPERIMENT_PLAN_AND_PROGRESS_20260915.md`
- `RESEARCH_MEMORY.md` and `RESEARCH_LOG.md` (canonical ledger; append-only)
