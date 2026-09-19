#!/bin/bash
# Environment setup only: no project model, weights, RGB-D, or GT access.
#SBATCH --job-name=gwm-py311-resolve
#SBATCH --partition=cpu
#SBATCH --account=mscitspod2026
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:15:00
set -eo pipefail
source /etc/profile.d/modules.sh
module load Anaconda3/2023.09-0
set -u
TASK_ENV="$HOME/.conda/envs/gwm-cut3r-py311-20260915"
TASK_RUN="$HOME/gwm_env_bootstrap_20260915"
mkdir -p "$TASK_RUN"
exec > >(tee "$TASK_RUN/job_${SLURM_JOB_ID}.log") 2>&1
date -u +%FT%TZ
hostname
printf 'job=%s\nenv=%s\n' "$SLURM_JOB_ID" "$TASK_ENV"
if [ -e "$TASK_ENV" ]; then
  echo 'Refusing to overwrite an existing environment.'
  exit 12
fi
conda create --prefix "$TASK_ENV" python=3.11 pip -y
PYTHONNOUSERSITE=1 "$TASK_ENV/bin/python" --version
PYTHONNOUSERSITE=1 "$TASK_ENV/bin/python" -m pip install --dry-run \
  --report "$TASK_RUN/requirements_resolver.json" \
  -r "$TASK_RUN/requirements-cut3r.txt"
conda list --prefix "$TASK_ENV" --explicit > "$TASK_RUN/conda_base_explicit.txt"
date -u +%FT%TZ
