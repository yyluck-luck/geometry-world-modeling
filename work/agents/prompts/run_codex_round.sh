#!/bin/bash
# usage: run_codex_round.sh <RNNN> <expected output path>; retries on capacity errors (max 10), alternating service tier.
cd "/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling"
R=$1; OUTF=$2; P=work/agents/prompts
cat work/agents/PREAMBLE_CODEX_CURRENT.md $P/${R}_PROMPT.md > $P/${R}_FULL.md
for a in 1 2 3 4 5 6 7 8 9 10; do
  tier=priority; [ $((a % 2)) -eq 0 ] && tier=default
  echo "[run] $R attempt $a tier $tier $(date -u +%FT%TZ)" >> $P/${R}_codex.log
  codex exec -m gpt-6-astra -c model_reasoning_effort="ultra" -c service_tier="$tier" -s workspace-write \
    -c sandbox_workspace_write.network_access=true --skip-git-repo-check - < $P/${R}_FULL.md >> $P/${R}_codex.log 2>&1
  [ -s "$OUTF" ] && { echo "[run] $R DONE $(date -u +%FT%TZ)" >> $P/${R}_codex.log; exit 0; }
  grep -q "at capacity" $P/${R}_codex.log || { echo "[run] $R ended without output (not capacity)" >> $P/${R}_codex.log; exit 1; }
  sleep 90
done
echo "[run] $R gave up after 10 attempts" >> $P/${R}_codex.log; exit 2
