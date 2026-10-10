#!/usr/bin/env bash
#SBATCH --job-name=s140-ssim
#SBATCH --partition=cpu
#SBATCH --account=mscitspod2026
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=/home/yliutz/gwm_probe_receipts/S140/ssim-%j.out
#SBATCH --error=/home/yliutz/gwm_probe_receipts/S140/ssim-%j.err
# S140: PSNR+SSIM of the S139 mem_vmem outputs (H800 seeds) with the S140 scorer; read-only on the S139 dir.
set -eo pipefail
source /etc/profile.d/modules.sh; module load apptainer; set -u
IMAGE=/home/yliutz/gwm-images/nvidia-cuda-12.6.3-runtime-ubuntu22.04.sif; ENVROOT=/home/yliutz/.conda/envs/gwm-cut3r-py311-20260915
CODE=/home/yliutz/gwm_code/S140; DS=/home/yliutz/datasets/heldout_7scenes_chess/extracted; OUTD=/home/yliutz/gwm_probe_receipts/S140
apptainer exec --containall --no-home --cleanenv --bind "$ENVROOT:$ENVROOT:ro" --bind "$DS:$DS:ro" \
  --bind "$CODE/score_s140.py:/opt/score.py:ro" --bind "$CODE/plan_s139_vmem_ssim.json:/opt/plan.json:ro" --bind "$CODE/warps_chess:/mnt/warps:ro" \
  --bind /home/yliutz/gwm_probe_receipts/S139/stepB_gen:/mnt/gen:ro --bind "$OUTD:/mnt/out:rw" "$IMAGE" \
  "$ENVROOT/bin/python3.11" /opt/score.py /mnt/gen "$DS" /opt/plan.json /mnt/warps /mnt/out/S139_VMEM_SSIM_superpod.json
echo "[s140ssim] done $(date -u +%FT%TZ)"
