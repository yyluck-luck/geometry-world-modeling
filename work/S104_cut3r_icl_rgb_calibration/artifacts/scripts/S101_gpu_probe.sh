#!/usr/bin/env bash
set -euo pipefail
echo "host=$(hostname)"
echo "utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
python3 --version
python3 - <<'PY'
import importlib.util
print('torch_available', bool(importlib.util.find_spec('torch')))
if importlib.util.find_spec('torch'):
    import torch
    print('torch_version', torch.__version__)
    print('cuda_available', torch.cuda.is_available())
    print('cuda_device_count', torch.cuda.device_count())
    if torch.cuda.is_available():
        print('torch_device', torch.cuda.get_device_name(0))
PY
