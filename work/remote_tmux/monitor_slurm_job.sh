#!/usr/bin/env bash
# Invoked inside tmux. Only owns submission and monitoring, never dataset access.
set -eo pipefail
SBATCH_SCRIPT="${1:?absolute sbatch script required}"
REMOTE_LOG="${2:?absolute log path required}"
STATE_DIR="${3:?state directory required}"
# SuperPOD's module initializer references unset variables; enable nounset later.
source /etc/profile.d/modules.sh
module load slurm/slurm/23.02.6
set -u
exec > >(tee -a "$REMOTE_LOG") 2>&1
trap 'code=$?; printf "%s\n" "$code" > "$STATE_DIR/monitor_exit_code"; date -Is > "$STATE_DIR/monitor_finished_at"' EXIT
printf 'started_at:'; date -Is
if ! RAW_JOB=$(sbatch --parsable "$SBATCH_SCRIPT"); then
  echo 'submission_failed'
  exit 4
fi
JOB_ID="${RAW_JOB%%;*}"
[[ "$JOB_ID" =~ ^[0-9]+$ ]] || { echo "invalid_sbatch_receipt:$RAW_JOB"; exit 5; }
printf '%s\n' "$JOB_ID" > "$STATE_DIR/job_id"
printf 'job_id:%s\n' "$JOB_ID"
# Failed status queries must not be interpreted as a completed job.
while true; do
  if QUEUE=$(squeue -h -j "$JOB_ID" -o '%i|%T' 2>"$STATE_DIR/squeue_error"); then
    [[ -n "$QUEUE" ]] || break
    printf '%s\n' "$QUEUE" > "$STATE_DIR/last_queue_state"
  else
    printf 'queue_query_failed_at:'; date -Is
  fi
  sleep 30
done
# Accounting may appear a few seconds after the job leaves squeue.
for TRY in 1 2 3 4 5 6; do
  if sacct -j "$JOB_ID" -X --noheader --format=JobIDRaw,State,Elapsed,ExitCode -P > "$STATE_DIR/accounting.tmp" && [[ -s "$STATE_DIR/accounting.tmp" ]]; then
    STATE=$(awk -F '|' 'NR==1 {print $2}' "$STATE_DIR/accounting.tmp")
    case "$STATE" in
      COMPLETED|FAILED|TIMEOUT|OUT_OF_MEMORY|NODE_FAIL|PREEMPTED|BOOT_FAIL|DEADLINE|REVOKED|CANCELLED*)
        mv "$STATE_DIR/accounting.tmp" "$STATE_DIR/final_accounting.txt"
        cat "$STATE_DIR/final_accounting.txt"
        printf 'finished_at:'; date -Is
        exit 0
        ;;
    esac
  fi
  sleep 10
done
echo 'accounting_unavailable; job completion not certified'
exit 6
