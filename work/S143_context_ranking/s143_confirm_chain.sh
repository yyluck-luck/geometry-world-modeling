#!/bin/bash
# S143 Amendment 1 (fresh-seed confirmation) on gpu13. usage: s143_confirm_chain.sh <gpu> <part 0|1>
# waits for the discovery part on this GPU to finish successfully -> generates seeds 42,7,1,2 -> scores.
set -euo pipefail
GPU=$1; PART=$2; R=/mnt/gluster_dcpu/yiyangliu/gwm_s134; G=/mnt/gluster_dcpu/yiyangliu/gwm_s143; S=$R/src/s143; PY=$R/env/bin/python
while tmux has-session -t s143p$PART 2>/dev/null; do sleep 60; done
grep -q "\[s143\] part $PART DONE" $G/logs/part$PART.log || { echo "[s143c] discovery part $PART did not finish cleanly"; exit 3; }
# Amendment 2 (R261): provenance must match the discovery run, else stop
REC=$(ls $G/gen_part$PART/CODE_SHA256_*.txt | head -1)
for f in gen_s141.py s141_common.py plan_s143_part$PART.json; do
  a=$(sha256sum $S/$f | cut -d' ' -f1); b=$(grep "/$f\$" $REC | cut -d' ' -f1)
  [ -n "$b" ] && [ "$a" = "$b" ] || { echo "[s143c] PROVENANCE DRIFT $f"; exit 7; }
done
[ "$(sha256sum $R/src/s140/score_s140.py | cut -d' ' -f1)" = "61f093cb2e40eeec2d862562dc6e28e98076447cde5819a2384536937cb00a79" ] || { echo "[s143c] PROVENANCE DRIFT score_s140.py"; exit 7; }
echo "[s143c] provenance OK (gen, common, plan match discovery; scorer 61f093cb2e40)"
export RUN_ROOT=$R/src WEIGHTS=$R/weights CUDA_VISIBLE_DEVICES=$GPU XDG_CACHE_HOME=$R/cache MPLCONFIGDIR=$R/cache/mpl HF_HOME=$R/cache/hf PYTHONNOUSERSITE=1
OUT=$G/gen_confirm_part$PART
[ -d $OUT ] && ls $OUT/*.npy >/dev/null 2>&1 && { echo "[s143c] $OUT not fresh"; exit 4; }
mkdir -p $OUT; sha256sum $S/*.py $S/plan_s143_part$PART.json > $OUT/CODE_SHA256.txt
echo "[s143c] gpu $GPU part $PART start $(date -u +%FT%TZ)"
VARIANT=A ADAPTER=NONE PLAN=$S/plan_s143_part$PART.json ARM_OUT=$OUT SEEDS=42,7,1,2 SHARD=0/1 DATA_ROOT=$R/data/s139_stage WARP_DIR=$G/warps \
  $PY $S/gen_s141.py 2>&1 | grep --line-buffered -E '^\[|Traceback|Error'
n=$(python3 -c "import json; print(4 * len(json.load(open('$S/plan_s143_part$PART.json'))['contexts']))")
[ "$(ls $OUT | grep -cE '__s(42|7|1|2)\.npy$')" -eq "$n" ] || { echo "[s143c] incomplete"; exit 5; }
OMP_NUM_THREADS=8 $PY $R/src/s140/score_s140.py $OUT $R/data/s139_datasets $S/plan_s143_part$PART.json $G/warps $G/SCORES_confirm_part$PART.json
python3 -c "import json,sys; sys.exit(0 if len(json.load(open('$G/SCORES_confirm_part$PART.json'))['runs'])==$n else 1)" || { echo "[s143c] scores incomplete"; exit 6; }
echo "[s143c] part $PART DONE $n $(date -u +%FT%TZ)"
