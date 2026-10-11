#!/bin/bash
# S146 operational v1 (Amendment 3 / codex R267). Fail-closed. Namespace operational_v1.
set -euo pipefail
R=/mnt/gluster_dcpu/yiyangliu/gwm_s134; G=/mnt/gluster_dcpu/yiyangliu/gwm_s146; OP=$G/operational_v1; S=$R/src/s146; PY=$R/env/bin/python
while tmux has-session -t s145chain 2>/dev/null || tmux has-session -t s144chain 2>/dev/null; do sleep 60; done
# Supply remaining GPU-seconds from the existing S146 accounting; no fresh 24 h reset.
if [ "${S146_BUDGET_CHILD:-0}" != 1 ]; then
  exec "$PY" - "$0" "${S146_REMAINING_GPU_SECONDS:?remaining S146 GPU-seconds required}" <<'BUDGET_PY'
import math, os, signal, subprocess, sys
remaining = float(sys.argv[2])
if not math.isfinite(remaining) or not 0 < remaining <= 24 * 3600:
    raise SystemExit("invalid remaining GPU budget")
# Charge both reserved GPUs for the whole chain, including CPU/idle time.
child_env = dict(os.environ, S146_BUDGET_CHILD="1")
p = subprocess.Popen(["bash", sys.argv[1]], env=child_env, start_new_session=True)
try:
    try:
        code = p.wait(timeout=remaining / 2.0)
    except subprocess.TimeoutExpired:
        print("[s146op] INCOMPLETE: remaining GPU budget exhausted", flush=True)
        code = 124
finally:
    try:
        os.killpg(p.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(p.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    p.wait()
raise SystemExit(code)
BUDGET_PY
fi
mkdir "$OP" || { echo "[s146op] namespace exists or cannot be created"; exit 4; }
mkdir "$OP/logs"; sha256sum $S/*.py $S/*.sh $S/PROTOCOL.md > $OP/CODE_SHA256.txt
export RUN_ROOT=$R/src WEIGHTS=$R/weights XDG_CACHE_HOME=$R/cache MPLCONFIGDIR=$R/cache/mpl HF_HOME=$R/cache/hf PYTHONNOUSERSITE=1
echo "[s146op] start $(date -u +%FT%TZ)"; T0=$(date +%s)
# These must be the deployed files, not merely local mirror receipts.
"$PY" - "$S" "$R/src/vmem" <<'SOURCE_PY'
import hashlib, sys
from pathlib import Path
s, v = map(Path, sys.argv[1:])
expected = {
    s / "kps.py": "71528da426aff2f573968411e7f60d3d112e62eaeb33f2f29007c63e50b0345f",
    s / "s141_common.py": "459549706fb3a965fc4f7c5021f4d49cc626158e94a7c9cdc94cf8784cccb6cc",
    v / "modeling/pipeline.py": "680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255",
}
for path, want in expected.items():
    got = hashlib.sha256(path.read_bytes()).hexdigest()
    if got != want:
        raise SystemExit(f"execution source mismatch: {path}: {got}")
SOURCE_PY
# 1. observer parity on an exposed chess window (same GPU): plain original KPS vs observer module
for m in kps kps_orig_obs; do mkdir -p $OP/parity_$m
  CUDA_VISIBLE_DEVICES=3 CAPTURE_POLICY_STATE=1 KPS_MODULE=$m DATA_ROOT=$R/data/s139_stage ARM_OUT=$OP/parity_$m WINDOW_MANIFEST=$S/PARITY_MANIFEST_chess_w0.json INIT=kps POSE_CONVENTION=gl \
    $PY $S/run_retrieval_s146op.py 2>&1 | tee "$OP/logs/parity_$m.log" | awk '/s146op|records|Traceback|Error/ {print; fflush()}'; done
python3 - <<PY | tee $OP/PARITY.json
import json, math, sys
a = json.load(open('$OP/parity_kps/RETRIEVAL_RECEIPT.json'))['records'][0]; b = json.load(open('$OP/parity_kps_orig_obs/RETRIEVAL_RECEIPT.json'))['records'][0]
same = a['status'] == b['status'] == 'OK' and a['raw_contexts'] == b['raw_contexts'] and a['n_surfels'] == b['n_surfels'] and \
       len(a['kps_log']) == len(b['kps_log']) == 3 and all(l.get('kps') == 'OK' and math.isfinite(l['sigma']) and l['sigma'] > 0 for r in (a,b) for l in r['kps_log']) and \
       [l['sigma'] for l in a['kps_log']] == [l['sigma'] for l in b['kps_log']] and \
       bool(a.get('parity_state_sha256')) and a['parity_state_sha256'] == b.get('parity_state_sha256')
print(json.dumps({'parity': same, 'raw_plain': a['raw_contexts'], 'raw_observer': b['raw_contexts'], 'n_surfels': [a['n_surfels'], b['n_surfels']]}))
sys.exit(0 if same else 3)
PY
# 2. step A per room with the pinned policy
stepA() { mkdir -p $OP/stepA/$2; CUDA_VISIBLE_DEVICES=$1 KPS_MODULE=kps_orig_obs DATA_ROOT=$G/stage12 ARM_OUT=$OP/stepA/$2 WINDOW_MANIFEST=$G/manifests/WINDOW_MANIFEST_$2.json \
  INIT=kps POSE_CONVENTION=gl $PY $S/run_retrieval_s146op.py 2>&1 | tee "$OP/logs/stepA_$2.log" | awk '/s146op|records|Traceback|Error/ {print; fflush()}'; }
( stepA 3 apt1_kitchen; stepA 3 office2_5a ) & P1=$!; stepA 4 apt2_luke & P2=$!; wait $P1 || exit 7; wait $P2 || exit 7
# 3. global availability gate + pool
$PY $S/pool_op_s146.py $G/stage12 $G/manifests $OP/stepA $OP/POOL_OP.json || { echo "[s146op] OPERATIONAL_PANEL_UNAVAILABLE"; exit 5; }
$PY $S/build_plans_s146.py $OP/POOL_OP.json $OP
# 4. exposed generator replay
mkdir -p $OP/replay; CUDA_VISIBLE_DEVICES=3 VARIANT=A ADAPTER=NONE PLAN=$S/plan_s143_replay.json ARM_OUT=$OP/replay SEEDS=3 SHARD=0/1 \
  DATA_ROOT=$R/data/s139_stage WARP_DIR=/mnt/gluster_dcpu/yiyangliu/gwm_s143/warps $PY $S/gen_s141.py 2>&1 | tee "$OP/logs/replay.log" | awk '/^\[|Traceback|Error/ {print; fflush()}' 
K=$(python3 -c "import json; print(json.load(open('$S/plan_s143_replay.json'))['contexts'][0]['ctx_key'])")
[ "$(sha256sum $OP/replay/${K}__s3.npy | cut -d' ' -f1)" = "913394e0f8d25b5f179aaffbdd6ba3d9ac7ed21d8f86dd393bf9235ccaf111bb" ] || { echo "[s146op] REPLAY FAILED"; exit 3; }
# 5. evaluation-seed generation
gen() { local out=$OP/gen_part$2; mkdir -p $out; sha256sum $S/gen_s141.py $S/s141_common.py $OP/plan_s146_part$2.json > $out/CODE_SHA256.txt
  CUDA_VISIBLE_DEVICES=$1 VARIANT=A ADAPTER=NONE PLAN=$OP/plan_s146_part$2.json ARM_OUT=$out SEEDS=42,7,1,2 SHARD=0/1 DATA_ROOT=$G/stage12 WARP_DIR=$G/warps \
    timeout 10h $PY $S/gen_s141.py 2>&1 | tee "$OP/logs/gen_part$2.log" | awk '/^\[done\]|Traceback|Error|bad output/ {print; fflush()}'; }
gen 3 0 & P1=$!; gen 4 1 & P2=$!; wait $P1 || exit 6; wait $P2 || exit 6
for p in 0 1; do n=$(python3 -c "import json; print(4 * len(json.load(open('$OP/plan_s146_part$p.json'))['contexts']))")
  [ "$(ls $OP/gen_part$p | grep -cE '__s(42|7|1|2)\.npy$')" -eq "$n" ] || { echo "[s146op] part $p incomplete"; exit 6; }; done
# 6. seal before any target scoring
sha256sum -c "$OP/CODE_SHA256.txt"
"$PY" - "$OP" "$S" "$G" <<'SEAL_PY'
import hashlib, json, shutil, sys
from pathlib import Path
import numpy as np
op, source, data = map(Path, sys.argv[1:])
for part in (0, 1):
    plan = json.loads((op / f"plan_s146_part{part}.json").read_text())["contexts"]
    names = [f"{c['ctx_key']}__s{s}.npy" for c in plan for s in (42,7,1,2)]
    assert len(names) == len(set(names)), "duplicate planned output"
    assert all(len(c["ctx_refs"]) == len(c["target_refs"]) == 4 for c in plan)
    actual = {p.name for p in (op / f"gen_part{part}").glob("*.npy")}
    assert actual == set(names), ("output identity mismatch", part)
    for name in names:
        a = np.load(op / f"gen_part{part}" / name, mmap_mode="r", allow_pickle=False)
        assert a.shape == (4,3,576,576) and np.isfinite(a).all(), name
inputs = op / "sealed_input_receipts"
inputs.mkdir()
for path in [source / "PROTOCOL.md", source / "PARITY_MANIFEST_chess_w0.json",
             source / "plan_s143_replay.json", data / "METADATA_RECEIPT.json",
             data / "CONVENTION.json", data / "CONVENTION2.json",
             *sorted((data / "manifests").glob("WINDOW_MANIFEST_*.json"))]:
    shutil.copyfile(path, inputs / path.name)
def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""): h.update(block)
    return h.hexdigest()
paths = sorted(p for p in op.rglob("*") if p.is_file() and p.name != "SEAL_SHA256.txt")
(op / "SEAL_SHA256.txt").write_text("".join(f"{digest(p)}  {p.relative_to(op)}\n" for p in paths))
print("[s146op] complete prediction identities and all available namespace receipts sealed")
SEAL_PY
# 7. score + analysis
export OMP_NUM_THREADS=8
for p in 0 1; do $PY $S/score_gen_s146.py $OP/gen_part$p $G/stage12 $OP/plan_s146_part$p.json 42,7,1,2 $OP/SCORES_part$p.json; done
python3 -c "import json; a=json.load(open('$OP/SCORES_part0.json')); b=json.load(open('$OP/SCORES_part1.json')); assert not set(a['runs'])&set(b['runs']); json.dump({'runs': {**a['runs'], **b['runs']}}, open('$OP/GEN_SCORES.json','w'))"
$PY $S/analyze_s146.py op-primary $OP/POOL_OP.json $OP/GEN_SCORES.json $OP/S146_OP_PRIMARY.json
echo "[s146op] DONE $(date -u +%FT%TZ) elapsed_s $(( $(date +%s) - T0 ))"
