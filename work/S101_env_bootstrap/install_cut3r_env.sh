#!/bin/bash
# Isolated dependency installation only; no project model, data, RGB-D, or GT access.
#SBATCH --job-name=gwm-py311-install
#SBATCH --partition=cpu
#SBATCH --account=mscitspod2026
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
set -euo pipefail
source /etc/profile.d/modules.sh
module load Anaconda3/2023.09-0
TASK_ENV="$HOME/.conda/envs/gwm-cut3r-py311-20260915"
TASK_RUN="$HOME/gwm_env_bootstrap_20260915"
exec > >(tee "$TASK_RUN/install_${SLURM_JOB_ID}.log") 2>&1
date -u +%FT%TZ
hostname
printf 'job=%s\nenv=%s\n' "$SLURM_JOB_ID" "$TASK_ENV"
test -x "$TASK_ENV/bin/python"
PYTHONNOUSERSITE=1 "$TASK_ENV/bin/python" -m pip install --no-cache-dir -r "$TASK_RUN/requirements-cut3r.txt" diffusers==0.32.2
PYTHONNOUSERSITE=1 "$TASK_ENV/bin/python" -m pip freeze > "$TASK_RUN/pip_freeze_${SLURM_JOB_ID}.txt"
PYTHONNOUSERSITE=1 "$TASK_ENV/bin/python" - <<'PY'
import importlib, importlib.metadata as md, sys
mods = {"torch":"torch", "torchvision":"torchvision", "numpy":"numpy", "scipy":"scipy", "transformers":"transformers", "accelerate":"accelerate", "cv2":"opencv-python-headless", "imageio":"imageio", "diffusers":"diffusers"}
print("EXEC", sys.executable)
for mod, dist in mods.items():
    try:
        obj = importlib.import_module(mod)
        version = getattr(obj, "__version__", None) or md.version(dist)
        print(mod, "IMPORT_OK", version)
    except Exception as exc:
        print(mod, "IMPORT_FAIL", type(exc).__name__, str(exc))
PY
date -u +%FT%TZ
