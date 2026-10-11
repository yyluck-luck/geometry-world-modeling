#!/bin/bash
# S147 Anchor-A on TACC gpu13 (GPUs 3/4 only), protocol work/S147_anchor_a/PROTOCOL.md. Fail-closed. Waits for S146.
# 0 dev prep (CPU) -> 1 engineering gate (gradients, frozen tensors, resume/schedule parity) -> 2 pilot timing -> 3 init fidelity
# -> 4 training (one process per GPU, two waves) -> 5 schedule + bypass fidelity -> 6 development generation, scoring, gate.
set -euo pipefail
R=/mnt/gluster_dcpu/yiyangliu/gwm_s134; G=/mnt/gluster_dcpu/yiyangliu/gwm_s147; G1=/mnt/gluster_dcpu/yiyangliu/gwm_s141
G4=/mnt/gluster_dcpu/yiyangliu/gwm_s144; S=$R/src/s147; PY=$R/env/bin/python
ADA=$G1/runs/A/adapter_final.pt; ADA_SHA=635e6e319d4dbf40d5db58d42498303c5f15fb32107f976e8c315d173de87818
while tmux has-session -t s146op 2>/dev/null; do sleep 60; done
[ "$(sha256sum $ADA | cut -d' ' -f1)" = "$ADA_SHA" ] || { echo "[s147] adapter A hash mismatch"; exit 3; }
mkdir "$G" || { echo "[s147] namespace exists"; exit 4; }
mkdir -p $G/logs $G/runs $G/eng $G/pilot $G/fid
sha256sum $S/*.py $S/*.json $S/*.sh $S/PROTOCOL.md $G1/clips_s141.json $R/src/vmem/modeling/pipeline.py $R/weights/vmem_weights.pth > $G/CODE_SHA256.txt
export RUN_ROOT=$R/src WEIGHTS=$R/weights XDG_CACHE_HOME=$R/cache MPLCONFIGDIR=$R/cache/mpl HF_HOME=$R/cache/hf PYTHONNOUSERSITE=1
$PY -c "import torch, sys; print('[s147] torch', torch.__version__, 'cuda', torch.version.cuda, 'python', sys.version.split()[0])" | tee $G/RUNTIME.txt
nvidia-smi --query-gpu=index,name,driver_version --format=csv,noheader | sed -n '4,5p' | tee -a $G/RUNTIME.txt
echo "[s147] start $(date -u +%FT%TZ)"; T0=$(date +%s)
train() { # <gpu> <arm> <out>   (extra env passes through)
  mkdir -p $3; OMP_NUM_THREADS=4 CUDA_VISIBLE_DEVICES=$1 $PY $S/train_s147.py $2 $G1/clips_s141.json $G1/lat $G1/warps $ADA $S/INVALID_GEOMETRY.json $3 \
    >> $3/stdout.log 2>&1 || { echo "[s147] training $2 ($3) failed"; tail -n 5 $3/stdout.log; return 1; }
  grep -E '^\[train\] (arm|DONE|resumed)' $3/stdout.log | cut -c1-220; }
gen() { # <gpu> <variant> <adapter> <branch> <plan> <out> <seeds> <data_root> <warp_dir>
  if [ -d $6 ] && ls $6/*.npy >/dev/null 2>&1; then echo "[s147] $6 not fresh"; return 4; fi
  mkdir -p $6; sha256sum $S/gen_s147.py $S/s141_common.py $5 $3 > $6/CODE_SHA256.txt
  OMP_NUM_THREADS=8 CUDA_VISIBLE_DEVICES=$1 VARIANT=$2 ADAPTER=$3 BRANCH=$4 PLAN=$5 ARM_OUT=$6 SEEDS=$7 SHARD=0/1 DATA_ROOT=$8 WARP_DIR=$9 \
    $PY $S/gen_s147.py > $6/stdout.log 2>&1 || { echo "[s147] gen $6 failed"; tail -n 5 $6/stdout.log; return 1; }; }
same() { [ "$(sha256sum $1 | cut -d' ' -f1)" = "$(sha256sum $2 | cut -d' ' -f1)" ]; }
DV=$G4/stage7; WDV=$G4/warps_monitor_cpu; PD=$G/prep

# 0. development preparation (CPU, source-only validity, COPY, fallback warps, BL_A0 coefficient) - before any training
OMP_NUM_THREADS=8 $PY $S/prep_dev_s147.py $S/plan_dev_s147.json $DV $WDV $G4/dev_A $PD | tail -n 2
sha256sum $PD/*.json | tee $G/PREP_SHA256.txt

# 1. engineering gate: (a) gradients / update / frozen tensors / allowlist, (b) checkpointed-vs-ordinary + finite difference
CUDA_VISIBLE_DEVICES=3 OMP_NUM_THREADS=8 $PY $S/eng_s147.py $G1/clips_s141.json $G1/lat $G1/warps $ADA $S/INVALID_GEOMETRY.json $G/eng/ENG.json \
  > $G/eng/eng.log 2>&1 || { echo "[s147] ENGINEERING GATE FAILED (INVALID_IMPLEMENTATION)"; tail -n 3 $G/eng/eng.log; exit 3; }
#    (c) resume and cross-arm schedule parity on a 5-clip list (one invalid clip, epoch boundary every 5 attempts), 12 attempts
EC=c00001,c00020,c00002,c00003,c00004
ENG_CLIPS=$EC STEPS=12 VAL_EVERY=100000 train 3 F_geo $G/eng/U & P1=$!
ENG_CLIPS=$EC STEPS=12 VAL_EVERY=100000 train 4 A_cont $G/eng/X & P2=$!; wait $P1; wait $P2
ENG_CLIPS=$EC STEPS=12 VAL_EVERY=100000 MAX_STEPS_THIS_RUN=7 SAVE_AT_EXIT=1 train 3 F_geo $G/eng/I
ENG_CLIPS=$EC STEPS=12 VAL_EVERY=100000 train 3 F_geo $G/eng/I
$PY - $G/eng <<'PY' | tee $G/eng/RESUME_PARITY.json
import json, sys, torch
E = sys.argv[1]
sch = lambda d: [{k: v for k, v in json.loads(l).items()} for l in open(f'{E}/{d}/schedule.jsonl')]
U, I, X = sch('U'), sch('I'), sch('X')
a = torch.load(f'{E}/U/adapter_final.pt', weights_only=False); b = torch.load(f'{E}/I/adapter_final.pt', weights_only=False)
wk = [k for k in a['adapter'] if '.warp.' in k]
num = sum(float((a['adapter'][k] - b['adapter'][k]).double().pow(2).sum()) for k in wk) ** 0.5; den = sum(float(a['adapter'][k].double().pow(2).sum()) for k in wk) ** 0.5
rel = num / den   # relative Frobenius difference; kernels may be non-deterministic, a broken resume gives O(1)
lora_same = all(torch.equal(a['adapter'][k], b['adapter'][k]) for k in a['adapter'] if k not in wk)
ok = U == I and [dict(r) for r in U] == [dict(r) for r in X] and len(U) == 12 and sum(r['skip'] for r in U) == 2 and rel <= 0.05 and lora_same
print(json.dumps({'schedule_U_eq_I': U == I, 'schedule_U_eq_X': U == X, 'n_attempts': len(U), 'n_skipped': sum(r['skip'] for r in U),
                  'warp_rel_frobenius_U_vs_I': rel, 'tolerance': 0.05, 'lora_identical': lora_same, 'PASS': ok}))
sys.exit(0 if ok else 3)
PY

# 2. timing pilot: one process per GPU, 60 attempts incl. load and the step-0 validation
STEPS=10000 MAX_STEPS_THIS_RUN=60 VAL_EVERY=100000 train 3 F_geo $G/pilot/F_geo & P1=$!
STEPS=10000 MAX_STEPS_THIS_RUN=60 VAL_EVERY=100000 train 4 J_geo $G/pilot/J_geo & P2=$!; wait $P1; wait $P2
$PY - $G <<'PY' | tee $G/PILOT.json
import json, statistics, sys, os
G = sys.argv[1]; out = {}
for a in ('F_geo', 'J_geo'):
    r = [json.loads(l) for l in open(f'{G}/pilot/{a}/train_log.jsonl')]
    sps = statistics.median(x['sec_per_step'] for x in r if 'sec_per_step' in x and x['step'] > 20)
    out[a] = {'sec_per_attempt': sps, 'val_seconds': next(x['val_seconds'] for x in r if x['step'] == 0), 'max_mem_gb': max(x['max_mem_gb'] for x in r if 'max_mem_gb' in x)}
s = max(v['sec_per_attempt'] for v in out.values()); v = max(x['val_seconds'] for x in out.values())
per_run_h = (300 + 10000 * s + 6 * v + 20 * 30) / 3600      # startup, attempts, validations (0, 2000, ..., 10000), checkpoint saves
proj = 2 * (2 * per_run_h)                                    # two waves on two GPUs, physical GPU-hours
out.update({'per_run_hours': per_run_h, 'projected_training_gpu_h': proj, 'fits_20_gpu_h': proj <= 20.0})
print(json.dumps(out)); sys.exit(0 if out['fits_20_gpu_h'] else 6)
PY

# 3. init fidelity: every step-0 adapter and A itself reproduce the archived S144 ordinary-A output (c02000, seed 3)
K=c02000; REF=$G4/dev_A/${K}__s3.npy
gen 3 A $ADA orig $S/plan_replay_s147.json $G/fid/A_replay 3 $DV $WDV & P1=$!
gen 4 B $G/pilot/F_geo/adapter_000000.pt orig $S/plan_replay_s147.json $G/fid/F_geo_init 3 $DV $WDV & P2=$!; wait $P1; wait $P2
gen 3 B $G/pilot/F_geo/adapter_000000.pt null $S/plan_replay_s147.json $G/fid/F_null_init 3 $DV $WDV & P1=$!
gen 4 B $G/pilot/J_geo/adapter_000000.pt orig $S/plan_replay_s147.json $G/fid/J_geo_init 3 $DV $WDV & P2=$!; wait $P1; wait $P2
gen 3 A $G/eng/X/adapter_000000.pt orig $S/plan_replay_s147.json $G/fid/A_cont_init 3 $DV $WDV
for d in A_replay F_geo_init F_null_init J_geo_init A_cont_init; do
  same $G/fid/$d/${K}__s3.npy $REF || { echo "[s147] FIDELITY FAILED: $d (INVALID_IMPLEMENTATION)"; exit 3; }; done
echo "[s147] init fidelity + replay pass $(sha256sum $REF | cut -c1-16)" | tee $G/FIDELITY.txt

# 4. training: one process per GPU, two waves (F_geo | F_null), then (J_geo | A_cont); resume-safe
VAL_EVERY=2000 train 3 F_geo $G/runs/F_geo & P1=$!; VAL_EVERY=2000 train 4 F_null $G/runs/F_null & P2=$!; wait $P1; wait $P2
VAL_EVERY=2000 train 3 J_geo $G/runs/J_geo & P1=$!; VAL_EVERY=2000 train 4 A_cont $G/runs/A_cont & P2=$!; wait $P1; wait $P2
for a in F_geo F_null J_geo A_cont; do [ -f $G/runs/$a/adapter_final.pt ] || { echo "[s147] $a has no final adapter"; exit 5; }; done
sha256sum $G/runs/*/adapter_final.pt | tee $G/ADAPTERS_SHA256.txt
$PY - $G <<'PY' | tee $G/SCHEDULE_CHECK.json
import json, sys
G = sys.argv[1]
def sch(a):
    d = {}
    for l in open(f'{G}/runs/{a}/schedule.jsonl'): r = json.loads(l); d[r['step']] = r      # a resumed run may repeat steps: last wins
    return [d[k] for k in sorted(d)]
S = {a: sch(a) for a in ('F_geo', 'F_null', 'J_geo', 'A_cont')}
ok = all(len(v) == 10000 for v in S.values()) and all(S[a] == S['F_geo'] for a in S) and sum(r['skip'] for r in S['F_geo']) == 230
print(json.dumps({'attempts': {a: len(v) for a, v in S.items()}, 'identical': all(S[a] == S['F_geo'] for a in S),
                  'skipped': sum(r['skip'] for r in S['F_geo']), 'valid_updates': 10000 - sum(r['skip'] for r in S['F_geo']), 'PASS': ok}))
sys.exit(0 if ok else 3)
PY

# 5. bypass fidelity: both trained F arms with the true bypass reproduce A
gen 3 B $G/runs/F_geo/adapter_final.pt off $S/plan_replay_s147.json $G/fid/F_geo_off 3 $DV $WDV & P1=$!
gen 4 B $G/runs/F_null/adapter_final.pt off $S/plan_replay_s147.json $G/fid/F_null_off 3 $DV $WDV & P2=$!; wait $P1; wait $P2
for d in F_geo_off F_null_off; do same $G/fid/$d/${K}__s3.npy $REF || { echo "[s147] BYPASS FIDELITY FAILED: $d"; exit 3; }; done
echo "[s147] bypass fidelity pass" | tee -a $G/FIDELITY.txt

# 6. development: 32 monitor clips x seeds 3,4; six generated arms; fallback V for invalid packages
PG=$PD/plan_dev_s147_gen.json
( gen 3 B $G/runs/F_geo/adapter_final.pt orig $PG $G/dev/F_geo 3,4 $DV $WDV && gen 3 B $G/runs/J_geo/adapter_final.pt orig $PG $G/dev/J_geo 3,4 $DV $WDV && \
  gen 3 B $G/runs/F_geo/adapter_final.pt permuted $PG $G/dev/F_geo_perm 3,4 $DV $WDV ) & P1=$!
( gen 4 B $G/runs/F_null/adapter_final.pt null $PG $G/dev/F_null 3,4 $DV $WDV && gen 4 A $G/runs/A_cont/adapter_final.pt orig $PG $G/dev/A_cont 3,4 $DV $WDV && \
  gen 4 B $G/runs/F_geo/adapter_final.pt null $PG $G/dev/F_geo_proto 3,4 $DV $WDV && \
  gen 4 A $ADA orig $PD/plan_dev_fallback_vae.json $G/dev/fallback_V 0 $DV $PD/fallback_warps ) & P2=$!
wait $P1; wait $P2
for a in F_geo F_null J_geo A_cont F_geo_perm F_geo_proto; do [ "$(ls $G/dev/$a | grep -cE '__s[34]\.npy$')" -eq 64 ] || { echo "[s147] dev $a incomplete"; exit 5; }; done
OMP_NUM_THREADS=8 $PY $S/score_s147.py $DV $PG $WDV $PD $G/dev/fallback_V $G4/dev_F $G4/dev_A $G4/ALPHA.json $G/SCORES_dev.json \
  F_geo=$G/dev/F_geo F_null=$G/dev/F_null J_geo=$G/dev/J_geo A_cont=$G/dev/A_cont F_geo_proto=$G/dev/F_geo_proto F_geo_perm=$G/dev/F_geo_perm | tail -n 1
$PY $S/analyze_s147.py $G/SCORES_dev.json $G4/SCORES_dev.json $G/DEV_GATE.json
if python3 -c "import json,sys; sys.exit(0 if json.load(open('$G/DEV_GATE.json'))['GATE']['GO'] else 1)"; then
  touch $G/GO_CONFIRMATION_PENDING; echo "[s147] development GO: confirmation needs the office1 intake (separate step, per protocol)"
else touch $G/STOPPED_AT_DEV_GATE; echo "[s147] development GO not reached: S147 stops after the development report (frozen rule)"; fi
echo "[s147] DONE $(date -u +%FT%TZ) elapsed_s $(( $(date +%s) - T0 ))"
