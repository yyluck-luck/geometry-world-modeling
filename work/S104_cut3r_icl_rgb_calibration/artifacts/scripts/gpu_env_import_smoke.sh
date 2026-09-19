#!/bin/bash
# GPU/environment smoke only. No model construction, weights, data, or GT.
#SBATCH --job-name=gwm-gpu-env-smoke
#SBATCH --partition=normal
#SBATCH --account=mscitspod2026
#SBATCH --gpus=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:10:00
set -euo pipefail
source /etc/profile.d/modules.sh
module load Anaconda3/2023.09-0
ENV="$HOME/.conda/envs/gwm-cut3r-py311-20260915"
RUN="$HOME/gwm_source_transport_20260915"
VMEM_SOURCE="$RUN/vmem"
exec > >(tee "$RUN/gpu_env_smoke_${SLURM_JOB_ID}.log") 2>&1
date -u +%FT%TZ
hostname
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
PYTHONNOUSERSITE=1 PYTHONPATH="$VMEM_SOURCE:$VMEM_SOURCE/extern/CUT3R" "$ENV/bin/python" - <<'PY'
import importlib, json, sys, time, torch
mods = ["modeling", "modeling.pipeline", "modeling.modules.conditioner", "modeling.modules.autoencoder", "utils.util"]
out = {
    "python": sys.version,
    "torch": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
    "device_count": torch.cuda.device_count(),
    "data_access": False,
    "weight_access": False,
    "model_execution": False,
    "imports": {},
}
if not torch.cuda.is_available():
    raise SystemExit("CUDA_NOT_AVAILABLE")
out["device_name"] = torch.cuda.get_device_name(0)
torch.manual_seed(123)
a = torch.randn((1024, 1024), device="cuda", dtype=torch.float16)
b = torch.randn((1024, 1024), device="cuda", dtype=torch.float16)
torch.cuda.synchronize()
t0 = time.perf_counter()
c = a @ b
torch.cuda.synchronize()
out["matmul_ms"] = (time.perf_counter() - t0) * 1000
out["matmul_shape"] = list(c.shape)
for m in mods:
    try:
        importlib.import_module(m)
        out["imports"][m] = "IMPORT_OK"
    except Exception as e:
        out["imports"][m] = f"FAIL {type(e).__name__}: {e}"
print(json.dumps(out, indent=2))
PY
date -u +%FT%TZ
