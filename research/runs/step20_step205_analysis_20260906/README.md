# Step 20 and Step 20.5 analysis (2026-09-06)

This directory contains the frozen three-seed statistical and error analysis
for E1 (VM-UNet) versus E2_modify_2 (BiUMamba) on Synapse, ACDC, and BUSI.
No models were retrained for this update.

## Main protocol

- Seeds: 42, 3407, and 2026.
- Patient-level comparison for Synapse and ACDC; cleaned lesion-group comparison
  for BUSI.
- Each unit is averaged across seeds before paired testing. Slices and seeds are
  not pooled as independent observations.
- Patient/group bootstrap: 10,000 resamples, seed 20260906.
- Paired t-test if the paired differences meet the recorded Shapiro-Wilk rule;
  otherwise Wilcoxon signed-rank.
- Holm correction is included for multiple metric and organ/structure tests.

## Main finding

E2_modify_2 is comparable to E1 on Synapse CT and ACDC MRI at the patient level.
On BUSI ultrasound, Dice and NSD decrease and HD95 increases. The BUSI subgroup
analysis associates the largest corrected Dice decrease with low-contrast
lesions, but this exploratory association is not evidence of causality.

## Directory map

- `statistics/`: complete paired tests, effect sizes, confidence intervals,
  anomaly tables, and paper-ready figures.
- `qualitative_figures/error_analysis/`: size, shape, contrast, precision,
  recall, false-positive, and false-negative analyses.
- `qualitative_figures/fixed_selection_v2/`: public case-selection manifests.
  Medical images and masks are intentionally excluded.
- `repro_scripts/`: scripts used to regenerate the analyses and figures from the
  private frozen result tree.
- `manifests/`: completion and run logs.

Medical images, ground-truth masks, prediction masks, checkpoints, and patient
data are not included in this public repository.
