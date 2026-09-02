# E2_modify_2 ACDC v1 seed 42 report

- Exit status: successful.
- Best validation epoch: 242.
- Mean Dice: 0.905536.
- Mean HD95: 2.982069 mm.
- Mean NSD@1 mm: 0.904357.
- Training time: 0.8556 h.
- Mean epoch time: 9.6165 s.
- Peak GPU memory: 6.7160 GiB.
- Parameters: 27,427,636.
- Inference time: 1.2726 ms/slice.
- FLOPs: N/A; selective-scan custom operators are not counted reliably by generic profilers.

## Per-organ metrics

| Organ | Dice | HD95 (mm) | NSD@1 mm |
|---|---:|---:|---:|
| Right ventricle (RV) | 0.890867 | 4.207370 | 0.875774 |
| Myocardium (MYO) | 0.890296 | 2.206091 | 0.920649 |
| Left ventricle (LV) | 0.935446 | 2.532747 | 0.916648 |
