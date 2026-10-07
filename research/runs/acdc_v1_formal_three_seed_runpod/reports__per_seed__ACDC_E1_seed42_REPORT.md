# E1 ACDC v1 seed 42 report

- Exit status: successful.
- Best validation epoch: 230.
- Mean Dice: 0.908328.
- Mean HD95: 2.713670 mm.
- Mean NSD@1 mm: 0.910623.
- Training time: 1.2047 h.
- Mean epoch time: 13.7762 s.
- Peak GPU memory: 9.607 GB.
- Parameters: 27,427,636.
- Inference time: 1.8660 ms/slice.
- FLOPs: N/A; selective-scan custom operators are not counted reliably by generic profilers.

## Per-organ metrics

| Organ | Dice | HD95 (mm) | NSD@1 mm |
|---|---:|---:|---:|
| Right ventricle (RV) | 0.890508 | 4.170635 | 0.874407 |
| Myocardium (MYO) | 0.893160 | 2.091964 | 0.924736 |
| Left ventricle (LV) | 0.941317 | 1.878411 | 0.932727 |
