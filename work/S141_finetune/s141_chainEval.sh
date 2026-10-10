#!/bin/bash
# S141 evaluation chain on gpu13 (hardened after codex R254). usage: s141_chainEval.sh <gpu> <A|B>
# gates: fidelity receipt (base == A == B bytes) -> final adapter verified (step 10000, finite) -> fresh output dirs.
# A: chess (A_static, A_mem) -> RGB-D A_static.  B: chess B_mem -> chess B_static (exploratory, Amendment 1) -> RGB-D B_static.
# Every generation pass must produce exactly (contexts x 4) outputs; every score file must contain them all.
set -euo pipefail
GPU=$1; V=$2; R=/mnt/gluster_dcpu/yiyangliu/gwm_s134; G=/mnt/gluster_dcpu/yiyangliu/gwm_s141; S=$R/src/s141; PY=$R/env/bin/python
FID=$G/fid/FIDELITY_SHA256.txt
[ "$(awk '{print $1}' $FID | sort -u | wc -l)" -eq 1 ] && [ "$(wc -l < $FID)" -eq 3 ] || { echo "[eval$V] FIDELITY GATE FAILED"; exit 3; }
echo "[eval$V] fidelity gate OK: $(awk '{print $1}' $FID | sort -u)"
AD=$G/runs/$V/adapter_final.pt
until [ -f $AD ] && grep -q '"step": 10000, "val"' $G/runs/$V/train_log.jsonl 2>/dev/null; do sleep 120; done
sleep 30   # adapter_final.pt is written after the step-10000 validation record; let the write finish
ok=0; for i in $(seq 10); do   # retry: the file may still be being written
  if $PY $S/check_adapter_s141.py $AD $V 10000 > $G/eval/ADAPTER_CHECK_$V.txt 2>&1; then ok=1; break; fi; sleep 30; done
cat $G/eval/ADAPTER_CHECK_$V.txt; [ $ok = 1 ] || { echo "[eval$V] ADAPTER CHECK FAILED"; exit 7; }
run() {  # <plan> <out_dir> <data_root> <warp_dir> <data_for_scoring> <warp_for_scoring> <score_json>
  local plan=$1 out=$2 n
  if [ -d $out ] && ls $out/*.npy >/dev/null 2>&1; then echo "[eval$V] $out not fresh"; exit 4; fi
  DATA_ROOT_OVR=$3 WARP_DIR_OVR=$4 bash $S/tacc_s141.sh $GPU gen $V $plan $AD $out 3,4,5,6 2>&1 | grep --line-buffered -E '^\[|Traceback|Error'
  n=$(python3 -c "import json; print(4 * len(json.load(open('$plan'))['contexts']))")
  [ "$(ls $out | grep -c '__s[3-6]\.npy$')" -eq "$n" ] || { echo "[eval$V] $out incomplete"; exit 5; }
  OMP_NUM_THREADS=8 $PY $R/src/s140/score_s140.py $out $5 $plan $6 $7
  python3 -c "import json,sys; r=json.load(open('$7'))['runs']; sys.exit(0 if len(r)==$n else 1)" || { echo "[eval$V] $7 incomplete"; exit 6; }
  echo "[eval$V] $(basename $plan) generated+scored $n $(date -u +%FT%TZ)"
}
CH=$R/data/s139_stage; CHS=$R/data/s139_datasets; RG=$R/data/stage; RGS=$R/data/datasets
if [ "$V" = A ]; then
  run $S/plan_eval_A.json $G/eval/chess_A $CH $R/data/S140_warps_chess $CHS $R/data/S140_warps_chess $G/eval/SCORES_chess_A.json
  run $S/plan_rgbd_A.json $G/eval/rgbd_A $RG $R/data/S140_warps_dev $RGS $R/data/S140_warps_dev $G/eval/SCORES_rgbd_A.json
else
  run $S/plan_eval_B.json $G/eval/chess_B $CH $R/data/S140_warps_chess $CHS $R/data/S140_warps_chess $G/eval/SCORES_chess_B.json
  run $S/plan_eval_Bstatic.json $G/eval/chess_Bstatic $CH $R/data/S141_warps_chess_static $CHS $R/data/S141_warps_chess_static $G/eval/SCORES_chess_Bstatic.json
  run $S/plan_rgbd_B.json $G/eval/rgbd_B $RG $R/data/S140_warps_dev $RGS $R/data/S140_warps_dev $G/eval/SCORES_rgbd_B.json
fi
echo "[eval$V] DONE $(date -u +%FT%TZ)"
