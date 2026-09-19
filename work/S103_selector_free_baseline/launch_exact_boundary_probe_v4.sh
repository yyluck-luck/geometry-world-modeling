#!/usr/bin/env bash
set -eo pipefail
source /etc/profile.d/modules.sh
module load slurm/slurm/23.02.6
set -u

RECEIPT=/home/yliutz/gwm_boundary_receipts/S103_SCENE13_W001_20260917_v4
SLURM=/home/yliutz/gwm_boundary_s103_scene13_w001_20260917_v4/exact_boundary_probe.slurm
mkdir -p "$RECEIPT"
job_id=$(sbatch --parsable "$SLURM")
printf '%s\n' "$job_id" > "$RECEIPT/JOB_ID.txt"
printf 'submitted job=%s utc=%s\n' "$job_id" "$(date -u +%FT%TZ)"
while squeue -h -j "$job_id" | grep -q .; do
  squeue -h -j "$job_id" -o 'job=%i state=%T elapsed=%M node=%R'
  sleep 10
done
sacct -n -X -j "$job_id" -o JobIDRaw,State,ExitCode,Elapsed,NodeList > "$RECEIPT/SACCT.txt"
cat "$RECEIPT/SACCT.txt"
test -f "$RECEIPT/EXACT_ISOLATION_RECEIPT.json"
