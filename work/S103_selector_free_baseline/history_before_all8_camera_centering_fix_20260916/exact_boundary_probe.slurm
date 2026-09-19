#!/usr/bin/env bash
# Exact S103 boundary probe only: hashes allowlisted artifacts and tests CUDA/isolation; no model forward.
#SBATCH --job-name=s103-exact-boundary
#SBATCH --partition=normal
#SBATCH --account=mscitspod2026
#SBATCH --gpus=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --output=/home/yliutz/gwm_boundary_receipts/S103_SCENE13_W001_20260916_v2/slurm-%j.out
#SBATCH --error=/home/yliutz/gwm_boundary_receipts/S103_SCENE13_W001_20260916_v2/slurm-%j.err
set -eo pipefail
source /etc/profile.d/modules.sh
module load slurm/slurm/23.02.6
module load apptainer
set -u

IMG=/home/yliutz/gwm-images/nvidia-cuda-12.6.3-runtime-ubuntu22.04.sif
ENVROOT=/home/yliutz/.conda/envs/gwm-cut3r-py311-20260915
SOURCE=/home/yliutz/gwm_source_transport_20260915
WEIGHTS=/home/yliutz/gwm_weights_20260915
STAGE=/home/yliutz/gwm_stages/S103_SCENE13_W001_20260916
BUNDLE=/home/yliutz/gwm_boundary_s103_scene13_w001_20260916_v2
RECEIPT=/home/yliutz/gwm_boundary_receipts/S103_SCENE13_W001_20260916_v2

mkdir -p "$RECEIPT"
apptainer exec --nv --containall --no-home --cleanenv \
  --env "GWM_BOUNDARY_JOB_ID=${SLURM_JOB_ID}" \
  --bind "$ENVROOT:$ENVROOT:ro" \
  --bind "$SOURCE:$SOURCE:ro" \
  --bind "$WEIGHTS:$WEIGHTS:ro" \
  --bind "$STAGE:$STAGE:ro" \
  --bind "$BUNDLE:/opt/gwm-boundary:ro" \
  --bind "$RECEIPT:/mnt/receipt:rw" \
  "$IMG" "$ENVROOT/bin/python3.11" /opt/gwm-boundary/probe_exact_s103_boundary.py
