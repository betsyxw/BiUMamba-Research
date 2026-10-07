# BUSI v1 Clean: E1 vs E2_modify_2 Formal Three-Seed Evaluation

This archive contains the GitHub-safe part of the BUSI experiment using seeds
`42`, `3407`, and `2026`. Each method was trained for 300 epochs and evaluated
with its best validation checkpoint on the same frozen 105-group isolated test
set.

## Main result

| Model | Dice (%) | HD95 (px) | NSD @ 2 px (%) | Peak GPU memory (GB) | Mean epoch (s) | Inference (ms/image) | Approx. GFLOPs |
|---|---:|---:|---:|---:|---:|---:|---:|
| E1 (VM-UNet) | 75.46 ± 0.87 | 30.17 ± 3.42 | 56.75 ± 2.81 | 12.788 | 16.10 | 5.39 | 9.95 |
| E2_modify_2 (BiUMamba) | 72.60 ± 2.50 | 36.65 ± 8.75 | 53.16 ± 4.20 | 9.599 | 14.32 | 7.63 | 8.12 |

E2_modify_2 reduced mean epoch time by `11.02%`, peak allocated GPU memory by
`24.93%`, and approximate FLOPs by `18.36%`. However, Dice decreased by `2.86`
percentage points, HD95 increased by `6.48` pixels, and NSD decreased by `3.58`
percentage points. BUSI is therefore a negative cross-dataset accuracy result:
the grouped scan improved training efficiency but did not preserve E1
segmentation accuracy on breast ultrasound.

## Contents

- `formal_evaluation/`: per-seed test metrics, per-sample CSV files, aggregate
  tables, English and Chinese reports, protocol hashes, and text logs.
- `training_archive/`: text-only training reports, validation histories, run
  manifests, protocol records, and queue logs for all six runs.
- `deliverables/`: the formatted Excel workbook and a PPT-ready result table.

## Privacy and repository safety

The following files are intentionally excluded from GitHub:

- BUSI source images and masks;
- processed inputs and ground-truth images;
- model prediction images;
- checkpoints and model weights;
- the private qualitative PNG/PDF/ZIP package.

The private qualitative package is delivered separately to the researcher.

## Metric note

Dice, HD95, and NSD are computed on the 91 lesion-positive test groups. The 14
normal groups are reported separately with empty-mask accuracy and false-positive
area fraction. HD95 uses processed-image pixels, and NSD uses a 2-pixel
tolerance. FLOPs are approximate and are intended for comparison within this
codebase.
