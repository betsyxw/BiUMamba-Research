# E2_modify_2 Synapse v2 Formal Test — Seed 2026

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

## Completion and checkpoint audit

- Training exit status: `0`
- Training epochs: `300`
- Validation history: complete (`300` epoch records)
- Training/test text logs: archived and hash-audited
- Best validation epoch: `265`
- Checkpoint SHA-256: `7da0bba77d7fc979c2b9ffe370df91b14844935ab3dd69d264fc71bae62f4415`
- Evaluator SHA-256: `7b7f40f76b57155139005ba08815d2c99bcdc454e00303b4e1b2fe6c63b4dacb`
- Platform: `RunPod RTX 4090`
- GPU: `NVIDIA GeForce RTX 4090`

## Isolated 12-case test results

- Mean Dice: **77.79%**
- Mean HD95: **27.47 mm**
- Mean NSD@1 mm: **73.18%**

## Per-organ results

| Organ | Dice (%) | HD95 (mm) | NSD@1 mm (%) |
|---|---:|---:|---:|
| Aorta | 85.97 | 7.82 | 80.96 |
| Gallbladder | 60.64 | 80.84 | 62.05 |
| Left Kidney | 85.59 | 27.75 | 84.23 |
| Right Kidney | 80.88 | 31.73 | 76.72 |
| Liver | 94.06 | 17.70 | 83.34 |
| Pancreas | 55.20 | 10.53 | 56.80 |
| Spleen | 87.22 | 21.58 | 82.05 |
| Stomach | 72.77 | 21.79 | 59.30 |

## Training and efficiency record

- Total training + validation time: 8.78 h
- Mean epoch time: 104.76 s
- Peak training allocated memory: 9.04 GiB
- Parameters: 27,427,761
- THOP MACs: 3.158 G (custom selective-scan operations may be undercounted)
- Convention-based FLOPs (2 × MACs): 6.316 G
- Model forward time: 7.213 ms/slice on NVIDIA GeForce RTX 4090

Timing from different GPU models must not be directly used for an efficiency superiority claim.
