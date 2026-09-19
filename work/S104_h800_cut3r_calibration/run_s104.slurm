#!/bin/bash
#SBATCH --job-name=s104-cut3r-rgb
#SBATCH --partition=normal
#SBATCH --account=mscitspod2026
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=00:30:00
set -euo pipefail
source /etc/profile.d/modules.sh
module load Anaconda3/2023.09-0
ENV="$HOME/.conda/envs/gwm-cut3r-py311-20260915"
RUN="$HOME/gwm_source_transport_20260915"
export CUT3R_SOURCE="$RUN/vmem/extern/CUT3R"
export PYTHONPATH="$RUN/vmem:$CUT3R_SOURCE"
OUT="$RUN/S104_cut3r_calibration_${SLURM_JOB_ID}"
mkdir -p "$OUT"
RGB_DIR="$RUN/icl_rgb_s104"
exec > >(tee "$OUT/slurm.log") 2>&1
date -u +%FT%TZ
"$ENV/bin/python" "$RUN/run_cut3r_rgb_only.py" \
  --model "$HOME/gwm_weights_20260915/cut3r_512_dpt_4_64.pth" \
  --rgb "$RGB_DIR/id_1.png" "$RGB_DIR/id_31.png" "$RGB_DIR/id_61.png" "$RGB_DIR/id_91.png" --out "$OUT" --size 512
