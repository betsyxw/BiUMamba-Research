# E2_modify_2 Synapse v2 Formal Test — Seed 3407

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

## Completion and checkpoint audit

- Training exit status: `0`
- Training epochs: `300`
- Validation history: complete (`300` epoch records)
- Training/test text logs: archived and hash-audited
- Best validation epoch: `225`
- Checkpoint SHA-256: `35f7adb3d2c0024561d4567f62da342094dad1b09f16e733c0814059611c287a`
- Evaluator SHA-256: `7b7f40f76b57155139005ba08815d2c99bcdc454e00303b4e1b2fe6c63b4dacb`
- Platform: `RunPod RTX 4090`
- GPU: `NVIDIA GeForce RTX 4090`

## Isolated 12-case test results

- Mean Dice: **75.38%**
- Mean HD95: **37.21 mm**
- Mean NSD@1 mm: **69.74%**

## Per-organ results

| Organ | Dice (%) | HD95 (mm) | NSD@1 mm (%) |
|---|---:|---:|---:|
| Aorta | 85.15 | 17.49 | 80.36 |
| Gallbladder | 53.10 | 104.46 | 55.24 |
| Left Kidney | 81.74 | 38.26 | 77.94 |
| Right Kidney | 77.60 | 36.59 | 72.95 |
| Liver | 93.64 | 22.42 | 81.69 |
| Pancreas | 53.68 | 15.99 | 54.75 |
| Spleen | 84.89 | 36.55 | 77.21 |
| Stomach | 73.20 | 25.94 | 57.79 |

## Training and efficiency record

- Total training + validation time: 7.89 h
- Mean epoch time: 94.03 s
- Peak training allocated memory: 9.707 GB
- Parameters: 27,427,761
- THOP MACs: 3.158 G (custom selective-scan operations may be undercounted)
- Convention-based FLOPs (2 × MACs): 6.316 G
- Model forward time: 7.261 ms/slice on NVIDIA GeForce RTX 4090

Timing from different GPU models must not be directly used for an efficiency superiority claim.
