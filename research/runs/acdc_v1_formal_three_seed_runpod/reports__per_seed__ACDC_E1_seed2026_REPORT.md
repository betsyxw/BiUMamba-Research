# E1 ACDC v1 seed 2026 report

- Exit status: successful.
- Best validation epoch: 251.
- Mean Dice: 0.905059.
- Mean HD95: 2.930754 mm.
- Mean NSD@1 mm: 0.904645.
- Training time: 1.1607 h.
- Mean epoch time: 13.3206 s.
- Peak GPU memory: 8.9451 GiB.
- Parameters: 27,427,636.
- Inference time: 1.8209 ms/slice.
- FLOPs: N/A; selective-scan custom operators are not counted reliably by generic profilers.

## Per-organ metrics

| Organ | Dice | HD95 (mm) | NSD@1 mm |
|---|---:|---:|---:|
| Right ventricle (RV) | 0.881162 | 4.805099 | 0.857457 |
| Myocardium (MYO) | 0.894199 | 1.836232 | 0.929646 |
| Left ventricle (LV) | 0.939816 | 2.150931 | 0.926831 |
