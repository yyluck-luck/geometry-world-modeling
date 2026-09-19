# Geometry-aware World Modeling: Master Experiment Control from S0 to Date and SuperPod GPU Plan

> Source: `docs/GPU_EXPERIMENT_PLAN_AND_PROGRESS_20260915.md`  
> Source SHA-256: `1edbbb0acf22663069897c001dd95c80308c62bea0efa0bf3248fe86c973b371`

Updated: 2026-09-16 (recording times follow `RESEARCH_LOG.md` and the receipts for each experiment)

## Latest verified update: S102 (TUM metadata qualification)

SuperPOD job 588524 completed the TUM Freiburg3 long-office metadata qualification on an H800 after the resource correction `--gpus=1`. The archive contains 2,585 RGB rows, 2,509 depth rows, and 8,710 ground-truth pose rows; 2,488/2,585 RGB-depth pairs fall within the 20 ms audit tolerance. This is a qualification result only: no model forward, prediction, or future-GT scoring was performed. The current decision is `BLOCKED_FORMAL_BASELINE_PENDING_CONTRACT_FREEZE` because the camera/depth contract, future-GT isolation, and independent held-out scene are not yet all frozen.

The next executable experiment is **S103-VMemBase (selector-free VMem development baseline)**; the historical saved-prediction decomposition is **S103-GeoDiag** and must not be conflated with it. S103-VMemBase may be submitted only after the signed contract audit reaches `PRE_RUN_READY`. Formal GRC/SOCF scoring remains prohibited until predictions are sealed and same-pool controls are complete. Gemini is running a parallel, user-opened-browser review of contract circularity, S103 naming, future-data isolation, and staged-artifact hashes; it is advisory only and cannot grant Gate0. The latest primary-source innovation scan keeps SOCF-A conditional and FGB-Future as the safer evaluation contribution; `new_method_validated=false`.

### Persistent execution requirement

Every training or long GPU job will be launched and monitored from a remote `tmux` or `screen` session, which submits the Slurm job and records its final `sacct` state. The prepared launcher is `work/remote_tmux/launch_slurm_in_tmux.sh`; it has not yet submitted a formal run. VPN disconnection therefore cannot stop the detached monitoring shell or the Slurm allocation.

S102 pairing has now been audited with the project matcher in persistent session `s102-pairing` (job 588581): 2,507 candidate edges, 2,488 accepted one-to-one pairs, 97 dropped RGB rows, 21 dropped depth rows, and zero duplicate assigned depth rows. This closes the pairing sub-contract only; it does not close Gate0.

## Conclusion for beginners first

This does not mean that “all experiments are complete.” A large body of empirical evidence now exists for older batches of baselines, failure diagnoses, and qualification audits; **cross-scene experiments that depend on a complete VMem neural forward have not started**. The school SuperPod has been verified to allocate an NVIDIA H800. The correct job 584006 also verified remote torch 2.5.1+cu121 and CUDA matrix operations. Two earlier smoke jobs failed because of quoting errors in an additional Python print command; they remain failure records only.

Formal GRC-Memory still requires independent test data. ICL-NUIM `lr0` has been downloaded (711,444,709 bytes, SHA256 `4eca8c2e9f77c1bd7436c746d22ea6144b8c01fe9bc29a84e734186823f1f1ad`), but some official GT metadata had already been viewed before freezing, so it is marked `development/data-access-held-out candidate` and cannot be claimed as a zero-exposure blind test. The package text-mapping sub-gate passed: RGB/depth/association IDs are 0–1508 and pose IDs are 1–1508; after explicitly discarding association ID 0, the remaining 1508 pairs are one-to-one. Overall Gate 0 remains blocked because time semantics, units, intrinsics, coordinate conventions, split, and GT isolation have not all been frozen.

## Acceptance chain from the original proposal

1. **Problem and literature:** Long-horizon camera motion, object motion, sparse observation, occlusion, and revisits cause geometric inconsistency.
2. **Strong baselines:** First reproduce existing components such as VMem/CUT3R, recording inputs, weights, time, and failures.
3. **Failure taxonomy:** Separate depth/pose drift, visibility, memory update, retrieval, and generator ghosting.
4. **Method:** Keep only candidates that can be falsified by strong baselines; do not rename ordinary gating, confidence, warping, or post-processing as innovation.
5. **Evaluation:** Use the same candidate pool, memory slots, token/VRAM/forward budget, and compare RGB-D, pose, reprojection, tail risk, and cost across scenes.
6. **Delivery:** Independent review, failure boundaries, reproducible experiments, report, and demonstration.

## Actual experiment ledger from S0 to date

Internal IDs are retained for traceability; names in parentheses are the concrete experiment names used in briefings. Accepted old results are not blindly rerun merely to make the record look complete.

| Batch | Concrete experiment name | Actual status | Evidence and boundary |
|---|---|---|---|
| S0–S7 | Memory recovery, fixed-event controls, renderer/save-interface diagnosis | Completed local experiments and review | Mainly protocols, cache, components, and synthetic/local controls; not a complete video or new method |
| S8–S20 | TUM/Bonn data entry, timestamp/camera/depth qualification audit, CUT3R/VMem interface preparation | Mostly complete, failures retained | Multiple licensing, synchronization, optical-coordinate, and missing-data problems found; a data entry point is not a performance result |
| S21–S22 | 300-frame CUT3R/TTT3R/FILT3R geometric-trajectory baselines | Completed | Position RMSE is a baseline comparison for existing methods; not innovation in a generative world model |
| S34–S40 | VMem weights, dependencies, and download recovery | Several reusable components completed; main-weight identity/integrity was previously blocked | Actual model forward and weight identity still need re-verification on H800 |
| S48–S70 | Fixed history, camera response, geometric inputs, real VMem generation chain | Multiple rounds of real local generation/component computation completed | S70 three-arm 50-step real generation retained; original SD2.1 VAE identity is UNKNOWN, so this is not an exact external reproduction |
| S71–S81 | Generation matching, wrong camera labels, VAE round trip, sensor-depth/reprojection diagnosis | Completed and independently reviewed | Generated images still contain ghosting; matching and sensor scoring have coverage, synchronization, and approximate-K limitations |
| S82–S85 | Historical geometric prediction, fixed-camera optimization, fixed-geometry projection consumer | Completed local real/offline component experiments | Prediction fitting or projection consistency does not equal physically correct geometry or improved generation |
| S86 (single-scene four-target geometry-conditioned injection baseline) | G0/Gpaste/Gterminal/Gguide 50-step comparison | Completed | Gguide has lower RGB MSE, but targets 20–23 still show ghosting, smearing, and shape blur; no claim of improved 3D accuracy |
| S87 (terminal guidance-strength control and counterexample to multi-step necessity) | Strength .5/.75/1 and terminal control | Completed | The `.75` local counterexample rejects “this case requires multi-step guidance”; it does not establish GRC or generalization |
| S88 (RTMV camera JSON metadata and static-projection data qualification) | Official JSON/camera fields and static-projection entry audit | Completed, not a performance experiment | Only partial metadata obtained; no complete dynamic sequence obtained |
| S89 (RTMV paired-data TLS continuation failure audit) | Archive Range/TLS continuation and failure review | Completed, failure retained | No new RGB/EXR body; cannot be called a data experiment |
| S90 (RTMV archive paired-data recovery and indexing-protocol audit) | Archive indexing, license, and pairing protocol | Review completed | Still no independent RGB-D/pose test set |
| S91 (formal GRC-Memory evaluation) | Fixed-budget risk-calibrated memory selection | **Blocked** | Development-source identities are mixed; must wait for Gate0 |
| S92–S98 | Research handoff, data qualification, fixed future windows, camera/depth pairing audit | Preparation and review completed | TUM fr1/fr2 marked `DEVELOPMENT_SEEN`; window feasibility cannot become held-out evidence |
| S99 (fixed-rewrite-budget geometric-update comparison) | Same-block update of low-disagreement/random/confidence | Recomputed from seen cache | Low D advantage over confidence was not stable; claim stopped |
| S100 (fixed-context matched-amplitude pair-swap diagnosis) | Low-D versus confidence under the same background and candidate pool | Recomputed from seen cache | 144 consumer rerenders, mean benefit near zero with background sign reversals; mechanism clue only |
| S101 (school-GPU migration and run contract) | SSH, Slurm, resources, and experiment contract | **Preparation complete; GPU probe actually verified** | `slogin-02`, Slurm 23.02.6, account `mscitspod2026`, `normal`; job 584006 on `dgx-21` returned H800 81559 MiB, driver 580.159.03, Python 3.10.21, torch 2.5.1+cu121, CUDA available; VMem forward not started |
| S103-GeoDiag (historical predicted-geometry perturbation decomposition diagnosis) | Decomposition of support/identity/context changes | **Completed locally** | 72 sealed prediction records; H_support/H_depth did not pass, `MECHANISM_UNRESOLVED` |

### Supplementary H800 dependency audit

Dependency probe job `584098` completed on `dgx-09` in the `normal` partition with 1 GPU, 4 seconds, and exit code 0. The isolated environment can run `torch 2.5.1+cu121` and `numpy 2.2.6`; `diffusers`, `transformers`, `accelerate`, `opencv-python`, `imageio`, and `scipy` are not installed. The parenthesis error in the first probe `584095` is retained as a failure record. Evidence: `work/agents/gpu_dependency_probe_20260915.md`. The next step is therefore a reproducible dependency-installation/container plan and a new import receipt; data must still not be read and VMem must not be run.

A subsequent read-only check of existing server environments found that the Anaconda3 `base` environment (Python 3.11.5) can pass a CUDA/PyTorch smoke on an H800 compute node and import torch 2.7.0+cu126, transformers 4.48.3, accelerate 1.4.0, scipy 1.11.1, imageio 2.31.1, torchvision 0.22.0+cu126, Pillow 9.4.0, and cv2 4.11.0; the only clearly missing package is `diffusers`. The personal `torch` environment (Python 3.10.21) still lacks scipy, diffusers, transformers, accelerate, cv2, and imageio. A `geometry` environment appears in the conda listing, but its expected `bin/python` path does not exist and cannot be used directly. Because shared base and project-specific pins still differ for NumPy/SciPy/Pillow, the status can only be recorded as `PREPARATION_SMOKE_PASS`; isolation, version locking, and a project-level import smoke remain necessary.

## Formal experiments to run on H800

These are the missing GPU research experiments, submitted in order; if an earlier step fails, stop the method claim but retain the failure result.

| Experiment | What it does | Key outputs | Estimated H800 time |
|---|---|---|---:|
| S102 (unseen RGB-D/camera qualification gate) | Check one-to-one RGB/depth, time/frame identity, K, pose, depth units, SHA, license, and GT isolation | `GATE0_RESULT.json`, per-frame manifest | 0.5–1 day |
| S103-VMemBase (cross-scene long-horizon VMem baseline reproduction) | Actually run VMem on frozen scenes, recording neural forward and long-horizon output | Prediction seal, video, environment and cost receipts | 1–2 days |
| S104 (fixed-budget strong memory-baseline comparison) | Compare recent, random, pose, coverage, confidence, persistent, and utility-only at k=2/4/8 | Same-budget selection table, RGB-D/pose/reprojection metrics | 1 day |
| S105 (GRC-Memory risk-calibrated selection) | Let the selector read only historical geometric risk and predict future RGB-D/pose loss | Risk calibration, primary metrics, confidence intervals, failure examples | 1–2 days |
| S106 (occlusion-revisit stress test) | Measure legal prefixes, risk, and future recovery after people/objects are occluded and reappear | Revisit strata, occlusion-length curves, tail errors | 1 day |
| S107 (source-level counterfactual memory intervention) | Hold noise and other conditions fixed and replace/remove one memory | Signed future effect, replay-noise control | 1–2 days |
| S108 (tail risk and support localization) | Report worst-5%, CVaR95, reprojection, and coverage, locating where benefit comes from | Tail table, spatial heatmap, support denominator | 0.5–1 day |
| S109 (multiple seeds and resource audit) | Use at least 3 seeds and record GPU memory, I/O, forward, latency, and failures | Reproduction package, cost curves, final statistics | 1 day |

Estimated total duration: **about 7–10 working days when existing weights and dependencies are directly usable; about 10–14 working days if VMem weights or data must be downloaded/adapted again**. This is an engineering-duration estimate, not a paper-acceptance probability or proof of student hours. H800 does not shorten data qualification, near-duplicate exclusion, or review time.

## Current innovation judgment

Broad “geometry-aware memory,” “fixed-budget selection,” and “confidence calibration” have close precedents and cannot directly be contributions. Only two narrow candidates are retained:

1. **SOCF (Sparse Occlusion Competition Future-utility calibration):** Under sparse occlusion/revisit conditions, use historical visible geometric risk to predict future RGB-D/pose utility; it must beat same-budget strong baselines and remain stable across scenes and tail metrics.
2. **FGB-Future (Future Geometry Benefit evaluation):** Define whether historical memory helps an independent future geometric state as a new evaluation problem under a fixed real memory budget; the initial contribution is a reproducible evaluation protocol, and it can be upgraded to a method paper only if near-neighbor differences and real results hold.

The current review-style synthesis is approximately 6.8–7.1/10, with main deductions for near-neighbor risk, data independence, and the unverified complete forward. The scientific state must remain: `new_method_validated=false`, `novelty_authorization=NONE`. Evidence that could truly impress a teacher is not a name, but simultaneous success of the same candidate/same budget, future-answer isolation, cross-scene, tail-risk, and single-memory counterfactual requirements.

## Current next steps

1. Read the ICL-NUIM download receipt and perform the structural qualification audit; do not write `lr0` as a zero-exposure blind test.
2. Fix one CUDA/PyTorch smoke without quoting errors, then upload the minimum code and contract; do not upload private keys or OpenRouter credentials.
3. Run Gate0 first, then the cross-scene VMem baseline; if Gate0 fails, perform development/diagnostic work only and submit no GRC claim.
4. For every job save the command, commit, data SHA, seed, GPU, memory, wall time, prediction seal, post-GT scoring, and independent review.

Detailed primary evidence for all experiments remains in the project `RESEARCH_LOG.md`, `RESEARCH_MEMORY.md`, `docs/RESEARCH_HANDOFF_CURRENT.md`, and the individual S directories. This file is an overview for advisor briefing and GPU handoff and does not supersede old results.

SuperPod scheduling basis: HKUST ITSC’s official instructions require cluster jobs to use Slurm and manage jobs with `sinfo`, `sbatch`, `squeue`, and `scontrol`; this project submits short smoke and subsequent GPU jobs accordingly: <https://itso.hkust.edu.hk/services/academic-teaching-support/high-performance-computing/superpod/slurm>.
