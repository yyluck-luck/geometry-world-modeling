# Persistent remote GPU launcher

All training and long GPU work starts inside a remote tmux session, which submits and monitors the Slurm job. VPN loss disconnects the viewer; the tmux server and Slurm allocation continue independently. A surviving session is operational protection, not evidence that an experiment succeeded.

The verified deployment directory is `/home/yliutz/gwm_remote_tmux_20260916`. The files there were syntax-checked and their hashes compared to the local copies on 2026-09-16. No formal experiment was submitted during this preflight.

- `launch_slurm_in_tmux.sh`: qualification and smoke jobs only.
- `launch_formal_slurm_in_tmux.sh`: formal experiments; first validates Gate0, then checks the frozen manifest's contract and Slurm-script hashes.
- `monitor_slurm_job.sh`: runs inside tmux, initializes the exact SuperPOD Slurm module, submits once, and records job/accounting state.

The formal manifest must contain `status: "FROZEN"`, `gate0_contract_sha256`, and `sbatch_script_sha256`. These hashes bind the exact bytes supplied at dispatch; they do not replace scientific review. The Gate0 validator must be deployed beside the launchers, or its absolute path supplied through `GWM_GATE0_VALIDATOR`.

A formal invocation takes: session name, absolute contract JSON path, absolute frozen manifest path, absolute Slurm script path, and absolute log path. Use a new session/log name for a new authorized run. Existing receipt directories refuse duplicate submission; inspect the receipt instead of deleting it and retrying blindly.

The monitor keeps `<log>.state/job_id`, `last_queue_state`, `final_accounting.txt`, `monitor_exit_code`, and timestamps. `monitor_exit_code=0` means a terminal Slurm state was retrieved; inspect `final_accounting.txt` for the actual experiment state and Slurm exit code. `FAILED` or `TIMEOUT` remain failed experiments.

Reconnect using the recorded SSH identity and inspect the saved session/job:

```bash
ssh -i ~/.ssh/id_ed25519_superpod yliutz@superpod.ust.hk
source /etc/profile.d/modules.sh
module load slurm/slurm/23.02.6
tmux list-sessions
squeue -u "$USER"
```

Initialize modules before enabling `set -u`: the current cluster initializer refers to an unset `ENABLE_LMOD` variable. Completed tmux sessions exit naturally; absence of a session alone says nothing about experiment success. Retained Slurm/accounting logs are the evidence.
