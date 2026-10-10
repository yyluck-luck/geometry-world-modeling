#!/usr/bin/env bash
#SBATCH --job-name=s139-stepB
#SBATCH --partition=normal
#SBATCH --account=mscitspod2026
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=/home/yliutz/gwm_probe_receipts/S139/stepB-%j.out
#SBATCH --error=/home/yliutz/gwm_probe_receipts/S139/stepB-%j.err
# S139 step B on H800: seeds 42,7,1,2 of plan.json (resumable), then CPU scoring in a separate process.
set -eo pipefail
source /etc/profile.d/modules.sh
module load slurm/slurm/23.02.6
module load apptainer
set -u
IMAGE=/home/yliutz/gwm-images/nvidia-cuda-12.6.3-runtime-ubuntu22.04.sif
ENVROOT=/home/yliutz/.conda/envs/gwm-cut3r-py311-20260915
SOURCE=/home/yliutz/gwm_source_transport_20260915
WEIGHTS=/home/yliutz/gwm_weights_20260915
CODE=/home/yliutz/gwm_code/S139
DS=/home/yliutz/datasets/heldout_7scenes_chess/extracted
BASE=/home/yliutz/gwm_probe_receipts/S139; STAGE=$BASE/stage; GEN=$BASE/stepB_gen; JOBDIR=$BASE/stepB-${SLURM_JOB_ID}
mkdir -p "$GEN" "$JOBDIR"
echo "[s139B] start $(date -u +%FT%TZ) host=$(hostname) job=$SLURM_JOB_ID"
STEPA=${STEPA_JOB:?set STEPA_JOB}
"$ENVROOT/bin/python3.11" "$CODE/build_plan_s139.py" "$CODE/WINDOW_MANIFEST.json" "$BASE/stepA-$STEPA/RETRIEVAL_RECEIPT.json" "$CODE/POSE_ARMS.json" "$JOBDIR/plan.json"
sha256sum "$CODE"/gen_s139.py "$CODE"/score_s139.py "$CODE"/build_plan_s139.py "$JOBDIR/plan.json" | tee "$JOBDIR/CODE_SHA256.txt"
echo "[s139B] staged depth files: $(find -L "$STAGE" -name '*.depth.png' | wc -l) (must be 0)"
apptainer exec --nv --containall --no-home --cleanenv \
  --env RUN_ROOT="$SOURCE" --env DATA_ROOT=/mnt/stage --env ARM_OUT=/mnt/out --env PLAN=/opt/plan.json \
  --env SEEDS=42,7,1,2 --env SHARD=0/1 --env "SLURM_JOB_ID=$SLURM_JOB_ID" \
  --bind "$ENVROOT:$ENVROOT:ro" --bind "$SOURCE:$SOURCE:ro" --bind "$WEIGHTS:$WEIGHTS:ro" \
  --bind "$STAGE:/mnt/stage:ro" --bind "$CODE/gen_s139.py:/opt/run.py:ro" --bind "$JOBDIR/plan.json:/opt/plan.json:ro" \
  --bind "$GEN:/mnt/out:rw" --pwd /mnt/out "$IMAGE" "$ENVROOT/bin/python3.11" /opt/run.py
echo "[s139B] generation done $(date -u +%FT%TZ)"
apptainer exec --containall --no-home --cleanenv \
  --bind "$ENVROOT:$ENVROOT:ro" --bind "$DS:$DS:ro" --bind "$CODE/score_s139.py:/opt/score.py:ro" --bind "$JOBDIR/plan.json:/opt/plan.json:ro" \
  --bind "$GEN:/mnt/out:rw" --pwd /mnt/out "$IMAGE" "$ENVROOT/bin/python3.11" /opt/score.py /mnt/out "$DS" /opt/plan.json
cp "$GEN/S139_SCORES.json" "$JOBDIR/S139_SCORES_superpod.json"
echo "[s139B] done $(date -u +%FT%TZ)"
