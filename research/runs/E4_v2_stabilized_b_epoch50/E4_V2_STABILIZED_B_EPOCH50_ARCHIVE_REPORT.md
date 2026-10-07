# E4_v2_stabilized_B Epoch-50 Archive and Cross-Experiment Comparison

**Research Author and Repository Maintainer:** xuwen
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

## E4_v2-B result

- Completed: 50/50 epochs, exit code 0.
- Validation-selected checkpoint: Epoch 50.
- Official test Mean Dice: **74.9931%**.
- Official test Mean HD95: **37.9087**.
- Training-only time: **4,890.43 s (1.3585 h)**.
- Mean epoch time: **97.81 s**.
- End-to-end wall time including five held-out validations and final test: **6,509 s (1.8081 h)**.
- Peak allocated/reserved GPU memory: **12.058 / 13.189 GB**.
- Final training loss: **0.1046**.

## Overall comparison

| Experiment | Epochs | Protocol | Mean Dice | Mean HD95 | Mean epoch | Peak memory |
|---|---:|---|---:|---:|---:|---:|
| E1 | 300 | Full300 | 80.0488% | 24.6136 | 177.86 s | 15.377 GB |
| E2 | 300 | Full300 | 78.6080% | 26.1111 | 164.48 s | 11.269 GB |
| E2_modify_2 | 300 | Full300 | 80.2540% | 21.9206 | 157.06 s | 11.551 GB |
| E3_screen50 | 50 | Screen50 | 75.6773% | 36.0624 | 152.66 s | 13.587 GB |
| E3_full300 | 300 | Full300 | 80.0049% | 25.5669 | 139.09 s | 13.587 GB |
| E4_version_1_full300 | 300 | Full300 | 70.9089% | 35.3190 | 117.91 s | 14.191 GB |
| E4_v2_stabilized_b_epoch50 | 50 | Screen50+held-out | 74.9931% | 37.9087 | 97.81 s | 12.058 GB |

## Per-organ E4_v2-B test result

| Organ | Dice | HD95 | Dice change vs E2_modify_2 | HD95 change vs E2_modify_2 |
|---|---:|---:|---:|---:|
| Aorta | 82.9401% | 14.8694 | -3.6901 pt | -5.0710 |
| Gallbladder | 64.3470% | 46.8933 | -3.5032 pt | 20.7948 |
| Left kidney | 84.0758% | 30.7352 | -1.2347 pt | 0.7495 |
| Right kidney | 72.9395% | 59.2118 | -7.7806 pt | 27.6659 |
| Liver | 90.9171% | 31.6147 | -3.2177 pt | 10.4474 |
| Pancreas | 53.4397% | 18.3433 | -5.2843 pt | 9.3282 |
| Spleen | 80.5223% | 61.5219 | -9.2785 pt | 39.9701 |
| Stomach | 70.7632% | 40.0799 | -8.0984 pt | 24.0203 |

## Interpretation

The stabilization engineering succeeded: the 50-epoch run completed normally, alpha remained persistent in checkpoints, and the previous catastrophic trajectory mismatch did not recur. However, E4_v2-B did not establish an accuracy gain. Relative to the previous E3 50-epoch screen, Dice was 0.6842 points lower and HD95 was 1.8463 higher.

This is **not a controlled architectural comparison**. E4_v2-B trained on 1,778 slices because 433 slices from four cases were reserved for validation, whereas earlier experiments used all 2,211 training slices and a different checkpoint-selection protocol. Therefore, its 5.2609-point Dice gap versus E2_modify_2 is confounded by reduced training data and protocol changes.

## Decision

- Keep **E2_modify_2** as the current main model and strongest valid full-300 result.
- Treat **E4_v2-B** as a successful stability pilot but an inconclusive accuracy experiment.
- Before any publication claim, freeze one common train/validation/test split and rerun E1, E2_modify_2, E3 and E4_v2-B under identical epochs, checkpoint selection and seeds.
- Do not proceed directly to a 300-epoch E4_v2-B run under the current unmatched protocol.
