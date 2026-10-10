#!/usr/bin/env bash
#SBATCH --job-name=s140-devreg
#SBATCH --partition=cpu
#SBATCH --account=mscitspod2026
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=/home/yliutz/gwm_probe_receipts/S140/devreg-%j.out
#SBATCH --error=/home/yliutz/gwm_probe_receipts/S140/devreg-%j.err
# S140: rescoring of the stage-1 outputs with the covered/hole region split (read-only on dev_gen).
set -eo pipefail
source /etc/profile.d/modules.sh; module load apptainer; set -u
IMAGE=/home/yliutz/gwm-images/nvidia-cuda-12.6.3-runtime-ubuntu22.04.sif; ENVROOT=/home/yliutz/.conda/envs/gwm-cut3r-py311-20260915
CODE=/home/yliutz/gwm_code/S140; DS=/home/yliutz/datasets; OUTD=/home/yliutz/gwm_probe_receipts/S140
apptainer exec --containall --no-home --cleanenv --bind "$ENVROOT:$ENVROOT:ro" --bind "$DS:$DS:ro" \
  --bind "$CODE/score_s140.py:/opt/score.py:ro" --bind "$CODE/plan_dev.json:/opt/plan.json:ro" --bind "$CODE/warps_dev:/mnt/warps:ro" \
  --bind /home/yliutz/gwm_probe_receipts/S140/dev_gen:/mnt/gen:ro --bind "$OUTD:/mnt/out:rw" "$IMAGE" \
  "$ENVROOT/bin/python3.11" /opt/score.py /mnt/gen "$DS" /opt/plan.json /mnt/warps /mnt/out/S140_DEV_REGION_SCORES.json
echo "[s140devreg] done $(date -u +%FT%TZ)"
