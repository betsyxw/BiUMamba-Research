#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-/workspace/repos/BiUMamba-Research}"
PYTHON_BIN="${PYTHON_BIN:-/workspace/miniconda3/envs/vmunet/bin/python}"
ACDC_ROOT="${ACDC_ROOT:-/workspace/datasets/ACDC_hf_preprocessed_train100}"
FRACTAL_ARCHIVE="${FRACTAL_ARCHIVE:-/workspace/datasets/FractalDB/downloads/FractalDB-60.tar.gz}"
FRACTAL_PARENT="${FRACTAL_PARENT:-/workspace/datasets/FractalDB/extracted}"
FRACTAL_ROOT="$FRACTAL_PARENT/fractaldb_cat60_ins1000"
IMAGENET_CKPT="${IMAGENET_CKPT:-/workspace/repos/VM-UNet_E2_modify_2_ACDC_v1/pre_trained_weights/vmamba_small_e238_ema.pth}"
RUN_ROOT="${RUN_ROOT:-/workspace/runs/acdc_fractaldb60_pilot_v1_seed42_runpod}"
PROTOCOL="research/protocols/acdc_fractaldb60_pilot_v1"

mkdir -p "$RUN_ROOT" "$FRACTAL_PARENT"
exec > >(tee -a "$RUN_ROOT/queue.log") 2>&1

finish() {
  code=$?
  printf '%s\n' "$code" > "$RUN_ROOT/QUEUE_EXIT_CODE.txt"
  date -u +%FT%TZ > "$RUN_ROOT/QUEUE_FINISHED_UTC.txt"
}
trap finish EXIT

cd "$REPO_ROOT"
date -u +%FT%TZ > "$RUN_ROOT/QUEUE_STARTED_UTC.txt"
"$PYTHON_BIN" "$PROTOCOL/verify_protocol.py" | tee "$RUN_ROOT/protocol_verification.json"

test -f "$FRACTAL_ARCHIVE"
test -f "$IMAGENET_CKPT"
if [[ ! -d "$FRACTAL_ROOT" ]]; then
  tar -xzf "$FRACTAL_ARCHIVE" -C "$FRACTAL_PARENT" --exclude='*/._*' --exclude='./._*'
fi
test "$(find "$FRACTAL_ROOT" -mindepth 2 -maxdepth 2 -type f -name '*.png' | wc -l)" -eq 60000

"$PYTHON_BIN" "$PROTOCOL/pretrain_fractaldb60.py" \
  --data-root "$FRACTAL_ROOT" \
  --work-dir "$RUN_ROOT/fractaldb60_pretrain_smoke" \
  --epochs 1 --batch-size 8 --num-workers 2 --max-samples 64 --seed 42

"$PYTHON_BIN" "$PROTOCOL/pretrain_fractaldb60.py" \
  --data-root "$FRACTAL_ROOT" \
  --work-dir "$RUN_ROOT/fractaldb60_pretrain_full90" \
  --epochs 90 --batch-size 64 --num-workers 8 --seed 42

FRACTAL_CKPT="$RUN_ROOT/fractaldb60_pretrain_full90/fractaldb60_vmamba_encoder_epoch90.pth"
test -f "$FRACTAL_CKPT"

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
