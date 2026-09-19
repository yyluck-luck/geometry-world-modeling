#!/bin/bash
source /etc/profile.d/modules.sh >/dev/null 2>&1
module load slurm/slurm/23.02.6 >/dev/null 2>&1
D="$HOME/geometry-world-modeling/work/S103_selector_free_baseline/gpu_image_isolation_20260916"
LOG="$HOME/gwm_image_probe_20260916/runner.log"
{
  echo "runner_start_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) host=$(hostname)"
  JOB=$(sbatch --parsable "$D/probe_isolation.slurm")
  echo "submitted_job=$JOB"
  for i in $(seq 1 60); do
    ST=$(sacct -j "$JOB" -X -n -o State 2>/dev/null | head -1 | tr -d ' ')
    if [ -n "$ST" ] && [ "$ST" != "PENDING" ] && [ "$ST" != "RUNNING" ] && [ "$ST" != "CONFIGURING" ] && [ "$ST" != "COMPLETING" ]; then break; fi
    sleep 15
  done
  sacct -j "$JOB" -o JobID,JobName%20,State,Elapsed,ExitCode,NodeList
  echo "runner_end_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "RUNNER_DONE"
} > "$LOG" 2>&1
