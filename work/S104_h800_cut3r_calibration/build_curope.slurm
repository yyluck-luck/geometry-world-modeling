#!/bin/bash
#SBATCH --job-name=s104-curope-build
#SBATCH --partition=normal
#SBATCH --account=mscitspod2026
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=00:20:00
set -euo pipefail
source /etc/profile.d/modules.sh
module load Anaconda3/2023.09-0
module load slurm
module load cuda12.2/toolkit/12.2.2
ENV="$HOME/.conda/envs/gwm-cut3r-py311-20260915"
RUN="$HOME/gwm_source_transport_20260915"
SRC="$RUN/vmem/extern/CUT3R/src/croco/models/curope"
OUT="$RUN/S104_curope_build_${SLURM_JOB_ID}"
mkdir -p "$OUT"
exec > >(tee "$OUT/slurm.log") 2>&1
date -u +%FT%TZ
cd "$SRC"
export CC=/usr/bin/gcc
export CXX=/usr/bin/g++
export CUDAHOSTCXX=/usr/bin/g++
export CUDA_HOME=/cm/shared/apps/cuda12.2/toolkit/12.2.2
"$ENV/bin/python" setup.py build_ext --inplace
find "$SRC" -maxdepth 1 -type f -name '*.so' -printf '%f %s\\n' | tee "$OUT/extension_files.txt"
sha256sum "$SRC"/*.so | tee "$OUT/extension_sha256.txt"
after=$($ENV/bin/python - <<'PY'
import importlib, torch
m=importlib.import_module('curope')
print('IMPORT_OK',m,torch.cuda.is_available(),torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NO_CUDA')
PY
)
printf '%s\\n' "$after" | tee "$OUT/import_probe.txt"
