#!/bin/bash
#SBATCH --job-name=e1-v2-test
#SBATCH --partition=GPU-1A
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:nvidia_a100:1
#SBATCH --time=02:00:00
#SBATCH --output=/home/s2530007/BiUMamba/logs/e1_synapse_v2_test-%j.log
#SBATCH --error=/home/s2530007/BiUMamba/logs/e1_synapse_v2_test-%j.log

# Research Author and Repository Maintainer: xuwen
# Affiliation: Japan Advanced Institute of Science and Technology (JAIST)

set -euo pipefail

ROOT=/home/s2530007/BiUMamba
SOURCE_REPO="$ROOT/repos/E2_modify_2_synapse_v2_exec"
ENV_PREFIX="$ROOT/envs/vmunet-py38"
SOURCE_TEST="$ROOT/datasets/Synapse/test_vol_h5"
FINAL_ROOT="$ROOT/runs/formal_test_synapse_v2"

if [ -z "${JOBDIR:-}" ] || [ ! -d "$JOBDIR" ]; then
  echo "JOBDIR is unavailable; refusing to run outside HAKUSAN job-local storage."
  exit 70
fi

source "$ROOT/envs/miniforge3/etc/profile.d/conda.sh"
conda activate "$ENV_PREFIX"

STAGED_REPO="$JOBDIR/repo"
STAGED_TEST="$JOBDIR/test_vol_h5"
STAGED_CHECKPOINTS="$JOBDIR/checkpoints"
STAGED_RESULTS="$JOBDIR/results"
mkdir -p "$STAGED_CHECKPOINTS" "$STAGED_RESULTS" "$FINAL_ROOT"
cp -a "$SOURCE_REPO" "$STAGED_REPO"
cp -aL "$SOURCE_TEST" "$STAGED_TEST"

test_count=$(find "$STAGED_TEST" -maxdepth 1 -type f -name '*.npy.h5' | wc -l)
if [ "$test_count" -ne 12 ]; then
  echo "Unexpected staged test volume count: $test_count"
  exit 71
fi

run_one_seed() {
  local seed="$1"
  local job_id="$2"
  local source_checkpoint="$ROOT/runs/e1_synapse_v2_full300_seed${seed}_hakusan_${job_id}/checkpoints/best_validation.pth"
  local staged_checkpoint="$STAGED_CHECKPOINTS/E1_seed${seed}_best_validation.pth"
  local staged_output="$STAGED_RESULTS/E1_seed${seed}"
  local final_output="$FINAL_ROOT/E1_seed${seed}"

  if [ -e "$final_output" ]; then
    echo "Refusing to overwrite existing output: $final_output"
    return 72
  fi
  cp "$source_checkpoint" "$staged_checkpoint"
  mkdir -p "$staged_output"

  set +e
  (
    cd "$STAGED_REPO"
    CUDA_VISIBLE_DEVICES=0 python research/protocols/synapse_v2/run_formal_test.py \
      --method E1 \
      --seed "$seed" \
      --checkpoint "$staged_checkpoint" \
      --test-volume-dir "$STAGED_TEST" \
      --output-dir "$staged_output"
  ) 2>&1 | tee "$staged_output/console.log"
  local code=${PIPESTATUS[0]}
  set -e
  echo "$code" > "$staged_output/EXIT_CODE.txt"
  cp -a "$staged_output" "$final_output"
  return "$code"
}

nvidia-smi --query-gpu=name,uuid,memory.total,driver_version --format=csv,noheader
run_one_seed 3407 644012
run_one_seed 2026 644013

