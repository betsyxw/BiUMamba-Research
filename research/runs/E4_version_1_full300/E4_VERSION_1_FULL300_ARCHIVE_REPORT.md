# E4 Version 1 Full-300 Archive Report

**Research Author and Repository Maintainer:** xuwen

**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

**Experiment:** E4 Version 1 — grouped 2D bidirectional scan with constrained residual adaptive gate

**Dataset:** Synapse abdominal CT

**Status:** Completed successfully (`exit_code=0`), but the accuracy result is a **Red decision outcome**.

## 1. Configuration

| Item | Value |
|---|---|
| Network | VM-UNet-derived BiUMamba |
| Scan/fusion mode | `grouped_2d_adaptive_gate_v1` |
| Classes | 9 including background; 8 evaluated organs |
| Input | 224 × 224, 3 channels |
| Epochs | 300 |
| Batch size | 32 |
| Seed | 42 |
| Optimizer | AdamW |
| Initial learning rate | 1e-3 |
| Scheduler | CosineAnnealingLR (`T_max=100`, `eta_min=1e-5`) |
| AMP | Disabled |
| Validation interval | 100 epochs |
| GPU | NVIDIA GeForce RTX 4090, 24 GB |
| Run directory | `/workspace/runs/e4_version_1_full300_seed42_20260829_vmunetenv` |
| Source repository | `/workspace/repos/VM-UNet_E4_version_1` |
| Source Git commit | `24fa3744e56d96e5bc46b3e2abf084b58545e139` |

## 2. Final selected-checkpoint result

The training script selects `best.pth` using **minimum training loss**, not maximum validation Dice. The minimum-loss epoch was Epoch 285. After training, that checkpoint was evaluated and renamed:

`best-epoch285-mean_dice0.7091-mean_hd9535.3190.pth`

| Metric | Result |
|---|---:|
| Mean Dice | **70.9089%** |
| Mean HD95 | **35.3190** |
| Sum of 300 epoch-training times | 35,373.86 s = **9 h 49 min 34 s** |
| Mean epoch time | **117.9129 s** |
| Full wall-clock run, including validation/testing | approximately **10 h 39 min** |
| Peak GPU memory | **13,534 MiB** |
| Exit code | **0** |

For reference, the Epoch-300 model before reloading the Epoch-285 minimum-loss checkpoint produced Dice 71.5616% and HD95 34.3401. The archived final test result above is the result of the selected Epoch-285 checkpoint.

## 3. Per-organ result

| Class | Organ | Dice | HD95 |
|---:|---|---:|---:|
| 1 | Aorta | 78.5798% | 17.7237 |
| 2 | Gallbladder | 58.3896% | 38.4225 |
| 3 | Left kidney | 76.7140% | 74.5540 |
| 4 | Right kidney | 65.1852% | 52.2558 |
| 5 | Liver | 92.8237% | 21.4043 |
| 6 | Pancreas | 44.3075% | 19.2998 |
| 7 | Spleen | 85.7250% | 33.3952 |
| 8 | Stomach | 65.5467% | 25.4970 |

## 4. Comparison with the strongest current candidate

Compared with E2_modify_2:

| Metric | E2_modify_2 | E4 | Change |
|---|---:|---:|---:|
| Mean Dice | 80.2540% | 70.9089% | **−9.3451 pt** |
| Mean HD95 | 21.9206 | 35.3190 | **+13.3985** |
| Mean epoch time | 157.0617 s | 117.9129 s | −24.93% |
| Peak memory | 11,016 MiB | 13,534 MiB | +22.86% |

All eight organs lost Dice relative to E2_modify_2. Only aortic HD95 improved; the remaining seven organ-level HD95 values worsened. Therefore, E4 Version 1 does not satisfy the accuracy or stability requirements for the main model.

## 5. Reproducibility warning

The 50-epoch screening run and the full-300 run used the same logged model mode, seed, batch size, optimizer, scheduler settings, and pretrained path. Nevertheless:

| Run | Epoch-50 training loss | Final screening Dice |
|---|---:|---:|
| E4 screen-50 | 0.1146 | 76.7074% |
| E4 full-300, state at Epoch 50 | 0.7409 | not evaluated at Epoch 50 |

This large divergence indicates that the full run is not a faithful continuation of the favorable screening trajectory. Possible causes include uncontrolled nondeterminism, a launch/state difference not represented in the logged configuration, a pretrained-weight loading difference, or instability introduced by the gate.

Consequently, the current result supports two conclusions:

1. This particular full-300 run is a valid negative result and must be archived.
2. It is not yet sufficient to conclude that the adaptive-gate concept itself is invalid until the screen/full initialization and determinism mismatch is audited.

## 6. Decision

**Red:** Do not extend E4 Version 1 to ACDC, BUSI, multiple seeds, or FractalDB yet.

Recommended next action:

1. Keep E2_modify_2 as the current main directional model.
2. Verify that E4 screen-50 and full-300 use identical source hashes, pretrained-weight hashes, initialization, and launch arguments.
3. Reproduce only the first 10–50 epochs before spending another full 300-epoch run.
4. If the favorable trajectory cannot be reproduced, retain E4 as a negative ablation and continue the paper with E2_modify_2 plus the FractalDB contribution.
