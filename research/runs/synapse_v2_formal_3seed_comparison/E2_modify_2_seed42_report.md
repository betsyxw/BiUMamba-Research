# E2_modify_2 Synapse v2 Formal Test — Seed 42

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

## Completion and checkpoint audit

- Training exit status: `0`
- Training epochs: `300`
- Validation history: complete (`300` epoch records)
- Training/test text logs: archived and hash-audited
- Best validation epoch: `271`
- Checkpoint SHA-256: `08fe6fd0c461b9c23c82055f094f1430d129ddccdc3c5dd48828c5fa81ea6006`
- Evaluator SHA-256: `7b7f40f76b57155139005ba08815d2c99bcdc454e00303b4e1b2fe6c63b4dacb`
- Platform: `RunPod RTX 4090`
- GPU: `NVIDIA GeForce RTX 4090`

## Isolated 12-case test results

- Mean Dice: **76.82%**
- Mean HD95: **34.69 mm**
- Mean NSD@1 mm: **71.85%**

## Per-organ results

| Organ | Dice (%) | HD95 (mm) | NSD@1 mm (%) |
|---|---:|---:|---:|
| Aorta | 85.04 | 5.05 | 79.58 |
| Gallbladder | 60.43 | 111.01 | 63.39 |
| Left Kidney | 84.40 | 39.44 | 81.68 |
| Right Kidney | 80.96 | 27.04 | 77.27 |
| Liver | 93.57 | 25.21 | 82.38 |
| Pancreas | 50.25 | 12.45 | 52.53 |
| Spleen | 85.91 | 33.37 | 78.76 |
| Stomach | 73.99 | 23.94 | 59.20 |

## Training and efficiency record

- Total training + validation time: 9.01 h
- Mean epoch time: 107.42 s
- Peak training allocated memory: 9.707 GB
- Parameters: 27,427,761
- THOP MACs: 3.158 G (custom selective-scan operations may be undercounted)
- Convention-based FLOPs (2 × MACs): 6.316 G
- Model forward time: 6.950 ms/slice on NVIDIA GeForce RTX 4090

Timing from different GPU models must not be directly used for an efficiency superiority claim.
