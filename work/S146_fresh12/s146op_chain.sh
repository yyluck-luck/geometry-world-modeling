#!/bin/bash
# S146 operational v1 (Amendment 3 / codex R267). Fail-closed. Namespace operational_v1.
set -euo pipefail
R=/mnt/gluster_dcpu/yiyangliu/gwm_s134; G=/mnt/gluster_dcpu/yiyangliu/gwm_s146; OP=$G/operational_v1; S=$R/src/s146; PY=$R/env/bin/python
while tmux has-session -t s145chain 2>/dev/null || tmux has-session -t s144chain 2>/dev/null; do sleep 60; done
[ -d $OP ] && ls $OP/*.json >/dev/null 2>&1 && { echo "[s146op] namespace not fresh"; exit 4; }
mkdir -p $OP/logs; sha256sum $S/*.py $S/*.sh $S/PROTOCOL.md > $OP/CODE_SHA256.txt
export RUN_ROOT=$R/src WEIGHTS=$R/weights XDG_CACHE_HOME=$R/cache MPLCONFIGDIR=$R/cache/mpl HF_HOME=$R/cache/hf PYTHONNOUSERSITE=1
echo "[s146op] start $(date -u +%FT%TZ)"; T0=$(date +%s)
# 1. observer parity on an exposed chess window (same GPU): plain original KPS vs observer module
for m in kps kps_orig_obs; do mkdir -p $OP/parity_$m
  CUDA_VISIBLE_DEVICES=3 KPS_MODULE=$m DATA_ROOT=$R/data/s139_stage ARM_OUT=$OP/parity_$m WINDOW_MANIFEST=$S/PARITY_MANIFEST_chess_w0.json INIT=kps POSE_CONVENTION=gl \
    $PY $S/run_retrieval_s146op.py 2>&1 | grep --line-buffered -E 's146op|records|Traceback|Error'; done
python3 - <<PY | tee $OP/PARITY.json
import json, sys
a = json.load(open('$OP/parity_kps/RETRIEVAL_RECEIPT.json'))['records'][0]; b = json.load(open('$OP/parity_kps_orig_obs/RETRIEVAL_RECEIPT.json'))['records'][0]
same = a['status'] == b['status'] == 'OK' and a['raw_contexts'] == b['raw_contexts'] and a['n_surfels'] == b['n_surfels'] and \
       [round(l['sigma'], 12) for l in a['kps_log']] == [round(l['sigma'], 12) for l in b['kps_log']]
print(json.dumps({'parity': same, 'raw_plain': a['raw_contexts'], 'raw_observer': b['raw_contexts'], 'n_surfels': [a['n_surfels'], b['n_surfels']]}))
sys.exit(0 if same else 3)
PY
# 2. step A per room with the pinned policy
stepA() { mkdir -p $OP/stepA/$2; CUDA_VISIBLE_DEVICES=$1 KPS_MODULE=kps_orig_obs DATA_ROOT=$G/stage12 ARM_OUT=$OP/stepA/$2 WINDOW_MANIFEST=$G/manifests/WINDOW_MANIFEST_$2.json \
  INIT=kps POSE_CONVENTION=gl $PY $S/run_retrieval_s146op.py 2>&1 | grep --line-buffered -E 's146op|records|Traceback|Error'; }
( stepA 3 apt1_kitchen; stepA 3 office2_5a ) & P1=$!; stepA 4 apt2_luke & P2=$!; wait $P1 || exit 7; wait $P2 || exit 7
# 3. global availability gate + pool
$PY $S/pool_op_s146.py $G/stage12 $G/manifests $OP/stepA $OP/POOL_OP.json || { echo "[s146op] OPERATIONAL_PANEL_UNAVAILABLE"; exit 5; }
$PY $S/build_plans_s146.py $OP/POOL_OP.json $OP
# 4. exposed generator replay
mkdir -p $OP/replay; CUDA_VISIBLE_DEVICES=3 VARIANT=A ADAPTER=NONE PLAN=$S/plan_s143_replay.json ARM_OUT=$OP/replay SEEDS=3 SHARD=0/1 \
  DATA_ROOT=$R/data/s139_stage WARP_DIR=/mnt/gluster_dcpu/yiyangliu/gwm_s143/warps $PY $S/gen_s141.py 2>&1 | grep --line-buffered -E '^\[|Traceback|Error'
K=$(python3 -c "import json; print(json.load(open('$S/plan_s143_replay.json'))['contexts'][0]['ctx_key'])")
[ "$(sha256sum $OP/replay/${K}__s3.npy | cut -d' ' -f1)" = "913394e0f8d25b5f179aaffbdd6ba3d9ac7ed21d8f86dd393bf9235ccaf111bb" ] || { echo "[s146op] REPLAY FAILED"; exit 3; }
# 5. evaluation-seed generation
gen() { local out=$OP/gen_part$2; mkdir -p $out; sha256sum $S/gen_s141.py $S/s141_common.py $OP/plan_s146_part$2.json > $out/CODE_SHA256.txt
  CUDA_VISIBLE_DEVICES=$1 VARIANT=A ADAPTER=NONE PLAN=$OP/plan_s146_part$2.json ARM_OUT=$out SEEDS=42,7,1,2 SHARD=0/1 DATA_ROOT=$G/stage12 WARP_DIR=$G/warps \
    timeout 10h $PY $S/gen_s141.py 2>&1 | grep --line-buffered -E '^\[done\]|Traceback|Error|bad output'; }
gen 3 0 & P1=$!; gen 4 1 & P2=$!; wait $P1 || exit 6; wait $P2 || exit 6
for p in 0 1; do n=$(python3 -c "import json; print(4 * len(json.load(open('$OP/plan_s146_part$p.json'))['contexts']))")
  [ "$(ls $OP/gen_part$p | grep -cE '__s(42|7|1|2)\.npy$')" -eq "$n" ] || { echo "[s146op] part $p incomplete"; exit 6; }; done
# 6. seal before any target scoring
( cd $OP && sha256sum gen_part0/*.npy gen_part1/*.npy POOL_OP.json stepA/*/RETRIEVAL_RECEIPT.json plan_s146_part*.json > SEAL_SHA256.txt ); echo "[s146op] sealed $(wc -l < $OP/SEAL_SHA256.txt) $(date -u +%FT%TZ)"
# 7. score + analysis
export OMP_NUM_THREADS=8
for p in 0 1; do $PY $S/score_gen_s146.py $OP/gen_part$p $G/stage12 $OP/plan_s146_part$p.json 42,7,1,2 $OP/SCORES_part$p.json; done
python3 -c "import json; a=json.load(open('$OP/SCORES_part0.json')); b=json.load(open('$OP/SCORES_part1.json')); assert not set(a['runs'])&set(b['runs']); json.dump({'runs': {**a['runs'], **b['runs']}}, open('$OP/GEN_SCORES.json','w'))"
$PY $S/analyze_s146.py op-primary $OP/POOL_OP.json $OP/GEN_SCORES.json $OP/S146_OP_PRIMARY.json
echo "[s146op] DONE $(date -u +%FT%TZ) elapsed_s $(( $(date +%s) - T0 ))"
