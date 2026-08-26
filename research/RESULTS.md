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

Status: complete (seed 42, 300 epochs, exit status 0).

- Mean Dice: 0.786080 (78.6080%)
- Mean HD95: 26.1111
- Wall-clock duration: 14 h 30 min 11 s
- Mean training time per epoch: 164.48 s
- Peak sampled device memory: 10,747 MiB
- Relative to E1: Dice -1.4408 percentage points; HD95 +1.4975
- Decision: Red — audit lost transposed/vertical coverage before E3/E4

The complete report, per-organ comparison, manifests, and logs are stored in
[`runs/e2_synapse_seed42/`](runs/e2_synapse_seed42/).
