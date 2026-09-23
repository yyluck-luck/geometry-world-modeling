#!/bin/bash
# Run a codex round; on capacity errors, resume the SAME session instead of restarting.
# usage: resume_loop.sh <worktree> <prompt_file> <output_rel_path> <logfile>
WT="$1"; PROMPT="$2"; OUT="$3"; LOG="$4"
cd "$WT" || exit 2
FLAGS=(-m gpt-6-astra -c model_reasoning_effort="ultra" -c service_tier="fast")
codex exec "${FLAGS[@]}" -s workspace-write -c sandbox_workspace_write.network_access=true \
  --skip-git-repo-check - < "$PROMPT" > "$LOG" 2>&1
[ -f "$OUT" ] && { echo "OUTPUT WRITTEN (first pass)"; exit 0; }
SID=$(grep -m1 -oE "session id: [0-9a-f-]+" "$LOG" | awk '{print $3}')
[ -z "$SID" ] && { echo "no session id; first pass failed"; tail -5 "$LOG"; exit 1; }
MSG="Your previous turn was interrupted before you wrote the output file. Continue from exactly where you stopped, reusing all work already done in this session. Do not start over. Complete every part of the original brief and write the required output. Write entirely in English."
for attempt in $(seq 1 40); do
  if tail -60 "$LOG" | grep -qE "at capacity|usage limit|Reconnecting"; then sleep 90; fi
  codex exec resume "$SID" "${FLAGS[@]}" -c sandbox_mode="workspace-write" \
    -c sandbox_workspace_write.network_access=true --skip-git-repo-check "$MSG" >> "$LOG" 2>&1
  [ -f "$OUT" ] && { echo "OUTPUT WRITTEN after resume $attempt"; exit 0; }
  if tail -60 "$LOG" | grep -q "usage limit"; then echo "resume $attempt: usage limit, waiting 20 min"; sleep 1200; fi
done
echo "gave up after 40 resumes"; exit 1
