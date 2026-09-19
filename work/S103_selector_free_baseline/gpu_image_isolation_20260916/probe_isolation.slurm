#!/usr/bin/env bash
# Synthetic GPU image/isolation probe: no model, checkpoint, dataset, future outcome or ground truth.
#SBATCH --job-name=gwm-img-isolation
#SBATCH --partition=normal
#SBATCH --account=mscitspod2026
#SBATCH --gpus=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:05:00
#SBATCH --output=/home/yliutz/gwm_image_probe_20260916/slurm-%j.out
#SBATCH --error=/home/yliutz/gwm_image_probe_20260916/slurm-%j.err
source /etc/profile.d/modules.sh
module load slurm/slurm/23.02.6
module load apptainer

IMG="$HOME/gwm-images/nvidia-cuda-12.6.3-runtime-ubuntu22.04.sif"
ENV="$HOME/.conda/envs/gwm-cut3r-py311-20260915"
STAGE="$HOME/gwm_isolation_stage_20260916"
DENY="$HOME/gwm_isolation_deny_20260916"
RCPT="$HOME/gwm_image_probe_20260916"
mkdir -p "$RCPT"

echo "schema=gwm-image-isolation-probe-v1"
echo "job_id=${SLURM_JOB_ID:-none} host=$(hostname) node_list=${SLURM_JOB_NODELIST:-none}"
echo "apptainer=$(apptainer --version 2>&1)"
echo "image=$IMG"
if [ ! -f "$IMG" ]; then echo "FATAL image_missing=$IMG"; exit 2; fi
echo "sif_bytes=$(stat -c %s "$IMG")"
echo "sif_sha256=$(sha256sum "$IMG" | awk '{print $1}')"
echo "stage_marker=$(cat "$STAGE/stage_history_marker.txt" 2>&1)"
echo "deny_sentinel_present_on_host=$(test -f "$DENY/DO_NOT_READ.txt" && echo yes || echo no)"

apptainer exec --nv --containall --no-home --cleanenv \
  --bind "$ENV:$ENV:ro" \
  --bind "$STAGE:/mnt/stage:ro" \
  "$IMG" "$ENV/bin/python3.11" /mnt/stage/probe_inside.py \
    /mnt/stage/stage_history_marker.txt "$DENY/DO_NOT_READ.txt" \
    > "$RCPT/probe_inside_${SLURM_JOB_ID}.json" 2> "$RCPT/probe_inside_${SLURM_JOB_ID}.err"
probe_rc=$?
echo "probe_inside_exit=$probe_rc"
echo "=== probe stdout ==="
cat "$RCPT/probe_inside_${SLURM_JOB_ID}.json"
echo "=== probe stderr (tail) ==="
tail -20 "$RCPT/probe_inside_${SLURM_JOB_ID}.err"
echo "finished_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
exit $probe_rc
