#!/bin/bash
#SBATCH --job-name=s103-load-smoke
#SBATCH --partition=normal
#SBATCH --account=mscitspod2026
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=00:30:00
set -euo pipefail
source /etc/profile.d/modules.sh
module load Anaconda3/2023.09-0
module load slurm
module load cuda12.2/toolkit/12.2.2
ENV="$HOME/.conda/envs/gwm-cut3r-py311-20260915"
RUN="$HOME/gwm_source_transport_20260915"
OUT="$RUN/S103_h800_model_load_smoke_${SLURM_JOB_ID}"
mkdir -p "$OUT"
exec > >(tee "$OUT/slurm.log") 2>&1
export PYTHONPATH="$RUN/vmem:$RUN/vmem/extern/CUT3R:$RUN/vmem/extern/CUT3R/src"
export OUT_DIR="$OUT"
export RUN_ROOT="$RUN"
export CUDA_HOME=/cm/shared/apps/cuda12.2/toolkit/12.2.2
"$ENV/bin/python" "$RUN/load_pipeline_no_data.py"
