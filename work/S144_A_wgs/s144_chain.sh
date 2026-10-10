#!/bin/bash
# S144 orchestrator on gpu13 (GPU 3 = frozen F, GPU 4 = adapter A). Waits for S143 confirmation to finish.
# replay gate -> development (seeds 3,4) -> alpha fit -> dev gate (+ timing projection vs 12 GPU-h) -> cases if GO.
set -euo pipefail
R=/mnt/gluster_dcpu/yiyangliu/gwm_s134; G=/mnt/gluster_dcpu/yiyangliu/gwm_s144; S=$R/src/s144; PY=$R/env/bin/python
ADA=/mnt/gluster_dcpu/yiyangliu/gwm_s141/runs/A/adapter_final.pt; ADA_SHA=635e6e319d4dbf40d5db58d42498303c5f15fb32107f976e8c315d173de87818
while tmux has-session -t s143c0 2>/dev/null || tmux has-session -t s143c1 2>/dev/null; do sleep 60; done
[ "$(sha256sum $ADA | cut -d' ' -f1)" = "$ADA_SHA" ] || { echo "[s144] adapter A hash mismatch"; exit 3; }
export RUN_ROOT=$R/src WEIGHTS=$R/weights XDG_CACHE_HOME=$R/cache MPLCONFIGDIR=$R/cache/mpl HF_HOME=$R/cache/hf PYTHONNOUSERSITE=1
gen() { # <gpu> <variant-adapter F|A> <plan> <out> <seeds> <data_root> <warp_dir>
  local ad=NONE; [ "$2" = A ] && ad=$ADA
  mkdir -p $4; sha256sum $S/*.py $3 > $4/CODE_SHA256_$(date -u +%H%M%S).txt
  CUDA_VISIBLE_DEVICES=$1 VARIANT=A ADAPTER=$ad PLAN=$3 ARM_OUT=$4 SEEDS=$5 SHARD=0/1 DATA_ROOT=$6 WARP_DIR=$7 \
    $PY $S/gen_s144.py 2>&1 | grep --line-buffered -E '^\[|Traceback|Error|bad output|Assertion'; }
fresh() { if [ -d $1 ] && ls $1/*.npy >/dev/null 2>&1; then echo "[s144] $1 not fresh"; exit 4; fi; }
CH=$R/data/s139_stage; CHS=$R/data/s139_datasets; WCH=$R/data/S140_warps_chess
RG=$R/data/stage; RGS=$R/data/datasets; WRG=$R/data/S140_warps_dev; DV=$G/stage7; WDV=$G/warps_monitor_cpu
echo "[s144] start $(date -u +%FT%TZ)"
# 1. replay: new F_C on chess window 0 seed 3 == archived S140 W2 output
fresh $G/replay; gen 3 F $S/plan_replay.json $G/replay 3 $CH $WCH
K=$(python3 -c "import json; print(json.load(open('$S/plan_replay.json'))['contexts'][0]['ctx_key'])")
A_SHA=$(sha256sum $R/out/s140_confirm_tacc/gen/seq-02_from_seq-01_s0150__gl__W2_0.5__s3.npy | cut -d' ' -f1)
N_SHA=$(sha256sum $G/replay/${K}__C__s3.npy | cut -d' ' -f1)
echo "$A_SHA archived_S140_W2  $N_SHA new_F_C" | tee $G/REPLAY_SHA256.txt
[ "$A_SHA" = "$N_SHA" ] || { echo "[s144] REPLAY FAILED (blocked assay)"; exit 3; }
# 2. development
[ "$(ls $WDV/*.npz | wc -l)" -eq 128 ] || { echo "[s144] monitor warps incomplete"; exit 5; }
fresh $G/dev_F; fresh $G/dev_A; T0=$(date +%s)
gen 3 F $S/plan_dev_F.json $G/dev_F 3,4 $DV $WDV & P1=$!; gen 4 A $S/plan_dev_A.json $G/dev_A 3,4 $DV $WDV & P2=$!; wait $P1; wait $P2
T1=$(date +%s)
[ "$(ls $G/dev_F | grep -c '__[CR]__s[34]\.npy$')" -eq 128 ] && [ "$(ls $G/dev_F | grep -c '__V__s0\.npy$')" -eq 32 ] \
  && [ "$(ls $G/dev_A | grep -c '__[CR]__s[34]\.npy$')" -eq 128 ] && [ "$(ls $G/dev_A | grep -cE '^c[0-9]+__s[34]\.npy$')" -eq 64 ] || { echo "[s144] dev incomplete"; exit 5; }
OMP_NUM_THREADS=8 $PY $S/score_s144.py $G/dev_F $G/dev_A $DV $S/plan_dev_F.json $WDV 3,4 FIT $G/SCORES_dev_fit.json | tail -n 1
$PY $S/analyze_s144.py dev-fit $G/SCORES_dev_fit.json $G/ALPHA.json
OMP_NUM_THREADS=8 $PY $S/score_s144.py $G/dev_F $G/dev_A $DV $S/plan_dev_F.json $WDV 3,4 $G/ALPHA.json $G/SCORES_dev.json | tail -n 1
$PY $S/analyze_s144.py dev-gate $G/SCORES_dev.json $G/DEV_GATE.json
# timing projection: dev wall time on 2 GPUs covered 64 W2CR cells per GPU (+vae / +64 none on A); case = 160 W2CR cells per GPU
python3 - <<PY | tee $G/TIMING.json
import json; dt=$T1-$T0; per_cell=dt/ (64+32)   # conservative: A side had 64 W2CR + 64 none (none ~2x W2CR)
case_gpu_h = 2 * 160 * per_cell / 3600
print(json.dumps({'dev_wall_s': dt, 'est_s_per_W2CR_cell': per_cell, 'case_projected_gpu_h': case_gpu_h, 'dev_gpu_h': 2*dt/3600,
                  'fits_cap_12': 2*dt/3600 + case_gpu_h <= 12}))
PY
python3 -c "import json,sys; sys.exit(0 if json.load(open('$G/TIMING.json'))['fits_cap_12'] else 1)" || { echo "[s144] projected over the 12 GPU-h cap: stop before cases"; exit 6; }
python3 -c "import json,sys; sys.exit(0 if json.load(open('$G/DEV_GATE.json'))['PERFORMANCE_GO'] else 1)" || { echo "[s144] PERFORMANCE GO failed: S144 stops (frozen rule)"; touch $G/STOPPED_AT_DEV_GATE; exit 0; }
# 3. case panels
for P in chess rgbd; do
  if [ $P = chess ]; then D=$CH; W=$WCH; DS=$CHS; else D=$RG; W=$WRG; DS=$RGS; fi
  fresh $G/${P}_F; fresh $G/${P}_A
  gen 3 F $S/plan_${P}_F.json $G/${P}_F 3,4,5,6 $D $W & P1=$!; gen 4 A $S/plan_${P}_A.json $G/${P}_A 3,4,5,6 $D $W & P2=$!; wait $P1; wait $P2
  OMP_NUM_THREADS=8 $PY $S/score_s144.py $G/${P}_F $G/${P}_A $DS $S/plan_${P}_F.json $W 3,4,5,6 $G/ALPHA.json $G/SCORES_${P}.json | tail -n 1
done
$PY $S/analyze_s144.py case $G/SCORES_chess.json $G/SCORES_rgbd.json $S/POSE_ARMS.json $G/S144_ANALYSIS.json
echo "[s144] DONE $(date -u +%FT%TZ)"
