#!/usr/bin/env bash
# Author: xuwen, JAIST
# Launch two sequential, strictly configured 12-epoch A/A diagnostics.

set -u

repo_dir="/workspace/repos/VM-UNet_E4_version_2_stabilized_gate"
run_root="${1:-/workspace/runs/e4_v2_stabilized_aa12}"

if [[ -e "${run_root}" ]]; then
  echo "Refusing to overwrite existing A/A directory: ${run_root}" >&2
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
  > "${run_root}/SOURCE_SHA256.txt"

python research/run_stabilized_aa.py \
  --run-id aa_run_1 \
  --work-dir "${run_root}/run_1" \
  --epochs 12 \
  > "${run_root}/run_1.console.log" 2>&1
code_1=$?
echo "${code_1}" > "${run_root}/run_1/exit_code.txt"

if [[ "${code_1}" -ne 0 ]]; then
  echo "A/A run 1 failed with exit code ${code_1}; run 2 was not started." >&2
  exit "${code_1}"
fi

python research/run_stabilized_aa.py \
  --run-id aa_run_2 \
  --work-dir "${run_root}/run_2" \
  --epochs 12 \
  > "${run_root}/run_2.console.log" 2>&1
code_2=$?
echo "${code_2}" > "${run_root}/run_2/exit_code.txt"

if [[ "${code_2}" -ne 0 ]]; then
  echo "A/A run 2 failed with exit code ${code_2}; comparison was not generated." >&2
  exit "${code_2}"
fi

python research/analyze_stabilized_aa.py "${run_root}" \
  > "${run_root}/analyze.console.log" 2>&1
code_analyze=$?
echo "${code_analyze}" > "${run_root}/analyze.exit_code.txt"
exit "${code_analyze}"
