# GPU plan and S104 launch audit (2026-09-15)

## Verdict

**Do not submit S104 yet.** The runner is a useful RGB-only CUT3R component probe, but it is not the next formal VMem experiment and its Slurm template is not launch-ready. Gate0 is `PASS_CONDITIONAL_SYNTHETIC_CONTROLLED_DATA_ACCESS_HELDOUT`: the ICL sample decode, pairing, camera/depth contracts, split, and GT-isolation rules are recorded, but the dataset is single-scene and not zero-metadata blind. The remote VMem checkpoint remains partial (`2,666,233,856 / 5,056,346,672` bytes at the last receipt) and has no final remote hash.

## Required inputs before any GPU job

- **Frozen experiment identity:** exact experiment ID/name, purpose (component calibration, VMem baseline, or baseline comparison), source commit/tree SHA, command, working directory, seed, resolution, dtype, context/target IDs, inference steps, and resource request. Do not call an S104 component success a VMem baseline or GRC result.
- **Dataset contract:** archive SHA `4eca8c2e9f77c1bd7436c746d22ea6144b8c01fe9bc29a84e734186823f1f1ad`; explicit RGB↔depth↔association↔pose mapping (drop association ID 0, retain 1..1508); official camera/depth units and coordinate convention; frame-index time rule `(id-1)/30`; frozen split manifest SHA `5295e5ed115f6a6e0014e96a7b8615a418250c6a35b7816c7c736fabe7465b91`. Record the pre-freeze metadata exposure boundary.
- **Data-path qualification:** resolve and list every input path in the job manifest, with file existence, dimensions, mode/dtype, frame ID, and SHA. For S104, prove the four paths are RGB-only IDs `1,31,61,91`; the Python name-marker check is only a guard, not a complete provenance receipt.
- **Weights/config:** verify remote SHA-256 for every required file before VMem: `vmem_weights.pth`, CUT3R checkpoint, OpenCLIP weights, diffusion/VAE weights, and `config.json`; record byte sizes and model/config identity. A complete file size without a remote hash is insufficient.
- **Environment/source:** record the absolute Python executable, package freeze, CUDA/PyTorch versions, GPU identity, VMem tree SHA, CUT3R tree/commit SHA, and `PYTHONPATH`. The successful H800/import smoke proves environment readiness only; it did not construct/load VMem or read data.
- **S104-specific launch contract:** set `ICL_RGB_1`, `ICL_RGB_31`, `ICL_RGB_61`, and `ICL_RGB_91` explicitly (or pass explicit paths from a generated manifest); use an absolute runner path or `cd` to the project root; verify `CUT3R_SOURCE` and checkpoint existence before Python starts. Capture the exact resolved command in the receipt.

## Receipts required after a run

- Scheduler submission ID, node, exit code, `slurm.log`, wall time, CPU/GPU/memory utilization, and failure traceback if applicable.
- Immutable input manifest: resolved paths, IDs, RGB dimensions/modes, per-file SHA-256, archive/split/source/checkpoint/config SHAs, and a statement that depth/pose/GT bytes were not read for S104.
- Environment receipt: executable, package versions, CUDA/PyTorch, GPU name, source SHAs, command-line arguments, seed, resolution, and dtype.
- CUT3R receipt: model bytes/hash, synchronized load and inference timing, input tensor shapes, peak allocated memory, `forward_completed`, raw-output file SHA, and an independent readback of the receipt and raw output.
- For VMem baseline and later comparisons: prediction seal before any future GT is opened; calibration/development/test role for every frame; post-seal scoring receipt with RGB-D, pose/reprojection, coverage, tail-risk and cost metrics; same candidate pool, slot budget, and compute budget across recent/random/pose/coverage/confidence/persistent/utility baselines.

## Stop criteria

- **Before launch:** stop if any required remote hash is pending/mismatched, checkpoint/config identity is uncertain, input paths are unresolved, environment/source SHAs are missing, or the job can access future depth/pose/GT.
- **During S104:** stop and retain a failure receipt if CUDA is unavailable, model load fails, any input is non-RGB or wrong size/ID, forbidden paths are detected, source import resolves outside the pinned CUT3R tree, or outputs cannot be sealed and hashed. Do not retry by changing the contract silently.
- **After S104:** a successful RGB-only CUT3R forward is component evidence only. It does not support VMem reproduction, geometry accuracy, memory-selection benefit, GRC benefit, real-world generalization, or novelty.
- **Before formal VMem scoring:** stop at any split/GT-isolation violation, leakage or post-selection use of future answers, missing independent review, or failed baseline reproduction. If S103 VMem forward fails, retain the failure and stop method claims; proceed only with clearly labeled diagnostics.
- **For any innovation claim:** stop the claim unless the candidate beats strong same-budget baselines on the frozen future protocol, with cross-scene/independent evidence, confidence intervals, tail metrics, and (where claimed) a single-memory counterfactual. Current status remains `new_method_validated=false`, `novelty_authorization=NONE`.

## Sequencing decision

1. Finish and remotely hash-verify all VMem/config files; then run the no-data H800 model-load smoke.
2. Complete the implementation/pre-run audit and freeze the VMem baseline contract.
3. Run the declared VMem calibration/development baseline on the conditional synthetic ICL split, with prediction sealing and independent readback.
4. Use S104 only as a separately labeled CUT3R component calibration if its four RGB paths and source/data receipts are fixed; do not let it substitute for S103.
5. Run same-budget memory baselines before SOCF/FGB or any GRC claim; open held-out GT only after predictions and selector decisions are sealed.

## Evidence inspected

`work/S104_h800_cut3r_calibration/README.md`, `run_cut3r_rgb_only.py`, `run_s104.slurm`; `work/S103_H800_VMEM_BASELINE_PREFLIGHT_20260915.json`; `work/S102_gate0/ICL_NUIM_GATE0_DECISION.json`, `ICL_SPLIT_AND_GT_ISOLATION_MANIFEST_20260915.json`, and sample decode receipt; `work/S101_env_bootstrap/WEIGHT_TRANSFER_STATUS_20260915.json`; `docs/plans_en/GPU_EXPERIMENT_PLAN_AND_PROGRESS_20260915.md`; `docs/plans_en/RESEARCH_WORKFLOW_CHECKLIST.md`; latest `RESEARCH_LOG.md` entries.
