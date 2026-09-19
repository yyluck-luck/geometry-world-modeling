# CURRENT EXECUTION OVERRIDE — 2026-09-19 21:54 Asia/Shanghai

This override supersedes the older 2026-09-16 image-blocker paragraphs below. The repository ledger records that the signed S103 launch/isolation chain completed a **fixed-context video-generation forward** in job 594155: the predictor bypassed `VMemPipeline.__init__`, surfel construction, and context retrieval, and used the manually fixed history frames 0/15/30/45. It produced `PREDICTION_SEALED`; the bound artifacts are at `work/S103_selector_free_baseline/run_receipts_594155/` and `work/S103_selector_free_baseline/baseline_score_594155/`. The score receipt reports 16.026 dB but remains `RGB_SCORE_COMPLETE_PENDING_INDEPENDENT_RECOMPUTE`. This is a development-scope RGB result on already exposed scene_13/scene_14 data; it is not a VMem memory-system baseline, held-out result, or method-validation result.

The later S105–S111 diagnostics are also development-scope and their interpretation is constrained by the state-leak correction recorded in the ledger. The current software-only dispatch-guard regression is **9/9 PASS** after the raw validator-receipt hash and bundled-fixture fixes (`work/remote_tmux/LAUNCH_GATE0_V2_REGRESSION_RECEIPT.json`); this receipt proves only local dispatch accounting.

The latest project decision is **END-LINE for the proposed new mechanism**: the axis-(e) occupancy gate is closed by the recorded Steady-Forcing/Internal-DW evidence. Do not submit the previously discussed clean re-test, training, or any new method run. `new_method_validated=false` and `novelty_authorization=NONE` remain unchanged; the withdrawn 800 GPU-hour tranche stays withdrawn.

The remaining work is evidence/reporting for the reproducible frozen-generator case study, not another smoke test or candidate search. Gemini remains advisory only.

# Gate 0 and GPU start status (2026-09-16)

## Current decision

`BLOCKED_FORMAL_BASELINE_PENDING_CONTRACT_FREEZE`.

The next GPU inference work package is **S103-VMemBase (selector-free VMem development baseline)**. The saved-prediction geometry decomposition uses the display alias **S103-GeoDiag**; historical directory names remain unchanged. These are separate work packages. S103-VMemBase will start only after a new reviewed Gate0 contract revision reaches `PRE_RUN_READY`; it will be launched and monitored from a remote `tmux`/`screen` session. A held-out/method claim still requires separately qualified scope and the later post-run acceptance chain.

## Parallel review track

Gemini is being used through the user-opened in-app browser as an independent implementation and leakage review. Its role is limited to reviewing the frozen contract questions and proposing falsifiable checks; it does not receive credentials or private files, does not change the repository, and its advice is not a Gate0 PASS. The current Gemini review confirms four immediate actions: separate pre-run from post-run checks, disambiguate S103 identifiers, enforce runtime input isolation rather than keyword scanning, and recompute staged artifact hashes before dispatch.

The old formal launcher remains preserved. A new fail-closed v2 guard, `work/remote_tmux/launch_gate0_v2_in_tmux.sh`, now requires the v2 validator to return `PRE_RUN_READY` with no errors and binds the contract, protocol, validator, Slurm script, run ID and scope before creating tmux. Its 9/9 dispatch regressions are software checks only; no remote job was submitted through it.

## GPU work already started

Job `588611` completed on 2026-09-16 with Slurm `COMPLETED|00:00:48|0:0`, launched from persistent tmux session `s103-load-smoke-20260916`. It loaded all four model components in 23.96 seconds, with 7.884 GB peak allocated GPU memory. It is a model-load smoke only (`data_access=NONE`, `forward_completed=false`, no scoring); the receipt and final accounting are retained in `work/S103_h800_model_load_smoke/remote_receipts_588611/`. This job does not grant formal Gate0 or authorize S103-VMemBase.

## Remaining Gate0 work

1. Freeze camera intrinsics, distortion, pixel-center convention, and pose transform direction for the selected source.
2. Freeze depth invalid-value handling, scale, and radial-versus-optical-axis conversion.
3. Freeze deterministic one-to-one RGB-D pairing, tie rule, and complete drop/duplicate counts.
4. Freeze history, calibration, and future query windows; hash predictions before any future GT is opened.
5. Acquire and hash an independent held-out scene with no pre-freeze metadata exposure. TUM FR3 and ICL-NUIM currently remain development/conditional candidates.
6. Freeze candidate pool, selection budget, seed/RNG, context/output counts, steps, resolution, dtype, runtime, checkpoint hashes, source/config hashes, and independent readback.

## Timing estimate

- Contract completion: **hours to one working day after the independent data/implementation review**, assuming no new data-access problem.
- First S103 H800 run: **same day the contract passes**; one development run is expected to take hours, with queued GPU time and retries recorded separately.
- S103 baseline family and readback: approximately **1–2 working days**.
- Formal GRC/SOCF and FGB-Future comparisons: only after the baseline prediction seal and same-pool controls; expected additional **2–4 working days**.

These are operational estimates, not guarantees of scientific success or paper acceptance.

## Persistent execution

Use `work/remote_tmux/launch_slurm_in_tmux.sh`. VPN disconnection must not stop the detached session or Slurm job. Save the tmux session name, Slurm job ID, remote log, output seal, and final `sacct` receipt.

## Innovation rotation

At least one innovation agent is continuously assigned when a slot is available. The current rotation is `/root/innovation_round3_counterfactual`; after it completes, assign the next bounded primary-source or falsification task before releasing the slot. Current status remains `new_method_validated=false` and `novelty_authorization=NONE`.

## Apptainer GPU-compatible isolation probe (2026-09-16 02:21 Asia/Shanghai)

The H800 resource path is schedulable, but the enforced predictor boundary is still not accepted. Persistent tmux jobs 588659, 588660, 588661, 588662 and 588664 tested Apptainer 1.1.9 with `--nv --containall --no-home --cleanenv` and no model, checkpoint, dataset, or GT access. 588659 failed because an empty sandbox had no `/dev` mount target; 588661–588664 failed to execute the bound Python environment from the minimal sandbox (including a direct `python3.11` attempt). The retained receipt is `work/S103_selector_free_baseline/apptainer_cuda_probe_receipts_20260916/RECEIPT.json`.

Decision: GPU-compatible isolation remains `BLOCKED`. Do not dispatch S103-VMemBase through an unverified container or through the rejected `unshare` boundary (CUDA error 304). The next decisive prerequisite is a digest-pinned, executable GPU image/rootfs or an independently reviewed Pyxis image, followed by the synthetic allow/deny/escape probe and a pre-run isolation receipt. `new_method_validated=false`; `novelty_authorization=NONE`.

## VMem transfer integrity verified (2026-09-16 02:37 Asia/Shanghai)

The previously partial remote transfer is now complete and independently checked. `work/S101_env_bootstrap/VMEM_TRANSFER_INTEGRITY_RECEIPT_20260916.json` records byte and SHA-256 matches for VMem, CUT3R-512, OpenCLIP, VAE weights, and VAE config. The VMem remote SHA is `675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4`.

This closes transfer integrity only. The existing no-data model-load receipt 588611 is consistent with the same VMem SHA and remains a model-load smoke, not a forward. The next critical path is the implementation audit plus v2 Gate0 contract freeze; no S103-VMemBase forward is dispatched until the GPU-compatible isolation image and synthetic boundary probe pass.


### Future-manifest clarification (2026-09-16)

No pre-seal manifest is scorable. Set `prediction_sealed=true` only after all arm outputs and hashes freeze; keep `future_scoring_permitted=false` until then. Use separate `denominator_spec_hash` and post-seal `realized_denominator_hash`; SIPP is a score-to-source-ID permutation with preserved source tensors/features/support/pose and recorded seed/hash.


### Receipt namespace correction (2026-09-16)

Environment/transfer/CUDA/import PASS states do not imply VMem readiness; formal status remains `NOT_RUN|BLOCKED` until an explicit model-forward Gate0 receipt. Any single qualified held-out query is diagnostic only. Pre-seal future scoring uses `denominator_spec_hash` only; realized denominator and future modalities are unavailable until `prediction_sealed=true`.


### Image pull feasibility boundary (2026-09-16)

Apptainer/Enroot/Pyxis expose image interfaces, but registry pull permission, network, quota, cache, and an approved digest are UNKNOWN. No image was pulled or approved. Keep the formal blocker as `BLOCKED_GPU_ISOLATION_IMAGE`; do not treat tool capability as image availability.

## Dispatch guard implementation (2026-09-16 05:15 Asia/Shanghai)

The local Gate0 dispatch guard now writes an atomic `gwm-formal-launch-guard-receipt-v1` after successful tmux creation and binds the validator receipt, dispatch manifest, contract/protocol, predictor wrapper, execution boundary, Slurm/generic launcher, run ID, scope, state/log paths, and exact command. The software-only regression is 9/9 PASS. This is dispatch accounting only; it does not mean Slurm, predictor execution, isolation, or scientific validation succeeded.

## GPU image isolation resolved at probe level (2026-09-16 12:49 Asia/Shanghai)

This supersedes the `BLOCKED_GPU_ISOLATION_IMAGE` entries above; their historical content is unchanged.

- Digest-pinned image obtained: `docker://nvidia/cuda@sha256:63a18dd805367dacfb077aeced8384ab2fb569598ec5f5f5220c3f90a5c23650`, pulled anonymously from `registry-1.docker.io` on `slogin-02` in persistent tmux (`gwm-pull`, 2 m 33 s, exit 0). SIF `sha256:5a79221373914393c844cc92c32c89e722003591431f3545fc674c0739c59dd0`, 1,526,910,976 bytes, stored at `/home/yliutz/gwm-images/` outside the project tree so rsync cannot return it.
- Synthetic probe job `589607` (`gwm-img-isolation`) COMPLETED on `dgx-21`, 28 s, exit 0:0, launched from persistent tmux `gwm-img-probe`. `model_access=false`, `dataset_access=false`, `ground_truth_access=false`, `forward_completed=false`.
- Verdict `SYNTHETIC_PROBE_PASS`: the bound interpreter `/home/yliutz/.conda/envs/gwm-cut3r-py311-20260915/bin/python3.11` executes inside the image; the staged input bind is readable and read-only; the unbound sentinel and the project root are invisible; `/` is read-only; `torch 2.7.0+cu126` completed a 1024x1024 CUDA matmul with `NVIDIA H800` (driver 580.159.03), peak 53.5 MB.
- Receipt and hashes: `work/S103_selector_free_baseline/gpu_image_isolation_20260916/COMPUTE_ISOLATION_RECEIPT_20260916.json`, raw outputs in `.../remote_receipts_589607/`. Protocol frozen before the pull in `.../README.md`.

Boundaries preserved: this is infrastructure evidence, not a Gate0 pass, not a security boundary against malicious code, and not a scientific result. `formal_gate0_status=BLOCKED` and the missing artifacts are unchanged: effective v4 contract, scorer, independent verifier, full window manifests, command-camera provenance, then `PRE_RUN_READY` plus the formal launch guard receipt. The compute node lacks `squashfuse`/`fuse2fs`, so every `apptainer exec` converts the SIF to a temporary sandbox; measure that startup cost before the formal run.

## Exact S103 contract boundary and current blocker (2026-09-16 13:53 Asia/Hong_Kong)

This supersedes the earlier list of missing scorer/window/runtime artifacts while preserving the historical entries.

- Frozen development candidate: `S103-VMemBase-scene13-w001-v1`; scene13/seq-01 history frames 0/15/30/45 and predeclared command/target frames 60/75/90/105.
- Runtime identity is complete: 13 predictor records, 12 scorer-only future references, 188 source/config files, four model checkpoints, VAE config, predictor/scorer/verifier, and the digest-pinned CUDA SIF are hash-bound.
- Exact boundary job 589826 completed on dgx-09 in 25 seconds with exit 0:0. The stage/source/weights mounts were read-only; project root, dataset root, and every declared future-outcome path were invisible; H800 CUDA matmul passed. `model_loaded=false`, `model_forward=false`, `future_outcome_bytes_opened=false`.
- Candidate validation checked 216 non-review artifacts and returned `BLOCKED_INDEPENDENT_REVIEWS_ONLY`. The remaining real decisions are (1) independent adapter acceptance and (2) different-author approval of canonical protocol SHA `e8ba3f39806541b92948b0d6a92eb425d4dadb120f73b4eb35a3056d9ed70cad`.

Formal GPU prediction is still `NOT_RUN|BLOCKED`. Do not submit the predictor until both reviews exist, validator output is `PRE_RUN_READY` with no errors, and the formal launch guard binds the final contract. No scientific, geometry, held-out, method-comparison, or novelty claim is supported yet.

## v5 correction superseding v4 (2026-09-16 18:43 Asia/Hong_Kong)

The previous v4 execution candidate must not be used. Audit found a camera-intrinsics implementation defect: history K received the crop offset twice and query K incorrectly scaled the homogeneous row. The corrected predictor applies one shared transform to all eight frames and asserts exact history/query K consistency.

- Corrected predictor SHA: `534fd553e24b667fb50f01a6019d9d792b591d9bf3785024eaeadc40cfd46585`.
- Replacement runtime v2 SHA: `732c222536395664dd9cb99a66cf8818e97ac679c62b0b096c4b33e124b39a92`.
- Replacement exact boundary: Slurm 590696, dgx-27, `COMPLETED|0:0|00:00:49`, receipt SHA `dc69ee8c794cf9b4d60103b3585b1211579778ccfd757ac954ae27ecc56f24a5`.
- Current contract: v5 SHA `f0597ad547e6f443917c57dd8bf49f62daeb755f6ab1621587d9784793fa50ca`, protocol SHA `bfc3e843957ad6e3e0b26302d2ca47be1b67a9d93767e86acf18d4b2f7721df8`.
- Validator still verifies 216 non-review artifacts and blocks only on the two independent reviews.

No formal bundle exists, no predictor job was submitted, and no future outcome was opened. Formal status remains `NOT_RUN|BLOCKED_INDEPENDENT_REVIEWS_ONLY`.

## v6 correction superseding v5 (2026-09-16 21:44 Asia/Hong_Kong)

The v5 predictor must not run. Supervisor review against the official VMem pipeline found that v5 centered the four history cameras first and appended four uncentered query cameras, whereas VMem concatenates all eight cameras before one shared centering/scaling step. The corrected predictor SHA is `75af8cad1de25ea7e43ad90c6c7bd89de33d7aa86da50afe8735da612a11189f`; its 12/12 static regression includes an all-eight-camera ordering check and a runtime pairwise-translation invariant.

- Runtime v3 SHA: `7b635f37f3af25bf27b20a2707e2a8dac2fa9765c25ca91750d270dcda41a007`.
- Exact boundary: Slurm 591500, dgx-21/H800, `COMPLETED|0:0|00:00:30`; receipt SHA `d3152f127fd6ca4c6aa6194dcc8fb29b0367cf786e52799e0dd0f91b7368a605`.
- Base candidate v6 SHA: `f866ce3def2b99d3502e80d75b6d4ddd607069a12b2aa611b03238dfde84d4cc`; base protocol SHA `b2ca723942f66617698c4862669d32a70102893c2fcb63d635af39ad07b4c11f`.
- Hardened review gates: different reviewer identity plus substantive findings/limitations; adapter review must bind before final protocol review. Server regressions are 11/11, 6/6, 12/12, 4/4, 11/11, and launch guard PASS.
- Validator verifies 217 non-review artifacts. The ten messages reduce to two missing decisions: independent adapter acceptance and different-author approval of the final adapter-bound protocol SHA.

The first formal GPU forward can be submitted approximately 60–120 minutes after real reviewers become available, assuming neither review finds a new defect. Slurm queue delay follows submission and is not predictable here. Without genuine reviewers there is no honest start date. The current blocked contract correctly refuses formal bundle creation; no forward, score, prediction output, or future-outcome access exists.
