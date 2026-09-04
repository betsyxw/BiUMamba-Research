#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-/workspace/repos/VM-UNet_E2_modify_2_ACDC_v1}"
PYTHON_BIN="${PYTHON_BIN:-/workspace/miniconda3/envs/vmunet/bin/python}"
ACDC_ROOT="${ACDC_ROOT:-/workspace/datasets/ACDC_hf_preprocessed_train100}"
IMAGENET_CKPT="${IMAGENET_CKPT:-$REPO_ROOT/pre_trained_weights/vmamba_small_e238_ema.pth}"
STEP16_ROOT="${STEP16_ROOT:-/workspace/runs/acdc_fractaldb60_pilot_v1_seed42_runpod_r4}"
RUN_ROOT="${RUN_ROOT:-/workspace/runs/acdc_fractaldb60_extension_v1_seed42_runpod}"
PROTOCOL="research/protocols/acdc_fractaldb60_pilot_v1"
FRACTAL_CKPT="$STEP16_ROOT/fractaldb60_pretrain_full90/fractaldb60_vmamba_encoder_epoch90.pth"

mkdir -p "$RUN_ROOT"
exec > >(tee -a "$RUN_ROOT/queue.log") 2>&1

finish() {
  code=$?
  printf '%s\n' "$code" > "$RUN_ROOT/QUEUE_EXIT_CODE.txt"
  date -u +%FT%TZ > "$RUN_ROOT/QUEUE_FINISHED_UTC.txt"
}
trap finish EXIT

cd "$REPO_ROOT"
date -u +%FT%TZ > "$RUN_ROOT/QUEUE_STARTED_UTC.txt"
test -f "$FRACTAL_CKPT"
test -f "$IMAGENET_CKPT"
"$PYTHON_BIN" "$PROTOCOL/verify_extension.py" | tee "$RUN_ROOT/protocol_verification.json"

for fraction in 50 100; do
  for condition in scratch imagenet fractaldb60; do
    "$PYTHON_BIN" "$PROTOCOL/train_acdc25.py" \
      --condition "$condition" --label-fraction "$fraction" --epochs 1 --seed 42 \
      --work-dir "$RUN_ROOT/downstream_${fraction}pct_smoke_$condition" \
      --data-root "$ACDC_ROOT" --protocol-dir "$PROTOCOL" \
      --imagenet-checkpoint "$IMAGENET_CKPT" \
      --fractaldb60-checkpoint "$FRACTAL_CKPT"
  done
done

for fraction in 50 100; do
  for condition in scratch imagenet fractaldb60; do
    "$PYTHON_BIN" "$PROTOCOL/train_acdc25.py" \
      --condition "$condition" --label-fraction "$fraction" --epochs 300 --seed 42 \
      --work-dir "$RUN_ROOT/downstream_${fraction}pct_full300_$condition" \
      --data-root "$ACDC_ROOT" --protocol-dir "$PROTOCOL" \
      --imagenet-checkpoint "$IMAGENET_CKPT" \
      --fractaldb60-checkpoint "$FRACTAL_CKPT"
  done
done

date -u +%FT%TZ > "$RUN_ROOT/ALL_STAGES_COMPLETED_UTC.txt"
