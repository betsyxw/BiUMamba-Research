# E1–E4 Synapse Experiment Comparison

**Research Author and Repository Maintainer:** xuwen

**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

## Overall results

| Experiment | Epochs | Mean Dice ↑ | Mean HD95 ↓ | Mean epoch time ↓ | Peak memory ↓ |
|---|---:|---:|---:|---:|---:|
| E1 | 300 | 80.0488% | 24.6136 | 177.8620 s | 14,665 MiB |
| E2 | 300 | 78.6080% | 26.1111 | 164.4835 s | 10,747 MiB |
| **E2_modify_2** | **300** | **80.2540%** | **21.9206** | 157.0617 s | **11,016 MiB** |
| E3 screening | 50 | 75.6773% | 36.0624 | 152.6574 s | 12,958 MiB |
| E3 | 300 | 80.0049% | 25.5669 | 139.0918 s | 12,958 MiB |
| E4 Version 1 | 300 | 70.9089% | 35.3190 | **117.9129 s** | 13,534 MiB |

The 50-epoch E3 result is included for screening-history completeness and must not be treated as a direct full-training comparison.

## E4 relative to E2_modify_2

- Dice: −9.3451 percentage points.
- HD95: +13.3985, indicating worse boundary accuracy.
- Mean epoch time: 24.93% faster.
- Peak memory: 22.86% higher.
- Dice decreased for all eight organs.
- Aortic HD95 improved by 2.2168; HD95 worsened for the other seven organs.

Therefore, the E4 Version 1 run provides speed but fails the accuracy, boundary-quality, memory, and organ-stability decision criteria.

## Organ-level diagnosis

The largest Dice degradations relative to E2_modify_2 occurred in:

1. Right kidney: −15.5349 pt.
2. Pancreas: −14.4165 pt.
3. Stomach: −13.3149 pt.
4. Gallbladder: −9.4606 pt.
5. Left kidney: −8.5965 pt.

The left-kidney HD95 increased by 44.5683, indicating a serious boundary/localization failure. The liver was comparatively stable in Dice (−1.3111 pt), but did not improve overall.

## Current scientific interpretation

E2 demonstrated that removing vertical coverage harms segmentation. E2_modify_2 recovered 2D coverage and became the strongest current result. E3 showed that a globally shared static fusion weight does not reliably improve the model. E4 Version 1 attempted case- and channel-dependent adaptive fusion, but this full run diverged strongly from its favorable 50-epoch screening trajectory.

The immediate conclusion is not “adaptive fusion can never work.” The defensible conclusion is:

> The current constrained residual adaptive-gate implementation is not reproducibly stable under the full-300 training protocol.

Until the screen/full mismatch is explained, E2_modify_2 should remain the main model and E4 should be reported as a negative ablation.
