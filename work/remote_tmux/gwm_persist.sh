#!/usr/bin/env bash
# gwm_persist.sh - reboot-resilient job control for HKUST SuperPOD.
#
# WHY THIS EXISTS
#   The login nodes reboot every Wednesday 10:00-12:00 and may reboot without
#   notice.  The official MOTD states: "Login nodes may reboot, tasks run on
#   login nodes and srun jobs can be killed without notice. sbatch jobs stay
#   unaffected."  Verified 2026-09-17 on this account:
#     - crontab            : DENIED ("You (yliutz) are not allowed to use this program")
#     - loginctl Linger    : no  (systemd --user dies with the last session)
#     - normal partition   : TimeLimit=infinite, DefaultTime=8:00:00
#     - cpu partition      : TimeLimit=12:00:00
#   Therefore neither cron nor a user systemd unit can restart anything after a
#   reboot.  The ONLY durable execution substrate available is Slurm itself.
#
# DESIGN RULES
#   1. Real work is always an sbatch job.  Never srun, never a bare login-node
#      process, never a process that only lives inside tmux.
#   2. Supervision that must outlive a reboot is itself an sbatch job on the cpu
#      partition that re-submits its successor before its walltime expires
#      ("driver chain").  A chain link that dies is replaced by the next link;
#      a chain that is cancelled stops cleanly because the stop-file is checked.
#   3. tmux is a viewer only.  Losing it must never lose work.  Every command
#      here reconstructs its view from `squeue`/`sacct` and on-disk state, so it
#      is safe to run repeatedly.
#   4. Every action is idempotent and refuses to double-submit: submission is
#      guarded by a job-name singleton check plus a state file.
#
# USAGE
#   gwm_persist.sh submit   <name> <script.slurm>   # sbatch once, guarded
#   gwm_persist.sh status   [name]                  # queue + last accounting
#   gwm_persist.sh watch    <name>                  # attach a tmux viewer
#   gwm_persist.sh chain-start <name> <driver.sh> [hours]
#   gwm_persist.sh chain-stop  <name>
#   gwm_persist.sh doctor                           # environment facts
set -uo pipefail

STATE_ROOT="${GWM_STATE_ROOT:-$HOME/gwm_persist_state}"
mkdir -p "$STATE_ROOT"

load_slurm() {
  # shellcheck disable=SC1091
  [ -f /etc/profile.d/modules.sh ] && source /etc/profile.d/modules.sh
  command -v sbatch >/dev/null 2>&1 || module load slurm/slurm/23.02.6 2>/dev/null
  command -v sbatch >/dev/null 2>&1 || { echo "FATAL: sbatch unavailable" >&2; exit 3; }
}

utc() { date -u +%FT%TZ; }

# Refuse to submit if a job with this name is already pending or running.
# This is what makes re-running the script after a reboot safe.
already_active() {
  local name="$1"
  [ -n "$(squeue -h -u "$USER" -n "$name" -o '%i' 2>/dev/null)" ]
}

cmd_submit() {
  local name="$1" script="$2"
  [ -f "$script" ] || { echo "FATAL: no such script: $script" >&2; exit 2; }
  load_slurm
  local dir="$STATE_ROOT/$name"; mkdir -p "$dir"
  if already_active "$name"; then
    echo "SKIP: '$name' already pending/running: $(squeue -h -u "$USER" -n "$name" -o '%i %T')"
    return 0
  fi
  local job
  job="$(sbatch --parsable --job-name="$name" "$script")" || exit $?
  printf '%s\n' "$job" > "$dir/JOB_ID"
  printf '%s submitted job=%s script=%s\n' "$(utc)" "$job" "$script" >> "$dir/HISTORY.log"
  echo "SUBMITTED name=$name job=$job at=$(utc)"
}

cmd_status() {
  load_slurm
  local name="${1:-}"
  echo "=== queue ($(utc)) ==="
  if [ -n "$name" ]; then squeue -u "$USER" -n "$name"; else squeue -u "$USER"; fi
  echo "=== last accounting ==="
  local dirs
  if [ -n "$name" ]; then dirs="$STATE_ROOT/$name"; else dirs="$STATE_ROOT"/*; fi
  for d in $dirs; do
    [ -f "$d/JOB_ID" ] || continue
    printf -- '--- %s ---\n' "$(basename "$d")"
    sacct -n -X -j "$(cat "$d/JOB_ID")" -o JobIDRaw,JobName%24,State,ExitCode,Elapsed,NodeList 2>/dev/null
  done
}

# tmux viewer. Safe to kill; safe to recreate; holds no authoritative state.
cmd_watch() {
  local name="$1" session="gwm-view-$1"
  command -v tmux >/dev/null || { echo "FATAL: tmux unavailable" >&2; exit 3; }
  if ! tmux has-session -t "$session" 2>/dev/null; then
    tmux new-session -d -s "$session" \
      "while :; do clear; '$0' status '$name'; echo; echo 'refresh 20s  (Ctrl-b d to detach)'; sleep 20; done"
  fi
  echo "viewer session: $session   attach with:  tmux attach -t $session"
}

# --- Self-chaining driver -------------------------------------------------
# Creates a cpu-partition job that runs <driver.sh> and, shortly before its
# walltime ends, submits its own successor.  Survives login node reboots because
# it never executes on a login node.
cmd_chain_start() {
  local name="$1" driver="$2" hours="${3:-11}"
  [ -f "$driver" ] || { echo "FATAL: no such driver: $driver" >&2; exit 2; }
  load_slurm
  local dir="$STATE_ROOT/$name"; mkdir -p "$dir"
  rm -f "$dir/STOP"
  local wrapper="$dir/chain.slurm"
  cat > "$wrapper" <<EOF
#!/usr/bin/env bash
#SBATCH --job-name=$name
#SBATCH --partition=cpu
#SBATCH --account=mscitspod2026
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=${hours}:30:00
#SBATCH --output=$dir/chain-%j.out
#SBATCH --error=$dir/chain-%j.err
set -uo pipefail
source /etc/profile.d/modules.sh 2>/dev/null || true
command -v sbatch >/dev/null || module load slurm/slurm/23.02.6 2>/dev/null
STOP="$dir/STOP"
DEADLINE=\$(( \$(date +%s) + $hours*3600 ))
echo "chain link start job=\$SLURM_JOB_ID utc=\$(date -u +%FT%TZ)"
while [ ! -f "\$STOP" ] && [ "\$(date +%s)" -lt "\$DEADLINE" ]; do
  bash "$driver" >> "$dir/driver.log" 2>&1
  sleep 300
done
if [ ! -f "\$STOP" ]; then
  # Hand over before this link's walltime expires.
  next=\$(sbatch --parsable "$wrapper") && echo "chain handover -> \$next utc=\$(date -u +%FT%TZ)"
  printf '%s handover %s -> %s\n' "\$(date -u +%FT%TZ)" "\$SLURM_JOB_ID" "\$next" >> "$dir/HISTORY.log"
else
  echo "chain stopped by STOP file utc=\$(date -u +%FT%TZ)"
fi
EOF
  chmod +x "$wrapper"
  if already_active "$name"; then
    echo "SKIP: chain '$name' already active: $(squeue -h -u "$USER" -n "$name" -o '%i %T')"
    return 0
  fi
  local job; job="$(sbatch --parsable "$wrapper")" || exit $?
  printf '%s\n' "$job" > "$dir/JOB_ID"
  printf '%s chain-start job=%s driver=%s hours=%s\n' "$(utc)" "$job" "$driver" "$hours" >> "$dir/HISTORY.log"
  echo "CHAIN STARTED name=$name job=$job link_hours=$hours"
  echo "stop with: $0 chain-stop $name"
}

cmd_chain_stop() {
  local name="$1" dir="$STATE_ROOT/$1"
  load_slurm
  touch "$dir/STOP"
  # The STOP file prevents handover; cancel the current link so it ends now.
  local ids; ids="$(squeue -h -u "$USER" -n "$name" -o '%i')"
  [ -n "$ids" ] && scancel $ids
  printf '%s chain-stop ids=%s\n' "$(utc)" "${ids:-none}" >> "$dir/HISTORY.log"
  echo "CHAIN STOPPED name=$name cancelled='${ids:-none}'"
}

cmd_doctor() {
  load_slurm
  echo "host          : $(hostname)"
  echo "utc           : $(utc)"
  echo "state root    : $STATE_ROOT"
  printf 'crontab       : '; crontab -l >/dev/null 2>&1 && echo "available" || echo "DENIED (expected on this cluster)"
  printf 'linger        : '; loginctl show-user "$USER" 2>/dev/null | grep -i '^Linger=' || echo "unknown"
  echo "--- partitions ---"; sinfo -o '%20P %12l %12L %8D %10T' | sort -u
  echo "--- my queue ---"; squeue -u "$USER"
  echo "--- tmux ---"; tmux ls 2>&1 | head
  echo
  echo "RULE: anything that must survive a login-node reboot MUST be an sbatch job."
}

case "${1:-}" in
  submit)      shift; cmd_submit "$@" ;;
  status)      shift; cmd_status "$@" ;;
  watch)       shift; cmd_watch "$@" ;;
  chain-start) shift; cmd_chain_start "$@" ;;
  chain-stop)  shift; cmd_chain_stop "$@" ;;
  doctor)      shift; cmd_doctor "$@" ;;
  *) sed -n '1,40p' "$0"; exit 1 ;;
esac
