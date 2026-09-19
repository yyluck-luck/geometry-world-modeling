#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${HOME}/datasets/icl_nuim"
URL="https://www.doc.ic.ac.uk/~ahanda/living_room_traj0_frei_png.tar.gz"
OUT="${DATA_DIR}/living_room_traj0_frei_png.tar.gz"
RECEIPT="${DATA_DIR}/icl_nuim_download_receipt.txt"
mkdir -p "${DATA_DIR}"
{
  echo "start_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "hostname=$(hostname)"
  echo "url=${URL}"
  echo "output=${OUT}"
  echo "mode=download_only_no_unpack_no_model_no_gt_score"
} > "${RECEIPT}"
curl -L --fail --retry 3 --continue-at - --output "${OUT}" "${URL}"
printf 'bytes=' >> "${RECEIPT}"
wc -c < "${OUT}" >> "${RECEIPT}"
printf 'sha256=' >> "${RECEIPT}"
sha256sum "${OUT}" | awk '{print $1}' >> "${RECEIPT}"
printf 'end_utc=' >> "${RECEIPT}"
date -u +%Y-%m-%dT%H:%M:%SZ >> "${RECEIPT}"
