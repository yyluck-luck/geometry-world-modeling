#!/bin/bash
# Gate 0 sample qualification only; no selection, model, or formal GRC.
#SBATCH --job-name=icl-gate0-sample
#SBATCH --partition=cpu
#SBATCH --account=mscitspod2026
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:15:00
set -euo pipefail
source /etc/profile.d/modules.sh
module load Anaconda3/2023.09-0
ENV="$HOME/.conda/envs/gwm-cut3r-py311-20260915"
ARCHIVE="/home/yliutz/datasets/icl_nuim/living_room_traj0_frei_png.tar.gz"
RUN="$HOME/gwm_source_transport_20260915"
exec > >(tee "$RUN/icl_gate0_sample_${SLURM_JOB_ID}.log") 2>&1
date -u +%FT%TZ
hostname
test -f "$ARCHIVE"
PYTHONNOUSERSITE=1 "$ENV/bin/python" "$RUN/icl_sample_decode_audit.py" "$ARCHIVE"
date -u +%FT%TZ
