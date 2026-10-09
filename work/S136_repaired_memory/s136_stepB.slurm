#!/usr/bin/env bash
#SBATCH --job-name=s136-stepB
#SBATCH --partition=normal
#SBATCH --account=mscitspod2026
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=/home/yliutz/gwm_probe_receipts/S136/stepB-%j.out
#SBATCH --error=/home/yliutz/gwm_probe_receipts/S136/stepB-%j.err
# S136 step B on H800: seeds 42,7,1,2 of plan.json (resumable output dir), then CPU scoring (separate process) and the
# S111 harness gate (static native seeds 42/7 vs sealed job 594957). Recipe from s134_stepB.slurm / C9.
set -eo pipefail
source /etc/profile.d/modules.sh
module load slurm/slurm/23.02.6
module load apptainer
set -u
IMAGE=/home/yliutz/gwm-images/nvidia-cuda-12.6.3-runtime-ubuntu22.04.sif
ENVROOT=/home/yliutz/.conda/envs/gwm-cut3r-py311-20260915
SOURCE=/home/yliutz/gwm_source_transport_20260915
WEIGHTS=/home/yliutz/gwm_weights_20260915
CODE=/home/yliutz/gwm_code/S136
DS=/home/yliutz/datasets
S111=/home/yliutz/gwm_probe_receipts/S111/job-594957
BASE=/home/yliutz/gwm_probe_receipts/S136
GEN=$BASE/stepB_gen; STAGE=$BASE/stepB_stage; JOBDIR=$BASE/stepB-${SLURM_JOB_ID}
mkdir -p "$GEN" "$STAGE" "$JOBDIR"
echo "[s136B] start $(date -u +%FT%TZ) host=$(hostname) job=$SLURM_JOB_ID"
sha256sum "$CODE"/gen_s134.py "$CODE"/score_s134.py "$CODE"/plan.json | tee "$JOBDIR/CODE_SHA256.txt"
for sc in 13 14; do
  REL=heldout_3dmatch_scene$sc/extracted/rgbd-scenes-v2-scene_$sc
  mkdir -p "$STAGE/$REL/seq-01"; cp "$DS/$REL/camera-intrinsics.txt" "$STAGE/$REL/"
  for w in 0 50 100 150 200 250 300 350; do
    for o in 0 5 10 15 20 25 30 35 40 45 50 55; do f=$(printf 'frame-%06d' $((w+o)))
      cp -n "$DS/$REL/seq-01/$f.color.png" "$DS/$REL/seq-01/$f.pose.txt" "$STAGE/$REL/seq-01/"; done
    for o in 60 75 90 105; do f=$(printf 'frame-%06d' $((w+o)))
      cp -n "$DS/$REL/seq-01/$f.pose.txt" "$STAGE/$REL/seq-01/"; done
  done
done
echo "[s136B] staged depth files: $(find -L "$STAGE" -name '*.depth.png' | wc -l) (must be 0)"
apptainer exec --nv --containall --no-home --cleanenv \
  --env RUN_ROOT="$SOURCE" --env DATA_ROOT=/mnt/stage --env ARM_OUT=/mnt/out --env PLAN=/opt/plan.json \
  --env SEEDS=42,7,1,2 --env SHARD=0/1 --env "SLURM_JOB_ID=$SLURM_JOB_ID" \
  --bind "$ENVROOT:$ENVROOT:ro" --bind "$SOURCE:$SOURCE:ro" --bind "$WEIGHTS:$WEIGHTS:ro" \
  --bind "$STAGE:/mnt/stage:ro" --bind "$CODE/gen_s134.py:/opt/run.py:ro" --bind "$CODE/plan.json:/opt/plan.json:ro" \
  --bind "$GEN:/mnt/out:rw" --pwd /mnt/out "$IMAGE" "$ENVROOT/bin/python3.11" /opt/run.py
echo "[s136B] generation done $(date -u +%FT%TZ)"
apptainer exec --containall --no-home --cleanenv \
  --bind "$ENVROOT:$ENVROOT:ro" --bind "$DS:$DS:ro" --bind "$CODE/score_s134.py:/opt/score.py:ro" \
  --bind "$GEN:/mnt/out:rw" --pwd /mnt/out "$IMAGE" "$ENVROOT/bin/python3.11" /opt/score.py /mnt/out "$DS"
cp "$GEN/S134_SCORES.json" "$JOBDIR/S136_SCORES_superpod.json"
sha256sum "$S111"/scene_1?__w????__static__s*.npy > "$JOBDIR/SEALED_S111_STATIC_SHA256.txt"
sha256sum "$GEN"/scene_1?__w????__native__*__s*.npy > "$JOBDIR/GEN_NATIVE_SHA256.txt"
echo "[s136B] done $(date -u +%FT%TZ)"
