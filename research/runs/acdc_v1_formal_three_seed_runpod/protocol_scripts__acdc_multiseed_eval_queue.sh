#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="/workspace/miniconda3/envs/vmunet/bin/python"
REPO="/workspace/repos/VM-UNet_E2_modify_2_ACDC_v1"
EVALUATOR="${REPO}/research/acdc_offline_evaluate_multiseed.py"
DATA_ROOT="/workspace/datasets/ACDC_hf_preprocessed_train100"
PROTOCOL_DIR="${REPO}/research/protocols/acdc_v1"
QUEUE_LOG="/workspace/outputs/acdc_v1_multiseed_offline_evaluation.log"

mkdir -p /workspace/outputs

run_seed() {
  local seed="$1"
  local output_dir="/workspace/outputs/acdc_v1_formal_seed${seed}_runpod"
  local e1_run="/workspace/runs/e1_acdc_v1_full300_seed${seed}_runpod"
  local e2_run="/workspace/runs/e2_modify_2_acdc_v1_full300_seed${seed}_runpod"

  if [[ -e "${output_dir}" ]]; then
    echo "Refusing to overwrite existing output: ${output_dir}" >&2
    return 91
  fi

  echo "START_OFFLINE_EVAL seed=${seed} utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  "${PYTHON_BIN}" "${EVALUATOR}" \
    --seed "${seed}" \
    --data-root "${DATA_ROOT}" \
    --protocol-dir "${PROTOCOL_DIR}" \
    --e1-checkpoint "${e1_run}/checkpoints/best_validation.pth" \
    --e2-checkpoint "${e2_run}/checkpoints/best_validation.pth" \
    --e1-summary "${e1_run}/training_summary.json" \
    --e2-summary "${e2_run}/training_summary.json" \
    --output-dir "${output_dir}" \
    --batch-size 32 \
    --nsd-tolerance-mm 1.0
  printf '0\n' > "${output_dir}/EXIT_CODE.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ > "${output_dir}/FINISHED_UTC.txt"
  echo "FINISH_OFFLINE_EVAL seed=${seed} utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}

{
  run_seed 3407
  run_seed 2026
  echo "ALL_ACDC_V1_OFFLINE_EVALUATIONS_FINISHED utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} 2>&1 | tee "${QUEUE_LOG}"

