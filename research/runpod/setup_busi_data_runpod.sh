#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="/workspace"
DATASETS_DIR="${WORKSPACE}/datasets"
FINAL_DATA="${DATASETS_DIR}/Dataset_BUSI_with_GT"
STAGE_DIR="${DATASETS_DIR}/busi_v1_download_stage"
ARCHIVE="${STAGE_DIR}/breast-ultrasound-images-dataset.zip"
DOWNLOAD_URL="https://www.kaggle.com/api/v1/datasets/download/aryashah2k/breast-ultrasound-images-dataset"
STATUS_DIR="${WORKSPACE}/outputs/busi_v1_clean_setup_runpod"

mkdir -p "${STATUS_DIR}"
date -u +%Y-%m-%dT%H:%M:%SZ > "${STATUS_DIR}/STARTED_UTC.txt"

finish() {
  code=$?
  trap - EXIT
  printf '%s\n' "${code}" > "${STATUS_DIR}/EXIT_CODE.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ > "${STATUS_DIR}/FINISHED_UTC.txt"
  exit "${code}"
}
trap finish EXIT

if [[ -d "${FINAL_DATA}" ]]; then
  png_count=$(find "${FINAL_DATA}" -type f -name '*.png' | wc -l | tr -d ' ')
  if [[ "${png_count}" == "1578" ]]; then
    echo "Existing BUSI dataset verified: ${png_count} PNG files."
  else
    echo "Refusing to use incomplete existing BUSI directory: ${png_count} PNG files." >&2
    exit 71
  fi
else
  if [[ -e "${STAGE_DIR}" ]]; then
    echo "Refusing to overwrite existing staging directory: ${STAGE_DIR}" >&2
    exit 72
  fi
  mkdir -p "${STAGE_DIR}/unpacked"
  curl --fail --location --retry 5 --output "${ARCHIVE}" "${DOWNLOAD_URL}"
  unzip -q "${ARCHIVE}" -d "${STAGE_DIR}/unpacked"
  source_data=$(find "${STAGE_DIR}/unpacked" -type d -name 'Dataset_BUSI_with_GT' -print -quit)
  if [[ -z "${source_data}" ]]; then
    echo "Dataset_BUSI_with_GT was not found in downloaded archive." >&2
    exit 73
  fi
  png_count=$(find "${source_data}" -type f -name '*.png' | wc -l | tr -d ' ')
  if [[ "${png_count}" != "1578" ]]; then
    echo "Unexpected BUSI PNG count after download: ${png_count}" >&2
    exit 74
  fi
  mv "${source_data}" "${FINAL_DATA}"
  echo "BUSI dataset installed: ${FINAL_DATA} (${png_count} PNG files)."
fi

REPO="${WORKSPACE}/repos/BUSI_v1_clean_exec_runpod"
mkdir -p "${REPO}/pre_trained_weights"
WEIGHT_TARGET="${WORKSPACE}/repos/VM-UNet/pre_trained_weights/vmamba_small_e238_ema.pth"
if [[ ! -f "${WEIGHT_TARGET}" ]]; then
  echo "Required VMamba pretrained weight is missing: ${WEIGHT_TARGET}" >&2
  exit 75
fi
ln -sfn "${WEIGHT_TARGET}" "${REPO}/pre_trained_weights/vmamba_small_e238_ema.pth"

sha256sum \
  "${REPO}/models/vmunet/vmamba.py" \
  "${REPO}/experiments/BUSI_v1_clean/train_busi_v1_clean.py" \
  "${REPO}/research/protocols/busi_v1_clean/clean_manifest.csv" \
  > "${STATUS_DIR}/FROZEN_SOURCE_SHA256.txt"
find "${FINAL_DATA}" -type f -name '*.png' | sort > "${STATUS_DIR}/PNG_FILE_LIST.txt"
printf '%s\n' "1578" > "${STATUS_DIR}/PNG_COUNT.txt"
echo "BUSI_SETUP_PASS"
