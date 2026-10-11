#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")"
export CUDA_VISIBLE_DEVICES=""
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2
export PYTHONUNBUFFERED=1
printf '%s\n' "$(date -u +%FT%TZ) P1 CPU pilot started"
nice -n 10 timeout 3600 /mnt/gluster_dcpu/yiyangliu/gwm_s134/env/bin/python pilot.py .
status=$?
printf '%s\n' "$status" > RUN_EXIT_CODE.txt
printf '%s\n' "$(date -u +%FT%TZ) P1 CPU pilot exit=$status"
exit "$status"
