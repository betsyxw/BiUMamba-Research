# E1 Synapse v2 Formal Test — Seed 42

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

## Completion and checkpoint audit

- Training exit status: `0`
- Training epochs: `300`
- Validation history: complete (`300` epoch records)
- Training/test text logs: archived and hash-audited
- Best validation epoch: `242`
- Checkpoint SHA-256: `91d446b37909eb33c1533d9b6dcd6c7ddfc0fed722d67c8bcd08024341316b28`
- Evaluator SHA-256: `7b7f40f76b57155139005ba08815d2c99bcdc454e00303b4e1b2fe6c63b4dacb`
- Platform: `RunPod RTX 4090`
- GPU: `NVIDIA GeForce RTX 4090`

## Isolated 12-case test results

- Mean Dice: **76.24%**
- Mean HD95: **31.63 mm**
- Mean NSD@1 mm: **70.86%**

## Per-organ results

| Organ | Dice (%) | HD95 (mm) | NSD@1 mm (%) |
|---|---:|---:|---:|
| Aorta | 85.79 | 18.72 | 79.75 |
| Gallbladder | 56.24 | 90.78 | 58.63 |
| Left Kidney | 81.85 | 25.15 | 78.17 |
| Right Kidney | 76.75 | 27.56 | 73.63 |
| Liver | 93.45 | 26.31 | 81.11 |
| Pancreas | 55.39 | 12.93 | 57.39 |
| Spleen | 87.22 | 30.75 | 81.04 |
| Stomach | 73.25 | 20.85 | 57.14 |

## Training and efficiency record

- Total training + validation time: 8.61 h
- Mean epoch time: 102.69 s
- Peak training allocated memory: 11.96 GiB
- Parameters: 27,427,761
- THOP MACs: 3.158 G (custom selective-scan operations may be undercounted)
- Convention-based FLOPs (2 × MACs): 6.316 G
- Model forward time: 4.786 ms/slice on NVIDIA GeForce RTX 4090

Timing from different GPU models must not be directly used for an efficiency superiority claim.
