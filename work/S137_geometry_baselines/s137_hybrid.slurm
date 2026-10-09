#!/usr/bin/env bash
#SBATCH --job-name=s137-hybrid
#SBATCH --partition=cpu
#SBATCH --account=mscitspod2026
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=/home/yliutz/gwm_probe_receipts/S137/hybrid-%j.out
#SBATCH --error=/home/yliutz/gwm_probe_receipts/S137/hybrid-%j.err
# S137c-1 hybrid + SSIM on H800 outputs (CPU scoring process; reads target RGB). Static (S136) and warp4 (S137c).
set -eo pipefail
source /etc/profile.d/modules.sh
module load slurm/slurm/23.02.6
module load apptainer
set -u
IMAGE=/home/yliutz/gwm-images/nvidia-cuda-12.6.3-runtime-ubuntu22.04.sif
ENVROOT=/home/yliutz/.conda/envs/gwm-cut3r-py311-20260915
CODE=/home/yliutz/gwm_code/S137; DS=/home/yliutz/datasets; B=/home/yliutz/gwm_probe_receipts
run() { apptainer exec --containall --no-home --cleanenv --bind "$ENVROOT:$ENVROOT:ro" --bind "$DS:$DS:ro" \
  --bind "$CODE/hybrid_score.py:/opt/h.py:ro" --bind "$CODE/S137_warps:/mnt/warps:ro" --bind "$1:/mnt/gen:ro" \
  --bind "$B/S137:/mnt/out:rw" "$IMAGE" "$ENVROOT/bin/python3.11" /opt/h.py /mnt/gen "$DS" /mnt/warps "/mnt/out/$2" ${3:-}; }
run $B/S136/stepB_gen HYBRID_static_superpod.json
run $B/S137/warp4_gen HYBRID_warp4_superpod.json warp4
echo "[s137h] done $(date -u +%FT%TZ)"
