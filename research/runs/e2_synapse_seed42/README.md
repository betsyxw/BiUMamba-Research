# E2 Synapse report — bidirectional fixed sum

Research Author and Repository Maintainer: xuwen
Affiliation: Japan Advanced Institute of Science and Technology (JAIST)
GitHub: @betsyxw

Research-specific designs, experiment implementations, ablation records, evaluation reports, and reproducibility documentation in this repository are maintained by xuwen. The original VM-UNet/VMamba code remains attributed to its upstream authors under the retained license. See AUTHORS.md.

## Outcome

E2 completed all 300 epochs and the final Synapse test pass with exit status
0. The implementation used a forward row-major scan (direction index 0) and
its reverse row-major scan (direction index 2), fused as
`y = y_forward + y_backward` with fixed weights `(1.0, 1.0)`.

The single-seed screening result is negative relative to E1: mean Dice fell by
1.4408 percentage points and mean HD95 increased by 1.4975. E2 used less GPU
memory and trained faster, but it did not preserve baseline accuracy.

| Metric | E1 original four-direction | E2 bidirectional fixed sum | Delta |
|---|---:|---:|---:|
| Mean Dice | 0.800488 | 0.786080 | -0.014408 |
| Mean HD95 | 24.613612 | 26.111135 | +1.497523 |
| Wall-clock duration | 56,955 s | 52,211 s | -4,744 s |
| Summed epoch-training time | 53,358.59 s | 49,345.06 s | -4,013.53 s |
| Mean epoch-training time | 177.86 s | 164.48 s | -13.38 s |
| Peak device memory | 14,665 MiB | 10,747 MiB | -3,918 MiB |

## Final E2 test metrics

| Class | Organ | Dice | HD95 |
|---:|---|---:|---:|
| 1 | Aorta | 0.854665 | 6.915247 |
| 2 | Gallbladder | 0.679945 | 19.994433 |
| 3 | Left Kidney | 0.838143 | 22.630792 |
| 4 | Right Kidney | 0.775787 | 71.502560 |
| 5 | Liver | 0.942568 | 26.711554 |
| 6 | Pancreas | 0.581973 | 11.483462 |
| 7 | Spleen | 0.876423 | 24.549186 |
| 8 | Stomach | 0.739135 | 25.101845 |

## Interpretation and decision gate

The result is classified **Red** for the current two-path definition. The
largest degradations occur for stomach Dice (-5.8620 percentage points),
pancreas Dice (-2.7027 points), right-kidney HD95 (+33.5680), and stomach HD95
(+7.2878). At the same time, HD95 improved for aorta, gallbladder, and left
kidney. This organ-dependent pattern is consistent with, but does not by
itself prove, loss of transposed/vertical scan coverage.

Do not launch E3 or E4 using the same two-path scan definition before a scan
coverage audit. The next controlled experiment should retain matched
horizontal and vertical bidirectional coverage, then compare fixed fusion,
static learnable fusion, and input-adaptive gating.

## Run configuration

- Source commit: `4ef87e068c084a16e0cd4f1fe669bfc08530c423`
- Branch: `experiment/e2-bidirectional-fixed-sum`
- Dataset: Synapse, 2,211 training slices and 12 test volumes
- Seed: 42
- Epochs: 300
- Batch size: 32
- Input size: 224 x 224
- Classes: 9 including background
- Optimizer: AdamW, initial learning rate 0.001, weight decay 0.01
- Scheduler: CosineAnnealingLR
- Loss: cross-entropy + Dice
- AMP: disabled
- Pretraining: `vmamba_small_e238_ema.pth`
- GPU: NVIDIA GeForce RTX 4090

## Timing and checkpoint notes

- Run start (UTC): 2026-08-26 02:50:38
- Run end epoch timestamp: 2026-08-26 17:20:49
- Wall-clock duration: 52,211 seconds (14 h 30 min 11 s), including periodic
  validation and the final test pass.
- Summed training-only epoch time: 49,345.06 seconds (13 h 42 min 25 s).
- Mean training time per epoch: 164.48 seconds.
- Validation was performed at epochs 100, 200, and 300 only.
- The best checkpoint filename is
  `best-epoch299-mean_dice0.7861-mean_hd9526.1111.pth`; the zero-based filename
  corresponds to the completed 300th epoch. The checkpoint itself is excluded
  from GitHub.
- Peak device memory from five-second `nvidia-smi` sampling: 10,747 MiB.
- Smoke-test peak allocated memory from PyTorch: 8,695.39 MiB; peak reserved:
  9,136 MiB.

## Archived files

- `train.info.log`: complete structured configuration, training, validation,
  per-case, per-class, and final test log.
- `console.log`: complete console capture including progress output.
- `metrics.csv`: E1/E2 aggregate comparison.
- `per_organ_metrics.csv`: E1/E2 per-organ comparison.
- `manifest.txt`: immutable run configuration and artifact policy.

The 12 image, ground-truth, and prediction NIfTI triplets, pretrained weights,
and checkpoints remain on RunPod and are intentionally excluded from GitHub.
NSD was not computed by the original evaluation code and is therefore not
reported here.
