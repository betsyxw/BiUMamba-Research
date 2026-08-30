# Frozen Evaluation Policy — Synapse v1

**Author:** xuwen

## Labels

| Label | Organ |
|---:|---|
| 1 | Aorta |
| 2 | Gallbladder |
| 3 | Left Kidney |
| 4 | Right Kidney |
| 5 | Liver |
| 6 | Pancreas |
| 7 | Spleen |
| 8 | Stomach |

Background label 0 is not included in reported metrics.

## Metrics

- Dice: binary Sørensen–Dice coefficient.
- HD95: 95th percentile of bidirectional physical surface distances in mm.
- NSD@1 mm: fraction of prediction and ground-truth surface points whose
  nearest opposite surface is within 1.0 mm.

All distances use the physical NIfTI voxel spacing, not voxel indices.

## Empty-mask rule

- Both masks empty: mark the case/organ pair `both_empty` and exclude it from
  that organ's mean.
- Exactly one mask empty: Dice=0, NSD=0, and HD95 equals the physical volume
  diagonal. This penalizes a missed organ or pure false positive without
  incorrectly reporting HD95=0.

## Aggregation

1. Compute metrics for every test case and foreground organ.
2. Average included cases within each organ.
3. Macro-average the eight organ means for the overall result.

The evaluator exports per-case, per-organ, overall, and input-hash records.
No case or organ may be manually removed after predictions are inspected.
