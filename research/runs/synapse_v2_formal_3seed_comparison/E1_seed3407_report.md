# E1 Synapse v2 Formal Test — Seed 3407

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

## Completion and checkpoint audit

- Training exit status: `0`
- Training epochs: `300`
- Validation history: complete (`300` epoch records)
- Training/test text logs: archived and hash-audited
- Best validation epoch: `209`
- Checkpoint SHA-256: `b20a3532eee54c138f5845c7bc7b0b3755a30d14504c54d7ea05fb9806cc4bf7`
- Evaluator SHA-256: `7b7f40f76b57155139005ba08815d2c99bcdc454e00303b4e1b2fe6c63b4dacb`
- Platform: `JAIST HAKUSAN A100`
- GPU: `NVIDIA A100-PCIE-40GB`

## Isolated 12-case test results

- Mean Dice: **76.12%**
- Mean HD95: **37.31 mm**
- Mean NSD@1 mm: **69.80%**

## Per-organ results

| Organ | Dice (%) | HD95 (mm) | NSD@1 mm (%) |
|---|---:|---:|---:|
| Aorta | 85.63 | 6.41 | 80.69 |
| Gallbladder | 55.64 | 113.28 | 58.05 |
| Left Kidney | 81.25 | 45.08 | 77.60 |
| Right Kidney | 76.25 | 43.71 | 70.86 |
| Liver | 93.10 | 30.15 | 79.66 |
| Pancreas | 53.73 | 16.74 | 51.17 |
| Spleen | 87.81 | 20.97 | 80.94 |
| Stomach | 75.53 | 22.14 | 59.39 |

## Training and efficiency record

- Total training + validation time: 9.44 h
- Mean epoch time: 109.94 s
- Peak training allocated memory: 12.07 GiB
- Parameters: 27,427,761
- THOP MACs: 3.158 G (custom selective-scan operations may be undercounted)
- Convention-based FLOPs (2 × MACs): 6.316 G
- Model forward time: 11.851 ms/slice on NVIDIA A100-PCIE-40GB

Timing from different GPU models must not be directly used for an efficiency superiority claim.
