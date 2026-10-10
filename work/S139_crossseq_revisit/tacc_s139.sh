#!/bin/bash
# S139 generation on TACC gpu13. usage: tacc_s139.sh <gpu> <seeds>
set -euo pipefail
R=/mnt/gluster_dcpu/yiyangliu/gwm_s134
export RUN_ROOT=$R/src WEIGHTS=$R/weights DATA_ROOT=$R/data/s139_stage CUDA_VISIBLE_DEVICES=$1 SEEDS=$2 SHARD=0/1
export PLAN=$R/src/s139/plan.json ARM_OUT=$R/out/s139_tacc/gen
export XDG_CACHE_HOME=$R/cache MPLCONFIGDIR=$R/cache/mpl HF_HOME=$R/cache/hf PYTHONNOUSERSITE=1
mkdir -p $ARM_OUT; sha256sum $R/src/s139/*.py $PLAN > $R/logs/s139_seeds${2//,/_}_CODE_SHA256.txt
echo "[s139] seeds=$2 gpu=$1 start $(date -u +%FT%TZ)"
$R/env/bin/python $R/src/s139/gen_s139.py
echo "[s139] seeds=$2 done $(date -u +%FT%TZ)"
