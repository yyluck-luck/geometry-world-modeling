#!/bin/bash
# S135 CPU stage-1 arms, 14 windows each, 3 in parallel (4 threads each)
cd "$(dirname "$0")/../.."
export PYTHONPATH=work/S17C_environment/site-packages S133_THREADS=4
D=work/S135_scale_init; P=".venv-cut3r/bin/python $D/repro_kps.py"
run() { name=$1; shift; $P "$@" --out $D/ARM_$name.json > $D/log_$name.txt 2>&1; echo "done $name"; }
run gl_orig --convention gl & run gl_fix --convention gl --pnp-fix & run gl_kps --convention gl --kps & wait
run gl_kpsK --convention gl --kps --kps-known-k & run native_fix --convention native --pnp-fix & run native_kpsK --convention native --kps --kps-known-k & wait
echo ALL_DONE
