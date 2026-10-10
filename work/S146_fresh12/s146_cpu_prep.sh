#!/bin/bash
# S146 CPU preparation (no GPU, no target scoring): receipt -> convention -> pool phase 1 -> phase-1 warps (3 shards).
set -euo pipefail
R=/mnt/gluster_dcpu/yiyangliu/gwm_s134; G=/mnt/gluster_dcpu/yiyangliu/gwm_s146; S=$R/src/s146; PY=$R/env/bin/python
export RUN_ROOT=$R/src WEIGHTS=$R/weights CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 PYTHONNOUSERSITE=1 XDG_CACHE_HOME=$R/cache
sha256sum $S/*.py > $G/CODE_SHA256_cpu_prep.txt
[ -s $G/METADATA_RECEIPT.json ] || $PY $S/metadata_receipt_s146.py /home/yiyangliu/s146_data $G/stage12 $G/logs/zips.sha256 $G/METADATA_RECEIPT.json
[ -s $G/CONVENTION.json ] || $PY $S/convention_check_s146.py $G/stage12 $G/manifests $G/CONVENTION.json 2>&1 | grep -vE 'INFO|DEBUG|Processing|Running|Inference completed|Processing reconstruction'
$PY $S/convention_check2_s146.py $G/stage12 $G/manifests $G/CONVENTION2.json 2>&1 | grep -E ' -> |Error|Traceback'
python3 - <<PY
import json, math, sys
def decide(r):   # Amendment 1: winner finite; loser non-finite or >= 2x winner
    a, b = r['gl']['median_reproj_px'], r['native']['median_reproj_px']
    w, l = (a, b) if a <= b else (b, a)
    if not math.isfinite(w): return None
    return r['winner'] if (not math.isfinite(l) or l >= 2 * w) else None
c1 = {r['room']: decide(r) for r in json.load(open('$G/CONVENTION.json'))['rows']}
c2 = {r['room']: decide(r) for r in json.load(open('$G/CONVENTION2.json'))['rows']}
print('check1', c1, 'check2', c2)
bad = [k for k in c1 if c1[k] is None or c1[k] != c2.get(k)]
if bad: print('convention INELIGIBLE', bad); sys.exit(3)
PY
$PY $S/build_pool_s146.py 1 $G/stage12 $G/manifests $G/CONVENTION.json $G/POOL_phase1.json 2>&1 | grep -vE 'INFO|DEBUG|Processing|Running|Inference completed|reconstruction output'
OMP_NUM_THREADS=6 MKL_NUM_THREADS=6
for i in 0 1 2; do $PY $S/warps_s146.py $G/stage12 $G/POOL_phase1.json $G/warps $i/3 2>&1 | grep -E '^\[warp\]|Error|Traceback|Assertion' & done; wait
echo "[s146-cpu] DONE $(date -u +%FT%TZ)"
