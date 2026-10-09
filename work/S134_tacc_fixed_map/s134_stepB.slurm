#!/usr/bin/env bash
#SBATCH --job-name=s134-stepB
#SBATCH --partition=normal
#SBATCH --account=mscitspod2026
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=/home/yliutz/gwm_probe_receipts/S134/stepB-%j.out
#SBATCH --error=/home/yliutz/gwm_probe_receipts/S134/stepB-%j.err
# S134 step B on H800: seeds 42,7,1,2 from the canonical plan; then a separate CPU scoring process and the
# S111 harness gate (static seeds 42/7 byte-identical to sealed job 594957). Recipe from C9 c9_convention.slurm.
set -eo pipefail
source /etc/profile.d/modules.sh
module load slurm/slurm/23.02.6
module load apptainer
set -u
IMAGE=/home/yliutz/gwm-images/nvidia-cuda-12.6.3-runtime-ubuntu22.04.sif
ENVROOT=/home/yliutz/.conda/envs/gwm-cut3r-py311-20260915
SOURCE=/home/yliutz/gwm_source_transport_20260915
WEIGHTS=/home/yliutz/gwm_weights_20260915
CODE=/home/yliutz/gwm_code/S134
DS=/home/yliutz/datasets
S111=/home/yliutz/gwm_probe_receipts/S111/job-594957
STAGE=${STAGE_DIR:?set STAGE_DIR to the step-A stage}
JOBDIR=/home/yliutz/gwm_probe_receipts/S134/stepB-${SLURM_JOB_ID}; mkdir -p "$JOBDIR/gen"
echo "[s134B] start $(date -u +%FT%TZ) host=$(hostname) job=$SLURM_JOB_ID"
sha256sum "$CODE"/*.py "$CODE"/plan.json | tee "$JOBDIR/CODE_SHA256.txt"
apptainer exec --nv --containall --no-home --cleanenv \
  --env RUN_ROOT="$SOURCE" --env DATA_ROOT=/mnt/stage --env ARM_OUT=/mnt/out --env PLAN=/opt/plan.json \
  --env SEEDS=42,7,1,2 --env SHARD=0/1 --env "SLURM_JOB_ID=$SLURM_JOB_ID" \
  --bind "$ENVROOT:$ENVROOT:ro" --bind "$SOURCE:$SOURCE:ro" --bind "$WEIGHTS:$WEIGHTS:ro" \
  --bind "$STAGE:/mnt/stage:ro" --bind "$CODE/gen_s134.py:/opt/run.py:ro" --bind "$CODE/plan.json:/opt/plan.json:ro" \
  --bind "$JOBDIR/gen:/mnt/out:rw" --pwd /mnt/out "$IMAGE" "$ENVROOT/bin/python3.11" /opt/run.py
echo "[s134B] generation done $(date -u +%FT%TZ)"
apptainer exec --containall --no-home --cleanenv \
  --bind "$ENVROOT:$ENVROOT:ro" --bind "$DS:$DS:ro" --bind "$CODE/score_s134.py:/opt/score.py:ro" \
  --bind "$JOBDIR/gen:/mnt/out:rw" --pwd /mnt/out "$IMAGE" "$ENVROOT/bin/python3.11" /opt/score.py /mnt/out "$DS"
sha256sum "$S111"/scene_1?__w????__static__s*.npy > "$JOBDIR/SEALED_S111_STATIC_SHA256.txt"
sha256sum "$JOBDIR"/gen/scene_1?__w????__native__*__s*.npy > "$JOBDIR/GEN_NATIVE_SHA256.txt"
echo "[s134B] done $(date -u +%FT%TZ)"
