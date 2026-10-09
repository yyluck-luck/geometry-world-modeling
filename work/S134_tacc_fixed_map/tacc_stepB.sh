#!/bin/bash
# S134 step B on TACC gpu13 RTX 3090. usage: tacc_stepB.sh <gpu> <seeds e.g. 3,4>
set -euo pipefail
R=/mnt/gluster_dcpu/yiyangliu/gwm_s134
export RUN_ROOT=$R/src WEIGHTS=$R/weights DATA_ROOT=$R/data/stage CUDA_VISIBLE_DEVICES=$1 SEEDS=$2 SHARD=0/1
export PLAN=$R/src/s134/plan.json ARM_OUT=$R/out/stepB_tacc/gen
export XDG_CACHE_HOME=$R/cache MPLCONFIGDIR=$R/cache/mpl HF_HOME=$R/cache/hf PYTHONNOUSERSITE=1
mkdir -p $ARM_OUT
sha256sum $R/src/s134/*.py $PLAN > $R/logs/stepB_tacc_seeds${2//,/_}_CODE_SHA256.txt
echo "[stepB] seeds=$2 gpu=$1 start $(date -u +%FT%TZ)"
$R/env/bin/python $R/src/s134/gen_s134.py
echo "[stepB] seeds=$2 done $(date -u +%FT%TZ)"
