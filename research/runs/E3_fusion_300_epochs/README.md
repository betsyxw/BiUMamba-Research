# E3 Static Fusion — 300-Epoch Archive

**Research Author and Repository Maintainer:** xuwen
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

E3 uses the coverage-preserving channel-grouped horizontal/vertical
bidirectional scan from E2_modify_2 and replaces fixed sum with static
learnable fusion.

## Official result

| Experiment | Epochs | Mean Dice ↑ | Mean HD95 ↓ | Mean epoch time | Peak sampled memory |
|---|---:|---:|---:|---:|---:|
| E1 | 300 | 80.0488% | 24.6136 | 177.86 s | 15.377 GB |
| E2 | 300 | 78.6080% | 26.1111 | 164.48 s | 11.269 GB |
| **E2_modify_2** | **300** | **80.2540%** | **21.9206** | 157.06 s | 11.551 GB |
| E3 screening | 50 | 75.6773% | 36.0624 | 152.66 s | 13.587 GB |
| E3 full run | 300 | 80.0049% | 25.5669 | **139.09 s** | 13.587 GB |

E3 did not replace E2_modify_2. Compared with E2_modify_2, E3 lost `0.2491`
Dice percentage points and worsened HD95 by `3.6464`. It remains a useful
negative/neutral ablation showing that static input-independent weighting is
insufficient after two-dimensional coverage has been restored.

## Files

- [`E3_static_fusion_full300_archive_report.md`](E3_static_fusion_full300_archive_report.md): complete method, configuration, result, efficiency and decision record.
- [`E3_static_fusion_full300_metrics.csv`](E3_static_fusion_full300_metrics.csv): overall and eight-organ E3 metrics.
- [`E1_E2_E2_modify_2_E3_overall_comparison.csv`](E1_E2_E2_modify_2_E3_overall_comparison.csv): E1, E2, E2_modify_2, E3-50 and E3-300 overall comparison.
- [`E1_E2_E2_modify_2_E3_per_organ_comparison.csv`](E1_E2_E2_modify_2_E3_per_organ_comparison.csv): per-organ comparison and E3 versus E2_modify_2 deltas.
- [`E1_E2_E2M2_E3_per_organ_PPT_summary_CN_EN_JP.md`](E1_E2_E2M2_E3_per_organ_PPT_summary_CN_EN_JP.md): Chinese, English and Japanese midterm-presentation summary.
- [`E3_static_fusion_full300_manifest.txt`](E3_static_fusion_full300_manifest.txt): reproducibility manifest and hashes.

Datasets, patient volumes, NIfTI predictions, checkpoints, pretrained weights,
compressed archives and credentials are intentionally excluded.
