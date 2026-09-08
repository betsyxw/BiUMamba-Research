# Synapse Step 20 correction report

Last updated: 20260909

## Scope and cause

Six frozen runs (E1 and E2_modify_2; seeds 42, 3407 and 2026), twelve cases and eight organs provide 576 case-organ-seed records. The previous Step 20 reader retained only rows with status "ok", unintentionally dropping six valid single-empty penalty rows.

All six affected rows have an empty gallbladder Ground Truth mask and a nonempty prediction. This is not a missed nonempty Ground Truth organ. The CSV audit cannot establish whether the anatomy is absent or its annotation is missing.

## Unified policy

- Retain single-empty pairs with the stored Dice = 0, NSD = 0 and volume-diagonal HD95 penalty.
- Exclude both-empty undefined pairs according to the original frozen policy; none occur in these six runs.
- Do not alter checkpoints, predictions, frozen splits or original result files.
- Synapse evaluation uses spacing (1,1,1). HD95 is in protocol-space units, not verified original CT millimetres; NSD tolerance is one protocol unit.

## Corrected descriptive results

Mean ± sample standard deviation across the three fixed seeds:

| Model | Dice (%) | HD95 (protocol units) | NSD (%) |
|---|---:|---:|---:|
| E1 / VM-UNet | 76.8427 ± 1.1507 | 32.1289 ± 4.9505 | 71.5911 ± 2.2523 |
| E2_modify_2 / BiUMamba | 76.6620 ± 1.2151 | 33.1240 ± 5.0583 | 71.5904 ± 1.7345 |

The original Table 1 descriptive values were already consistent with these results. The old downstream Step 20 aggregation was not.

## Corrected patient-level paired analysis

Average organs within each case, then average the three seeds within each model and case. Pair the resulting twelve E1 and BiUMamba case means. Do not pool slices or seeds as independent patients.

Bootstrap: 10,000 patient resamples, seed 20260909; unadjusted percentile 95% confidence intervals. Existing selection rule: paired t-test if Shapiro–Wilk p >= 0.05, otherwise Wilcoxon signed-rank. All three Synapse metrics select paired t-test. Holm family: three overall metrics.

| Metric | BiUMamba − E1 | Bootstrap 95% CI | Raw p | Holm p | Cohen's dz |
|---|---:|---|---:|---:|---:|
| Dice (percentage points) | -0.18072 | [-1.00645, +0.70612] | 0.697696 | 1.000000 | -0.115114 |
| HD95 (protocol units) | +0.99505 | [-0.74899, +2.70181] | 0.300065 | 0.900196 | +0.313938 |
| NSD (percentage points) | -0.00069 | [-0.75680, +0.83275] | 0.998731 | 1.000000 | -0.000470 |

Wilcoxon sensitivity p-values are 0.518555 (Dice), 0.339355 (HD95) and 0.969727 (NSD). These do not change the significance interpretation.

The corrected organ tables retain the original eight-organ, within-metric Holm adjustment and additionally report a separate family of 24 Synapse organ-metric tests. These families must not be silently mixed.

ACDC and BUSI statistics are unchanged and retain bootstrap seed 20260906.

## Updated conclusion

On the frozen Synapse protocol, BiUMamba showed small observed mean differences from E1. The corrected patient-level paired analysis found no statistically significant differences in Dice, HD95 or NSD. This supports a cautious observed accuracy–memory trade-off, not equivalence, non-inferiority or absence of accuracy loss.

Confidence intervals are conditional on the three trained seeds and do not fully represent retraining uncertainty. No raw-mask reevaluation or equivalence/non-inferiority test was performed in this correction.
