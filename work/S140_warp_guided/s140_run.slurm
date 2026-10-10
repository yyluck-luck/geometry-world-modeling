#!/usr/bin/env bash
#SBATCH --job-name=s140
#SBATCH --partition=normal
#SBATCH --account=mscitspod2026
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --output=/home/yliutz/gwm_probe_receipts/S140/run-%j.out
#SBATCH --error=/home/yliutz/gwm_probe_receipts/S140/run-%j.err
# S140 WGS on H800. env: STAGE_DIR, PLAN_NAME (plan file in CODE), WARP_SUB (warp dir in CODE), SEEDS, DS_ROOT, TAG.
set -eo pipefail
source /etc/profile.d/modules.sh
module load slurm/slurm/23.02.6
module load apptainer
set -u
IMAGE=/home/yliutz/gwm-images/nvidia-cuda-12.6.3-runtime-ubuntu22.04.sif
ENVROOT=/home/yliutz/.conda/envs/gwm-cut3r-py311-20260915
SOURCE=/home/yliutz/gwm_source_transport_20260915
WEIGHTS=/home/yliutz/gwm_weights_20260915
CODE=/home/yliutz/gwm_code/S140
BASE=/home/yliutz/gwm_probe_receipts/S140; GEN=$BASE/${TAG}_gen; JOBDIR=$BASE/${TAG}-${SLURM_JOB_ID}
mkdir -p "$GEN" "$JOBDIR"
echo "[s140] $TAG start $(date -u +%FT%TZ) host=$(hostname) job=$SLURM_JOB_ID"
sha256sum "$CODE"/gen_s140.py "$CODE"/score_s140.py "$CODE/$PLAN_NAME" | tee "$JOBDIR/CODE_SHA256.txt"
echo "[s140] staged depth files: $(find -L "$STAGE_DIR" -name '*.depth.png' | wc -l) (must be 0)"
apptainer exec --nv --containall --no-home --cleanenv \
  --env RUN_ROOT="$SOURCE" --env DATA_ROOT=/mnt/stage --env ARM_OUT=/mnt/out --env PLAN=/opt/plan.json --env WARP_DIR=/mnt/warps \
  --env SEEDS=$SEEDS --env SHARD=0/1 --env "SLURM_JOB_ID=$SLURM_JOB_ID" \
  --bind "$ENVROOT:$ENVROOT:ro" --bind "$SOURCE:$SOURCE:ro" --bind "$WEIGHTS:$WEIGHTS:ro" \
  --bind "$STAGE_DIR:/mnt/stage:ro" --bind "$CODE/gen_s140.py:/opt/run.py:ro" --bind "$CODE/$PLAN_NAME:/opt/plan.json:ro" \
  --bind "$CODE/$WARP_SUB:/mnt/warps:ro" --bind "$GEN:/mnt/out:rw" --pwd /mnt/out "$IMAGE" "$ENVROOT/bin/python3.11" /opt/run.py
echo "[s140] generation done $(date -u +%FT%TZ)"
apptainer exec --containall --no-home --cleanenv \
  --bind "$ENVROOT:$ENVROOT:ro" --bind "$DS_ROOT:$DS_ROOT:ro" --bind "$CODE/score_s140.py:/opt/score.py:ro" \
  --bind "$CODE/$PLAN_NAME:/opt/plan.json:ro" --bind "$CODE/$WARP_SUB:/mnt/warps:ro" \
  --bind "$GEN:/mnt/out:rw" --pwd /mnt/out "$IMAGE" "$ENVROOT/bin/python3.11" /opt/score.py /mnt/out "$DS_ROOT" /opt/plan.json /mnt/warps
cp "$GEN/S140_SCORES.json" "$JOBDIR/S140_SCORES_${TAG}.json"
sha256sum "$GEN"/*__ref_1.0__s*.npy "$GEN"/*__none_1.0__s*.npy > "$JOBDIR/FIDELITY_SHA256.txt" 2>/dev/null || true
echo "[s140] $TAG done $(date -u +%FT%TZ)"
