# GPU image isolation probe (2026-09-16) — protocol

**Purpose.** Clear the recorded blocker `BLOCKED_GPU_ISOLATION_IMAGE` by (a) obtaining a
digest-pinned executable GPU image and (b) running a synthetic allow/deny/escape plus CUDA
probe on a compute node. This is infrastructure evidence only.

**Status.** `probe_protocol=FROZEN_BEFORE_PULL`; no model, checkpoint, dataset, future outcome
or ground truth is touched. `new_method_validated=false`; `novelty_authorization=NONE`.

## Image identity (pinned by registry digest, resolved 2026-09-16 12:43 HKT)

| field | value |
|---|---|
| registry | `registry-1.docker.io` |
| repository | `nvidia/cuda` |
| tag (human label only) | `12.6.3-runtime-ubuntu22.04` |
| pinned index digest | `sha256:63a18dd805367dacfb077aeced8384ab2fb569598ec5f5f5220c3f90a5c23650` |
| amd64 manifest digest | `sha256:4cf7f8137bdeeb099b1f2de126e505aa1f01b6e4471d13faf93727a9bf83d539` |
| compressed layer total | 1529.9 MB (9 layers) |
| auth | anonymous pull token (no ITSC or NGC credential required) |
| local artifact | `$HOME/gwm-images/nvidia-cuda-12.6.3-runtime-ubuntu22.04.sif` (outside the project tree; not synced back) |

The tag is recorded only as a label; the pinned digest is the identity. A future pull by tag
would not be the same artifact and must not be substituted silently.

## Why this image

The earlier probes (588659, 588660, 588661, 588662, 588664) bound the conda environment into a
bare apptainer *sandbox* directory. That sandbox had no base OS, so the bound interpreter could
not execute. A real CUDA runtime rootfs supplies the loader/libc/CUDA userspace while the
existing conda env (bound read-only) supplies the Python packages. No custom build is required.

## Probe arms (all inside one GPU Slurm job)

1. **ALLOW** — read `/mnt/stage/stage_history_marker.txt` from a read-only bind of a staged
   input directory. Expected: readable.
2. **DENY** — the absolute path of an unbound sentinel directory
   (`$HOME/gwm_isolation_deny_20260916/DO_NOT_READ.txt`) must not exist inside the container.
   `--containall --no-home` is expected to hide it. Expected: absent.
3. **ESCAPE** — no bound path may be writable; `/home`, the project tree and the deny directory
   must be absent; record `/proc/self/mountinfo` lines for every bind.
4. **CUDA** — `torch.cuda.is_available()`, device name and a real 1024x1024 matmul through the
   bound conda interpreter.
5. **EGRESS (informational)** — whether the containerised process can reach a container
   registry. Recorded, not a pass/fail gate for this probe.

## Receipt and acceptance

A JSON receipt is written under `$HOME/gwm_image_probe_20260916/` and copied back to this
directory. Required fields: `slurm_job_id`, `host`, `sif_sha256`, `sif_bytes`, `apptainer_version`,
`python`, `torch`, `cuda_available`, `device_name`, `allow_read`, `deny_visible`, `write_allowed`,
`mountinfo_gwm_lines`, `egress`, `model_access=false`, `dataset_access=false`,
`ground_truth_access=false`, `forward_completed=false`.

Pass requires: ALLOW readable, DENY absent, no bind writable, CUDA device visible and matmul
executed. A CUDA pass alone is not an isolation pass, and neither is an isolation pass a
scientific result.

## Kill / stop rules

- If the container cannot execute the bound interpreter, record the exact error and stop; do not
  substitute a different image without a new pinned digest and a new protocol revision.
- If DENY is visible, the isolation boundary fails; keep `BLOCKED` and do not dispatch S103.
- No formal S103-VMemBase, Gate0, SOCF, FGB-SI or scoring is authorized by this probe.
