#!/usr/bin/env bash
#SBATCH --job-name=xover-null-ctrl
#SBATCH --partition=normal
#SBATCH --account=mscitspod2026
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --output=/home/yliutz/gwm_probe_receipts/XOVER/slurm-%j.out
#SBATCH --error=/home/yliutz/gwm_probe_receipts/XOVER/slurm-%j.err
set -eo pipefail
source /etc/profile.d/modules.sh
module load slurm/slurm/23.02.6
module load apptainer
set -u

IMAGE=/home/yliutz/gwm-images/nvidia-cuda-12.6.3-runtime-ubuntu22.04.sif
ENVROOT=/home/yliutz/.conda/envs/gwm-cut3r-py311-20260915
SOURCE=/home/yliutz/gwm_source_transport_20260915
WEIGHTS=/home/yliutz/gwm_weights_20260915
STAGE=/home/yliutz/gwm_stages/S105_SCENE13_BANK12_20260917
CODE=/home/yliutz/geometry-world-modeling/work/S103_selector_free_baseline
OUTDIR=/home/yliutz/gwm_probe_receipts/XOVER/job-${SLURM_JOB_ID}
mkdir -p "$OUTDIR"

apptainer exec --nv --containall --no-home --cleanenv \
  --env "RUN_ROOT=$SOURCE" \
  --env "DATA_ROOT=/home/yliutz/datasets" \
  --env "SEEDS=42" \
  --env "NULL_CONTROL_ONLY=1" \
  --env "ARM_OUT=/mnt/out" \
  --env "SLURM_JOB_ID=$SLURM_JOB_ID" \
  --bind "$ENVROOT:$ENVROOT:ro" \
  --bind "$SOURCE:$SOURCE:ro" \
  --bind "$WEIGHTS:$WEIGHTS:ro" \
  --bind "/home/yliutz/datasets:/home/yliutz/datasets:ro" \
  --bind "$CODE/crossover_context_reference.py:/opt/arms.py:ro" \
  --bind "$OUTDIR:/mnt/out:rw" \
  --pwd /mnt/out \
  "$IMAGE" "$ENVROOT/bin/python3.11" /opt/arms.py
