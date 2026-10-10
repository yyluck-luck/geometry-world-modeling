#!/bin/bash
# S141 on TACC gpu13. usage: tacc_s141.sh <gpu> <cmd> ...
#   train <A|B> <run_dir>            (env STEPS etc. pass through)
#   warps <shard i/N>
#   gen <A|B> <plan> <adapter|NONE> <out_dir> <seeds>
set -euo pipefail
R=/mnt/gluster_dcpu/yiyangliu/gwm_s134; G=/mnt/gluster_dcpu/yiyangliu/gwm_s141; S=$R/src/s141
export RUN_ROOT=$R/src WEIGHTS=$R/weights CUDA_VISIBLE_DEVICES=$1
export XDG_CACHE_HOME=$R/cache MPLCONFIGDIR=$R/cache/mpl HF_HOME=$R/cache/hf PYTHONNOUSERSITE=1
cmd=$2; shift 2
echo "[s141] $cmd $* gpu=$CUDA_VISIBLE_DEVICES start $(date -u +%FT%TZ)"
case $cmd in
  train) mkdir -p $2; sha256sum $S/*.py $G/clips_s141.json > $2/CODE_SHA256.txt
         W=NONE; [ "$1" = B ] && W=$G/warps
         $R/env/bin/python $S/train_s141.py $1 $G/clips_s141.json $G/lat $W $2 ;;
  warps) SHARD=$1 $R/env/bin/python $S/warps_s141.py /home/yiyangliu/s141_data/7scenes $G/clips_s141.json $G/warps 2>&1 | grep -E '^\[warp\]|Error|Traceback|error' ;;
  gen)   mkdir -p $4; sha256sum $S/*.py $2 > $4/CODE_SHA256_$(date -u +%H%M%S).txt
         VARIANT=$1 PLAN=$2 ADAPTER=$3 ARM_OUT=$4 SEEDS=$5 SHARD=0/1 DATA_ROOT=$R/data/s139_stage WARP_DIR=$R/data/S140_warps_chess \
           $R/env/bin/python $S/gen_s141.py ;;
esac
echo "[s141] $cmd done $(date -u +%FT%TZ)"
