#!/bin/bash
# Direct VMem runtime imports only. No model construction, weights, data, or GT.
#SBATCH --job-name=gwm-vmem-direct
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
exec > >(tee "$TASK_RUN/install_direct_${SLURM_JOB_ID}.log") 2>&1
date -u +%FT%TZ
hostname
test -x "$TASK_ENV/bin/python"
PYTHONNOUSERSITE=1 "$TASK_ENV/bin/python" -m pip install --no-cache-dir --upgrade-strategy only-if-needed kornia==0.8.0 open-clip-torch==2.30.0 matplotlib==3.9.2 torcheval==0.0.7
PYTHONNOUSERSITE=1 "$TASK_ENV/bin/python" -m pip freeze > "$TASK_RUN/pip_freeze_direct_${SLURM_JOB_ID}.txt"
PYTHONNOUSERSITE=1 "$TASK_ENV/bin/python" - <<'PY'
import importlib, importlib.metadata as md, json, sys
mods = {"kornia":"kornia", "open_clip":"open-clip-torch", "matplotlib":"matplotlib", "torcheval":"torcheval"}
out = {"python":sys.version, "data_access":False, "weight_access":False, "model_execution":False, "results":{}}
for mod, dist in mods.items():
    try:
        obj=importlib.import_module(mod)
        out["results"][mod]={"status":"IMPORT_OK", "version":getattr(obj,"__version__",None) or md.version(dist)}
    except Exception as e:
        out["results"][mod]={"status":"IMPORT_FAIL", "error":f"{type(e).__name__}: {e}"}
print(json.dumps(out, indent=2))
PY
date -u +%FT%TZ
