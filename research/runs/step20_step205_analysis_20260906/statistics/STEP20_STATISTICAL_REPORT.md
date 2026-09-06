# Step 20 Statistical Report

Status: complete for the planned three-seed patient-level analysis.

## Frozen protocol

- Seeds: 42, 3407, and 2026.
- The independent unit is the patient for Synapse and ACDC and the cleaned lesion group for BUSI.
- Results are first averaged within each unit across the three seeds; slices and seeds are not pooled as independent samples.
- Bootstrap confidence intervals use 10,000 unit-level resamples with seed 20260906.
- A paired t-test is used when the paired differences pass the Shapiro-Wilk rule (p >= 0.05); otherwise a Wilcoxon signed-rank test is used.
- Holm adjustment is reported across Dice, HD95, and NSD within each dataset. Organ/structure tests have their own Holm-adjusted table.

## Main results

| Dataset | Metric | E1 mean | E2_modify_2 mean | Mean difference | Bootstrap 95% CI | Test | Holm p |
|---|---:|---:|---:|---:|---:|---|---:|
| Synapse | DICE | 0.7773 | 0.7754 | -0.0018 | [-0.0100, +0.0066] | paired t-test | 1 |
| Synapse | HD95 | 24.5919 | 25.5714 | +0.9795 | [-0.7877, +2.7089] | paired t-test | 0.9275 |
| Synapse | NSD | 0.7246 | 0.7247 | +0.0001 | [-0.0075, +0.0085] | paired t-test | 1 |
| ACDC | DICE | 0.9077 | 0.9073 | -0.0005 | [-0.0028, +0.0018] | paired t-test | 1 |
| ACDC | HD95 | 2.9144 | 3.0303 | +0.1159 | [-0.1633, +0.4120] | paired t-test | 1 |
| ACDC | NSD | 0.9106 | 0.9091 | -0.0015 | [-0.0074, +0.0038] | paired t-test | 1 |
| BUSI | DICE | 0.7546 | 0.7260 | -0.0286 | [-0.0542, -0.0046] | Wilcoxon signed-rank | 0.01074 |
| BUSI | HD95 | 30.1720 | 36.6485 | +6.4764 | [+1.6692, +12.0065] | Wilcoxon signed-rank | 0.002806 |
| BUSI | NSD | 0.5675 | 0.5316 | -0.0358 | [-0.0547, -0.0182] | Wilcoxon signed-rank | 0.001039 |

## Interpretation

E2_modify_2 achieved comparable patient-level Dice, HD95, and NSD to E1 on Synapse CT and ACDC MRI. On BUSI ultrasound, Dice and NSD decreased and HD95 increased after Holm correction. Therefore, the evidence supports an accuracy-memory trade-off on Synapse and ACDC, but not equal performance across all medical-image types.

## Supporting files

- `patient_level_paired_differences.csv`: paired unit-level source table.
- `paired_patient_statistics.csv`: complete tests, confidence intervals, and effect sizes.
- `organ_or_class_paired_statistics_holm.csv`: organ/structure/class analyses with Holm adjustment.
- `anomaly_cases/`: ranked Synapse, ACDC, and BUSI cases.
- `figures/paired_difference_forest_plot.*`: paper-ready forest plot.
- `figures/paired_difference_distributions.*`: paired-difference distributions.
