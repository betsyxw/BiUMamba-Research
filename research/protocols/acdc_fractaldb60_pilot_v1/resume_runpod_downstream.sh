#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-/workspace/repos/VM-UNet_E2_modify_2_ACDC_v1}"
PYTHON_BIN="${PYTHON_BIN:-/workspace/miniconda3/envs/vmunet/bin/python}"
ACDC_ROOT="${ACDC_ROOT:-/workspace/datasets/ACDC_hf_preprocessed_train100}"
IMAGENET_CKPT="${IMAGENET_CKPT:-$REPO_ROOT/pre_trained_weights/vmamba_small_e238_ema.pth}"
RUN_ROOT="${RUN_ROOT:-/workspace/runs/acdc_fractaldb60_pilot_v1_seed42_runpod_r4}"
PROTOCOL="research/protocols/acdc_fractaldb60_pilot_v1"
FRACTAL_CKPT="$RUN_ROOT/fractaldb60_pretrain_full90/fractaldb60_vmamba_encoder_epoch90.pth"

mkdir -p "$RUN_ROOT"
exec > >(tee -a "$RUN_ROOT/downstream_resume.log") 2>&1

finish() {
  code=$?
  printf '%s\n' "$code" > "$RUN_ROOT/DOWNSTREAM_RESUME_EXIT_CODE.txt"
  date -u +%FT%TZ > "$RUN_ROOT/DOWNSTREAM_RESUME_FINISHED_UTC.txt"
}
trap finish EXIT

cd "$REPO_ROOT"
date -u +%FT%TZ > "$RUN_ROOT/DOWNSTREAM_RESUME_STARTED_UTC.txt"

test -f "$FRACTAL_CKPT"
test -f "$IMAGENET_CKPT"
test -f research/protocols/acdc_v1/checkpointing.py
test -f research/protocols/acdc_v1/validation_acdc_v1.py

"$PYTHON_BIN" -c \
  'from research.protocols.acdc_v1.checkpointing import ValidationCheckpointSelector; from research.protocols.acdc_v1.validation_acdc_v1 import evaluate_validation'

for condition in scratch imagenet fractaldb60; do
  "$PYTHON_BIN" "$PROTOCOL/train_acdc25.py" \
    --condition "$condition" --epochs 1 --seed 42 \
    --work-dir "$RUN_ROOT/downstream_smoke_$condition" \
    --data-root "$ACDC_ROOT" --protocol-dir "$PROTOCOL" \
    --imagenet-checkpoint "$IMAGENET_CKPT" \
    --fractaldb60-checkpoint "$FRACTAL_CKPT"
done

for condition in scratch imagenet fractaldb60; do
  "$PYTHON_BIN" "$PROTOCOL/train_acdc25.py" \
    --condition "$condition" --epochs 300 --seed 42 \
    --work-dir "$RUN_ROOT/downstream_full300_$condition" \
    --data-root "$ACDC_ROOT" --protocol-dir "$PROTOCOL" \
    --imagenet-checkpoint "$IMAGENET_CKPT" \
    --fractaldb60-checkpoint "$FRACTAL_CKPT"
done

date -u +%FT%TZ > "$RUN_ROOT/ALL_STAGES_COMPLETED_UTC.txt"
