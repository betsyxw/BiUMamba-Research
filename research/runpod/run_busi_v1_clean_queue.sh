#!/usr/bin/env bash
set -euo pipefail

AUTHOR="xuwen"
WORKSPACE="/workspace"
PYTHON_BIN="${WORKSPACE}/miniconda3/envs/vmunet/bin/python"
REPO="${WORKSPACE}/repos/BUSI_v1_clean_exec_runpod"
DATA_ROOT="${WORKSPACE}/datasets/Dataset_BUSI_with_GT"
PROTOCOL_DIR="${REPO}/research/protocols/busi_v1_clean"
QUEUE_DIR="${WORKSPACE}/outputs/busi_v1_clean_queue_seed42_runpod"
SEED=42

if [[ -e "${QUEUE_DIR}" ]]; then
  echo "Refusing to overwrite existing queue record: ${QUEUE_DIR}" >&2
  exit 80
fi
mkdir -p "${QUEUE_DIR}"
date -u +%Y-%m-%dT%H:%M:%SZ > "${QUEUE_DIR}/STARTED_UTC.txt"

finish_queue() {
  code=$?
  trap - EXIT
  printf '%s\n' "${code}" > "${QUEUE_DIR}/EXIT_CODE.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ > "${QUEUE_DIR}/FINISHED_UTC.txt"
  exit "${code}"
}
trap finish_queue EXIT

png_count=$(find "${DATA_ROOT}" -type f -name '*.png' | wc -l | tr -d ' ')
if [[ "${png_count}" != "1578" ]]; then
  echo "Unexpected BUSI PNG count: ${png_count}" >&2
  exit 81
fi

SOURCE_COMMIT=$(git -C "${REPO}" rev-parse HEAD)
TRAINER_SHA=$(sha256sum "${REPO}/experiments/BUSI_v1_clean/train_busi_v1_clean.py" | awk '{print $1}')
VMAMBA_SHA=$(sha256sum "${REPO}/models/vmunet/vmamba.py" | awk '{print $1}')
MANIFEST_SHA=$(sha256sum "${PROTOCOL_DIR}/clean_manifest.csv" | awk '{print $1}')

{
  echo "Author: ${AUTHOR}"
  echo "Affiliation: Japan Advanced Institute of Science and Technology (JAIST)"
  echo "Protocol: busi_v1_clean"
  echo "Seed: ${SEED}"
  echo "Platform: RunPod RTX 4090"
  echo "Order: E1 smoke -> E1 full300 -> E2_modify_2 smoke -> E2_modify_2 full300"
  echo "Checkpoint rule: highest validation lesion-positive Dice; lower HD95 tie-breaker"
  echo "Test access during training: forbidden"
  echo "Source commit: ${SOURCE_COMMIT}"
  echo "Trainer SHA256: ${TRAINER_SHA}"
  echo "VMamba SHA256: ${VMAMBA_SHA}"
  echo "Clean manifest SHA256: ${MANIFEST_SHA}"
  echo "BUSI PNG count: ${png_count}"
} > "${QUEUE_DIR}/QUEUE_MANIFEST.txt"
git -C "${REPO}" status --short > "${QUEUE_DIR}/SOURCE_STATUS.txt"
nvidia-smi --query-gpu=name,uuid,memory.total,driver_version --format=csv,noheader > "${QUEUE_DIR}/GPU_INFO.txt"

run_stage() {
  local method="$1"
  local scope="$2"
  local run_dir="$3"
  local program="$4"
  shift 4

  if [[ -e "${run_dir}" ]]; then
    echo "Refusing to overwrite existing output: ${run_dir}" >&2
    return 82
  fi
  mkdir -p "${run_dir}"
  date -u +%Y-%m-%dT%H:%M:%SZ > "${run_dir}/STARTED_UTC.txt"
  printf '%s\n' "${SEED}" > "${run_dir}/SEED.txt"
  {
    echo "Author: ${AUTHOR}"
    echo "Method: ${method}"
    echo "Protocol: busi_v1_clean"
    echo "Scope: ${scope}"
    echo "Seed: ${SEED}"
    echo "Platform: RunPod RTX 4090"
    echo "Source commit: ${SOURCE_COMMIT}"
    echo "Trainer SHA256: ${TRAINER_SHA}"
    echo "VMamba SHA256: ${VMAMBA_SHA}"
    echo "Clean manifest SHA256: ${MANIFEST_SHA}"
    echo "Test access during training: false"
  } > "${run_dir}/run_manifest.txt"
  nvidia-smi --query-gpu=name,uuid,memory.total,driver_version --format=csv,noheader > "${run_dir}/gpu_info.txt"

  echo "START method=${method} scope=${scope} utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  set +e
  (
    cd "${REPO}"
    export PYTHONHASHSEED="${SEED}"
    export CUBLAS_WORKSPACE_CONFIG=":4096:8"
    export CUDA_VISIBLE_DEVICES=0
    "${PYTHON_BIN}" "${program}" \
      --method "${method}" \
      --seed "${SEED}" \
      --work-dir "${run_dir}" \
      --data-root "${DATA_ROOT}" \
      --protocol-dir "${PROTOCOL_DIR}" \
      "$@"
  ) 2>&1 | tee "${run_dir}/console.log"
  run_code=${PIPESTATUS[0]}
  set -e
  printf '%s\n' "${run_code}" > "${run_dir}/EXIT_CODE.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ > "${run_dir}/FINISHED_UTC.txt"
  echo "FINISH method=${method} scope=${scope} exit=${run_code} utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if [[ "${run_code}" -ne 0 ]]; then
    return "${run_code}"
  fi
}

run_stage \
  "E1" "smoke" \
  "${WORKSPACE}/runs/e1_busi_v1_clean_smoke_seed42_runpod" \
  "experiments/BUSI_v1_clean/smoke_test_busi_v1_clean.py"

run_stage \
  "E1" "full300" \
  "${WORKSPACE}/runs/e1_busi_v1_clean_full300_seed42_runpod" \
  "experiments/BUSI_v1_clean/train_busi_v1_clean.py" \
  --epochs 300

run_stage \
  "E2_modify_2" "smoke" \
  "${WORKSPACE}/runs/e2_modify_2_busi_v1_clean_smoke_seed42_runpod" \
  "experiments/BUSI_v1_clean/smoke_test_busi_v1_clean.py"

run_stage \
  "E2_modify_2" "full300" \
  "${WORKSPACE}/runs/e2_modify_2_busi_v1_clean_full300_seed42_runpod" \
  "experiments/BUSI_v1_clean/train_busi_v1_clean.py" \
  --epochs 300

echo "ALL_BUSI_V1_CLEAN_SEED42_RUNS_FINISHED utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
