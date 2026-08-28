# E3 Static Learnable Fusion — 50-Epoch Screening Report

**Research Author and Repository Maintainer:** xuwen

**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

**GitHub:** [@betsyxw](https://github.com/betsyxw)

## Run status

- Experiment: **E3 — Channel-Grouped 2D Bidirectional Scan with Static Learnable Fusion**
- Dataset: Synapse multi-organ CT
- Status: **completed successfully**
- Exit code: `0`
- Epochs: `50`
- Seed: `42`
- Batch size: `32`
- Input size: `224 × 224`
- Checkpoint epoch: `48`
- Source commit: `25bde91e5a6b5f55432b62eb0b1e760ea29c437c`
- Source branch: `experiment/e3-static-learnable-fusion`
- Run directory: `/workspace/runs/e3_static_fusion_screen50_seed42_20260828_vmunetenv`

This is a short screening experiment, not a converged 300-epoch publication result.

## Official checkpoint result

| Metric | Result |
|---|---:|
| Mean Dice | **0.7567725296 (75.6773%)** |
| Mean HD95 | **36.0623788848** |
| Test cases | 12 |
| Test time | 657.31 s |

The Epoch-50 current-weight validation result was Dice `0.7539140799` and HD95 `34.0561673040`. The formal screening comparison uses the Epoch-48 checkpoint-test result, matching the E2_modify_2 screening protocol.

## Per-organ checkpoint metrics

| Class | Organ | Dice | Dice (%) | HD95 |
|---:|---|---:|---:|---:|
| 1 | Aorta | 0.827091 | 82.7091 | 21.421077 |
| 2 | Gallbladder | 0.645435 | 64.5435 | 43.877589 |
| 3 | Left Kidney | 0.807222 | 80.7222 | 42.443877 |
| 4 | Right Kidney | 0.723226 | 72.3226 | 46.264663 |
| 5 | Liver | 0.926377 | 92.6377 | 21.990614 |
| 6 | Pancreas | 0.566128 | 56.6128 | 13.014664 |
| 7 | Spleen | 0.852426 | 85.2426 | 80.589141 |
| 8 | Stomach | 0.706274 | 70.6274 | 18.897406 |

## Time and GPU usage

| Item | Result |
|---|---:|
| Sum of 50 epoch times | 7,632.87 s |
| Training-only duration | 2 h 07 m 12.87 s |
| Mean epoch time | **152.6574 s** |
| Logged wall duration | approximately 8,989 s (2 h 29 m 49 s) |
| Peak sampled GPU memory | **12,958 MiB** |
| Peak sampled utilization | 100% |

## Matched 50-epoch comparison

| Metric | E2_modify_2 fixed sum | E3 static fusion | E3 − E2_modify_2 |
|---|---:|---:|---:|
| Mean Dice | 0.750737 | **0.756773** | **+0.006035 (+0.6035 pp)** |
| Mean HD95 | 40.415915 | **36.062379** | **−4.353536** |
| Training time | 8,535.29 s | **7,632.87 s** | **−902.42 s (−10.57%)** |
| Mean epoch time | 170.71 s | **152.66 s** | **−18.05 s (−10.57%)** |
| Peak GPU memory | **11,016 MiB** | 12,958 MiB | +1,942 MiB (+17.63%) |

E3 improves both screening accuracy criteria and training speed. Six of eight organs improve in Dice; the exceptions are right kidney and spleen. HD95 improves in seven organs, while spleen HD95 becomes substantially worse.

## Project-wide status

| Experiment | Epochs | Mean Dice | Mean HD95 | Mean epoch time | Peak memory |
|---|---:|---:|---:|---:|---:|
| E1 four-direction fixed sum | 300 | 80.0488% | 24.6136 | 177.86 s | 14,665 MiB |
| E2 row-only bidirectional fixed sum | 300 | 78.6080% | 26.1111 | 164.48 s | 10,747 MiB |
| E2_modify_2 grouped-2D fixed sum | 300 | **80.2540%** | **21.9206** | 157.06 s | 11,016 MiB |
| E3 grouped-2D static learnable fusion | **50** | 75.6773% | 36.0624 | **152.66 s** | 12,958 MiB |

E1, E2, and E2_modify_2 are 300-epoch results; E3 is a 50-epoch screening result. E3 must not be ranked directly against the full runs. Its valid decision comparison is the matched E2_modify_2 50-epoch run.

## Decision

**E3 passes the short-screening gate and is worth a matched 300-epoch run.** This is single-seed preliminary evidence, not a statistical superiority claim. Before a final claim, inspect the spleen boundary outlier, run the matched 300-epoch experiment, export the learned fusion weights, and later repeat with multiple seeds.

Datasets, patient-derived NIfTI files, checkpoints, pretrained weights, compressed archives, and credentials are intentionally excluded from GitHub.
