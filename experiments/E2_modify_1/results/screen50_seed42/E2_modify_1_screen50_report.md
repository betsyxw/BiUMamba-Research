# E2_modify_1 Short-Screening Report

## Purpose

This 50-epoch run is a low-cost screening experiment for **E2_modify_1: alternating-axis bidirectional scan with fixed-sum fusion**. Consecutive VM-UNet blocks alternate between horizontal forward/backward scans and vertical forward/backward scans. Its purpose is to test whether restoring two-dimensional directional coverage can recover the degradation observed in the row-major-only E2 design.

This is **not** a final 300-epoch result and must not be compared as if it were fully converged.

## Run status

- Status: **PASS / completed normally**
- Process exit code: `0`
- Epochs: `50`
- Best checkpoint epoch by training loss: `50`
- Final training loss: `0.1478`
- Mean Dice: `0.725396` (`72.54%`)
- Mean HD95: `35.579682`
- Training time (sum of 50 epochs): `10,690.67 s` (`2 h 58 min 11 s`)
- Mean time per epoch: `213.81 s`
- Final evaluation time: `655.74 s` (`10 min 56 s`)
- Accounted training + evaluation time: `11,346.41 s` (`3 h 9 min 6 s`)
- Wall time from configuration logging to final evaluation: approximately `3 h 10 min 38 s`
- Peak GPU memory from 30-second sampling: `10,396 MiB` (`10.15 GiB`)
- Peak sampled GPU utilization: `100%`

## Per-organ result

| Class | Organ | Dice | HD95 |
|---:|---|---:|---:|
| 1 | Aorta | 0.804839 | 27.920707 |
| 2 | Gallbladder | 0.612600 | 28.112656 |
| 3 | Left kidney | 0.767680 | 49.026018 |
| 4 | Right kidney | 0.716257 | 57.633590 |
| 5 | Liver | 0.925184 | 27.271579 |
| 6 | Pancreas | 0.454485 | 17.772487 |
| 7 | Spleen | 0.837986 | 51.442490 |
| 8 | Stomach | 0.684138 | 25.457931 |

## Configuration

- Dataset: Synapse
- Split: repository `lists_Synapse` train/test split; 12 test volumes
- Seed: `42`
- Batch size: `32`
- Input size: `224 x 224`
- Optimizer: AdamW
- Initial learning rate: `0.001`
- Weight decay: `0.01`
- Scheduler: CosineAnnealingLR (`T_max=100`, `eta_min=1e-5`)
- Loss: cross-entropy + Dice loss
- AMP: disabled
- Pretrained initialization: `vmamba_small_e238_ema.pth`
- Scan fusion: `alternating_axis_sum`
- Source commit on RunPod: `3d39ce6057b2f2696f1d593bce42efdd1e179ce9`
- Source tag: `E2_modify_1_smoke_pass`

## Interpretation and decision rule

The run proves that the implementation is trainable and produces a valid full-volume Synapse evaluation. The 50-epoch Dice of 72.54% is a screening signal only; E1 and E2 were trained for 300 epochs, so it is methodologically invalid to conclude superiority or inferiority from this number alone.

The next fair step is to run E2_modify_2 with the same 50-epoch configuration, then compare Dice, HD95, convergence, time, memory, and per-organ behavior. The stronger and more interpretable variant should be selected for the 300-epoch experiment.

## Artifact policy

The GitHub archive contains only source code, configuration, Markdown/CSV/JSON summaries, and text logs. It intentionally excludes datasets, patient images, NIfTI predictions, checkpoints, pretrained weights, compressed archives, SSH keys, tokens, and credentials.
