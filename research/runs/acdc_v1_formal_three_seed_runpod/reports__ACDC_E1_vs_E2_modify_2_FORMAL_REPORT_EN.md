# ACDC v1 Formal Three-Seed Comparison

## Protocol

- Models: E1 and E2_modify_2.
- Seeds: 42, 3407, 2026.
- Fixed split: 70 training, 10 validation, and 20 isolated test patients (40 ED/ES volumes).
- Best checkpoint: validation Dice; lower validation HD95 is the tie-breaker.
- Final metrics: Dice, physical HD95 (mm), and NSD@1 mm.
- The test set was not used for checkpoint selection.

## Overall result (mean ± sample standard deviation)

| Model | Dice | HD95 (mm) | NSD@1 mm |
|---|---:|---:|---:|
| E1 | 0.9077 ± 0.0024 | 2.9144 ± 0.1931 | 0.9106 ± 0.0060 |
| E2_modify_2 | 0.9073 ± 0.0015 | 3.0303 ± 0.2605 | 0.9091 ± 0.0044 |

E2_modify_2 changed Dice by -0.046 percentage points, HD95 by +0.116 mm, and NSD by -0.155 percentage points. Accuracy is close to E1, but mean boundary accuracy is slightly worse.

## Efficiency

| Model | Training (h) | Epoch (s) | Memory (GB) | Inference (ms/slice) | Parameters |
|---|---:|---:|---:|---:|---:|
| E1 | 1.181 ± 0.022 | 13.539 ± 0.228 | 9.606 ± 0.001 | 1.833 ± 0.029 | 27,427,636 |
| E2_modify_2 | 0.824 ± 0.027 | 9.288 ± 0.286 | 7.211 ± 0.000 | 1.199 ± 0.064 | 27,427,636 |

E2_modify_2 reduced total training time by 30.25%, mean epoch time by 31.40%, peak GPU memory by 24.93%, and inference time by 34.58%. Parameter count was unchanged.

FLOPs: **N/A**. Generic profilers do not count the selective-scan custom operator reliably, so no FLOP value is invented.

## Per-organ result

| Model | Organ | Dice | HD95 (mm) | NSD@1 mm |
|---|---|---:|---:|---:|
| E1 | Right ventricle (RV) | 0.8881 ± 0.0061 | 4.9288 ± 0.8270 | 0.8723 ± 0.0139 |
| E1 | Myocardium (MYO) | 0.8942 ± 0.0011 | 1.8835 ± 0.1893 | 0.9282 ± 0.0030 |
| E1 | Left ventricle (LV) | 0.9409 ± 0.0009 | 1.9308 ± 0.1991 | 0.9313 ± 0.0040 |
| E2_modify_2 | Right ventricle (RV) | 0.8909 ± 0.0015 | 4.6388 ± 0.8343 | 0.8777 ± 0.0058 |
| E2_modify_2 | Myocardium (MYO) | 0.8921 ± 0.0019 | 2.2713 ± 0.0570 | 0.9227 ± 0.0026 |
| E2_modify_2 | Left ventricle (LV) | 0.9388 ± 0.0029 | 2.1810 ± 0.3052 | 0.9269 ± 0.0089 |

## Decision

**Yellow / efficiency-oriented result.** E2_modify_2 keeps nearly the same mean Dice as E1 and clearly improves speed and memory, but it does not improve the three-seed mean Dice, HD95, or NSD. The defensible claim is an accuracy-efficiency trade-off, not a universal accuracy gain.
