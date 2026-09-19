#!/usr/bin/env bash
# Formal S103 predictor only. The scorer and future data are deliberately absent.
#SBATCH --job-name=s103-vmem-base-w001
#SBATCH --partition=normal
#SBATCH --account=mscitspod2026
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=/home/yliutz/gwm_prediction_runs/S103_VMEMBASE_SCENE13_W001/slurm-%j.out
#SBATCH --error=/home/yliutz/gwm_prediction_runs/S103_VMEMBASE_SCENE13_W001/slurm-%j.err
set -eo pipefail
source /etc/profile.d/modules.sh
module load slurm/slurm/23.02.6
module load apptainer
set -u

IMAGE=/home/yliutz/gwm-images/nvidia-cuda-12.6.3-runtime-ubuntu22.04.sif
ENVROOT=/home/yliutz/.conda/envs/gwm-cut3r-py311-20260915
SOURCE=/home/yliutz/gwm_source_transport_20260915
WEIGHTS=/home/yliutz/gwm_weights_20260915
STAGE=/home/yliutz/gwm_stages/S103_SCENE13_W001_20260916
FORMAL_BUNDLE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_PARENT=/home/yliutz/gwm_prediction_runs/S103_VMEMBASE_SCENE13_W001
JOB_ROOT="$RUN_PARENT/job-${SLURM_JOB_ID}"
PREDICTOR_OUT="$JOB_ROOT/predictions"

mkdir "$JOB_ROOT"
mkdir "$PREDICTOR_OUT"
set +e
apptainer exec --nv --containall --no-home --cleanenv \
  --env "RUN_ROOT=$SOURCE" \
  --env "PREDICTOR_ROOT=$STAGE" \
  --env "PREDICTOR_OUT=/mnt/predictions" \
  --env "EXECUTION_BOUNDARY_ID=s103-scene13-w001-vmem-base-v3-k-and-camera-frame-consistent" \
  --env "RUN_ID=S103-VMemBase-scene13-w001-v1" \
  --bind "$ENVROOT:$ENVROOT:ro" \
  --bind "$SOURCE:$SOURCE:ro" \
  --bind "$WEIGHTS:$WEIGHTS:ro" \
  --bind "$STAGE:$STAGE:ro" \
  --bind "$FORMAL_BUNDLE:/opt/gwm-formal:ro" \
  --bind "$PREDICTOR_OUT:/mnt/predictions:rw" \
  "$IMAGE" "$ENVROOT/bin/python3.11" /opt/gwm-formal/predictor_s103.py
predictor_rc=$?
set -e

# Seal inside a second clean container that can see only the immutable bundle and output.
set +e
apptainer exec --containall --no-home --cleanenv \
  --bind "$ENVROOT:$ENVROOT:ro" \
  --bind "$FORMAL_BUNDLE:/opt/gwm-formal:ro" \
  --bind "$PREDICTOR_OUT:/mnt/predictions:rw" \
  "$IMAGE" "$ENVROOT/bin/python3.11" /opt/gwm-formal/seal_predictions_s103.py \
    --bundle /opt/gwm-formal \
    --output-dir /mnt/predictions \
    --host-output-dir "$PREDICTOR_OUT" \
    --predictor-exit-code "$predictor_rc"
seal_rc=$?
set -e

if [[ "$predictor_rc" -ne 0 ]]; then
  exit "$predictor_rc"
fi
exit "$seal_rc"
