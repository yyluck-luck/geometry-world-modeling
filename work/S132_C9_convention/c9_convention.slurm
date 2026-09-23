#!/usr/bin/env bash
#SBATCH --job-name=c9-convention
#SBATCH --partition=normal
#SBATCH --account=mscitspod2026
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --output=/home/yliutz/gwm_probe_receipts/C9/c9-%j.out
#SBATCH --error=/home/yliutz/gwm_probe_receipts/C9/c9-%j.err
# DECISION C9: pose-convention test. Recipe from nms_s111.slurm / C8 support_audit_v2.slurm.
set -eo pipefail
source /etc/profile.d/modules.sh
module load slurm/slurm/23.02.6
module load apptainer
set -u
IMAGE=/home/yliutz/gwm-images/nvidia-cuda-12.6.3-runtime-ubuntu22.04.sif
ENVROOT=/home/yliutz/.conda/envs/gwm-cut3r-py311-20260915
SOURCE=/home/yliutz/gwm_source_transport_20260915
WEIGHTS=/home/yliutz/gwm_weights_20260915
C9=/home/yliutz/geometry-world-modeling/work/S132_C9_convention
DS=/home/yliutz/datasets
S111=/home/yliutz/gwm_probe_receipts/S111/job-594957
OUTDIR=/home/yliutz/gwm_probe_receipts/C9/job-${SLURM_JOB_ID}
STAGE=$OUTDIR/stage
mkdir -p "$OUTDIR/gen" "$OUTDIR/surfel_gl" "$STAGE"
echo "[c9] start $(date -u +%FT%TZ) host=$(hostname) job=$SLURM_JOB_ID"
sha256sum "$C9"/*.py | tee "$OUTDIR/CODE_SHA256.txt"
sha256sum "$S111"/scene_1?__w????__static__s*.npy > "$OUTDIR/SEALED_S111_STATIC_SHA256.txt"

# ---- staging (dataset-relative layout): context/bank color+pose, target pose; no depth, no target RGB ----
for sc in 13 14; do
  REL=heldout_3dmatch_scene$sc/extracted/rgbd-scenes-v2-scene_$sc
  mkdir -p "$STAGE/$REL/seq-01"; cp "$DS/$REL/camera-intrinsics.txt" "$STAGE/$REL/"
  for w in 0 50 100 150 200 250 300 350; do
    for o in 0 5 10 15 20 25 30 35 40 45 50 55; do f=$(printf 'frame-%06d' $((w+o)))
      [ -f "$DS/$REL/seq-01/$f.color.png" ] && cp -n "$DS/$REL/seq-01/$f.color.png" "$DS/$REL/seq-01/$f.pose.txt" "$STAGE/$REL/seq-01/"; done
    for o in 60 75 90 105; do f=$(printf 'frame-%06d' $((w+o)))
      [ -f "$DS/$REL/seq-01/$f.pose.txt" ] && cp -n "$DS/$REL/seq-01/$f.pose.txt" "$STAGE/$REL/seq-01/"; done
  done
  ln -sfn "$REL" "$STAGE/scene_$sc"          # layout used by the support-retrieval runner
done
echo "[c9] staged depth files: $(find -L "$STAGE" -name '*.depth.png' | wc -l) (must be 0)"
( cd "$STAGE" && find . -type f | sort | xargs sha256sum ) > "$OUTDIR/STAGE_MANIFEST_SHA256.txt"

run_gpu() { apptainer exec --nv --containall --no-home --cleanenv \
  --env RUN_ROOT="$SOURCE" --env DATA_ROOT=/mnt/stage --env "SLURM_JOB_ID=$SLURM_JOB_ID" "$@"; }

# ---- 1. static generation, native vs gl ----
run_gpu --env ARM_OUT=/mnt/out --env SEEDS=42,7 \
  --bind "$ENVROOT:$ENVROOT:ro" --bind "$SOURCE:$SOURCE:ro" --bind "$WEIGHTS:$WEIGHTS:ro" \
  --bind "$STAGE:/mnt/stage:ro" --bind "$C9/convention_test_c9.py:/opt/run.py:ro" \
  --bind "$OUTDIR/gen:/mnt/out:rw" --pwd /mnt/out "$IMAGE" "$ENVROOT/bin/python3.11" /opt/run.py

# ---- 2. surfel memory under gl poses (secondary diagnostic) ----
run_gpu --env ARM_OUT=/mnt/out --env POSE_CONVENTION=gl \
  --bind "$ENVROOT:$ENVROOT:ro" --bind "$SOURCE:$SOURCE:ro" --bind "$WEIGHTS:$WEIGHTS:ro" \
  --bind "$STAGE:/mnt/stage:ro" --bind "$C9/run_support_retrieval_c9.py:/opt/run.py:ro" \
  --bind "$OUTDIR/surfel_gl:/mnt/out:rw" --pwd /mnt/out "$IMAGE" "$ENVROOT/bin/python3.11" /opt/run.py

# ---- 3. scoring: separate CPU process, reads target RGB ----
apptainer exec --containall --no-home --cleanenv \
  --bind "$ENVROOT:$ENVROOT:ro" --bind "$DS:$DS:ro" --bind "$C9/score_c9.py:/opt/score.py:ro" \
  --bind "$OUTDIR/gen:/mnt/out:rw" --pwd /mnt/out "$IMAGE" "$ENVROOT/bin/python3.11" /opt/score.py /mnt/out "$DS"
echo "[c9] done $(date -u +%FT%TZ)"
