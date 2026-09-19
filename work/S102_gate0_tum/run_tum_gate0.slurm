#!/bin/bash
#SBATCH --job-name=s102-tum-gate0
#SBATCH --partition=normal
#SBATCH --account=mscitspod2026
# The SuperPOD QOS requires a GPU allocation even for this metadata-only
# qualification job; the script itself performs no model inference.
#SBATCH --gpus=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:20:00
set -euo pipefail
source /etc/profile.d/modules.sh
module load Anaconda3/2023.09-0
module load slurm
ENV="$HOME/.conda/envs/gwm-cut3r-py311-20260915"
RUN="$HOME/gwm_source_transport_20260915"
OUT="$RUN/S102_tum_gate0_${SLURM_JOB_ID}"
mkdir -p "$OUT"
exec > >(tee "$OUT/slurm.log") 2>&1
"$ENV/bin/python" "$RUN/run_tum_gate0_metadata.py" --archive "$HOME/datasets/tum_fr3_long_office/rgbd_dataset_freiburg3_long_office_household.tgz" --out "$OUT/RESULTS.json"
