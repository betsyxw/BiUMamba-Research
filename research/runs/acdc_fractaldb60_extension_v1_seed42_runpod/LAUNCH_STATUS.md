# ACDC FractalDB-60 50%/100% extension launch

- Status: running on the RunPod RTX 4090.
- Queue start: 2026-09-04T01:17:18Z (2026-09-04 10:17:18 JST).
- Remote queue PID: 56115.
- Remote output root: `/workspace/runs/acdc_fractaldb60_extension_v1_seed42_runpod`.
- Downstream dataset/model: ACDC / E2_modify_2.
- Seed: 42.
- Conditions at each label fraction: Scratch, ImageNet, FractalDB-60.
- Full training: 300 epochs per condition.
- Smoke tests: all six passed before the first full run started.
- Current first full run: 50% Scratch.
- Isolated test access during training: disabled.

## Frozen patient sets

- 50%: 35 of the frozen 70 training patients; includes all 18 pilot patients.
  SHA-256: `88bccd11e978827b8440f8445cfe35dac121fe801bb57208469121eed1027700`.
- 100%: all 70 frozen training patients.
  SHA-256: `d2bec93123b85ca4f7a7da3a86848a41b86f7f5a6717bc70828f6d5fb984f618`.
- Validation: unchanged 10 patients.
- Isolated test: unchanged 20 patients.

The 25% seed-42 pilot did not pass the primary Dice decision gate. This
extension was explicitly authorized as an exploratory label-fraction
sensitivity analysis and does not change that pilot conclusion.
