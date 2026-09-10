# E1-Narrow three-seed statistical report

Updated: 20260911

## Seed-level results

| Method | Dice (%) | HD95 | NSD (%) |
|---|---:|---:|---:|
| E1 | 76.84 ± 1.15 | 32.13 ± 4.95 | 71.59 ± 2.25 |
| E1-Narrow | 75.04 ± 2.82 | 33.89 ± 3.99 | 69.15 ± 2.34 |
| BiUMamba | 76.66 ± 1.22 | 33.12 ± 5.06 | 71.59 ± 1.73 |

Values are mean ± sample standard deviation across fixed seeds 42, 2026, and 3407.

## Patient-level paired results

Each of the 12 Synapse patients was first averaged across the three fixed seeds. Positive differences favor the first method for Dice and NSD; negative differences favor the first method for HD95.

| Contrast | Metric | Mean difference | Bootstrap 95% CI | Selected test | Raw p | Holm p | Effect |
|---|---|---:|---:|---|---:|---:|---:|
| E1-Narrow − E1 | Dice | −0.0180 | [−0.0284, −0.0093] | Paired t-test | 0.0047 | 0.0094 | Cohen dz = −1.019 |
| E1-Narrow − E1 | HD95 | +1.7594 | [−1.2521, +4.8486] | Paired t-test | 0.2964 | 0.2964 | Cohen dz = +0.316 |
| E1-Narrow − E1 | NSD | −0.0244 | [−0.0350, −0.0143] | Paired t-test | 0.0010 | 0.0030 | Cohen dz = −1.282 |
| BiUMamba − E1-Narrow | Dice | +0.0162 | [+0.0026, +0.0327] | Wilcoxon signed-rank | 0.0342 | 0.0683 | Rank-biserial = +0.692 |
| BiUMamba − E1-Narrow | HD95 | −0.7644 | [−4.2477, +2.3491] | Paired t-test | 0.6684 | 0.6684 | Cohen dz = −0.127 |
| BiUMamba − E1-Narrow | NSD | +0.0244 | [+0.0123, +0.0397] | Wilcoxon signed-rank | 0.0037 | 0.0111 | Rank-biserial = +0.949 |

Bootstrap used 10,000 patient-level resamples and seed 20260911. Normality was checked on paired differences using Shapiro–Wilk. Holm correction was applied across Dice, HD95, and NSD within each contrast.

## Interpretation

E1-Narrow was significantly worse than E1 for Dice and NSD after Holm correction. BiUMamba had higher observed Dice than E1-Narrow, but this Dice difference did not remain significant after Holm correction. Its NSD advantage remained significant. BiUMamba also had lower observed seed-level Dice and NSD variability, but three seeds do not support a formal variance claim.
