#!/usr/bin/env bash
#SBATCH --job-name=c8-support
#SBATCH --partition=normal
#SBATCH --account=mscitspod2026
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --output=/home/yliutz/gwm_probe_receipts/C8/support-%j.out
#SBATCH --error=/home/yliutz/gwm_probe_receipts/C8/support-%j.err
# C8 Experiment 2, GPU part: rebuild surfel memory per window and save retrieval maps. No diffusion.
# The model container sees only a staged copy of bank color+pose and target pose. Target RGB and
# all depth files stay outside; the B/C/J evaluator runs later as a separate CPU process.
set -eo pipefail
source /etc/profile.d/modules.sh
module load slurm/slurm/23.02.6
module load apptainer
set -u
IMAGE=/home/yliutz/gwm-images/nvidia-cuda-12.6.3-runtime-ubuntu22.04.sif
ENVROOT=/home/yliutz/.conda/envs/gwm-cut3r-py311-20260915
SOURCE=/home/yliutz/gwm_source_transport_20260915
WEIGHTS=/home/yliutz/gwm_weights_20260915
C8=/home/yliutz/geometry-world-modeling/work/S130_C8_diagnostics
DS=/home/yliutz/datasets
OUTDIR=/home/yliutz/gwm_probe_receipts/C8/support-job-${SLURM_JOB_ID}
STAGE=$OUTDIR/stage
mkdir -p "$OUTDIR" "$STAGE"
echo "[c8-support] start $(date -u +%FT%TZ) host=$(hostname) job=$SLURM_JOB_ID"
sha256sum "$C8/run_support_retrieval_v2.py" | tee "$OUTDIR/CODE_SHA256.txt"

# ---- staging: bank color+pose and target pose only (no target RGB, no depth) ----
for sc in 13 14; do
  SRC=$DS/heldout_3dmatch_scene$sc/extracted/rgbd-scenes-v2-scene_$sc
  DST=$STAGE/scene_$sc; mkdir -p "$DST/seq-01"; cp "$SRC/camera-intrinsics.txt" "$DST/"
  for w in 50 100 150 200 250 300 350; do
    for o in 0 5 10 15 20 25 30 35 40 45 50 55; do f=$(printf 'frame-%06d' $((w+o)))
      [ -f "$SRC/seq-01/$f.color.png" ] && cp -n "$SRC/seq-01/$f.color.png" "$SRC/seq-01/$f.pose.txt" "$DST/seq-01/"; done
    for o in 60 75 90 105; do f=$(printf 'frame-%06d' $((w+o)))
      [ -f "$SRC/seq-01/$f.pose.txt" ] && cp -n "$SRC/seq-01/$f.pose.txt" "$DST/seq-01/"; done
  done
done
echo "[c8-support] staged: $(find "$STAGE" -name '*.color.png' | wc -l) bank images, $(find "$STAGE" -name '*.pose.txt' | wc -l) poses, $(find "$STAGE" -name '*.depth.png' | wc -l) depth files (must be 0)"
( cd "$STAGE" && find . -type f | sort | xargs sha256sum ) > "$OUTDIR/STAGE_MANIFEST_SHA256.txt"

# ---- GPU: surfel memory + retrieval maps ----
apptainer exec --nv --containall --no-home --cleanenv \
  --env RUN_ROOT="$SOURCE" --env DATA_ROOT=/mnt/stage --env ARM_OUT=/mnt/out \
  --env "SLURM_JOB_ID=$SLURM_JOB_ID" \
  --bind "$ENVROOT:$ENVROOT:ro" --bind "$SOURCE:$SOURCE:ro" --bind "$WEIGHTS:$WEIGHTS:ro" \
  --bind "$STAGE:/mnt/stage:ro" --bind "$C8/run_support_retrieval_v2.py:/opt/run.py:ro" \
  --bind "$OUTDIR:/mnt/out:rw" --pwd /mnt/out \
  "$IMAGE" "$ENVROOT/bin/python3.11" /opt/run.py
echo "[c8-support] done $(date -u +%FT%TZ)"
