# ACDC v1 Formal Comparison: E1 vs E2_modify_2 (Seed 42)

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)  
**Evaluation date:** 2026-09-02  
**Platform:** RunPod RTX 4090  

## 1. Fair Evaluation Protocol

- Split: 70 training, 10 validation, and 20 isolated test patients.
- Both models used 300 epochs, seed 42, and the same input, augmentation, optimizer, and learning-rate protocol.
- The best checkpoint was selected only by validation Dice, with lower validation HD95 as the tie-breaker.
- The test set was never used for checkpoint selection.
- One frozen evaluator was applied to the same 20 patients and 40 ED/ES volumes.
- Metrics: Dice, HD95 in millimeters, and NSD at a fixed 1 mm tolerance.
- Dataset limitation: the Hugging Face derivative used here contains an LV-mask-centred crop. Results must be interpreted with this limitation.

## 2. Overall Test Results

| Model | Mean Dice | Mean HD95 (mm) | Mean NSD@1mm | Training time | Mean epoch | Peak memory | Inference |
|---|---:|---:|---:|---:|---:|---:|---:|
| E1: original four-direction SS2D | **90.83%** | **2.714** | **91.06%** | 1.205 h | 13.776 s | 9.607 GB | 1.866 ms/slice |
| E2_modify_2: grouped 2D bidirectional scan | 90.55% | 2.982 | 90.44% | **0.856 h** | **9.617 s** | **7.211 GB** | **1.273 ms/slice** |

Compared with E1, E2_modify_2:

- decreased Dice by 0.28 percentage points;
- increased HD95 by 0.268 mm;
- decreased NSD by 0.63 percentage points;
- reduced total training time by 28.98%;
- reduced mean epoch time by 30.19%;
- reduced peak allocated GPU memory by 24.94%;
- reduced inference time per slice by 31.80%;
- kept the same 27,427,636 parameters.

## 3. Per-Structure Results

| Structure | E1 Dice | E2 Dice | Dice delta | E1 HD95 | E2 HD95 | E1 NSD | E2 NSD |
|---|---:|---:|---:|---:|---:|---:|---:|
| Right ventricle | 89.05% | **89.09%** | +0.04 pp | **4.171** | 4.207 | 87.44% | **87.58%** |
| Myocardium | **89.32%** | 89.03% | -0.29 pp | **2.092** | 2.206 | **92.47%** | 92.06% |
| Left ventricle | **94.13%** | 93.54% | -0.59 pp | **1.878** | 2.533 | **93.27%** | 91.66% |

Right-ventricle Dice and NSD increased slightly. Myocardium and left-ventricle metrics decreased slightly, with the largest boundary degradation in the left ventricle. Because this is one seed, it is not a statistically stable structure-level conclusion.

## 4. Training and Checkpoint Archive

| Item | E1 | E2_modify_2 |
|---|---|---|
| Source commit | `d151646082d3f4f1a7b3995fb174f3e0a65cb92f` | `cf8ccfacf7931666c11971dc5ab3431d38863fa5` |
| Best validation epoch | 230 | 242 |
| Best validation Dice | 0.899855 | 0.901558 |
| Best validation HD95 | 2.390 mm | 2.417 mm |
| Checkpoint SHA-256 | `a0f1cdff...c900b2c3` | `cadec1fb...7b926e4f` |
| Exit code | 0 | 0 |
| Epoch 300 completed | Yes | Yes |

Checkpoints, datasets, patient images, and NIfTI predictions are excluded from GitHub.

## 5. Decision Gate

**Decision: Yellow.**

E2_modify_2 provides clear training-time, memory, and inference-efficiency gains on ACDC seed 42, but its test Dice, HD95, and NSD are slightly worse than E1. The current ACDC result therefore supports an efficiency-accuracy trade-off, not a simultaneous accuracy and efficiency improvement. No statistically stable claim should be made until multi-seed ACDC evaluation is completed.

A defensible paper statement is: the coverage-preserving bidirectional scan retains approximately 90.55% Dice on cardiac MRI while reducing training time by about 29% and peak memory by about 25%, although boundary accuracy still requires improvement.

## 6. Qualitative Case Selection

The comparison uses the same patient, cardiac phase, slice, preprocessing, and colors:

`Input MRI | Ground Truth | E1 | E2_modify_2`

- Typical: combined model Dice closest to the test-set median.
- Difficult: lowest combined model Dice.
- E2 failure: largest negative E2_modify_2 minus E1 Dice difference.
- Thin-myocardium/boundary: highest GT myocardium surface-to-volume ratio.

Medical-image PDF and PNG files are provided for the paper and PPT but are not uploaded to GitHub.

## 7. Missing Items

- FLOPs are marked unavailable because no reliable measurement was obtained.
- Only seed 42 is complete for ACDC, so mean ± std and statistical significance are not yet available.

