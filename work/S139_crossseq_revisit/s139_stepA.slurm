#!/usr/bin/env bash
#SBATCH --job-name=s139-stepA
#SBATCH --partition=normal
#SBATCH --account=mscitspod2026
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=04:00:00
#SBATCH --output=/home/yliutz/gwm_probe_receipts/S139/stepA-%j.out
#SBATCH --error=/home/yliutz/gwm_probe_receipts/S139/stepA-%j.err
# S139 step A (canonical contexts, H800): cross-sequence revisit banks, gl + KPS + coverage priming. From s136_stepA.slurm.
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
SRCDS=/home/yliutz/datasets/heldout_7scenes_chess/extracted/chess
BASE=/home/yliutz/gwm_probe_receipts/S139; STAGE=$BASE/stage; OUTDIR=$BASE/stepA-${SLURM_JOB_ID}
mkdir -p "$STAGE/chess" "$OUTDIR"
echo "[s139A] start $(date -u +%FT%TZ) host=$(hostname) job=$SLURM_JOB_ID"
sha256sum "$CODE"/*.py "$CODE"/WINDOW_MANIFEST.json | tee "$OUTDIR/CODE_SHA256.txt"
printf '585 0 320\n0 585 240\n0 0 1\n' > "$STAGE/chess/camera-intrinsics.txt"
"$ENVROOT/bin/python3.11" - "$CODE/WINDOW_MANIFEST.json" "$SRCDS" "$STAGE/chess" <<'PY'
import json, shutil, sys
from pathlib import Path
m = json.load(open(sys.argv[1])); src, dst = Path(sys.argv[2]), Path(sys.argv[3])
color, posef = set(), set()
for w in m['windows']:
    color |= set(w['bank']); posef |= set(w['bank']) | set(w['targets'])
for ref in sorted(posef):
    s, f = ref.split('/'); (dst / s).mkdir(parents=True, exist_ok=True)
    shutil.copy2(src / s / f'frame-{f}.pose.txt', dst / s / f'frame-{f}.pose.txt')
    if ref in color: shutil.copy2(src / s / f'frame-{f}.color.png', dst / s / f'frame-{f}.color.png')
print('staged poses', len(posef), 'colors', len(color))
PY
echo "[s139A] staged depth files: $(find -L "$STAGE" -name '*.depth.png' | wc -l) (must be 0)"
( cd "$STAGE" && find . -type f | sort | xargs sha256sum ) > "$OUTDIR/STAGE_MANIFEST_SHA256.txt"
apptainer exec --nv --containall --no-home --cleanenv \
  --env RUN_ROOT="$SOURCE" --env DATA_ROOT=/mnt/stage --env ARM_OUT=/mnt/out --env POSE_CONVENTION=gl \
  --env INIT=kps --env WINDOW_MANIFEST=/opt/manifest.json --env "SLURM_JOB_ID=$SLURM_JOB_ID" \
  --bind "$ENVROOT:$ENVROOT:ro" --bind "$SOURCE:$SOURCE:ro" --bind "$WEIGHTS:$WEIGHTS:ro" \
  --bind "$STAGE:/mnt/stage:ro" --bind "$CODE/run_retrieval_s139.py:/opt/run.py:ro" --bind "$CODE/kps.py:/opt/kps.py:ro" \
  --bind "$CODE/WINDOW_MANIFEST.json:/opt/manifest.json:ro" \
  --bind "$OUTDIR:/mnt/out:rw" --pwd /mnt/out "$IMAGE" "$ENVROOT/bin/python3.11" /opt/run.py
echo "[s139A] done $(date -u +%FT%TZ)"
