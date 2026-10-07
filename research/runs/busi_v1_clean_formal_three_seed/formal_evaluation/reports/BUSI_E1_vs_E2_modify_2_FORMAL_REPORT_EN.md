# BUSI E1 vs E2_modify_2 Formal Three-Seed Report

## Protocol

- Dataset: BUSI v1 clean, duplicate-cleaned image-group split.
- Split: 371 training groups, 53 validation groups, and 105 isolated test groups.
- Seeds: 42, 3407, and 2026.
- Models: E1 (original VM-UNet SS2D) and E2_modify_2 (channel-grouped two-axis bidirectional scan).
- Checkpoint rule: highest validation lesion-positive Dice; lower HD95 as the tie-breaker.
- Test metrics: lesion-positive Dice, HD95 in pixels, and NSD at a 2-pixel tolerance.

## Main results

| Model | Dice (%) | HD95 (px) | NSD (%) | Peak memory (GB) | Mean epoch (s) | Inference (ms/image) | Approx. GFLOPs |
|---|---:|---:|---:|---:|---:|---:|---:|
| E1 | 75.46 ± 0.87 | 30.17 ± 3.42 | 56.75 ± 2.81 | 12.788 | 16.10 | 5.39 | 9.95 |
| E2_modify_2 | 72.60 ± 2.50 | 36.65 ± 8.75 | 53.16 ± 4.20 | 9.599 | 14.32 | 7.63 | 8.12 |

## Interpretation

E2_modify_2 reduced peak allocated training memory by 24.93% and the estimated total FLOPs by 18.36%. Its mean epoch time was 11.02% lower. However, mean Dice decreased by 2.86 percentage points, mean HD95 increased by 6.48 pixels, and mean NSD decreased by 3.58 percentage points. Batch-1 inference was 41.64% slower in the measured implementation.

The BUSI result is therefore a negative cross-dataset result: the grouped scan improved training efficiency but did not keep E1 segmentation accuracy on breast ultrasound. The main claim should remain limited to the datasets where formal multi-seed results support it.

## FLOPs note

The FLOPs values are approximate. They combine THOP-supported layers with analytical estimates for the unregistered projection einsums and selective-scan core. Elementwise and normalization operations are not fully counted. The selective-scan core MAC estimate is 50% lower for E2_modify_2 by design.
