#!/usr/bin/env bash
#SBATCH --job-name=gwm-container-cap
#SBATCH --partition=normal
#SBATCH --account=mscitspod2026
#SBATCH --gpus=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:02:00
set -euo pipefail
source /etc/profile.d/modules.sh
module load slurm/slurm/23.02.6
printf 'CAPABILITY_PROBE_SCHEMA gwm-container-capability-v1\n'
printf 'HOST '; hostname
printf 'KERNEL '; uname -sr
printf 'MODULE_APPTAINER\n'
(module spider apptainer 2>&1 || true) | head -n 80
printf 'MODULE_SINGULARITY\n'
(module spider singularity 2>&1 || true) | head -n 80
printf 'LOAD_APPTAINER\n'
if module load apptainer 2>&1; then
  printf 'APPTAINER_MODULE_LOAD PASS\n'
  command -V apptainer 2>&1 || true
  apptainer --version 2>&1 || true
  apptainer exec --help 2>&1 | grep -Ei 'nv|bind|contain|no-home|userns' | head -n 50 || true
else
  printf 'APPTAINER_MODULE_LOAD FAIL\n'
fi
printf 'ENROOT\n'
command -V enroot 2>&1 || true
enroot --version 2>&1 || true
enroot list 2>&1 || true
printf 'SLURM_CONTAINER_FLAGS\n'
srun --help 2>&1 | grep -Ei -- '--container|container-image|container-mount|remap-root|mount-home' | head -n 80 || true
printf 'CAPABILITY_PROBE_END\n'
