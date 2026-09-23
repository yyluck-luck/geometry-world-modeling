#!/bin/bash
# 20-minute heartbeat. Always exits after the wait (so the agent is woken) whatever the codex quota.
LOG="${1:-$HOME/.gwm_heartbeat.log}"
sleep 1200
cd /tmp
out=$(echo 'Reply with exactly: HB_OK' | codex exec -m gpt-6-astra -c model_reasoning_effort=low \
      -c service_tier=fast -s read-only --skip-git-repo-check - 2>&1)
if echo "$out" | grep -qE '^HB_OK$'; then st="CODEX_OK"
elif echo "$out" | grep -qi 'usage limit'; then st="CODEX_USAGE_LIMIT $(echo "$out" | grep -oE 'try again at [^.]+' | head -1)"
elif echo "$out" | grep -qi 'at capacity'; then st="CODEX_CAPACITY"
else st="CODEX_OTHER"; fi
line="$(date '+%Y-%m-%d %H:%M') HEARTBEAT $st"; echo "$line" >> "$LOG"; echo "$line"
