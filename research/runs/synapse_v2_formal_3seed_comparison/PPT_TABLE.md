# Synapse v2 Formal Three-Seed Result (PPT-ready)

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

| Method | Dice (%) ↑ | HD95 (mm) ↓ | NSD@1 mm (%) ↑ | Peak train memory (seed 42, GB) ↓ |
|---|---:|---:|---:|---:|
| E1: Original four-direction VM-UNet | 76.84 ± 1.15 | **32.13 ± 4.95** | **71.59 ± 2.25** | 12.842 |
| E2_modify_2: Grouped 2D bidirectional scan | 76.66 ± 1.22 | 33.12 ± 5.06 | 71.59 ± 1.73 | **9.707** |

**Decision: Yellow.** E2_modify_2 reduces peak training memory by approximately 24.4%, but the three-seed test accuracy is essentially tied and HD95 is 1.00 mm worse. Under the frozen Synapse_v2 protocol, it should be described as an accuracy–memory trade-off, not as universally more accurate or faster.

## Per-organ change: E2_modify_2 − E1

| Organ | Dice change (pp) | HD95 change (mm) | NSD change (pp) |
|---|---:|---:|---:|
| Aorta | -0.44 | -0.85 | -0.46 |
| Gallbladder | +1.58 | +3.28 | +0.44 |
| Left Kidney | +1.25 | +5.67 | +1.84 |
| Right Kidney | +2.20 | -1.19 | +1.78 |
| Liver | +0.25 | -3.68 | +0.97 |
| Pancreas | -2.81 | -0.48 | -1.66 |
| Spleen | -1.79 | +2.12 | -2.27 |
| Stomach | -1.68 | +3.09 | -0.63 |

Positive Dice/NSD and negative HD95 changes indicate improvement.
