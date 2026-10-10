#!/bin/bash
# S146 GPU chain on gpu13 (after S145 and the CPU preparation). Fail-closed; see PROTOCOL.md / R265.
set -euo pipefail
R=/mnt/gluster_dcpu/yiyangliu/gwm_s134; G=/mnt/gluster_dcpu/yiyangliu/gwm_s146; S=$R/src/s146; PY=$R/env/bin/python
while tmux has-session -t s145chain 2>/dev/null || tmux has-session -t s144chain 2>/dev/null || tmux has-session -t s146cpu 2>/dev/null; do sleep 60; done
grep -q "\[s146-cpu\] DONE" $G/logs/cpu_prep.log || { echo "[s146] CPU preparation did not finish"; exit 3; }
export RUN_ROOT=$R/src WEIGHTS=$R/weights XDG_CACHE_HOME=$R/cache MPLCONFIGDIR=$R/cache/mpl HF_HOME=$R/cache/hf PYTHONNOUSERSITE=1
conv() { python3 -c "import json; print({r['room']: r['winner'] for r in json.load(open('$G/CONVENTION.json'))['rows']}['$1'])"; }
stepA() { # <gpu> <room>
  local out=$G/stepA/$2; [ -d $out ] && ls $out/*/WINDOW_RECEIPT.json >/dev/null 2>&1 && { echo "[s146] stepA $2 not fresh"; exit 4; }
  mkdir -p $out; CUDA_VISIBLE_DEVICES=$1 DATA_ROOT=$G/stage12 ARM_OUT=$out WINDOW_MANIFEST=$G/manifests/WINDOW_MANIFEST_$2.json INIT=kps \
    POSE_CONVENTION=$(conv $2) $PY $S/run_retrieval_s139.py 2>&1 | grep --line-buffered -E 's139A|records|Traceback|Error' ; }
echo "[s146] start $(date -u +%FT%TZ)"; T0=$(date +%s)
( stepA 3 apt1_kitchen; stepA 3 office2_5a ) & P1=$!; stepA 4 apt2_luke & P2=$!; wait $P1; wait $P2
for r in apt1_kitchen apt2_luke office2_5a; do
  python3 -c "import json,sys; d=json.load(open('$G/stepA/$r/RETRIEVAL_RECEIPT.json')); sys.exit(0 if d['blocked_records']==0 and len(d['records'])==8 else 1)" || { echo "[s146] stepA $r blocked"; exit 5; }
done
$PY $S/build_pool_s146.py 2 $G/POOL_phase1.json $G/stepA $G/POOL.json
OMP_NUM_THREADS=6 CUDA_VISIBLE_DEVICES= ; for i in 0 1 2; do CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=6 $PY $S/warps_s146.py $G/stage12 $G/POOL.json $G/warps $i/3 2>&1 | grep -E '^\[warp\]|Error|Traceback|Assertion' & done; wait
$PY $S/build_plans_s146.py $G/POOL.json $S
# replay of an archived exposed cell (S139 chess mem_vmem window 0 seed 3)
mkdir -p $G/replay; CUDA_VISIBLE_DEVICES=3 VARIANT=A ADAPTER=NONE PLAN=$S/plan_s143_replay.json ARM_OUT=$G/replay SEEDS=3 SHARD=0/1 \
  DATA_ROOT=$R/data/s139_stage WARP_DIR=/mnt/gluster_dcpu/yiyangliu/gwm_s143/warps $PY $S/gen_s141.py 2>&1 | grep --line-buffered -E '^\[|Traceback|Error'
K=$(python3 -c "import json; print(json.load(open('$S/plan_s143_replay.json'))['contexts'][0]['ctx_key'])")
[ "$(sha256sum $G/replay/${K}__s3.npy | cut -d' ' -f1)" = "913394e0f8d25b5f179aaffbdd6ba3d9ac7ed21d8f86dd393bf9235ccaf111bb" ] || { echo "[s146] REPLAY FAILED"; exit 3; }
echo "[s146] replay OK"
gen() { # <gpu> <part>
  local out=$G/gen_part$2; [ -d $out ] && ls $out/*.npy >/dev/null 2>&1 && { echo "[s146] $out not fresh"; exit 4; }
  mkdir -p $out; sha256sum $S/*.py $S/plan_s146_part$2.json > $out/CODE_SHA256.txt
  CUDA_VISIBLE_DEVICES=$1 VARIANT=A ADAPTER=NONE PLAN=$S/plan_s146_part$2.json ARM_OUT=$out SEEDS=3,4,5,6,42,7,1,2 SHARD=0/1 \
    DATA_ROOT=$G/stage12 WARP_DIR=$G/warps timeout 12h $PY $S/gen_s141.py 2>&1 | grep --line-buffered -E '^\[done\]|Traceback|Error|bad output' ; }
gen 3 0 & P1=$!; gen 4 1 & P2=$!; wait $P1; wait $P2
for p in 0 1; do n=$(python3 -c "import json; print(8 * len(json.load(open('$S/plan_s146_part$p.json'))['contexts']))")
  [ "$(ls $G/gen_part$p | grep -cE '__s(3|4|5|6|42|7|1|2)\.npy$')" -eq "$n" ] || { echo "[s146] part $p incomplete (budget-truncated or failure)"; exit 6; }; done
# seal before any target scoring
( cd $G && sha256sum gen_part0/*.npy gen_part1/*.npy warps/*.npz POOL.json stepA/*/RETRIEVAL_RECEIPT.json > SEAL_SHA256.txt ); echo "[s146] sealed $(wc -l < $G/SEAL_SHA256.txt) files $(date -u +%FT%TZ)"
export OMP_NUM_THREADS=8
for p in 0 1; do $PY $R/src/s140/score_s140.py $G/gen_part$p $G/stage12 $S/plan_s146_part$p.json $G/warps $G/SCORES_part$p.json; done
python3 -c "import json; a=json.load(open('$G/SCORES_part0.json')); b=json.load(open('$G/SCORES_part1.json')); json.dump({'runs': {**a['runs'], **b['runs']}}, open('$G/GEN_SCORES.json','w'))"
$PY $S/score_warps_s146.py $G/stage12 $G/POOL.json $G/warps $G/WARP_SCORES.json | tail -n 1
$PY $S/analyze_s146.py primary $G/POOL.json $G/GEN_SCORES.json $G/S146_PRIMARY.json
$PY $S/analyze_s146.py seal $G/POOL.json $G/WARP_SCORES.json $G/GEN_SCORES.json $G/FROZEN_DISCOVERY.json
$PY $S/analyze_s146.py evaluate $G/POOL.json $G/FROZEN_DISCOVERY.json $G/GEN_SCORES.json $G/S146_EVALUATE.json
$PY $S/analyze_s146.py prep143 $G/POOL.json $G/WARP_SCORES.json $G/GEN_SCORES.json $G/a143
$PY $S/analyze_s143.py $G/a143/POOL143.json $G/a143/WARPS143.json $G/a143/GEN143.json $G/a143/PAIRS143.json $G/S146_DISCOVERY_R.json 100000 | tail -n 3
echo "[s146] DONE $(date -u +%FT%TZ) elapsed_s $(( $(date +%s) - T0 ))"
