#!/bin/bash
# S134 step A on TACC gpu13 (cross-hardware reproduction check). usage: tacc_stepA.sh <gpu> <pnp_fix 0|1>
set -euo pipefail
R=/mnt/gluster_dcpu/yiyangliu/gwm_s134
export RUN_ROOT=$R/src WEIGHTS=$R/weights DATA_ROOT=$R/data/stage CUDA_VISIBLE_DEVICES=$1 PNP_FIX=$2
export XDG_CACHE_HOME=$R/cache MPLCONFIGDIR=$R/cache/mpl HF_HOME=$R/cache/hf PYTHONNOUSERSITE=1
mkdir -p $R/cache/mpl $R/cache/hf
sha256sum $R/src/s134/*.py > $R/logs/stepA_tacc_fix$2_CODE_SHA256.txt
for conv in native gl; do
  export POSE_CONVENTION=$conv ARM_OUT=$R/out/stepA_tacc/${conv}_fix$2
  echo "[stepA] $conv fix=$2 start $(date -u +%FT%TZ) gpu=$1"
  $R/env/bin/python $R/src/s134/run_retrieval_s134.py > $R/logs/stepA_tacc_${conv}_fix$2.log 2>&1
  echo "[stepA] $conv fix=$2 done $(date -u +%FT%TZ)"
done
