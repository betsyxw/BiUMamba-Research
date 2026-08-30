# E2_modify_1 Synapse 50-Epoch Screening Archive

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

This folder mirrors the complete text-only archive for **E2_modify_1: alternating-axis bidirectional scan with fixed-sum fusion** under the matched Synapse 50-epoch screening protocol.

The canonical implementation and original archive remain under:

`experiments/E2_modify_1/`

The duplicate under `research/runs/` is provided so E2_modify_1 can be found next to the E1, E2, E2_modify_2, E3, and E4 experiment records. The original files are intentionally retained to avoid breaking existing links and reproducibility references.

## Key results

| Metric | Result |
|---|---:|
| Epochs | 50 |
| Seed | 42 |
| Mean Dice | 72.5396% |
| Mean HD95 | 35.5797 |
| Final training loss | 0.1478 |
| Mean epoch time | 213.81 s |
| Peak GPU memory | 10,396 MiB |

This was a screening experiment, not a converged 300-epoch result. It must not be directly ranked against the 300-epoch E1, E2, or E2_modify_2 results.

## Included files

- `E2_modify_1_screen50_report.md`
- `E2_modify_1_screen50_metrics.csv`
- `manifest.json`
- `train.info.log`
- `train_console.log`
- `E2_modify_1_vs_E2_modify_2_screen50_comparison.md`
- `E2_modify_1_vs_E2_modify_2_screen50_comparison.csv`

## Screening decision

Compared with E2_modify_1, E2_modify_2 improved Mean Dice by 2.5341 percentage points, improved Dice in seven of eight organs, and reduced mean epoch time by 20.16%. However, its screening HD95 was 4.8362 worse. E2_modify_2 was therefore selected as the first full-training candidate, with boundary outliers explicitly flagged for review after convergence.

No datasets, patient images, NIfTI predictions, checkpoints, pretrained weights, credentials, or authentication information are included.
