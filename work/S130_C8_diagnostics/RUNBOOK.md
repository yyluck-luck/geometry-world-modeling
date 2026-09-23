# C8 runbook

This runbook is for the owner-reviewed remote deployment. It does not authorize extra jobs. The exact working recipe is copied from `work/S103_selector_free_baseline/orderbalanced_s107.slurm` and `s113.slurm`: Apptainer image `/home/yliutz/gwm-images/nvidia-cuda-12.6.3-runtime-ubuntu22.04.sif`, environment `/home/yliutz/.conda/envs/gwm-cut3r-py311-20260915`, source `/home/yliutz/gwm_source_transport_20260915`, weights `/home/yliutz/gwm_weights_20260915`, account `mscitspod2026`, partition `normal`, one H800, eight CPUs, 64G.

Before dispatch, copy this directory to `/home/yliutz/geometry-world-modeling/work/S130_C8_diagnostics/`, verify its git SHA and hashes, and commit the preregistration. Start a tmux session on `superpod.ust.hk`; run `squeue -u $USER` and record an empty queue or existing jobs. Submit only the two reviewed sbatch files. Every stdout/stderr and receipt must be copied back.

Expected budget: Experiment 1 uses 2 multisets × 2 orders × 4 conventions × 1 seed = 16 diffusion forwards. The estimate is 0.5–2.0 H800-hours depending on observed runtime. Experiment 2 rebuilds the surfel memory for 14 windows × 4 arms without diffusion; estimate 0.5–2.0 H800-hours. Reserve 1.0 H800-hour for retries and remain below 5 H800-hours total, well below the 20-hour cap.

The CPU gate command is:

```text
C8_S107_POSES=/absolute/path/to/real/S107_pose_receipt.json \
C8_RUN_ROOT=/home/yliutz/gwm_source_transport_20260915 \
/home/yliutz/.conda/envs/gwm-cut3r-py311-20260915/bin/python3.11 \
  work/S130_C8_diagnostics/cpu_equivalence_test.py
```

The pose receipt must contain the real eight 4x4 poses, `order_a`, and `order_b` copied from the S107 run. If it is absent, stop. Do not build synthetic poses.

Receipt fields required for each job: schema, git SHA, source/weights/image/environment hashes, hostname, tmux session name, Slurm job ID, exact command, start/end UTC, window/seed/arm lists, output paths and SHA-256, dependency versions, errors, and the two flags. Retrieval outputs must include per-window/target `surfel_index_map`, `cos_value_map`, `depth`, `frame_count`, averaged target pose, scaled K, and context lists. No RGB/depth target files may be bound into the model process; evaluation geometry runs in a separate CPU process.

Stop conditions: missing real pose/context receipts; any target RGB read by the retrieval process; any pinned-source edit; any unregistered window/seed/arm; any failed null or hash gate; or any output that cannot be mapped to B/C/J under the preregistered tolerance. Mark the receipt `BLOCKED` or `UNTESTABLE` and do not reinterpret it as a result.
