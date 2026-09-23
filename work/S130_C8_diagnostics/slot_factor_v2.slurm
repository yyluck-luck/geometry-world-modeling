#!/usr/bin/env bash
#SBATCH --job-name=c8-slotfactor
#SBATCH --partition=normal
#SBATCH --account=mscitspod2026
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --output=/home/yliutz/gwm_probe_receipts/C8/slot-%j.out
#SBATCH --error=/home/yliutz/gwm_probe_receipts/C8/slot-%j.err
# C8 Experiment 1. Recipe copied from work/S103_selector_free_baseline/orderbalanced_s107.slurm.
# Process 1 (GPU) generates; process 2 (CPU) scores with the S106/S107 contract scorer.
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
C8=/home/yliutz/geometry-world-modeling/work/S130_C8_diagnostics
S103=/home/yliutz/geometry-world-modeling/work/S103_selector_free_baseline
SEQ=/home/yliutz/datasets/heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13/seq-01
OUTDIR=/home/yliutz/gwm_probe_receipts/C8/slot-job-${SLURM_JOB_ID}
mkdir -p "$OUTDIR"
echo "[c8] start $(date -u +%FT%TZ) host=$(hostname) job=$SLURM_JOB_ID"
sha256sum "$C8/run_slot_factor_v2.py" "$C8/factorized_conditioning.py" "$S103/score_arms_s106.py" | tee "$OUTDIR/CODE_SHA256.txt"

# ---- process 1: generation (GPU); no target RGB is bound into this container ----
apptainer exec --nv --containall --no-home --cleanenv \
  --env "RUN_ROOT=$SOURCE" --env "BANK_STAGE=$STAGE" --env "ARM_OUT=/mnt/out" \
  --env "SLURM_JOB_ID=$SLURM_JOB_ID" \
  --bind "$ENVROOT:$ENVROOT:ro" --bind "$SOURCE:$SOURCE:ro" --bind "$WEIGHTS:$WEIGHTS:ro" \
  --bind "$STAGE:$STAGE:ro" \
  --bind "$C8/run_slot_factor_v2.py:/opt/arms.py:ro" \
  --bind "$C8/factorized_conditioning.py:/opt/factorized_conditioning.py:ro" \
  --bind "$OUTDIR:/mnt/out:rw" --pwd /mnt/out \
  "$IMAGE" "$ENVROOT/bin/python3.11" /opt/arms.py

# ---- process 2: scoring (CPU), separate process, reads target RGB ----
apptainer exec --containall --no-home --cleanenv \
  --bind "$ENVROOT:$ENVROOT:ro" --bind "$SEQ:$SEQ:ro" \
  --bind "$S103/score_arms_s106.py:/opt/score.py:ro" \
  --bind "$OUTDIR:/mnt/out:rw" --pwd /mnt/out \
  "$IMAGE" "$ENVROOT/bin/python3.11" /opt/score.py /mnt/out
echo "[c8] done $(date -u +%FT%TZ)"
