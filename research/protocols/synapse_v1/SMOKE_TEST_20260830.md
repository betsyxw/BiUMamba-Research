# Synapse v1 Evaluator Smoke Test

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

## Status

- Date: 2026-08-30 (Asia/Tokyo)
- Environment: RunPod, VM-UNet `vmunet` Conda environment
- Evaluated cases: 12/12
- Evaluated organs: 8/8
- Exit code: `0`
- Output files: `overall_metrics.json`, `per_case_metrics.csv`, `per_organ_metrics.csv`, and `input_hashes.csv`

The smoke test used the archived E2_modify_2 prediction and ground-truth NIfTI files to verify that the frozen `synapse_v1` evaluator completes an end-to-end run. No training, checkpoint, prediction, or patient image was modified.

## Overall output

| Metric | Value |
|---|---:|
| Mean Dice | 0.7921235710 |
| Mean HD95 | 27.5487230297 mm |
| Mean NSD@1 mm | 0.7466564990 |

## Per-organ output

| Organ | Dice | HD95 (mm) | NSD@1 mm |
|---|---:|---:|---:|
| Aorta | 0.8663017067 | 10.9397040255 | 0.8230057083 |
| Gallbladder | 0.5951686790 | 86.5442077504 | 0.6299594321 |
| Left Kidney | 0.8531049421 | 28.6323689589 | 0.8298059432 |
| Right Kidney | 0.8072011197 | 30.4676236461 | 0.7601278879 |
| Liver | 0.9413481746 | 20.0508498553 | 0.8354487163 |
| Pancreas | 0.5872400426 | 8.3546288324 | 0.5984796146 |
| Spleen | 0.8980083946 | 20.5809305009 | 0.8412984669 |
| Stomach | 0.7886155088 | 14.8194706677 | 0.6551262230 |

## Output integrity

| File | SHA-256 |
|---|---|
| `input_hashes.csv` | `e275e210b2b6089814ee4c80f65dc94caca5117cbffc52ff0e4f045c0ddda4d5` |
| `overall_metrics.json` | `f91b064d6c2f4673c47b96693e523c1dc9466991ffa1314d2d713b50a31a09fa` |
| `per_case_metrics.csv` | `1c95205d8b880826435326cd6ffcd651d7ab5af32a817186279e7ae722a7e9f0` |
| `per_organ_metrics.csv` | `8bf9a6b46707db725c4efd3431a14b830a3949c12c44779f64c6a61c7cd5a9a3` |

## Interpretation

This is a runtime and output-integrity smoke test, not a new model-ranking result. The frozen evaluator uses physical voxel spacing, explicit empty-mask rules, NSD@1 mm, and case-to-organ-to-overall macro aggregation. Consequently, its values are not expected to be numerically identical to historical reports produced by the original evaluation implementation. Future formal comparisons must evaluate every model with this same frozen evaluator.

The largest boundary error in this smoke run is the gallbladder HD95. This is an observed output to inspect later, not evidence of an evaluator failure.
