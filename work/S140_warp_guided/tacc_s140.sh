#!/bin/bash
# S140 confirmation on TACC gpu13. usage: tacc_s140.sh <gpu> <seeds>
set -euo pipefail
R=/mnt/gluster_dcpu/yiyangliu/gwm_s134
export RUN_ROOT=$R/src WEIGHTS=$R/weights DATA_ROOT=$R/data/s139_stage CUDA_VISIBLE_DEVICES=$1 SEEDS=$2 SHARD=0/1
export PLAN=$R/src/s140/plan_confirm.json WARP_DIR=$R/data/S140_warps_chess ARM_OUT=$R/out/s140_confirm_tacc/gen
export XDG_CACHE_HOME=$R/cache MPLCONFIGDIR=$R/cache/mpl HF_HOME=$R/cache/hf PYTHONNOUSERSITE=1
mkdir -p $ARM_OUT; sha256sum $R/src/s140/*.py $PLAN > $R/logs/s140_seeds${2//,/_}_CODE_SHA256.txt
echo "[s140] seeds=$2 gpu=$1 start $(date -u +%FT%TZ)"
$R/env/bin/python $R/src/s140/gen_s140.py
echo "[s140] seeds=$2 done $(date -u +%FT%TZ)"
