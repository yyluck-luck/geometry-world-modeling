#!/bin/bash
# S145 on gpu13: waits for S144 to end -> replay (BRANCH=orig == S141 B output) -> 4 arms on GPUs 3/4 -> probe -> score -> analyze.
set -euo pipefail
R=/mnt/gluster_dcpu/yiyangliu/gwm_s134; G=/mnt/gluster_dcpu/yiyangliu/gwm_s145; G1=/mnt/gluster_dcpu/yiyangliu/gwm_s141; S=$R/src/s145; S4=$R/src/s144; PY=$R/env/bin/python
ADB=$G1/runs/B/adapter_final.pt; ADB_SHA=0dd40c86ea928b74abfa992ba0738f61950bd97d5d26aaa3d0bc494487de1c56
while tmux has-session -t s144chain 2>/dev/null; do sleep 60; done
[ "$(sha256sum $ADB | cut -d' ' -f1)" = "$ADB_SHA" ] || { echo "[s145] adapter B hash mismatch"; exit 3; }
export RUN_ROOT=$R/src WEIGHTS=$R/weights XDG_CACHE_HOME=$R/cache MPLCONFIGDIR=$R/cache/mpl HF_HOME=$R/cache/hf PYTHONNOUSERSITE=1
gen() { # <gpu> <branch> <plan> <out> <seeds>
  if [ -d $4 ] && ls $4/*.npy >/dev/null 2>&1; then echo "[s145] $4 not fresh"; exit 4; fi
  mkdir -p $4; sha256sum $S4/gen_s144.py $S4/s141_common.py $3 > $4/CODE_SHA256.txt
  CUDA_VISIBLE_DEVICES=$1 VARIANT=B BRANCH=$2 ADAPTER=$ADB PLAN=$3 ARM_OUT=$4 SEEDS=$5 SHARD=0/1 DATA_ROOT=$R/data/s139_stage WARP_DIR=$R/data/S140_warps_chess \
    $PY $S4/gen_s144.py 2>&1 | grep --line-buffered -E '^\[|Traceback|Error|bad output|Assertion'; }
echo "[s145] start $(date -u +%FT%TZ)"
gen 3 orig $S/plan_replay.json $G/replay 3
K=$(python3 -c "import json; print(json.load(open('$S/plan_replay.json'))['contexts'][0]['ctx_key'])")
A_SHA=$(sha256sum $G1/eval/chess_B/${K}__s3.npy | cut -d' ' -f1); N_SHA=$(sha256sum $G/replay/${K}__s3.npy | cut -d' ' -f1)
echo "$A_SHA S141_B  $N_SHA s145_orig" | tee $G/REPLAY_SHA256.txt
[ "$A_SHA" = "$N_SHA" ] || { echo "[s145] REPLAY FAILED (blocked assay)"; exit 3; }
( gen 3 off $S/plan_s145.json $G/off 3,4,5,6; gen 3 target_only $S/plan_s145.json $G/target_only 3,4,5,6 ) & P1=$!
( gen 4 bias_only $S/plan_s145.json $G/bias_only 3,4,5,6; gen 4 permuted $S/plan_s145.json $G/permuted 3,4,5,6;
  CUDA_VISIBLE_DEVICES=4 $PY $S/probe_s145.py $G1/clips_s141.json $G1/lat $G1/warps $ADB $G/PROBE.json | tail -n 3 || echo "[s145] probe failed (diagnostic only; arms unaffected)" ) & P2=$!
wait $P1; wait $P2
for a in off target_only bias_only permuted; do
  [ "$(ls $G/$a | grep -c '__s[3-6]\.npy$')" -eq 96 ] || { echo "[s145] $a incomplete"; exit 5; }
  OMP_NUM_THREADS=8 $PY $R/src/s140/score_s140.py $G/$a $R/data/s139_datasets $S/plan_score_B.json $R/data/S140_warps_chess $G/SCORES_$a.json
done
$PY $S/analyze_s145.py $G1/eval/SCORES_chess_B.json $G1/eval/SCORES_chess_A.json $G/SCORES_off.json $G/SCORES_target_only.json \
  $G/SCORES_bias_only.json $G/SCORES_permuted.json $S/POSE_ARMS.json $G/S145_ANALYSIS.json
echo "[s145] DONE $(date -u +%FT%TZ)"
