#!/bin/bash
# S136 step A on TACC gpu13 (cross-check). usage: tacc_stepA.sh <gpu> <init kps|kpsK> [convention gl] [priming chunk4]
set -euo pipefail
R=/mnt/gluster_dcpu/yiyangliu/gwm_s134
export RUN_ROOT=$R/src WEIGHTS=$R/weights DATA_ROOT=$R/data/stage CUDA_VISIBLE_DEVICES=$1 INIT=$2
export POSE_CONVENTION=${3:-gl} PRIMING=${4:-chunk4}
export XDG_CACHE_HOME=$R/cache MPLCONFIGDIR=$R/cache/mpl HF_HOME=$R/cache/hf PYTHONNOUSERSITE=1
export ARM_OUT=$R/out/s136_stepA_tacc/${POSE_CONVENTION}_${INIT}_${PRIMING}
mkdir -p $ARM_OUT; sha256sum $R/src/s136/*.py > $ARM_OUT/CODE_SHA256.txt
echo "[s136A] $POSE_CONVENTION $INIT $PRIMING gpu=$1 start $(date -u +%FT%TZ)"
$R/env/bin/python $R/src/s136/run_retrieval_s136.py > $ARM_OUT/run.log 2>&1
echo "[s136A] done $(date -u +%FT%TZ)"
