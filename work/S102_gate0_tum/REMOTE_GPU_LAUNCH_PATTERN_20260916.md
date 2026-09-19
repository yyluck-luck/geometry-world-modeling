# Persistent SuperPOD submission pattern (2026-09-16)

This is an operations pattern for preserving submission and monitoring across an SSH/VPN disconnect. It does **not** authorize or launch a formal experiment. The Slurm scheduler owns the actual GPU job after `sbatch` returns.

## Why this pattern

- `sbatch` is detached from the SSH process, so an accepted job continues after the local terminal closes.
- File transfer, manifest creation, and monitoring are client-side work and can be interrupted by VPN/SSH loss; run them inside `tmux` (or `screen`) and write every action to a dated log.
- Do not use a foreground `srun` for a long experiment when persistence is required.
- A submitted job is not a completed experiment. Reconnect and inspect `sacct`/the receipt before reporting a result.

## One persistent session

```bash
ssh -i /Users/rocket/.ssh/id_ed25519_superpod \
  -o ServerAliveInterval=60 -o ServerAliveCountMax=3 \
  yliutz@superpod.ust.hk

tmux new -As gwm-research
mkdir -p ~/gwm_ops/logs
cd ~/gwm_source_transport_20260915
```

If `tmux` is unavailable, use `screen -S gwm-research` and keep the same commands. Detach with `Ctrl-b d` (tmux) or `Ctrl-a d` (screen); reattach with `tmux attach -t gwm-research`.

## Submit only after the signed contract passes

```bash
# Precondition: validate_gate0_contract.py returned formal_status=PASS,
# and a new signed pre-run manifest binds all source/config/checkpoint hashes.
python3 work/S102_gate0_tum/validate_gate0_contract.py
sha256sum path/to/SIGNED_MANIFEST.json | tee ~/gwm_ops/logs/manifest.sha256
jid=$(sbatch --parsable path/to/run_formal.slurm)
printf '%s job=%s\n' "$(date -Is)" "$jid" | tee -a ~/gwm_ops/logs/submissions.log
squeue -j "$jid" -o '%.18i %.9P %.20j %.8T %.10M %.6D %R' | tee -a ~/gwm_ops/logs/submissions.log
```

The current v1 contract is intentionally blocked, so the commands above are a future pattern only. Do not replace `BLOCKED` with `PASS` merely to test submission.

## Reconnect and verify

```bash
tmux attach -t gwm-research
sacct -j JOB_ID --starttime "$(date -d '2 hours ago' '+%Y-%m-%dT%H:%M:%S')" \
  --format=JobIDRaw,State,ExitCode,Elapsed,MaxRSS,AllocTRES%30,End \
  | tee -a ~/gwm_ops/logs/accounting_JOB_ID.log
```

Then fetch the job receipt and verify its manifest/checkpoint hashes. `COMPLETED` only says the process exited successfully; scientific status requires the saved receipt, sealed predictions, independent readback, and scorer output under the contract.

## Safe monitoring loop

Use a bounded loop inside tmux, with no more than one status line per minute:

```bash
while sleep 60; do
  date -Is
  squeue -h -j JOB_ID -o '%i %T %M %R' || true
  sacct -n -X -j JOB_ID --format=State,ExitCode,Elapsed,MaxRSS || true
  if ! squeue -h -j JOB_ID | grep -q .; then break; fi
done | tee -a ~/gwm_ops/logs/monitor_JOB_ID.log
```

If the VPN drops, leave the Slurm job alone; reconnect later, reattach tmux, and inspect accounting plus the remote output directory. Do not resubmit automatically until the original state and receipt are known, otherwise duplicate runs can invalidate the fixed-budget comparison.

## Evidence rule

Record the exact SSH host, remote source directory, Slurm job ID, submission time, contract/manifest SHA, checkpoint SHA, final state, and receipt path. Preserve failed logs. This pattern prevents operational loss; it does not change Gate0, future-GT isolation, held-out identity, or novelty authorization.
