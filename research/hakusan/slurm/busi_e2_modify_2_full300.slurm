#!/bin/bash
#SBATCH --job-name=busi-e2-300
#SBATCH --partition=GPU-1A
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:nvidia_a100:1
#SBATCH --time=12:00:00
#SBATCH --output=/home/s2530007/BiUMamba/logs/busi_e2_modify_2_full300-%j.log
#SBATCH --error=/home/s2530007/BiUMamba/logs/busi_e2_modify_2_full300-%j.log

set -euo pipefail
ROOT=/home/s2530007/BiUMamba
SOURCE_REPO="$ROOT/repos/BUSI_v1_clean_exec"
SOURCE_DATA="$ROOT/datasets/Dataset_BUSI_with_GT"
ENV_PREFIX="$ROOT/envs/vmunet-py38"
OUTPUT="$ROOT/runs/e2_modify_2_busi_v1_clean_full300_seed42_hakusan_${SLURM_JOB_ID}"
mkdir -p "$OUTPUT"
finish() { code=$?; trap - EXIT; echo "$code" > "$OUTPUT/EXIT_CODE.txt"; date -u +%Y-%m-%dT%H:%M:%SZ > "$OUTPUT/FINISHED_UTC.txt"; sync; exit "$code"; }
trap finish EXIT
if [ -z "${JOBDIR:-}" ] || [ ! -d "$JOBDIR" ]; then echo "JOBDIR unavailable"; exit 70; fi
source "$ROOT/envs/miniforge3/etc/profile.d/conda.sh"
conda activate "$ENV_PREFIX"
STAGED_REPO="$JOBDIR/repo"
STAGED_DATA="$JOBDIR/Dataset_BUSI_with_GT"
cp -a "$SOURCE_REPO" "$STAGED_REPO"
cp -a "$SOURCE_DATA" "$STAGED_DATA"
png_count=$(find "$STAGED_DATA" -type f -name '*.png' | wc -l)
if [ "$png_count" -ne 1578 ]; then echo "Unexpected BUSI PNG count: $png_count"; exit 71; fi
PROTOCOL="$STAGED_REPO/research/protocols/busi_v1_clean"
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUTPUT/STARTED_UTC.txt"
{
  echo "Author: xuwen"; echo "Affiliation: Japan Advanced Institute of Science and Technology (JAIST)"
  echo "method=E2_modify_2"; echo "protocol=busi_v1_clean"; echo "seed=42"; echo "epochs=300"
  echo "job_id=$SLURM_JOB_ID"; echo "node=$(hostname)"; echo "source_commit=$(git -C "$SOURCE_REPO" rev-parse HEAD)"
  echo "trainer_sha256=$(sha256sum "$SOURCE_REPO/experiments/BUSI_v1_clean/train_busi_v1_clean.py" | awk '{print $1}')"
  echo "vmamba_sha256=$(sha256sum "$SOURCE_REPO/models/vmunet/vmamba.py" | awk '{print $1}')"
  echo "clean_manifest_sha256=$(sha256sum "$SOURCE_REPO/research/protocols/busi_v1_clean/clean_manifest.csv" | awk '{print $1}')"
  echo "png_count=$png_count"; echo "test_access_during_training=false"
} > "$OUTPUT/run_manifest.txt"
nvidia-smi --query-gpu=name,uuid,memory.total,driver_version --format=csv,noheader | tee "$OUTPUT/gpu_info.txt"
cd "$STAGED_REPO"
PYTHONHASHSEED=42 CUDA_VISIBLE_DEVICES=0 python experiments/BUSI_v1_clean/train_busi_v1_clean.py \
  --method E2_modify_2 --epochs 300 --seed 42 --work-dir "$OUTPUT" --data-root "$STAGED_DATA" --protocol-dir "$PROTOCOL" \
  2>&1 | tee "$OUTPUT/console.log"
exit "${PIPESTATUS[0]}"
