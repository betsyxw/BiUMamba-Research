# E2_modify_2 Short-Screening Report

## Purpose

This matched 50-epoch Synapse run evaluates **E2_modify_2: channel-grouped 2D bidirectional scan with fixed-sum fusion**. Half of the channels use horizontal forward/backward scans and half use vertical forward/backward scans in every block. The configuration matches the E2_modify_1 screening run.

This is an early screening result, not a converged 300-epoch result.

## Run status

- Status: **PASS / completed normally**
- Process exit code: `0`
- Epochs: `50`
- Best checkpoint epoch by training loss: `48`
- Final training loss: `0.1307`
- Mean Dice: `0.750737` (`75.07%`)
- Mean HD95: `40.415915`
- Training time (sum of 50 epochs): `8,535.29 s` (`2 h 22 min 15 s`)
- Mean time per epoch: `170.71 s`
- Final evaluation time: `650.39 s` (`10 min 50 s`)
- Accounted training + evaluation time: `9,185.68 s` (`2 h 33 min 6 s`)
- Wall time from configuration logging to final evaluation: approximately `9,247 s` (`2 h 34 min 7 s`)
- Peak GPU memory from 30-second sampling: `11,016 MiB` (`10.76 GiB`)
- Peak sampled GPU utilization: `100%`

## Per-organ result

| Class | Organ | Dice | HD95 |
|---:|---|---:|---:|
| 1 | Aorta | 0.816129 | 26.047898 |
| 2 | Gallbladder | 0.633108 | 46.447527 |
| 3 | Left kidney | 0.788762 | 70.177064 |
| 4 | Right kidney | 0.746203 | 59.991509 |
| 5 | Liver | 0.930443 | 25.007745 |
| 6 | Pancreas | 0.549673 | 13.664092 |
| 7 | Spleen | 0.859411 | 60.333604 |
| 8 | Stomach | 0.682168 | 21.657878 |

## Matched comparison with E2_modify_1

| Metric | E2_modify_1 | E2_modify_2 | Modify_2 minus Modify_1 |
|---|---:|---:|---:|
| Mean Dice | 0.725396 | **0.750737** | **+0.025341 (+2.5341 pp)** |
| Mean HD95 | **35.579682** | 40.415915 | +4.836232 (worse) |
| Final training loss | 0.1478 | **0.1307** | -0.0171 |
| Mean epoch time | 213.81 s | **170.71 s** | -43.10 s (-20.16%) |
| Peak GPU memory | **10,396 MiB** | 11,016 MiB | +620 MiB |

E2_modify_2 improved Dice in seven of eight organs; the largest gain was pancreas (+9.52 percentage points). Its overall HD95 worsened because boundary outliers increased in gallbladder, left kidney, right kidney, and spleen. The left-kidney HD95 increase was especially large.

## Recommendation

The result is mixed: E2_modify_2 provides a clear Dice and speed signal but does not satisfy the predeclared requirement that HD95 also improve. Nevertheless, it is the stronger candidate for the next 300-epoch run because it improves overlap accuracy broadly, is about 20% faster per epoch, and preserves horizontal and vertical coverage inside every block. The HD95 regression must be treated as the primary risk and re-evaluated after convergence; no 300-epoch run was started automatically.

## Configuration

- Dataset: Synapse; 12 test volumes
- Seed: `42`
- Batch size: `32`
- Input size: `224 x 224`
- Optimizer: AdamW; initial learning rate `0.001`; weight decay `0.01`
- Scheduler: CosineAnnealingLR (`T_max=100`, `eta_min=1e-5`)
- Loss: cross-entropy + Dice loss
- AMP: disabled
- Pretrained initialization: `vmamba_small_e238_ema.pth`
- Scan fusion: `grouped_2d_bidirectional_sum`
- Source commit on RunPod: `62fc67c2839f225bc86edcba9f3f108bdfb99beb`
- Source tag: `E2_modify_2_smoke_pass`

## Artifact policy

The GitHub archive contains source code, configuration, Markdown/CSV/JSON summaries, and text logs only. It excludes datasets, patient images, NIfTI outputs, checkpoints, pretrained weights, compressed archives, SSH keys, tokens, and credentials.
