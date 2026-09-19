# CURRENT EXECUTION OVERRIDE — 2026-09-19 21:54 Asia/Shanghai

This override supersedes the older 2026-09-16 image-blocker paragraphs below. The repository ledger records that the signed S103 launch/isolation chain completed a **fixed-context video-generation forward** in job 594155: the predictor bypassed `VMemPipeline.__init__`, surfel construction, and context retrieval, and used the manually fixed history frames 0/15/30/45. It produced `PREDICTION_SEALED`; the bound artifacts are at `work/S103_selector_free_baseline/run_receipts_594155/` and `work/S103_selector_free_baseline/baseline_score_594155/`. The score receipt reports 16.026 dB but remains `RGB_SCORE_COMPLETE_PENDING_INDEPENDENT_RECOMPUTE`. This is a development-scope RGB result on already exposed scene_13/scene_14 data; it is not a VMem memory-system baseline, held-out result, or method-validation result.

The later S105–S111 diagnostics are also development-scope and their interpretation is constrained by the state-leak correction recorded in the ledger. The current software-only dispatch-guard regression is **9/9 PASS** after the raw validator-receipt hash and bundled-fixture fixes (`work/remote_tmux/LAUNCH_GATE0_V2_REGRESSION_RECEIPT.json`); this receipt proves only local dispatch accounting.

The latest project decision is **END-LINE for the proposed new mechanism**: the axis-(e) occupancy gate is closed by the recorded Steady-Forcing/Internal-DW evidence. Do not submit the previously discussed clean re-test, training, or any new method run. `new_method_validated=false` and `novelty_authorization=NONE` remain unchanged; the withdrawn 800 GPU-hour tranche stays withdrawn.

The remaining work is evidence/reporting for the reproducible frozen-generator case study, not another smoke test or candidate search. Gemini remains advisory only.

## Dispatch guard implementation update — 2026-09-16 05:15 Asia/Shanghai

The local formal dispatch guard now persists an atomic `gwm-formal-launch-guard-receipt-v1` after successful tmux creation. It binds the validator receipt SHA and `PRE_RUN_READY` result, sealed dispatch-manifest SHA, contract/protocol/validator/Slurm/generic-launcher hashes, predictor-wrapper SHA, execution-boundary ID, run ID, scope, session, state directory, remote log, and exact command. The software-only regression suite now passes 9/9, including receipt persistence and wrapper-binding tamper rejection (`work/remote_tmux/LAUNCH_GATE0_V2_REGRESSION_RECEIPT.json`).

This closes a local dispatch-accounting gap only. It does not provide a GPU image, compute-node isolation receipt, Gate0 `PRE_RUN_READY`, or scientific evidence. No remote formal launch was made.

## CURRENT EXECUTION OVERRIDE — 2026-09-16 05:10 Asia/Shanghai

State reconciliation: the historical heartbeat says VMem transfer was partial, but the newer integrity receipt `work/S101_env_bootstrap/VMEM_TRANSFER_INTEGRITY_RECEIPT_20260916.json` is `PASS` with matching local/remote SHA-256 for all five required artifacts. Therefore transfer is **COMPLETE_SHA_VERIFIED**; do not resume or duplicate it. The no-data H800 model-load smoke `588611` is complete and must not be repeated.

Current formal state remains `formal_gate0_status=BLOCKED` / `BLOCKED_FORMAL_BASELINE_PENDING_CONTRACT_FREEZE`, with GPU isolation specifically `BLOCKED_GPU_ISOLATION_IMAGE`. Apptainer/Enroot/Pyxis interfaces exist, but no digest-pinned executable image or approved registry/cache path has been verified. The generic tmux launcher does not itself enforce Gate0; a future formal launch also requires a `formal_launch_guard_receipt` binding the validator result, sealed manifest SHA, guarded-wrapper execution, Slurm script, run ID, and execution boundary.

Completed evidence: S104 RGB-only CUT3R component jobs 586699 and 586719; transfer SHA receipt; VMem model-load receipt 588611; Apptainer probes 588659/588660/588661/588662/588664; Gate0 reconciliation report and validator self-test. No formal S103 forward, scoring, GRC, or method experiment is authorized.

Next critical path (bounded): obtain an approved digest-pinned executable GPU image or explicit cluster pull/cache permission; run the synthetic allow/deny/escape plus CUDA probe through the intended compute-node wrapper; create and independently review the fresh v4 contract; validate `PRE_RUN_READY`; create the formal launch guard receipt; only then dispatch the selector-free development baseline in persistent tmux. Failure at any branch retains `BLOCKED` and records the exact receipt.

Innovation Agent: `/root/innovation_next` is assigned a bounded read-only wording/falsification cycle. Its current SOCF-A-v2 note remains design-only, with `PILOT_DIAGNOSTIC_ONLY`, pre/post-seal denominator hashes, and `formal_gate0_status=PASS` requiring an explicit model-forward receipt.

GPU backfill: no useful gate-eligible forward exists while isolation is unresolved; do not submit a redundant smoke or use an unverified container.

# Geometry-aware World Modeling — English Research Plan Registry

**Version:** 2026-09-15T04:22:20Z  
**Language policy:** This file contains plans, protocols, gates, and scheduled-work instructions in English. Chinese files remain unchanged as historical evidence and beginner-facing explanations. Chinese progress summaries are maintained separately in `RESEARCH_MEMORY.md` and `RESEARCH_LOG.md`.

## Priority update: Gate0 and parallel GPU execution (2026-09-16)

The user requests the fastest evidence-supported Gate0 resolution and GPU start. Work proceeds in parallel:

1. **Execution owner:** the existing research task builds the real 3DMatch adapter, staged history/query manifests, enforced input-isolation preflight, and v2 contract. After a separately reviewed `PRE_RUN_READY` decision, start only the declared development baseline; held-out confirmation and method scoring retain separate gates.
2. **Independent implementation review:** a different agent audits and hardens `validate_gate0_v2.py`, binding window identities to actual input records and the isolation receipt to the exact wrapper, scorer manifest, runtime and execution-boundary identity.
3. **Gemini advisory review:** use the user-opened in-app Gemini browser in parallel for concrete contract and leakage questions. Save recommendations and root disposition in `work/agents/GEMINI_GATE0_REVIEW_20260916.md`; an AI response is not data qualification or run acceptance.
4. **GPU evidence:** H800 no-data component-load job 588611 is complete (48 s Slurm elapsed, 23.96 s model loading, 7.884 GB peak allocated memory). Do not repeat the successful smoke; the next missing evidence is actual scoped forward, not another model-load check.
5. **Bounded innovation:** refine falsifiable development-only diagnostics while Gate0 is assembled. No new method or held-out claim is authorized by these diagnostics.

The dispatch path is now split explicitly: the legacy formal launcher is preserved for provenance, while `work/remote_tmux/launch_gate0_v2_in_tmux.sh` is the guarded path for the new v2 contract. It fails closed unless the actual v2 validator returns `PRE_RUN_READY`, `pre_run_ready=true`, and `errors=[]`, and the dispatch manifest binds the protocol, contract, validator, Slurm script, run ID and scope. The launcher regression receipt has 9/9 software-only PASS cases and no remote submission.

Use `S103-GeoDiag` and `S103-VMemBase` as active-plan display aliases; retain immutable historical paths. Scene14 frame000000 is an exposed qualification sample and cannot be called an unseen future outcome. Keep `new_method_validated=false` and `novelty_authorization=NONE`.

## 1. Research contract

**Proposal problem.** Develop and evaluate mechanisms that preserve long-horizon geometric consistency when a world model leaves a view, changes viewpoint, and revisits previously observed content.

**Paper position.** New Problem + Method is the target framing. A method contribution is conditional: it may be claimed only after an independent future-geometry test, fair strong baselines, fixed computation budget, cross-scene confirmation, complete ablations, and an independent readback.

**Current candidate.** GRC-Memory (Geometry-Risk-Calibrated Memory Selection): select history under a fixed budget using future-prediction value penalised by calibrated geometric risk. `new_method_validated=false` and `novelty_authorization=NONE` remain the active status until the tests below succeed.

**Non-negotiable evidence rules.**

1. Freeze data identity, order, input permissions, model/checkpoint identity, budget, metrics, and kill criteria before scoring.
2. Keep calibration/development data separate from held-out future ground truth. A file not decoded is not equivalent to an answer that was never accessible.
3. Separate synthetic program checks, real model inference, saved-data reanalysis, sensor-ground-truth scoring, and end-to-end video generation.
4. Preserve failures, missing values, difficult examples, and all denominators.
5. Do not infer 3-D accuracy from RGB MSE, visual sharpness, retrieval counts, or model confidence.
6. Every innovation candidate must state its nearest published alternatives, mechanism difference, falsifiable prediction, cheapest discriminating experiment, and kill criterion.
7. A tool, agent, harness, or scheduled check is project infrastructure; it is not an algorithmic contribution.

## 2. Plan identity and translation scope

This document is an English working synthesis, not a line-by-line translation of every historical protocol. Historical S identifiers must retain their actual archived meanings. The earlier draft of this registry grouped stages too broadly and incorrectly assigned prospective tasks to existing S92-S100 identifiers. That mapping is withdrawn. No experiment ID is reassigned by this language rewrite.

The verified active entrypoints are:

- **S101 — Remote GPU environment, source, and checkpoint qualification:** `work/S101_env_bootstrap/` and `work/S101_GPU_RUN_MANIFEST.json`.
- **S102 — Dataset qualification and ICL-NUIM contract:** `work/S102_gate0/`.
- **S103, H800 baseline preflight:** `work/S103_H800_VMEM_BASELINE_PREFLIGHT_20260915.json`. This must be identified by its full path because a different S103 saved-prediction geometry decomposition already exists at `work/S103_prediction_geometry_decomposition/`.
- **S91R — Saved future-error reanalysis and confounding correction:** `work/S91R_saved_future_error_reanalysis/`.
- **S92 — Tail-risk decomposition:** `work/S92_tail_risk_decomposition/`.
- **S93 — Alternative TUM data qualification:** `work/S93_ALT_TUM01/`.
- **S94 — Evaluation-contract review and a separate 3RScan qualification route:** use their complete directory names to disambiguate.
- **S97 — Development RGB-D pair audit:** `work/S97_dev_rgbd_pair_audit/`.
- **S98 — Development-window feasibility:** `work/S98_dev_window_feasibility/`.
- **S100 — Context-matched swap:** `work/S100_context_matched_swap/`.

### Prospective work packages (not historical experiment IDs)

- **P01 — Transfer completion:** verify size and SHA-256 for all remote checkpoints.
- **P02 — Offline model construction:** load the declared model components on H800; record variants and fail if a dependency requests an unapproved checkpoint substitution.
- **P03 — Dataset adapter:** implement camera/depth conventions and time alignment with synthetic algebra checks and development-only readback.
- **P04 — Freeze implementation:** hash code, configuration, allowed inputs, seeds, precision, and budgets before inference.
- **P05 — Development baseline:** generate from fixed past RGB and allowed target cameras, retaining all outputs and failures.
- **P06 — Baseline scoring:** seal predictions before target RGB/depth access; separate image-quality and geometry endpoints.
- **P07 — Natural-failure classification:** identify actual long-horizon errors and test simpler camera, scale, and appearance explanations.
- **P08 — Same-pool strong selectors:** compare recency, random, pose-distance, coverage, confidence, and utility policies under measured equal budgets.
- **P09 — Geometry-risk prediction test:** test whether historical risk predicts signed future loss beyond confounders.
- **P10 — Source-conflict abstention candidate:** evaluate stable pairwise conflict and an explicit baseline fallback, subject to nearest-work verification.
- **P11 — Future-value residual candidate:** test incremental future value beyond risk/coverage; do not introduce held-out outcomes as inputs.
- **P12 — Event-triggered replacement candidate:** first verify natural leave/revisit events, then compare equal replacement counts.
- **P13 — Calibration:** learn thresholds only on calibration/development partitions; state exchangeability/sequence limitations.
- **P14 — Held-out confirmation:** freeze the selected method and protocol before accessing independent future outcomes.
- **P15 — Cross-scene confirmation:** acquire qualifying independent scenes; do not substitute repeated windows for independent scenes.
- **P16 — Ablations and cost:** measure component removal, matched compute, runtime, memory, coverage and tails with complete denominators.
- **P17 — Independent audit:** recompute metrics and inspect leakage, fairness, numerical stability and claim scope.
- **P18 — Chinese teaching report:** explain the proposal, methods, actual data, negative results and advisor questions; keep planning specifications in English.

### Source-protocol inventory

The entries below identify archived or active sources by their exact filenames. Listing an entry does not mean its full text has been translated, that it is still scheduled, or that its experiment succeeded. English equivalents must preserve the frozen semantics and source hash.

- `docs/GPU_EXPERIMENT_PLAN_AND_PROGRESS_20260915.md`
- `docs/RESEARCH_PLANS_EN.md`
- `docs/S0_PROTOCOL.md`
- `docs/S10_RENDERER_COMPARISON_PROTOCOL.md`
- `docs/S11_RENDERER_REGRESSION_PROTOCOL.md`
- `docs/S11_SOURCE_REGRESSION_PROTOCOL.md`
- `docs/S12_MATCHED_BUDGET_PROTOCOL.md`
- `docs/S14A_FEATURE_EXTRACTION_PROTOCOL.md`
- `docs/S14D_RAY_ONLY_PROTOCOL.md`
- `docs/S14E_FINAL_PROTOCOL.md`
- `docs/S14_SCENE_AND_PRECISION_PLAN.md`
- `docs/S15A_NATIVE_HISTORY_PROTOCOL.md`
- `docs/S15A_NATIVE_HISTORY_PROTOCOL_V2.md`
- `docs/S15B_CONSUMER_PROTOCOL.md`
- `docs/S15B_PREFIX_PROTOCOL.md`
- `docs/S15C_OBSERVED_DEPTH_PROTOCOL.md`
- `docs/S16_INTERFERENCE_PROTOCOL.md`
- `docs/S17B_DPT_TWO_FRAME_PROTOCOL.md`
- `docs/S17C_EMBEDDED_GEOMETRY_PROTOCOL.md`
- `docs/S18_EXECUTION_PROTOCOL.md`
- `docs/S1_PROTOCOL.md`
- `docs/S20_MINIMAL_VIDEO_PROTOCOL_DRAFT.md`
- `docs/S21_BASELINE_PROTOCOL.md`
- `docs/S22_FILT_BASELINE_PROTOCOL.md`
- `docs/S22_FILT_BASELINE_PROTOCOL_DRAFT.md`
- `docs/S22_FILT_SHARED_PRECISION_PROTOCOL.md`
- `docs/S23_GEOMETRY_DIAGNOSTIC_PROTOCOL.md`
- `docs/S24_BASELINE_EXPANSION_PROTOCOL.md`
- `docs/S24_HORIZON_DIAGNOSTIC_PROTOCOL.md`
- `docs/S26B_CONSUMER_SCORING_PROTOCOL.md`
- `docs/S26_CONSUMER_EXECUTION_PROTOCOL.md`
- `docs/S26_CONSUMER_SCORING_PROTOCOL.md`
- `docs/S2_S3_PROTOCOL.md`
- `docs/S4_TWO_FRAME_PROTOCOL.md`
- `docs/S5_SEQUENCE_PROTOCOL.md`
- `docs/S6_MEMORY_BRIDGE_PROTOCOL.md`
- `docs/S7_EVENT_REPLAY_PROTOCOL.md`
- `docs/S8_EXTERNAL_SCENE_PROTOCOL.md`
- `docs/S8_EXTERNAL_SCENE_PROTOCOL_V2.md`
- `docs/S9_COMPONENT_PROFILE_PROTOCOL.md`
- `work/S100_context_matched_swap/PROTOCOL.md`
- `work/S27_saved_scale_preparation/PROTOCOL.md`
- `work/S33_preparation/PROTOCOL_CANDIDATE.md`
- `work/S39_component_variant/PROTOCOL_DRAFT.md`
- `work/S40_declared_variant_generation/PROTOCOL_DRAFT.md`
- `work/S40_result_readback/PROTOCOL_DRAFT.md`
- `work/S41_vmem_xet_attempt4/PROTOCOL.md`
- `work/S42_baseline_failure_preregistration/PROTOCOL.md`
- `work/S42_statistical_preregistration/PROTOCOL.md`
- `work/S44_c1_confirmation_generation/PROTOCOL.md`
- `work/S45B_c1_numeric_camera_guard_preparation/PROTOCOL.md`
- `work/S45B_c1_numeric_camera_guard_supervised_v10/PROTOCOL.md`
- `work/S45B_c1_numeric_camera_guard_supervised_v11/PROTOCOL.md`
- `work/S45B_c1_numeric_camera_guard_supervised_v12/PROTOCOL.md`
- `work/S45B_c1_numeric_camera_guard_supervised_v5/PROTOCOL.md`
- `work/S45B_c1_numeric_camera_guard_supervised_v6/PROTOCOL.md`
- `work/S45B_c1_numeric_camera_guard_supervised_v7/PROTOCOL.md`
- `work/S45B_c1_numeric_camera_guard_supervised_v8/PROTOCOL.md`
- `work/S45B_c1_numeric_camera_guard_supervised_v9/PROTOCOL.md`
- `work/S45_c1_result_readback/PROTOCOL.md`
- `work/S46_c1_blind_scoring_wrapper/PROTOCOL_DRAFT.md`
- `work/S46_c1_blind_scoring_wrapper_v2/PROTOCOL_DRAFT.md`
- `work/S46_c1_blind_scoring_wrapper_v3/PROTOCOL_DRAFT.md`
- `work/S47B_c2_confirmation_generation_v8/PROTOCOL.md`
- `work/S47B_c2_confirmation_generation_v9/PROTOCOL.md`
- `work/S47_c2_confirmation_generation/PROTOCOL.md`
- `work/S57_camera_observer_calibration/PROTOCOL.md`
- `work/S58_c2_result_readback/PROTOCOL.md`
- `work/S60_renderer_unit_replay/PROTOCOL.md`
- `work/S61_unit_consistent_retrieval/PROTOCOL.md`
- `work/S62_b0_context_integration/PROTOCOL.md`
- `work/S63_c2_context_integration/PROTOCOL.md`
- `work/S64_unit_repaired_generation/PROTOCOL.md`
- `work/S66_s64_camera_scoring/PROTOCOL.md`
- `work/S67_translated_query_diagnostic/PROTOCOL.md`
- `work/S68_tum_vmem_cache_bridge/PROTOCOL.md`
- `work/S69_tum_camera_conditioning/PROTOCOL.md`
- `work/S70_fixed_context_generation/PROTOCOL.md`
- `work/S75_vae_history_roundtrip/PROTOCOL.md`
- `work/S76_relative_camera_response/PROTOCOL_DRAFT.md`
- `work/S76_relative_camera_response/PROTOCOL_RUN_V1.md`
- `work/S77_generated_wrong_pose_control/PROTOCOL.md`
- `work/S78_match_visual_preflight/PROTOCOL_DRAFT.md`
- `work/S87_terminal_strength_audit/PROTOCOL_DRAFT.md`
- `work/S91R_saved_future_error_reanalysis/PROTOCOL.md`
- `work/S91_grc_pilot_protocol/PROTOCOL.md`
- `work/S92_tail_risk_decomposition/PROTOCOL.md`
- `work/S93_ALT_TUM01/PROTOCOL.md`
- `work/S94_ALT_3RSCAN01/PROTOCOL.md`
- `work/S96_gim_saved_pose_audit/PROTOCOL.md`
- `work/S97_dev_rgbd_pair_audit/PROTOCOL.md`
- `work/S99_fixed_budget_risk_update/PROTOCOL.md`

## 3. Current execution order

1. Complete the interrupted remote weight transfer and verify every remote SHA-256. Record incomplete files as a failed transfer attempt.
2. Verify the declared VAE/config identity and the local CLIP checkpoint identity. If the original VMem VAE cannot be reproduced, label the run as a declared-variant baseline.
3. Run a model-load smoke on H800 with no dataset or future ground truth. Save memory usage, package versions, checkpoint paths, and exit status.
4. Run the frozen VMem baseline on calibration/development targets only. Seal predictions and metadata before opening held-out depth/pose answers.
5. Score RGB and geometry separately. Report AbsRel, RMSE, valid-pixel counts, reprojection/pose metrics where valid, coverage, collisions, and visual artifacts.
6. Run the same-candidate-pool, same-budget selector baselines. Only then execute GRC-Memory.
7. Apply independent recomputation and a cross-scene confirmation. If the first falsifiable hypothesis fails, stop the method claim and reframe as a diagnostic/benchmark result.

## 4. Scheduled workflow instruction

Every 30 minutes, check: (a) actual skill execution, (b) innovation and nearest-work evidence, (c) experiment authenticity and leakage, (d) local tools and GPU state, (e) English literature retrieval when needed, (f) agent roles and failures, and (g) memory/artefact records. Then perform the most important executable next step. Notify only on a meaningful change, completion, failure, or user action requirement.

The scheduler must use the latest completed experiment to rewrite its next prompt. It must not repeat a successful run merely to create activity, and it must not claim that an agent is working when the service reports capacity failure.

## 5. Claim boundary and handoff

The project currently has a reproducible environment and conditional synthetic-data access, not a completed VMem baseline and not a validated GRC method. The active scientific decision is whether a low-risk history predicts lower future geometric error under a fair fixed-budget comparison. Any result that fails this test remains a useful negative result, but it cannot be presented as a method improvement.

## 2026-09-16 GPU execution update: isolation is the hard gate

The H800 path is operational for no-data model loading, but the formal selector-free VMem baseline remains blocked. `unshare` reached the predictor boundary and then failed with CUDA error 304 on the compute node. Apptainer 1.1.9 exposes `--nv`, `--containall`, `--no-home`, and explicit bind flags, yet the current minimal sandboxes cannot execute the bound conda Python binary (jobs 588659, 588661, 588662, 588664). These probes opened no model, RGB-D, future outcome, or ground truth.

Required next step: use a digest-pinned executable GPU image/rootfs or reviewed Pyxis image, run a synthetic CUDA plus forbidden-path/escape probe, record mountinfo/device/network evidence, and bind only staged history, command-camera inputs, and output. A successful CUDA probe alone is insufficient. If no image can be verified, preserve the infrastructure failure and do not dispatch S103-VMemBase. `new_method_validated=false`; `novelty_authorization=NONE`.

## 2026-09-16 Transfer integrity closure and next critical path

The partial VMem transfer is now complete. A fresh remote SHA-256 check matched all five required files against the local manifest: VMem, CUT3R-512, OpenCLIP, VAE weights, and VAE config. The VMem digest is `675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4`; evidence is `work/S101_env_bootstrap/VMEM_TRANSFER_INTEGRITY_RECEIPT_20260916.json`. The prior 588611 no-data model-load smoke is consistent with that digest and should not be rerun.

The next executable task is implementation audit and v2 Gate0 contract reconciliation. The audit must bind the source-specific adapter, exact predictor/scorer/runtime hashes, the execution boundary, identity windows, and pre-run isolation receipt. If a digest-pinned executable Pyxis/Apptainer image is available, run the synthetic CUDA plus forbidden-path/escape probe; otherwise retain the infrastructure blocker. Do not dispatch S103-VMemBase or formal GRC/SOCF while isolation and Gate0 remain unresolved. `new_method_validated=false`; `novelty_authorization=NONE`.

### Next task specification after transfer PASS

- **Objective:** produce a reviewed v4 development contract without changing the frozen S103 implementation.
- **Inputs:** `VMEM_TRANSFER_INTEGRITY_RECEIPT_20260916.json`, `work/S102_gate0_3dmatch/adapter_v1/QUALIFICATION_RESULT.json`, `work/S102_gate0_tum/validate_gate0_v2.py`, and the current predictor/scorer/runtime files.
- **Local commands:** `python3 work/S102_gate0_tum/validate_gate0_v2.py --self-test`; then validate the new contract with `python3 work/S102_gate0_tum/validate_gate0_v2.py --stage pre-run <contract.json>`.
- **Agent assignment:** Gate0 audit agent drafts the field-level reconciliation; the Innovation Agent continues the read-only Pyxis/image falsification cycle.
- **GPU requirement:** none for contract construction. A compute-node synthetic probe is allowed only after a digest-pinned executable image is identified and must run in persistent `tmux`/Slurm.
- **Acceptance:** all required file descriptors, hashes, identity windows, runtime bindings, isolation receipt, budget, and independent pre-run review are bound and validator returns `PRE_RUN_READY` with `errors=[]`.
- **Stop branches:** retain `BLOCKED` if any descriptor is missing, if the image is not immutable/executable, if CUDA or any forbidden-path probe fails, or if the candidate scene is not genuinely eligible for the declared scope.

## Innovation cycle: SOCF-A-v2 (2026-09-16)

The dedicated Innovation Agent refined SOCF-A into a conditional, falsifiable hypothesis: a history-only source-conflict score may forecast the signed effect of replacing one source under a fixed VMem budget, with abstention for unstable directions. The closest mechanisms are pose/redundancy retrieval, geometry/coverage selection, and future-aware KV importance. The main competing explanation is a renamed pose/visibility/coverage/confidence or source-identity proxy.

This candidate is recorded in `work/agents/SOCF_A_v2_INNOVATION_UPDATE_20260916.md`. It remains design-only. The minimum experiment is one qualified held-out query, k=4, baseline versus one pose/support-matched replacement, three exact replays, sealed predictions, and paired future depth/reprojection/pose losses. It is prohibited until the selector-free baseline, same-pool controls, and compute-node isolation pass. Kill if intervention effects do not exceed replay variation, direction is unstable, a simpler proxy explains the effect, or fixed-denominator future geometry does not improve.

### SOCF-A-v2 adversarial refinement

A concrete confounder is renderer support/owner change: a source intervention can alter valid-pixel count, z-buffer visibility, source provenance, and evidence density, creating a signed loss delta without a conflict mechanism. The required control is SCMC (Support/Conflict-Matched Control), with exact pre-intervention target support-mask equality whenever possible, matched owner counts, pose distance, confidence, candidate pool, k, forward count, seed, and budget. If exact matching is impossible, report `UNTESTABLE_SUPPORT_MATCH` and stop causal interpretation. This control is design-only and remains downstream of Gate0, the selector-free baseline, and same-pool controls.

### SOCF-A-v2 second confounder: branch-dependent RNG

A second independent confounder is branch-dependent random-number consumption: the same integer seed can produce different noise when retain and intervention paths draw in different orders. Before any SOCF scoring, use NLPRC: freeze/hash initial noise and Python/NumPy/Torch CPU/CUDA RNG states, deterministic flags, schedule, execution order, forward count, and output count; restore snapshots before both arms; add a byte-identical no-op route for the replay envelope. Kill or downgrade if the no-op exceeds the envelope, replay signs flip, or the signed effect fails to exceed the predeclared 95% no-op variation. This remains design-only and blocked by Gate0/isolation.

### SOCF-A-v2 third confounder control: SIPP

Use a Source-ID Permutation Placebo (SIPP) to isolate candidate-pool/source-identity effects. Freeze candidate tensors/features, IDs/order, k, camera/history, model/config, full downstream recomputation, cost, and NLPRC snapshots; then permute only score-to-source-ID assignment across predeclared permutations. The source-aligned arm must exceed the placebo envelope under matched support/coverage/owner and cost. If the gain survives permutation or the mapping cannot be audited, downgrade or kill SOCF; if the control cannot run, report `UNTESTABLE`. This remains design-only.

### SOCF-A-v2 fourth confounder control: intention-to-treat denominator

SCMC, NLPRC, and SIPP still allow post-selection complete-case bias. Hash the full eligible target-query universe before any intervention/future scoring, retain unmatched, failed, abstained, and invalid cases in a feasibility ledger, and use one identical intention-to-treat denominator for SOCF, controls, and placebos. Complete-case results are secondary. Kill or downgrade if gains appear only after exclusions, arm inclusion differs, or the full-denominator effect is within zero/replay bounds.

### SOCF-A-v2 current claim boundary

After SCMC, NLPRC, SIPP, and ITT controls, the only defensible distinction is an auditable source-level signed intervention estimand: predict the change in externally supplied, held-out future RGB-D/pose reference loss when one named memory source is retained versus replaced, with complete consumer recomputation and abstention for unstable directions. Existing reviews identify CUE-R, ViewRope/SplaTAM, and cache-abstention threats. Even if controls pass, treat SOCF-A as a measurement/selection protocol unless residualized held-out gains replicate across scenes and horizons; otherwise downgrade to FGB-Future or a negative evaluation.

### Minimal decisive SOCF package (future, not authorized yet)

Only after an explicit formal Gate0 receipt, isolation, selector-free baseline, same-pool controls, and legal held-out scorer pass, run a cross-fitted signed-source intervention package: two calibration trajectories plus one untouched held-out trajectory/scene; three locked F0/F1 replays; control-only versus control-plus-conflict model; held-out arms SOCF, retain, SCMC, NLPRC no-op, and SIPP placebo; one hashed ITT denominator with pre-seal denominator_spec_hash; the scorer emits realized_denominator_hash only after prediction_sealed=true. Freeze pool/IDs/order, k=4, cameras, costs, hashes, conflict features, NLPRC states, abstention, and SIPP permutations before future access. Kill for replay-sized/sign-unstable effects, no incremental held-out value, failed matched-cost comparisons, exclusion-only gains, one-scene effects, or RGB-only gains with worse future geometry. This package remains unauthorized until every prerequisite passes.

### SOCF consumer-recomputation preflight

Before any signed intervention interpretation, run both F0→F1 and F1→F0 from identical serialized pre-consumer state in fresh processes. Hash memory input, encoded tokens/KV, attention outputs, renderer support/owner/provenance, and final RGB/depth/pose outputs. Require order-invariant results and explicit regeneration/audit of every downstream node of the replaced source. Stop as `INVALID_CONSUMER_RECOMPUTATION` on order dependence, stale mutable state, or untraceable source provenance. This remains downstream of all Gate0 and baseline prerequisites.

### Implementation preflight for the future SOCF package

Serialize the pre-consumer state and run retain/replacement arms in fresh processes in both orders before any future scoring. Hash memory, latent/KV, attention, renderer support/owner/provenance, and final outputs. Any order dependence or stale mutable state stops the estimand as `INVALID_CONSUMER_RECOMPUTATION`.

### Administrative simplification

No scientific gate is removable. To reduce bookkeeping without weakening validity, use one immutable preflight manifest and shared frozen inputs/arm matrix for baseline, SOCF, SCMC, SIPP, and no-op. Preserve all arm labels, fresh-process order reversal, full ITT denominator, and explicit `UNTESTABLE` outcomes.

### Immutable SOCF preflight manifest schema

Use one immutable manifest for any future SOCF package: authorization/gate receipts; environment and hashes; ordered candidate pool; hashed ITT target universe and fixed denominator; RNG/noise snapshots; F0/SOCF-F1/SCMC/NLPRC-no-op/SIPP arms; source-to-pixel provenance and order-reversal audit; prediction seal and future scorer receipt; explicit `UNTESTABLE_*` and invalid decision states. Missing legality, matching, provenance, replay, or denominator evidence can never be recorded as PASS.


### Manifest schema clarification (2026-09-16)

Use `prediction_sealed=true` only after all arm outputs and hashes freeze; keep `future_scoring_permitted=false` before that point and reserve `PASS` for a fully receipted decision. Separate `denominator_spec_hash` (pre-seal rule) from `realized_denominator_hash` (post-seal scorer output). SIPP is only `score_to_source_id_permutation`, preserving source tensors/features/support/pose and recording permutation seed/hash and arm-pool hash.


### Status namespace and pilot boundary (2026-09-16)

Treat transfer/CUDA/import PASS states as environment evidence only; require `formal_gate0_status=NOT_RUN|BLOCKED` until a model-forward Gate0 receipt exists. Any single qualified held-out query is `PILOT_DIAGNOSTIC_ONLY`; only the two-calibration-plus-untouched-held-out package can be `PROTOCOL_EVIDENCE`. Before `prediction_sealed=true`, permit only `denominator_spec_hash`; the scorer creates `realized_denominator_hash` after sealing, and future RGB/depth/pose plus realized valid-pixel counts stay unavailable.


### Innovation shortlist update — FGB-SI (design-only)

FGB-SI estimates the signed effect of retaining versus replacing one named history source on externally supplied, held-out future RGB-D/pose geometry, with complete consumer recomputation and source-to-pixel provenance. ReWorld, Future Forcing, and WorldRoamBench occupy pose-indexed retrieval, future-aware KV selection, and geometry/retention metrics; generic future-aware memory or KV importance cannot support novelty. Falsify FGB-SI if no residual held-out value remains beyond pose/coverage/confidence/utility, if source/common-bias or registration controls erase the effect, or if it appears only in one scene/horizon. This is design-only and remains behind Gate0, isolation, baseline, controls, and authorization.


### Formal launch receipt boundary (2026-09-16)

`gwm-formal-launch-guard-receipt-v1` with `status=PASS` means the software dispatch guard created the tmux session and persisted the bound receipt. It does not mean Slurm completed submission, the predictor wrapper executed, compute-node isolation passed, or a scientific result exists. The downstream worker/Slurm receipt remains required.


### Launch guard regression strengthening — 2026-09-16

The software-only guard regression now passes 9/9. The successful fixture checks required receipt field presence plus exact run/scope/session/log/state/command values, manifest/contract/validator/Slurm/generic/wrapper SHA relationships, execution-boundary ID, and embedded `PRE_RUN_READY` validator status with empty errors. A wrapper-file tamper case is also rejected. This remains dispatch accounting only; no remote formal launch or scientific execution occurred.
