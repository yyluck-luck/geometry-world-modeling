#!/usr/bin/env bash
#SBATCH --job-name=c8-slot-factor
#SBATCH --partition=normal
#SBATCH --account=mscitspod2026
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=/home/yliutz/gwm_probe_receipts/S130_slot/slurm-%j.out
#SBATCH --error=/home/yliutz/gwm_probe_receipts/S130_slot/slurm-%j.err
set -euo pipefail
source /etc/profile.d/modules.sh
module load slurm/slurm/23.02.6
module load apptainer
# Owner must set OUTDIR and bind a real S107 pose receipt after review.
: "${OUTDIR:?set OUTDIR before submission}"
IMAGE=/home/yliutz/gwm-images/nvidia-cuda-12.6.3-runtime-ubuntu22.04.sif
ENVROOT=/home/yliutz/.conda/envs/gwm-cut3r-py311-20260915
SOURCE=/home/yliutz/gwm_source_transport_20260915
WEIGHTS=/home/yliutz/gwm_weights_20260915
CODE=/home/yliutz/geometry-world-modeling/work/S130_C8_diagnostics
mkdir -p "$OUTDIR"
apptainer exec --nv --containall --no-home --cleanenv \
  --env RUN_ROOT="$SOURCE" --env BANK_STAGE=/home/yliutz/gwm_stages/S105_SCENE13_BANK12_20260917 --env ARM_OUT=/mnt/out --env C8_S107_POSES=/mnt/input/S107_pose_receipt.json \
  --bind "$ENVROOT:$ENVROOT:ro" --bind "$SOURCE:$SOURCE:ro" --bind "$WEIGHTS:$WEIGHTS:ro" \
  --bind "$CODE:/opt/c8:ro" --bind "$OUTDIR:/mnt/out:rw" --bind "${C8_POSE_DIR:?set C8_POSE_DIR}:/mnt/input:ro" \
  --pwd /mnt/out "$IMAGE" "$ENVROOT/bin/python3.11" /opt/c8/run_slot_factor.py
