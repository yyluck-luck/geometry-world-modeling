#!/bin/bash
# Repair one omitted runtime dependency, then re-run the no-data import probe.
#SBATCH --job-name=gwm-py311-imageio
#SBATCH --partition=cpu
#SBATCH --account=mscitspod2026
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:15:00
set -euo pipefail
source /etc/profile.d/modules.sh
module load Anaconda3/2023.09-0
TASK_ENV="$HOME/.conda/envs/gwm-cut3r-py311-20260915"
TASK_RUN="$HOME/gwm_env_bootstrap_20260915"
exec > >(tee "$TASK_RUN/fix_imageio_${SLURM_JOB_ID}.log") 2>&1
date -u +%FT%TZ
hostname
PYTHONNOUSERSITE=1 "$TASK_ENV/bin/python" -m pip install --no-cache-dir imageio==2.31.1
PYTHONNOUSERSITE=1 "$TASK_ENV/bin/python" -m pip freeze > "$TASK_RUN/pip_freeze_${SLURM_JOB_ID}.txt"
PYTHONNOUSERSITE=1 "$TASK_ENV/bin/python" - <<'PY'
import importlib, importlib.metadata as md, sys
mods = {"torch":"torch", "torchvision":"torchvision", "numpy":"numpy", "scipy":"scipy", "transformers":"transformers", "accelerate":"accelerate", "cv2":"opencv-python-headless", "imageio":"imageio", "diffusers":"diffusers"}
print("EXEC", sys.executable)
for mod, dist in mods.items():
    try:
        obj = importlib.import_module(mod)
        print(mod, "IMPORT_OK", getattr(obj, "__version__", None) or md.version(dist))
    except Exception as exc:
        print(mod, "IMPORT_FAIL", type(exc).__name__, str(exc))
PY
date -u +%FT%TZ
