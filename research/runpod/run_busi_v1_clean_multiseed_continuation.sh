#!/usr/bin/env bash
set -euo pipefail

AUTHOR="xuwen"
WORKSPACE="/workspace"
PYTHON_BIN="${WORKSPACE}/miniconda3/envs/vmunet/bin/python"
REPO="${WORKSPACE}/repos/BUSI_v1_clean_exec_runpod"
DATA_ROOT="${WORKSPACE}/datasets/Dataset_BUSI_with_GT"
PROTOCOL_DIR="${REPO}/research/protocols/busi_v1_clean"
SEED42_QUEUE="${WORKSPACE}/outputs/busi_v1_clean_queue_seed42_runpod"
QUEUE_DIR="${WORKSPACE}/outputs/busi_v1_clean_multiseed_continuation_runpod"

if [[ -e "${QUEUE_DIR}" ]]; then
  echo "Refusing to overwrite existing continuation record: ${QUEUE_DIR}" >&2
  exit 90
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

echo "Waiting for the complete seed-42 queue: ${SEED42_QUEUE}"
while [[ ! -f "${SEED42_QUEUE}/EXIT_CODE.txt" ]]; do
  sleep 60
done
seed42_code=$(tr -d '[:space:]' < "${SEED42_QUEUE}/EXIT_CODE.txt")
if [[ "${seed42_code}" != "0" ]]; then
  echo "Seed-42 queue failed with exit code ${seed42_code}; continuation will not start." >&2
  exit 91
fi

for required in \
  "${WORKSPACE}/runs/e1_busi_v1_clean_full300_seed42_runpod/training_summary.json" \
  "${WORKSPACE}/runs/e1_busi_v1_clean_full300_seed42_runpod/checkpoints/best_validation.pth" \
  "${WORKSPACE}/runs/e2_modify_2_busi_v1_clean_full300_seed42_runpod/training_summary.json" \
  "${WORKSPACE}/runs/e2_modify_2_busi_v1_clean_full300_seed42_runpod/checkpoints/best_validation.pth"; do
  if [[ ! -f "${required}" ]]; then
    echo "Seed-42 completion marker exists but required artifact is missing: ${required}" >&2
    exit 92
  fi
done

png_count=$(find "${DATA_ROOT}" -type f -name '*.png' | wc -l | tr -d ' ')
if [[ "${png_count}" != "1578" ]]; then
  echo "Unexpected BUSI PNG count before continuation: ${png_count}" >&2
  exit 93
fi

SOURCE_COMMIT=$(git -C "${REPO}" rev-parse HEAD)
TRAINER_SHA=$(sha256sum "${REPO}/experiments/BUSI_v1_clean/train_busi_v1_clean.py" | awk '{print $1}')
VMAMBA_SHA=$(sha256sum "${REPO}/models/vmunet/vmamba.py" | awk '{print $1}')
MANIFEST_SHA=$(sha256sum "${PROTOCOL_DIR}/clean_manifest.csv" | awk '{print $1}')

{
  echo "Author: ${AUTHOR}"
  echo "Affiliation: Japan Advanced Institute of Science and Technology (JAIST)"
  echo "Protocol: busi_v1_clean"
  echo "Platform: RunPod RTX 4090"
  echo "Completed prerequisite seed: 42"
  echo "Continuation order: seed3407 E1 -> seed3407 E2_modify_2 -> seed2026 E1 -> seed2026 E2_modify_2"
  echo "Epochs per run: 300"
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

run_full300() {
  local method="$1"
  local seed="$2"
  local run_dir="$3"

  if [[ -e "${run_dir}" ]]; then
    echo "Refusing to overwrite existing output: ${run_dir}" >&2
    return 94
  fi
  mkdir -p "${run_dir}"
  date -u +%Y-%m-%dT%H:%M:%SZ > "${run_dir}/STARTED_UTC.txt"
  printf '%s\n' "${seed}" > "${run_dir}/SEED.txt"
  {
    echo "Author: ${AUTHOR}"
    echo "Method: ${method}"
    echo "Protocol: busi_v1_clean"
    echo "Scope: full300"
    echo "Seed: ${seed}"
    echo "Platform: RunPod RTX 4090"
    echo "Source commit: ${SOURCE_COMMIT}"
    echo "Trainer SHA256: ${TRAINER_SHA}"
    echo "VMamba SHA256: ${VMAMBA_SHA}"
    echo "Clean manifest SHA256: ${MANIFEST_SHA}"
    echo "Test access during training: false"
  } > "${run_dir}/run_manifest.txt"
  nvidia-smi --query-gpu=name,uuid,memory.total,driver_version --format=csv,noheader > "${run_dir}/gpu_info.txt"

  echo "START method=${method} seed=${seed} utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  set +e
  (
    cd "${REPO}"
    export PYTHONHASHSEED="${seed}"
    export CUBLAS_WORKSPACE_CONFIG=":4096:8"
    export CUDA_VISIBLE_DEVICES=0
    "${PYTHON_BIN}" experiments/BUSI_v1_clean/train_busi_v1_clean.py \
      --method "${method}" \
      --epochs 300 \
      --seed "${seed}" \
      --work-dir "${run_dir}" \
      --data-root "${DATA_ROOT}" \
      --protocol-dir "${PROTOCOL_DIR}"
  ) 2>&1 | tee "${run_dir}/console.log"
  run_code=${PIPESTATUS[0]}
  set -e
  printf '%s\n' "${run_code}" > "${run_dir}/EXIT_CODE.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ > "${run_dir}/FINISHED_UTC.txt"
  echo "FINISH method=${method} seed=${seed} exit=${run_code} utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if [[ "${run_code}" -ne 0 ]]; then
    return "${run_code}"
  fi
}

for seed in 3407 2026; do
  run_full300 \
    "E1" "${seed}" \
    "${WORKSPACE}/runs/e1_busi_v1_clean_full300_seed${seed}_runpod"
  run_full300 \
    "E2_modify_2" "${seed}" \
    "${WORKSPACE}/runs/e2_modify_2_busi_v1_clean_full300_seed${seed}_runpod"
done

date -u +%Y-%m-%dT%H:%M:%SZ > "${QUEUE_DIR}/MULTISEED_TRAINING_COMPLETE_UTC.txt"
echo "ALL_BUSI_V1_CLEAN_THREE_SEED_TRAINING_FINISHED utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
