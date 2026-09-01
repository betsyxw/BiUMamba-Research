# Synapse v2 Formal Three-Seed Comparison

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

All values use the frozen 14/4/12 Synapse v2 protocol. Checkpoints were selected only by validation Dice (HD95 tie-breaker), and the isolated 12-case test set was evaluated once after training.

## Overall test results

| Method | Dice (%) | HD95 (mm) | NSD@1 mm (%) |
|---|---:|---:|---:|
| E1 | 76.84 ± 1.15 | 32.13 ± 4.95 | 71.59 ± 2.25 |
| E2_modify_2 | 76.66 ± 1.22 | 33.12 ± 5.06 | 71.59 ± 1.73 |

## Per-organ mean changes (E2_modify_2 − E1)

| Organ | Dice (pp) | HD95 (mm) | NSD (pp) |
|---|---:|---:|---:|
| Aorta | -0.44 | -0.85 | -0.46 |
| Gallbladder | +1.58 | +3.28 | +0.44 |
| Left Kidney | +1.25 | +5.67 | +1.84 |
| Right Kidney | +2.20 | -1.19 | +1.78 |
| Liver | +0.25 | -3.68 | +0.97 |
| Pancreas | -2.81 | -0.48 | -1.66 |
| Spleen | -1.79 | +2.12 | -2.27 |
| Stomach | -1.68 | +3.09 | -0.63 |

## Paired mean differences (E2_modify_2 − E1)

- Dice: -0.18 percentage points
- HD95: +1.00 mm (lower is better)
- NSD@1 mm: -0.00 percentage points

## Same-hardware efficiency comparison (seed 42, RTX 4090)

| Method | Train time (h) | Mean epoch (s) | Peak train memory (GiB) | Params | Inference (ms/slice) |
|---|---:|---:|---:|---:|---:|
| E1 | 8.61 | 102.69 | 11.96 | 27,427,761 | 4.786 |
| E2_modify_2 | 9.01 | 107.42 | 9.04 | 27,427,761 | 6.950 |

THOP reports the same parameter count and nominal convolution/linear MAC total for both methods, but custom selective-scan operations may be undercounted. Measured time and memory are therefore the primary efficiency evidence.

## Decision: **Yellow**

The metrics are mixed or close; report the efficiency/accuracy trade-off without claiming universal superiority.

The reported standard deviation is the sample standard deviation across the preregistered seeds 42, 2026, and 3407. With only three seeds, the report does not claim statistical significance from a normality-based test.

## Audit notes

- Test metrics: Dice, physical HD95 in mm, and NSD at 1 mm.
- Eight organs are aggregated by organ and then macro-averaged.
- E2_modify_2 inference used `grouped_2d_bidirectional_sum`; an earlier wrong-mode dry run was excluded and recorded in `FORMAL_TEST_CORRECTION_AUDIT.md`.
- Cross-platform source differences were audited as comments/whitespace only; no executable model difference was found.
- HAKUSAN A100 and RunPod RTX 4090 were both used for fixed-checkpoint inference. Accuracy aggregation is valid, but cross-platform timing is not used as the primary efficiency comparison.
- Fair efficiency claims must use E1 and E2_modify_2 measured on the same RTX 4090 hardware.
