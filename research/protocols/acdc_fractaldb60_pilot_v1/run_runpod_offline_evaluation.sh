#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-/workspace/repos/VM-UNet_E2_modify_2_ACDC_v1}"
PYTHON_BIN="${PYTHON_BIN:-/workspace/miniconda3/envs/vmunet/bin/python}"
DATA_ROOT="${DATA_ROOT:-/workspace/datasets/ACDC_hf_preprocessed_train100}"
PILOT_ROOT="${PILOT_ROOT:-/workspace/runs/acdc_fractaldb60_pilot_v1_seed42_runpod_r4}"
EXTENSION_ROOT="${EXTENSION_ROOT:-/workspace/runs/acdc_fractaldb60_extension_v1_seed42_runpod}"
OUTPUT_DIR="${OUTPUT_DIR:-/workspace/outputs/acdc_fractaldb60_label_fraction_seed42_isolated_test_runpod}"
PROTOCOL="research/protocols/acdc_fractaldb60_pilot_v1"

cd "$REPO_ROOT"
test -f "$EXTENSION_ROOT/ALL_STAGES_COMPLETED_UTC.txt"
test "$(cat "$EXTENSION_ROOT/QUEUE_EXIT_CODE.txt")" = "0"

for condition in scratch imagenet fractaldb60; do
  test -f "$PILOT_ROOT/downstream_full300_$condition/checkpoints/best_validation.pth"
  test -f "$PILOT_ROOT/downstream_full300_$condition/training_summary.json"
  for fraction in 50 100; do
    test -f "$EXTENSION_ROOT/downstream_${fraction}pct_full300_$condition/checkpoints/best_validation.pth"
    test -f "$EXTENSION_ROOT/downstream_${fraction}pct_full300_$condition/training_summary.json"
  done
done

"$PYTHON_BIN" "$PROTOCOL/offline_evaluate_label_fractions.py" \
  --data-root "$DATA_ROOT" \
  --protocol-dir "$PROTOCOL" \
  --pilot-root "$PILOT_ROOT" \
  --extension-root "$EXTENSION_ROOT" \
  --output-dir "$OUTPUT_DIR" \
  --batch-size 32 \
  --nsd-tolerance-mm 1.0

printf '0\n' > "$OUTPUT_DIR/EXIT_CODE.txt"
date -u +%FT%TZ > "$OUTPUT_DIR/FINISHED_UTC.txt"
