# E2_modify_2 VM-UNet Synapse Archive Report

Research Author and Repository Maintainer: xuwen
Affiliation: Japan Advanced Institute of Science and Technology (JAIST)
GitHub: @betsyxw

Research-specific designs, experiment implementations, ablation records, evaluation reports, and reproducibility documentation in this repository are maintained by xuwen. The original VM-UNet/VMamba code remains attributed to its upstream authors under the retained license. See AUTHORS.md.

## 1. Archive status

- Experiment: **E2_modify_2 / E2b — Channel-Grouped 2D Bidirectional Scan with Fixed Sum**
- Dataset: Synapse multi-organ CT
- Status: **Completed successfully**
- Exit code: `0`
- Completed epochs: `300`
- Run directory: `/workspace/runs/e2_modify_2_full300_seed42_20260827_vmunetenv`
- Source repository: `/workspace/repos/VM-UNet_E2_modify_2`
- Source commit: `62fc67c` (`experiment/e2c-grouped-2d`, tag `E2_modify_2_smoke_pass`)

## 2. Method definition

E2_modify_2 divides the inner channels of each SS2D block into two spatial groups:

- First half: horizontal forward/reverse scans using parameter sets `[0, 2]`.
- Second half: vertical forward/reverse scans using parameter sets `[1, 3]`.
- Fusion within each group: fixed equal-weight sum with weights `(1.0, 1.0)`.
- Horizontal and vertical group outputs are concatenated and mixed by the existing output projection.
- All four half-channel scans are packed into one selective-scan call.

This retains horizontal and vertical coverage in every block while keeping the total scanned channel volume approximately equivalent to two full-channel scans.

## 3. Official archived checkpoint result

The training script defines the best checkpoint by **minimum training loss**, not by validation Dice. The minimum-loss checkpoint was produced at Epoch 297 and was evaluated after training.

| Metric | Result |
|---|---:|
| Best checkpoint label | Epoch 297 |
| Mean Dice | **0.8025402377 (80.2540%)** |
| Mean HD95 | **21.9205560248** |
| Test cases | 12 |
| Test time | 641.63 s |

Checkpoint:

`/workspace/runs/e2_modify_2_full300_seed42_20260827_vmunetenv/checkpoints/best-epoch297-mean_dice0.8025-mean_hd9521.9206.pth`

SHA-256:

`ee3c9d952b056b80fc27d0b26754c8aca9c3287d88896e63e3db23edf3c4f17e`

### Supplementary Epoch-300 validation result

Before loading the minimum-loss checkpoint, the Epoch-300 current weights produced:

- Mean Dice: `0.8032517249` (80.3252%)
- Mean HD95: `21.0646408265`
- Validation time: `623.91 s`

This result is reported as supplementary evidence. The formal E1/E2/E2_modify_2 comparison uses the archived Epoch-297 checkpoint result for consistency with the checkpoint-based test protocol.

## 4. Per-organ checkpoint test metrics

| Class | Organ | Dice | Dice (%) | HD95 |
|---:|---|---:|---:|---:|
| 1 | Aorta | 0.866302 | 86.6302 | 19.940439 |
| 2 | Gallbladder | 0.678502 | 67.8502 | 26.098491 |
| 3 | Left Kidney | 0.853105 | 85.3105 | 29.985679 |
| 4 | Right Kidney | 0.807201 | 80.7201 | 31.545980 |
| 5 | Liver | 0.941348 | 94.1348 | 21.167291 |
| 6 | Pancreas | 0.587240 | 58.7240 | 9.015161 |
| 7 | Spleen | 0.898008 | 89.8008 | 21.551819 |
| 8 | Stomach | 0.788616 | 78.8616 | 16.059588 |

## 5. Training time and GPU usage

| Item | Result |
|---|---:|
| Sum of 300 epoch training times | 47,118.51 s |
| Training-only duration | 13 h 05 m 18.51 s |
| Mean epoch time | **157.0617 s** |
| Minimum epoch time | 127.33 s |
| Maximum epoch time | 192.21 s |
| Monitored wall time | 49,926.612 s |
| Wall duration | 13 h 52 m 06.61 s |
| Peak sampled GPU memory | **11,016 MiB** |
| Peak GPU utilization | 100% |
| Peak sampled temperature | 51 °C |
| Peak sampled power | 130.11 W |
| GPU monitor interval | 30 s |

The peak-memory value is sampled by `nvidia-smi` every 30 seconds. It is comparable with the E1/E2 archived sampled values but is not a CUDA allocator exact peak.

## 6. Training configuration

| Item | Value |
|---|---|
| Network | VM-UNet |
| Scan fusion | `grouped_2d_bidirectional_sum` |
| Classes | 9 including background |
| Input channels | 3 |
| Input size | 224 × 224 |
| Encoder depths | `[2, 2, 2, 2]` |
| Decoder depths | `[2, 2, 2, 1]` |
| Drop-path rate | 0.2 |
| Initialization | `vmamba_small_e238_ema.pth` |
| Loss | Cross-Entropy + Dice |
| Optimizer | AdamW |
| Initial learning rate | 0.001 |
| Weight decay | 0.01 |
| Scheduler | CosineAnnealingLR |
| `T_max` / `eta_min` | 100 / 1e-5 |
| Seed | 42 |
| Batch size | 32 |
| Epochs | 300 |
| Validation interval | 100 epochs |
| AMP | False |
| Number of workers | 0 |

The Synapse training and test split is the same split used by E1 and E2.

## 7. E1/E2 comparison summary

| Metric | E1 four-direction | E2 row-only | E2_modify_2 grouped 2D |
|---|---:|---:|---:|
| Mean Dice | 80.0488% | 78.6080% | **80.2540%** |
| Mean HD95 | 24.6136 | 26.1111 | **21.9206** |
| Mean epoch time | 177.86 s | 164.48 s | **157.06 s** |
| Training-only time | 14.82 h | 13.71 h | **13.09 h** |
| Wall time | 15.82 h | 14.50 h | **13.87 h** |
| Peak GPU memory | 14,665 MiB | **10,747 MiB** | 11,016 MiB |

Compared with E1, E2_modify_2:

- improves Dice by **0.2052 percentage points**;
- reduces HD95 by **2.6931** (10.94% lower);
- reduces mean epoch time by **11.69%**;
- reduces sampled peak memory by **24.88%**.

Compared with E2, E2_modify_2:

- improves Dice by **1.6460 percentage points**;
- reduces HD95 by **4.1906**;
- reduces mean epoch time by **4.51%**;
- uses 269 MiB more sampled GPU memory.

## 8. Interpretation

The result satisfies the predeclared **Strong Green** decision gate:

- Dice is not lower than E1.
- HD95 is lower than E1.
- Training time and memory are lower than E1.

The result supports the hypothesis that the E2 degradation was caused primarily by the loss of vertical spatial coverage rather than by bidirectional scanning itself. Channel-grouped horizontal/vertical bidirectional scanning restores two-dimensional coverage and, in this seed, provides a better accuracy–efficiency operating point than the original four-direction fixed-sum baseline.

This is still a **single-seed result**. It is sufficient to proceed to E3/E4 development, but it is not yet sufficient for a final publication claim. The final method must be evaluated with multiple seeds and ACDC.

## 9. Archived artifacts

### Checkpoints retained on RunPod

- Best/minimum-loss model: 109,782,501 bytes
- Latest training-state checkpoint: 329,401,047 bytes
- `latest.pth` SHA-256: `82a6b2bfc2fa10fee37b7ae83aa9d0a949e41580e3ffbe4def9ea63eea17b06c`

### Source snapshot

`/workspace/source_versions/E2_modify_2/VM-UNet_E2_modify_2_full300_62fc67c_source.tar.gz`

SHA-256:

`571c80f0dfa57210a1023c0a5d2489a9bfaae2e3b89c93b21b0142ddd0f17109`

The source snapshot contains tracked source at commit `62fc67c`. Dataset links and pretrained weight files are intentionally excluded.

### Logs

- `train_console.log` — SHA-256 `6759cbed5bfacd9d4ffb7eca403a649b45c23ee3f3f9f0c14b42647aa79637c1`
- `log/train.info.log` — SHA-256 `b5e1dda8c980b9f673377629438befa10764c1bffb73e42ec1f3499201296444`
- `gpu_monitor.csv` — SHA-256 `d2a9767f3c709eb7129a204495ec678ffa0f9950dcf4fbc26d25380da31c6719`
- Exit code: `0`

### NIfTI outputs

The RunPod archive retains 36 NIfTI files for 12 test cases:

- 12 input volumes (`*_img.nii.gz`)
- 12 ground-truth volumes (`*_gt.nii.gz`)
- 12 predictions (`*_pred.nii.gz`)

These patient-derived image artifacts are not uploaded to GitHub.

## 10. Missing or deferred items

- NSD is not calculated by the original evaluation code and does not require retraining. It should be added later with one shared offline evaluator for E1–E4.
- Statistical significance cannot be claimed from one seed.
- FLOPs, parameter count, and inference-only latency are not yet archived in this run.
- Final publication evidence requires matched multi-seed experiments and ACDC validation.

