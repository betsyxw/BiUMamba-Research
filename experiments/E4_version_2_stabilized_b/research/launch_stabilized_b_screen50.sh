#!/usr/bin/env bash
# Author: xuwen, JAIST

set -u

repo_dir="/workspace/repos/VM-UNet_E4_version_2_stabilized_b"
run_dir="${1:-/workspace/runs/e4_v2_stabilized_b_screen50_seed42_20260829}"

if [[ -e "${run_dir}" ]]; then
  echo "Refusing to overwrite existing screening directory: ${run_dir}" >&2
  exit 2
fi

source /workspace/miniconda3/etc/profile.d/conda.sh
conda activate vmunet
cd "${repo_dir}"
export PYTHONHASHSEED=42
export CUBLAS_WORKSPACE_CONFIG=:4096:8

python research/run_stabilized_b_screen50.py --work-dir "${run_dir}" \
  > "${run_dir}.console.log" 2>&1
code=$?
echo "${code}" > "${run_dir}.exit_code.txt"
exit "${code}"
