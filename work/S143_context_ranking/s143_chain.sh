#!/bin/bash
# S143 on gpu13. usage: s143_chain.sh <gpu> <part 0|1> <wait_for_tmux_session>
# waits for the S141 eval session on this GPU to end -> (part 0) replay gate vs archived S139 bytes -> generate -> score.
set -euo pipefail
GPU=$1; PART=$2; WAITS=$3; R=/mnt/gluster_dcpu/yiyangliu/gwm_s134; G=/mnt/gluster_dcpu/yiyangliu/gwm_s143; S=$R/src/s143; PY=$R/env/bin/python
while tmux has-session -t $WAITS 2>/dev/null; do sleep 60; done
echo "[s143] gpu $GPU part $PART start $(date -u +%FT%TZ)"
export RUN_ROOT=$R/src WEIGHTS=$R/weights CUDA_VISIBLE_DEVICES=$GPU XDG_CACHE_HOME=$R/cache MPLCONFIGDIR=$R/cache/mpl HF_HOME=$R/cache/hf PYTHONNOUSERSITE=1
gen() { mkdir -p $2; sha256sum $S/*.py $1 > $2/CODE_SHA256_$(date -u +%H%M%S).txt
        VARIANT=A ADAPTER=NONE PLAN=$1 ARM_OUT=$2 SEEDS=$3 SHARD=0/1 DATA_ROOT=$R/data/s139_stage WARP_DIR=$G/warps $PY $S/gen_s141.py 2>&1 | grep --line-buffered -E '^\[|Traceback|Error'; }
if [ "$PART" = 0 ]; then
  [ -d $G/replay ] && ls $G/replay/*.npy >/dev/null 2>&1 && { echo "[s143] replay dir not fresh"; exit 4; }
  gen $S/plan_s143_replay.json $G/replay 3
  K=$(python3 -c "import json; print(json.load(open('$S/plan_s143_replay.json'))['contexts'][0]['ctx_key'])")
  sha256sum $R/out/s139_tacc/gen/${K}__s3.npy $G/replay/${K}__s3.npy | tee $G/REPLAY_SHA256.txt
  [ "$(awk '{print $1}' $G/REPLAY_SHA256.txt | sort -u | wc -l)" -eq 1 ] || { echo "[s143] REPLAY GATE FAILED"; exit 3; }
  echo "[s143] replay gate OK"
else
  until [ -s $G/REPLAY_SHA256.txt ]; do sleep 60; done
  [ "$(awk '{print $1}' $G/REPLAY_SHA256.txt | sort -u | wc -l)" -eq 1 ] || { echo "[s143] replay gate failed (part 0)"; exit 3; }
fi
OUT=$G/gen_part$PART
[ -d $OUT ] && ls $OUT/*.npy >/dev/null 2>&1 && { echo "[s143] $OUT not fresh"; exit 4; }
gen $S/plan_s143_part$PART.json $OUT 3,4,5,6
n=$(python3 -c "import json; print(4 * len(json.load(open('$S/plan_s143_part$PART.json'))['contexts']))")
[ "$(ls $OUT | grep -c '__s[3-6]\.npy$')" -eq "$n" ] || { echo "[s143] incomplete"; exit 5; }
OMP_NUM_THREADS=8 $PY $R/src/s140/score_s140.py $OUT $R/data/s139_datasets $S/plan_s143_part$PART.json $G/warps $G/SCORES_part$PART.json
python3 -c "import json,sys; sys.exit(0 if len(json.load(open('$G/SCORES_part$PART.json'))['runs'])==$n else 1)" || { echo "[s143] scores incomplete"; exit 6; }
echo "[s143] part $PART DONE $n $(date -u +%FT%TZ)"
