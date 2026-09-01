# E1 Synapse v2 Formal Test — Seed 2026

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

## Completion and checkpoint audit

- Training exit status: `0`
- Training epochs: `300`
- Validation history: complete (`300` epoch records)
- Training/test text logs: archived and hash-audited
- Best validation epoch: `263`
- Checkpoint SHA-256: `11d33efc81563b2d58790eb9d6ac0cabc1837e5862ceed013024710b58598501`
- Evaluator SHA-256: `7b7f40f76b57155139005ba08815d2c99bcdc454e00303b4e1b2fe6c63b4dacb`
- Platform: `JAIST HAKUSAN A100`
- GPU: `NVIDIA A100-PCIE-40GB`

## Isolated 12-case test results

- Mean Dice: **78.17%**
- Mean HD95: **27.45 mm**
- Mean NSD@1 mm: **74.12%**

## Per-organ results

| Organ | Dice (%) | HD95 (mm) | NSD@1 mm (%) |
|---|---:|---:|---:|
| Aorta | 86.06 | 7.80 | 81.84 |
| Gallbladder | 57.56 | 82.41 | 62.69 |
| Left Kidney | 84.89 | 18.21 | 82.55 |
| Right Kidney | 79.82 | 27.66 | 77.11 |
| Liver | 93.97 | 19.91 | 83.73 |
| Pancreas | 58.45 | 10.74 | 60.52 |
| Spleen | 88.37 | 33.42 | 82.87 |
| Stomach | 76.23 | 19.42 | 61.65 |

## Training and efficiency record

- Total training + validation time: 9.48 h
- Mean epoch time: 110.43 s
- Peak training allocated memory: 12.07 GiB
- Parameters: 27,427,761
- THOP MACs: 3.158 G (custom selective-scan operations may be undercounted)
- Convention-based FLOPs (2 × MACs): 6.316 G
- Model forward time: 11.940 ms/slice on NVIDIA A100-PCIE-40GB

Timing from different GPU models must not be directly used for an efficiency superiority claim.
