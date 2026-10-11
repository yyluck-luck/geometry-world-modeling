#!/bin/bash
# S147 frozen-input manifest (R274 #6), built BEFORE launch, cross-checked locally against independent records, committed,
# and verified by s147_chain.sh with sha256sum --check --strict. Absolute paths. usage: build_manifest_s147.sh <out>
set -euo pipefail
R=/mnt/gluster_dcpu/yiyangliu/gwm_s134; G1=/mnt/gluster_dcpu/yiyangliu/gwm_s141; G4=/mnt/gluster_dcpu/yiyangliu/gwm_s144; S=$R/src/s147
{ ls $S/*.py $S/*.json $S/PROTOCOL.md $S/s147_chain.sh
  find $R/src/vmem -type f \( -name '*.py' -o -name '*.yaml' \) | sort
  find $R/weights -maxdepth 1 -type f | sort
  echo $G1/runs/A/adapter_final.pt; echo $G1/clips_s141.json
  ls $G1/lat/*.pt $G1/warps/*.pt $G1/warps/WARP_LOG_*.jsonl
  find $G4/stage7 -type f | sort
  ls $G4/warps_monitor_cpu/* $G4/dev_A/*.npy $G4/dev_F/*__V__s0.npy $G4/SCORES_dev.json $G4/ALPHA.json
} | grep -v 'S147_FROZEN_INPUTS' | xargs -d '\n' sha256sum > "$1"
wc -l < "$1"
