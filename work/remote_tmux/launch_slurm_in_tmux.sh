#!/usr/bin/env bash
# Generic launcher for qualification/smoke jobs. Formal jobs use the formal guard.
set -euo pipefail
SESSION="${1:?session name required}"
SBATCH_SCRIPT="${2:?absolute remote sbatch script required}"
REMOTE_LOG="${3:-$HOME/gwm_tmux_${SESSION}.log}"
[[ "$SESSION" =~ ^[A-Za-z0-9_-]+$ ]] || { echo 'invalid session name' >&2; exit 2; }
[[ "$SBATCH_SCRIPT" == /* && -f "$SBATCH_SCRIPT" ]] || { echo 'absolute existing sbatch script required' >&2; exit 2; }
[[ "$REMOTE_LOG" == /* ]] || { echo 'absolute log path required' >&2; exit 2; }
command -v tmux >/dev/null || { echo 'tmux is required on the remote host' >&2; exit 2; }
WORKER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/monitor_slurm_job.sh"
[[ -f "$WORKER" ]] || { echo "missing worker: $WORKER" >&2; exit 2; }
tmux has-session -t "$SESSION" 2>/dev/null && { echo "session_exists:$SESSION"; exit 3; }
mkdir -p "$(dirname "$REMOTE_LOG")"
STATE_DIR="${REMOTE_LOG}.state"
# Existing receipt means a prior launch may have succeeded; never duplicate it.
mkdir "$STATE_DIR" || { echo "receipt_directory_exists:$STATE_DIR; inspect before retry" >&2; exit 3; }
printf -v COMMAND 'exec bash %q %q %q %q' "$WORKER" "$SBATCH_SCRIPT" "$REMOTE_LOG" "$STATE_DIR"
if ! tmux new-session -d -s "$SESSION" "$COMMAND"; then
  echo 'tmux_creation_failed; no successful submission receipt' >&2
  exit 4
fi
printf 'tmux_session:%s\nreceipt_directory:%s\n' "$SESSION" "$STATE_DIR"
