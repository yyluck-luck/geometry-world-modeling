#!/bin/bash
# Pull S141 receipts (no images, no weights) from TACC into results/. usage: fetch_results_s141.sh
set -euo pipefail
cd "$(dirname "$0")"; G=/mnt/gluster_dcpu/yiyangliu/gwm_s141; H=yiyangliu@gpu13; O=results/tacc
mkdir -p $O/eval $O/runs/A $O/runs/B $O/fid $O/logs
rsync -a "$H:$G/eval/*.json" "$H:$G/eval/*.txt" $O/eval/ 2>/dev/null || true
for d in chess_A chess_B chess_Bstatic rgbd_A rgbd_B; do
  mkdir -p $O/eval/$d; rsync -a "$H:$G/eval/$d/RUNS_*.jsonl" "$H:$G/eval/$d/CODE_SHA256_*.txt" $O/eval/$d/ 2>/dev/null || true
done
for v in A B; do rsync -a "$H:$G/runs/$v/train_log.jsonl" "$H:$G/runs/$v/CODE_SHA256.txt" $O/runs/$v/; done
rsync -a "$H:$G/fid/FIDELITY_SHA256.txt" $O/fid/; rsync -a "$H:$G/fid/*/RUNS_*.jsonl" $O/fid/ 2>/dev/null || true
rsync -a "$H:$G/logs/chainB.log" "$H:$G/logs/evalA.log" "$H:$G/logs/evalB.log" "$H:$G/logs/zips.sha256" $O/logs/ 2>/dev/null || true
rsync -a "$H:$G/warps/WARP_LOG_*.jsonl" $O/logs/ 2>/dev/null || true
ls -R $O | head -50
