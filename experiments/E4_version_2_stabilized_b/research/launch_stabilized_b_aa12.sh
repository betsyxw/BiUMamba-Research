#!/usr/bin/env bash
# Author: xuwen, JAIST
# Two sequential 12-epoch A/A runs for E4_version_2_stabilized_b.

set -u

repo_dir="/workspace/repos/VM-UNet_E4_version_2_stabilized_b"
run_root="${1:-/workspace/runs/e4_v2_stabilized_b_aa12}"

if [[ -e "${run_root}" ]]; then
  echo "Refusing to overwrite existing B A/A directory: ${run_root}" >&2
  exit 2
fi

source /workspace/miniconda3/etc/profile.d/conda.sh
conda activate vmunet
cd "${repo_dir}"

export PYTHONHASHSEED=42
export CUBLAS_WORKSPACE_CONFIG=:4096:8

mkdir -p "${run_root}"
git rev-parse HEAD > "${run_root}/SOURCE_COMMIT.txt"
sha256sum \
  models/vmunet/vmamba.py \
  train_synapse.py \
  engine_synapse.py \
  utils.py \
  datasets/validation.py \
  configs/config_setting_synapse.py \
  research/run_stabilized_aa.py \
  research/analyze_stabilized_aa.py \
  research/analyze_gate_saturation.py \
  > "${run_root}/SOURCE_SHA256.txt"

python research/run_stabilized_aa.py \
  --run-id stabilized_b_aa_run_1 \
  --work-dir "${run_root}/run_1" \
  --epochs 12 \
  > "${run_root}/run_1.console.log" 2>&1
code_1=$?
echo "${code_1}" > "${run_root}/run_1/exit_code.txt"
if [[ "${code_1}" -ne 0 ]]; then
  echo "B A/A run 1 failed with exit code ${code_1}; run 2 was not started." >&2
  exit "${code_1}"
fi

python research/run_stabilized_aa.py \
  --run-id stabilized_b_aa_run_2 \
  --work-dir "${run_root}/run_2" \
  --epochs 12 \
  > "${run_root}/run_2.console.log" 2>&1
code_2=$?
echo "${code_2}" > "${run_root}/run_2/exit_code.txt"
if [[ "${code_2}" -ne 0 ]]; then
  echo "B A/A run 2 failed with exit code ${code_2}; analyses were not started." >&2
  exit "${code_2}"
fi

python research/analyze_stabilized_aa.py "${run_root}" \
  > "${run_root}/trajectory_analysis.console.log" 2>&1
code_trajectory=$?
echo "${code_trajectory}" > "${run_root}/trajectory_analysis.exit_code.txt"
if [[ "${code_trajectory}" -ne 0 ]]; then
  exit "${code_trajectory}"
fi

python research/analyze_gate_saturation.py \
  --run-root "${run_root}" \
  --output-dir "${run_root}/gate_saturation_population" \
  > "${run_root}/gate_saturation_population.console.log" 2>&1
code_saturation=$?
echo "${code_saturation}" > "${run_root}/gate_saturation_population.exit_code.txt"
exit "${code_saturation}"
