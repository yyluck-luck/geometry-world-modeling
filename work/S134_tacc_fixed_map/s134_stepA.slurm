#!/usr/bin/env bash
#SBATCH --job-name=s134-stepA
#SBATCH --partition=normal
#SBATCH --account=mscitspod2026
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:30:00
#SBATCH --output=/home/yliutz/gwm_probe_receipts/S134/stepA-%j.out
#SBATCH --error=/home/yliutz/gwm_probe_receipts/S134/stepA-%j.err
# S134 step A (canonical contexts). Recipe from C9 c9_convention.slurm, part 2. Sequential: native/gl x orig/fix
# (student QOS allows one running job, so no array).
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
JOBDIR=/home/yliutz/gwm_probe_receipts/S134/stepA-${SLURM_JOB_ID}
STAGE=$JOBDIR/stage
mkdir -p "$STAGE"
echo "[s134A] start $(date -u +%FT%TZ) host=$(hostname) job=${SLURM_JOB_ID}"
sha256sum "$CODE"/*.py | tee "$JOBDIR/CODE_SHA256.txt"
for sc in 13 14; do
  REL=heldout_3dmatch_scene$sc/extracted/rgbd-scenes-v2-scene_$sc
  mkdir -p "$STAGE/$REL/seq-01"; cp "$DS/$REL/camera-intrinsics.txt" "$STAGE/$REL/"
  for w in 50 100 150 200 250 300 350; do
    for o in 0 5 10 15 20 25 30 35 40 45 50 55; do f=$(printf 'frame-%06d' $((w+o)))
      cp -n "$DS/$REL/seq-01/$f.color.png" "$DS/$REL/seq-01/$f.pose.txt" "$STAGE/$REL/seq-01/"; done
    for o in 60 75 90 105; do f=$(printf 'frame-%06d' $((w+o)))
      cp -n "$DS/$REL/seq-01/$f.pose.txt" "$STAGE/$REL/seq-01/"; done
  done
  ln -sfn "$REL" "$STAGE/scene_$sc"
done
echo "[s134A] staged depth files: $(find -L "$STAGE" -name '*.depth.png' | wc -l) (must be 0)"
( cd "$STAGE" && find . -type f | sort | xargs sha256sum ) > "$JOBDIR/STAGE_MANIFEST_SHA256.txt"
for V in native:0 native:1 gl:0 gl:1; do
CONV=${V%%:*}; FIX=${V##*:}; OUTDIR=$JOBDIR/${CONV}_fix${FIX}; mkdir -p "$OUTDIR"
echo "[s134A] $CONV fix=$FIX start $(date -u +%FT%TZ)"
apptainer exec --nv --containall --no-home --cleanenv \
  --env RUN_ROOT="$SOURCE" --env DATA_ROOT=/mnt/stage --env ARM_OUT=/mnt/out --env POSE_CONVENTION=$CONV \
  --env PNP_FIX=$FIX --env "SLURM_JOB_ID=$SLURM_JOB_ID" \
  --bind "$ENVROOT:$ENVROOT:ro" --bind "$SOURCE:$SOURCE:ro" --bind "$WEIGHTS:$WEIGHTS:ro" \
  --bind "$STAGE:/mnt/stage:ro" --bind "$CODE/run_retrieval_s134.py:/opt/run.py:ro" \
  --bind "$OUTDIR:/mnt/out:rw" --pwd /mnt/out "$IMAGE" "$ENVROOT/bin/python3.11" /opt/run.py || echo "[s134A] $CONV fix=$FIX FAILED"
done
echo "[s134A] done $(date -u +%FT%TZ)"
