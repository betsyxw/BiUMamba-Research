# E1 ACDC v1 seed 3407 report

- Exit status: successful.
- Best validation epoch: 76.
- Mean Dice: 0.909782.
- Mean HD95: 3.098752 mm.
- Mean NSD@1 mm: 0.916558.
- Training time: 1.1791 h.
- Mean epoch time: 13.5198 s.
- Peak GPU memory: 8.9451 GiB.
- Parameters: 27,427,636.
- Inference time: 1.8113 ms/slice.
- FLOPs: N/A; selective-scan custom operators are not counted reliably by generic profilers.

## Per-organ metrics

| Organ | Dice | HD95 (mm) | NSD@1 mm |
|---|---:|---:|---:|
| Right ventricle (RV) | 0.892586 | 5.810724 | 0.885078 |
| Myocardium (MYO) | 0.895283 | 1.722360 | 0.930211 |
| Left ventricle (LV) | 0.941477 | 1.763173 | 0.934384 |
