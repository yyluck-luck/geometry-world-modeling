#!/bin/bash
# S137c warp4 on TACC gpu13. usage: tacc_s137c.sh <gpu> <seeds>
set -euo pipefail
R=/mnt/gluster_dcpu/yiyangliu/gwm_s134
export RUN_ROOT=$R/src WEIGHTS=$R/weights DATA_ROOT=$R/data/stage CUDA_VISIBLE_DEVICES=$1 SEEDS=$2 SHARD=0/1
export PLAN=$R/src/s137/plan_s137c.json WARP_DIR=$R/data/S137_warps ARM_OUT=$R/out/s137c_tacc/gen
export XDG_CACHE_HOME=$R/cache MPLCONFIGDIR=$R/cache/mpl HF_HOME=$R/cache/hf PYTHONNOUSERSITE=1
mkdir -p $ARM_OUT; sha256sum $R/src/s137/*.py $PLAN > $R/logs/s137c_seeds${2//,/_}_CODE_SHA256.txt
echo "[s137c] seeds=$2 gpu=$1 start $(date -u +%FT%TZ)"
$R/env/bin/python $R/src/s137/gen_s137.py
echo "[s137c] seeds=$2 done $(date -u +%FT%TZ)"
