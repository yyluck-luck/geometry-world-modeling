#!/usr/bin/env bash
# GPU capability probe only: no model, checkpoint, dataset or ground truth.
#SBATCH --job-name=gwm-apptainer-cuda3
#SBATCH --partition=normal
#SBATCH --account=mscitspod2026
#SBATCH --gpus=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:02:00
#SBATCH --output=/home/yliutz/gwm_remote_tmux_20260916/apptainer_cuda_probe_v3-%j.out
#SBATCH --error=/home/yliutz/gwm_remote_tmux_20260916/apptainer_cuda_probe_v3-%j.err
set -euo pipefail
source /etc/profile.d/modules.sh
module load slurm/slurm/23.02.6
module load apptainer
SANDBOX="$HOME/gwm_apptainer_sandbox_v3_20260916"
ENV="$HOME/.conda/envs/gwm-cut3r-py311-20260915"
mkdir -p "$SANDBOX"/{dev,proc,sys,tmp,etc,home,var,run} "$SANDBOX$ENV"
printf 'schema=gwm-apptainer-cuda-probe-v3\nhost=%s\napptainer=%s\n' "$(hostname)" "$(apptainer --version)"
apptainer exec --nv --containall --no-home --cleanenv \
  --bind "$ENV:$ENV:ro" \
  "$SANDBOX" "$ENV/bin/python3.11" -c 'import torch; print("torch="+torch.__version__); print("cuda_available="+str(torch.cuda.is_available())); print("device="+str(torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)); print("device_count="+str(torch.cuda.device_count())); x=torch.zeros((2,2),device="cuda"); print("alloc="+str(tuple(x.shape)))'
