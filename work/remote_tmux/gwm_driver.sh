#!/usr/bin/env bash
# gwm_driver.sh - one supervision tick for the S103+ GPU queue.
#
# Called repeatedly by `gwm_persist.sh chain-start`, which runs it inside a
# cpu-partition Slurm job so it survives login-node reboots.  This script is
# deliberately CONSERVATIVE:
#
#   * It NEVER submits a formal scientific job by itself.  Formal dispatch must
#     go through the Gate0 launch guard, which requires a zero-error
#     PRE_RUN_READY validator result and writes a binding receipt.  Automating
#     that away would defeat the entire evidence chain.
#   * It only OBSERVES: it records queue state, harvests finished-job receipts
#     into the repository, and writes a machine-readable status file.
#   * It is idempotent.  Running it twice changes nothing beyond timestamps.
#
# Everything a human/agent needs to decide the next action is left in
# $STATE/NEXT_ACTION.json.  Deciding is a separate, explicit step.
set -uo pipefail

ROOT="${GWM_PROJECT_ROOT:-$HOME/geometry-world-modeling}"
STATE="${GWM_DRIVER_STATE:-$HOME/gwm_persist_state/driver}"
RUNS="${GWM_RUN_ROOT:-$HOME/gwm_prediction_runs}"
mkdir -p "$STATE"

# shellcheck disable=SC1091
[ -f /etc/profile.d/modules.sh ] && source /etc/profile.d/modules.sh
command -v sacct >/dev/null 2>&1 || module load slurm/slurm/23.02.6 2>/dev/null

utc() { date -u +%FT%TZ; }
log() { printf '%s %s\n' "$(utc)" "$*" >> "$STATE/driver.log"; }

log "tick start"

# 1. Snapshot the queue.  Losing this is harmless; it is rebuilt every tick.
squeue -u "$USER" -o '%i %j %T %M %R' > "$STATE/queue.txt" 2>/dev/null
ACTIVE=$(($(wc -l < "$STATE/queue.txt") - 1))
[ "$ACTIVE" -lt 0 ] && ACTIVE=0

# 2. Harvest receipts for any completed prediction run that is not yet archived.
#    Copying receipts out of the scratch run tree into the repo is safe and
#    idempotent; it never overwrites an existing archived receipt.
HARVESTED=0
if [ -d "$RUNS" ]; then
  for jobdir in "$RUNS"/*/job-*; do
    [ -d "$jobdir" ] || continue
    jid="$(basename "$jobdir" | sed 's/^job-//')"
    dest="$ROOT/work/S103_selector_free_baseline/run_receipts_${jid}"
    [ -d "$dest" ] && continue
    state="$(sacct -n -X -j "$jid" -o State 2>/dev/null | head -1 | tr -d ' ')"
    case "$state" in
      ""|PENDING|RUNNING|REQUEUED|SUSPENDED) continue ;;
    esac
    mkdir -p "$dest"
    cp -n "$jobdir"/predictions/*.json "$dest/" 2>/dev/null
    cp -n "$RUNS"/*/slurm-"$jid".out "$RUNS"/*/slurm-"$jid".err "$dest/" 2>/dev/null
    sacct -j "$jid" -o JobIDRaw,JobName%24,State,ExitCode,Elapsed,NodeList,MaxRSS \
      > "$dest/SACCT.txt" 2>/dev/null
    # Record the executing node explicitly: review limitation N-1 requires
    # cross-node variance to remain auditable.
    sacct -n -X -j "$jid" -o NodeList 2>/dev/null | tr -d ' ' > "$dest/NODE.txt"
    log "harvested job=$jid state=$state -> $dest"
    HARVESTED=$((HARVESTED + 1))
  done
fi

# 3. Decide nothing; describe everything.
LAST_JOB="$(ls -1dt "$ROOT"/work/S103_selector_free_baseline/run_receipts_* 2>/dev/null | head -1)"
python3 - "$STATE/NEXT_ACTION.json" "$ACTIVE" "$HARVESTED" "${LAST_JOB:-}" <<'PY'
import json, os, pathlib, subprocess, sys
out, active, harvested, last = pathlib.Path(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
receipt = {}
if last:
    seal = pathlib.Path(last) / "PREDICTION_SEAL.json"
    if seal.is_file():
        try: receipt = json.loads(seal.read_text())
        except Exception: receipt = {"unreadable": True}
state = {
    "schema": "gwm-driver-status-v1",
    "recorded_utc": subprocess.run(["date","-u","+%FT%TZ"],capture_output=True,text=True).stdout.strip(),
    "active_jobs": active,
    "harvested_this_tick": harvested,
    "latest_receipt_dir": last or None,
    "latest_seal_status": receipt.get("status"),
    "latest_seal_prediction_complete": receipt.get("prediction_complete"),
    "latest_seal_node": None,
    "automation_boundary": (
        "This driver observes and harvests only. It never submits a formal "
        "scientific job; formal dispatch requires the Gate0 launch guard with a "
        "zero-error PRE_RUN_READY validator result and a binding receipt."),
    "human_decisions_outstanding": [
        "Scoring requires a separate, explicit run of scorer_s103.py AFTER the "
        "prediction seal exists; the driver must never open future RGB.",
        "Per review limitation N-1, no cross-arm comparison until a same-node "
        "replay envelope (>=3 byte-identical repeats) exists and cross-node "
        "variance is separately measured and reported.",
    ],
    "new_method_validated": False,
    "novelty_authorization": "NONE",
}
node = pathlib.Path(last)/"NODE.txt" if last else None
if node and node.is_file(): state["latest_seal_node"] = node.read_text().strip()
tmp = out.with_suffix(".tmp")
tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
os.replace(tmp, out)
print(json.dumps({"active_jobs": active, "harvested": harvested}))
PY

log "tick end active=$ACTIVE harvested=$HARVESTED"
