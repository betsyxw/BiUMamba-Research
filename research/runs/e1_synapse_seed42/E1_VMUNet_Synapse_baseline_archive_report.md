# E1 VM-UNet Synapse baseline archive report

Research Author and Repository Maintainer: xuwen
Affiliation: Japan Advanced Institute of Science and Technology (JAIST)
GitHub: @betsyxw

Research-specific designs, experiment implementations, ablation records, evaluation reports, and reproducibility documentation in this repository are maintained by xuwen. The original VM-UNet/VMamba code remains attributed to its upstream authors under the retained license. See AUTHORS.md.


## Archive status

E1 completed 300 training epochs and the final Synapse evaluation. The run is
preserved on RunPod at:

`/workspace/runs/vmunet_synapse_baseline_seed42_batch32_20260824T215505Z`

All required artifacts were rechecked on 2026-08-27. The best and latest
checkpoints, full logs, GPU sampling log, source snapshot, environment record,
and 36 NIfTI visualization files are present.

## Final metrics

| Metric | Result |
|---|---:|
| Mean Dice | 0.800488 (80.0488%) |
| Mean HD95 | 24.613612 |
| Best checkpoint label | epoch 286 |
| Completed training epochs | 300 |
| Wall-clock duration | 56,955 s (15 h 49 min 15 s) |
| Summed epoch-training time | 53,358.59 s (14 h 49 min 18.59 s) |
| Mean training time per epoch | 177.86 s |
| Peak sampled GPU memory | 14,665 MiB |

## Per-organ metrics

| Class | Organ | Dice | HD95 |
|---:|---|---:|---:|
| 1 | Aorta | 0.857881 | 22.799020 |
| 2 | Gallbladder | 0.682824 | 26.334050 |
| 3 | Left Kidney | 0.850418 | 36.076756 |
| 4 | Right Kidney | 0.789200 | 37.934594 |
| 5 | Liver | 0.938822 | 23.321075 |
| 6 | Pancreas | 0.609000 | 9.906766 |
| 7 | Spleen | 0.878004 | 22.722571 |
| 8 | Stomach | 0.797755 | 17.814066 |

## Training configuration

- Model: VM-UNet baseline with the original four-direction selective scan and
  fixed sum fusion
- Dataset: Synapse
- Training set: 2,211 2D slices
- Test set: 12 3D volumes
- Seed: 42
- Batch size: 32
- Input size: 224 x 224
- Classes: 9 including background
- Epochs: 300
- Optimizer: AdamW
- Initial learning rate: 0.001
- Weight decay: 0.01
- Scheduler: cosine annealing
- Loss: cross-entropy plus Dice loss
- AMP: disabled
- GPU: NVIDIA GeForce RTX 4090
- Pretrained weight: `vmamba_small_e238_ema.pth`

## Preserved artifacts on RunPod

- Best checkpoint:
  `checkpoints/best-epoch286-mean_dice0.8005-mean_hd9524.6136.pth`
- Latest checkpoint: `checkpoints/latest.pth`
- Full structured log: `log/train.info.log`
- Full console log: `console.log`
- GPU memory/utilization samples: `gpu.csv`
- Runtime configuration: `config_setting_synapse.py`
- Git revision: `git_commit.txt`
- Source snapshot:
  `source_snapshot/VM-UNet-b87827e-committed-source.tar.gz`
- Environment: `pip_freeze.txt` and `nvidia_smi_q.txt`
- Predictions: 12 image/ground-truth/prediction triplets, 36 `.nii.gz`
  files under `outputs/`

Checkpoints, pretrained weights, datasets, and NIfTI patient volumes are kept
on RunPod and are intentionally excluded from GitHub. NSD was not calculated
by the baseline evaluator; it will be added later with one common offline
evaluation script for E1-E4.

