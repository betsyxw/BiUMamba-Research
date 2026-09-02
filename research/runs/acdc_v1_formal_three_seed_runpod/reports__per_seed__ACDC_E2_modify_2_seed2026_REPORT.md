# E2_modify_2 ACDC v1 seed 2026 report

- Exit status: successful.
- Best validation epoch: 251.
- Mean Dice: 0.908327.
- Mean HD95: 3.311561 mm.
- Mean NSD@1 mm: 0.912951.
- Training time: 0.8105 h.
- Mean epoch time: 9.1484 s.
- Peak GPU memory: 6.7160 GiB.
- Parameters: 27,427,636.
- Inference time: 1.1700 ms/slice.
- FLOPs: N/A; selective-scan custom operators are not counted reliably by generic profilers.

## Per-organ metrics

| Organ | Dice | HD95 (mm) | NSD@1 mm |
|---|---:|---:|---:|
| Right ventricle (RV) | 0.892412 | 5.600428 | 0.884232 |
| Myocardium (MYO) | 0.891858 | 2.311488 | 0.921784 |
| Left ventricle (LV) | 0.940711 | 2.022766 | 0.932837 |
