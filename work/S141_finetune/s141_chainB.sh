#!/bin/bash
# S141 chain on gpu13 GPU 4: wait for all 2032 warps -> fidelity gate (A and B, zero-init adapters, seed 3) -> train B.
R=/mnt/gluster_dcpu/yiyangliu/gwm_s134; G=/mnt/gluster_dcpu/yiyangliu/gwm_s141; S=$R/src/s141
until [ "$(ls $G/warps | grep -c '\.pt$')" -ge 2032 ] && ! tmux ls 2>/dev/null | grep -q s141w; do sleep 60; done
echo "[chain] warps complete $(date -u +%FT%TZ): $(ls $G/warps | grep -c '\.pt$')"
for V in A B; do
  bash $S/tacc_s141.sh 4 gen $V $S/plan_fid_$V.json NONE $G/fid/$V 3 2>&1 | grep --line-buffered -E '^\[|Traceback|Error'
done
K=$(python3 -c "import json; print(json.load(open('$S/plan_fid_A.json'))['contexts'][0]['ctx_key'])")
sha256sum $R/out/s139_tacc/gen/${K}__s3.npy $G/fid/A/${K}__s3.npy $G/fid/B/${K}__s3.npy | tee $G/fid/FIDELITY_SHA256.txt
STEPS=10000 bash $S/tacc_s141.sh 4 train B $G/runs/B 2>&1 | grep --line-buffered -vE 'INFO|DEBUG'
