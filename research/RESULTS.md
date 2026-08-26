# Verified results

Only completed measurements are recorded here. Ongoing experiments are never
filled with estimates.

## E1 — VM-UNet Synapse baseline

- Best checkpoint: epoch 286
- Mean Dice: 0.800488 (80.0488%)
- Mean HD95: 24.6136
- Training duration: approximately 15 h 49 min
- Peak GPU memory: approximately 14.3 GB
- Test volumes: 12
- Qualitative exports: 36 NIfTI files (not stored in GitHub)

| Organ | Dice (%) | HD95 |
|---|---:|---:|
| Aorta | 85.7881 | 22.7990 |
| Gallbladder | 68.2824 | 26.3341 |
| Left Kidney | 85.0418 | 36.0768 |
| Right Kidney | 78.9200 | 37.9346 |
| Liver | 93.8822 | 23.3211 |
| Pancreas | 60.9000 | 9.9068 |
| Spleen | 87.8004 | 22.7226 |
| Stomach | 79.7755 | 17.8141 |

## E2 — bidirectional fixed sum

Status: training. Final Dice and HD95 will be added only after epoch 300 and
the complete Synapse test pass.
