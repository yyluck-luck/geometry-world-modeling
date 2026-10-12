#!/bin/bash
set -eu
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH='/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S17C_environment/site-packages'
bash /Users/rocket/Documents/Codex/2026-10-10/i-m-sharing-my-github-repo/work/week1-wt/work/W2_source_selection_20261010_codex/RUN_ACQUIRE.sh
bash /Users/rocket/Documents/Codex/2026-10-10/i-m-sharing-my-github-repo/work/week1-wt/work/W2_source_selection_20261010_codex/RUN_worker0.sh > /Users/rocket/Documents/Codex/2026-10-10/i-m-sharing-my-github-repo/work/week1-wt/work/W2_source_selection_20261010_codex/logs/worker0.log 2>&1 &
worker0_pid=$!
bash /Users/rocket/Documents/Codex/2026-10-10/i-m-sharing-my-github-repo/work/week1-wt/work/W2_source_selection_20261010_codex/RUN_worker1.sh > /Users/rocket/Documents/Codex/2026-10-10/i-m-sharing-my-github-repo/work/week1-wt/work/W2_source_selection_20261010_codex/logs/worker1.log 2>&1 &
worker1_pid=$!
wait "$worker0_pid"
wait "$worker1_pid"
bash /Users/rocket/Documents/Codex/2026-10-10/i-m-sharing-my-github-repo/work/week1-wt/work/W2_source_selection_20261010_codex/RUN_SCORE.sh
