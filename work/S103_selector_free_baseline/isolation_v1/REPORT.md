# Actual predictor read-boundary probe (isolation v1)

Date: 2026-09-16 Asia/Shanghai. This is a login-node software/security probe, deliberately using only synthetic text and a synthetic archive. It did not allocate a GPU, load a checkpoint, open TUM/Chess data, or produce a model prediction. It is evidence that the namespace mechanism works on `slogin-02`; it is not a Gate0 PASS and not a scientific result.

## Implementation

`isolated_predictor.py` launches an exact command through:

```text
/usr/bin/unshare --user --map-root-user --mount --pid --net --fork --kill-child=SIGKILL python3 isolated_predictor.py --policy POLICY --inner-root ROOT
```

Inside the child it makes mounts private, creates a temporary filesystem, bind-mounts only policy-listed read-only/read-write paths, creates a private `/proc`, mounts minimal device files, closes file descriptors ≥3, changes root and working directory, drops the capability bounding/effective/permitted sets, and sets `NoNewPrivs=1` before `execve` of the predictor. The full host `/home`, `/tmp`, `/dev`, and `/proc` trees are never mounted. The policy rejects broad roots and requires explicit denied paths plus hashes binding the predictor input, scorer input, and runtime binding manifests. `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, and a private network namespace prevent fallback downloads during a production run.

The wrapper SHA on the remote host is `80522a400ad01f71f5745e31b4efce918ef3e273ec3d39679a7ad056828e6849`, and local compilation passed. This wrapper is intentionally separate from the Gate0 contract; the parent task must bind this SHA to a real predictor manifest before using it for S103.

## Actual remote test

The authorized SSH command copied the wrapper and `run_fixture_probe.py` to `/home/yliutz/gwm_isolation_v1_20260916/` and ran the following raw command on `slogin-02`:

```text
/usr/bin/python3 /home/yliutz/gwm_isolation_v1_20260916/run_fixture_probe.py
```

Remote exit code: **0**. Boundary id: `namespace-fixture-d8a2fc57df9941f283ce952872599ba6`. The child reported `pid=1`, private `/proc`, network namespace, `CapEff=0`, `CapPrm=0`, `CapBnd=0`, `NoNewPrivs=1`.

Five real `open()` attempts were made inside the namespace:

| Attempt | Expected | Observed |
|---|---:|---:|
| synthetic staged history text | open | open, content returned |
| synthetic scorer outcome text | deny | `FileNotFoundError` (`errno=2`) |
| synthetic whole archive ZIP | deny | `FileNotFoundError` (`errno=2`) |
| staged symlink to scorer outcome | deny | `FileNotFoundError` (`errno=2`) |
| `/proc/1/root/.../outcome` escape attempt | deny | `FileNotFoundError` (`errno=2`) |

All five expectations and capability checks passed. The remote receipts were copied back without modification:

- `FIXTURE_PROBE_RECEIPT.json` records the probe result, input/runtime/scorer binding hashes, and `production_acceptance=false`.
- `FIXTURE_LAUNCH_RECEIPT.json` records the namespace command, wrapper SHA, kernel and exit code.
- `REMOTE_FIXTURE_OUTPUT.json` preserves the raw remote driver output.

## Scope and integration obligations

This is stronger evidence than a string-based path lint, but it is still a synthetic login-node test. The `slogin-02` namespace capability was previously observed; this probe now exercises the actual mount/chroot/capability boundary. The H800 compute node may differ in `/usr/bin/python3`, CUDA device nodes, `/sys`, and Slurm environment. Before S103, run the same fixture through the real **compute-node** `tmux`/Slurm wrapper, bind the exact execution-boundary id and wrapper SHA, and preserve the compute receipt. For CUDA, set `allow_nvidia_devices=true` only after enumerating the required `/dev/nvidia*` nodes; never mount the full `/dev` tree.

The production predictor's history files must be staged under a dedicated directory and listed individually in `predictor_inputs_ref`; the complete TUM/Chess archive and all future RGB/depth/pose paths must remain outside the namespace. The scorer runs later as a separate process with outcome access. A successful namespace probe cannot establish camera calibration, chronological windows, VMem output quality, GRC/SOCF benefit, or held-out independence.
