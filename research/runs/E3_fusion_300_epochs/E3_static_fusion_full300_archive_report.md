# E3 Static Learnable Fusion - 300-Epoch Archive and Comparison Report

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

## 1. Archive status

- Experiment: **E3 - Channel-Grouped 2D Bidirectional Scan with Static Learnable Fusion**
- Dataset: Synapse multi-organ CT
- Status: **Completed successfully**
- Exit code: `0`
- Completed epochs: `300`
- Run directory: `/workspace/runs/e3_static_fusion_full300_seed42_20260828_vmunetenv`
- Source repository: `/workspace/repos/VM-UNet_E3_static_fusion`
- Source commit: `25bde91e5a6b5f55432b62eb0b1e760ea29c437c`
- Source branch: `experiment/e3-static-learnable-fusion`

## 2. Method definition

E3 retains E2_modify_2's channel-grouped horizontal/vertical bidirectional scan and changes only the directional fusion rule:

- E2_modify_2: fixed weights `[1.0, 1.0]` for forward/backward outputs on each axis.
- E3: `2 * softmax(logits)` static learnable weights for each axis.
- Zero initialization makes E3 mathematically equivalent to E2_modify_2 at initialization.
- The factor of two preserves the fixed-sum output scale.
- The learned weights are block-specific but input-independent.

The best checkpoint contains 15 static-fusion tensors and 60 scalar logits. After training, the effective weights range from `0.8458` to `1.1542`; the mean absolute deviation from `1.0` is only `0.0373`. The fusion parameters learned non-zero asymmetry, but most blocks remained close to fixed equal-weight fusion.

## 3. Official checkpoint result

The training script selects the best checkpoint by **minimum training loss**, not by validation Dice. The selected checkpoint is Epoch 286 and was evaluated after all 300 epochs.

| Metric | Result |
|---|---:|
| Best checkpoint label | Epoch 286 |
| Mean Dice | **0.8000492093 (80.0049%)** |
| Mean HD95 | **25.5669445719** |
| Test cases | 12 |
| Test time | 662.27 s |

Checkpoint:

`/workspace/runs/e3_static_fusion_full300_seed42_20260828_vmunetenv/checkpoints/best-epoch286-mean_dice0.8000-mean_hd9525.5669.pth`

SHA-256:

`973abdb3bc321815a0e67e08afb67ba7b3132231f1da63f8967d0a02c930e94b`

### Supplementary Epoch-300 current-weight validation

Before loading the minimum-loss checkpoint, the Epoch-300 current weights produced:

- Mean Dice: `0.8002220522` (80.0222%)
- Mean HD95: `24.6363391372`
- Validation time: `645.54 s`

The formal comparison uses the minimum-loss checkpoint result to match the E1, E2 and E2_modify_2 archival protocol.

## 4. Per-organ checkpoint metrics

| Class | Organ | Dice | Dice (%) | HD95 |
|---:|---|---:|---:|---:|
| 1 | Aorta | 0.854378 | 85.4378 | 18.163547 |
| 2 | Gallbladder | 0.674310 | 67.4310 | 27.322921 |
| 3 | Left Kidney | 0.829962 | 82.9962 | 26.914643 |
| 4 | Right Kidney | 0.792149 | 79.2149 | 56.153157 |
| 5 | Liver | 0.937333 | 93.7333 | 16.385781 |
| 6 | Pancreas | 0.621206 | 62.1206 | 13.466890 |
| 7 | Spleen | 0.892844 | 89.2844 | 24.171640 |
| 8 | Stomach | 0.798212 | 79.8212 | 21.956978 |

## 5. Time and GPU usage

| Item | Result |
|---|---:|
| Sum of 300 epoch times | 41,727.53 s |
| Training-only duration | 11 h 35 m 27.53 s |
| Mean epoch time | **139.0918 s** |
| Minimum epoch time | 119.47 s |
| Maximum epoch time | 174.03 s |
| Logged wall duration | 44,634 s (12 h 23 m 54 s) |
| Peak sampled GPU memory | **12,958 MiB** |
| Peak sampled GPU utilization | 100% |
| Peak sampled temperature | 46 C |
| Peak sampled power | 133.82 W |
| GPU sampling interval | 30 s |

The memory figure is sampled by `nvidia-smi`, not the exact CUDA allocator peak.

## 6. Formal 300-epoch comparison

| Experiment | Method | Dice | HD95 | Mean epoch | Peak memory |
|---|---|---:|---:|---:|---:|
| E1 | Original four-direction SS2D + fixed sum | 80.0488% | 24.6136 | 177.86 s | 14,665 MiB |
| E2 | Row-only forward/backward + fixed sum | 78.6080% | 26.1111 | 164.48 s | **10,747 MiB** |
| E2_modify_2 | Grouped 2D bidirectional + fixed sum | **80.2540%** | **21.9206** | 157.06 s | 11,016 MiB |
| E3 | Grouped 2D bidirectional + static fusion | 80.0049% | 25.5669 | **139.09 s** | 12,958 MiB |

### E3 versus E2_modify_2

- Dice decreases by `0.2491` percentage points.
- HD95 increases by `3.6464`, indicating worse boundary performance.
- Mean epoch time decreases by `17.97 s` (`11.44%`).
- Peak sampled memory increases by `1,942 MiB` (`17.63%`).
- Dice improves only for pancreas and stomach; six of eight organs decrease.
- Right-kidney HD95 increases from `31.5460` to `56.1532`, the largest adverse boundary change.

### E3 versus E1

- Dice is nearly tied but decreases by `0.0439` percentage points.
- HD95 increases by `0.9533`.
- Mean epoch time decreases by approximately `21.8%`.
- Peak sampled memory decreases by `1,707 MiB` (`11.64%`).

## 7. E3-50 versus E3-300

| Metric | E3 50 epochs | E3 300 epochs |
|---|---:|---:|
| Mean Dice | 75.6773% | 80.0049% |
| Mean HD95 | 36.0624 | 25.5669 |
| Mean epoch time | 152.66 s | 139.09 s |
| Peak sampled memory | 12,958 MiB | 12,958 MiB |

The 50-epoch screening correctly showed that E3 could converge, but its favorable ranking against the matched E2_modify_2 50-epoch run did **not** persist at 300 epochs. Short screening remains useful for eliminating broken variants, but it cannot establish the final ranking of closely matched methods.

## 8. Decision

**Decision: E3 does not replace E2_modify_2 as the current best model.**

Static learnable fusion produced a substantial speed measurement improvement in this run, but it did not improve final Dice or HD95 and consumed more memory than E2_modify_2. The learned weights stayed close to equal fusion, suggesting that a global input-independent directional preference offers limited additional information for this task.

E3 remains important as a negative/neutral ablation result:

1. The main gain comes from preserving horizontal and vertical spatial coverage.
2. Replacing fixed fusion with static learnable weights is not sufficient to improve segmentation.
3. E4 can still test the distinct hypothesis that **input-dependent** fusion is more useful than a global static preference.

Recommended next gate:

- Keep E2_modify_2 as the reference model.
- Implement E4 from the coverage-preserving E2_modify_2 structure.
- Initialize E4 to reproduce fixed fusion.
- Run smoke test and a matched 50-epoch screening only.
- Do not start E4-300 unless E4-50 improves Dice and HD95 without a prohibitive memory increase.

## 9. Configuration

| Item | Value |
|---|---|
| Network | VM-UNet |
| Dataset | Synapse |
| Scan fusion | `grouped_2d_static_fusion` |
| Classes | 9 including background |
| Input size | 224 x 224 |
| Initialization | `vmamba_small_e238_ema.pth` |
| Loss | Cross-Entropy + Dice |
| Optimizer | AdamW |
| Initial learning rate | 0.001 |
| Weight decay | 0.01 |
| Scheduler | CosineAnnealingLR |
| T_max / eta_min | 100 / 1e-5 |
| Seed | 42 |
| Batch size | 32 |
| Epochs | 300 |
| Validation interval | 100 epochs |
| AMP | False |
| Number of workers | 0 |

The data split matches E1, E2, E2_modify_2 and E3-50.

## 10. Archived remote artifacts

- Best checkpoint: 105 MiB, retained only on RunPod.
- Latest training-state checkpoint: 315 MiB, retained only on RunPod.
- Complete training console log: retained on RunPod.
- Structured training/test log: retained on RunPod.
- GPU monitor CSV: retained on RunPod.
- NIfTI outputs: 36 files for 12 test cases, retained only on RunPod.

Log hashes:

- `train_console.log`: `79aa2f4d7547ed961b87274e6d74c2678678c4350cc97e7a6445eba56a384d75`
- `log/train.info.log`: `b2ccab5fc99067e778e00948c91562fbfc65380d1d11b4ee897b69eb32d4becb`
- `gpu_monitor.csv`: `88b94d710dd87722ddc8b9aaa3f063b8c0ab91fa8bb2f872f9df7c89afa1b026`

Datasets, checkpoints, pretrained weights and NIfTI volumes are intentionally excluded from this local report package.

## 11. Deferred publication items

- NSD must be computed later with the same offline evaluator for E1-E4.
- This is a single-seed result; no significance claim is permitted.
- Parameters, FLOPs and inference-only latency still require a shared evaluator.
- Efficiency measurements should be repeated under a controlled, identical hardware state.

## 12. Sequential per-organ change summary

Dice is better when higher; HD95 is better when lower. Therefore, a Dice increase and an HD95 decrease are counted as improvements.

### E1 to E2: removing vertical coverage

- Dice improved for **1/8 organs**: liver (`+0.3746 pp`).
- Dice decreased for **7/8 organs**. The largest decreases were stomach (`-5.8620 pp`), pancreas (`-2.7027 pp`), right kidney (`-1.3413 pp`) and left kidney (`-1.2275 pp`).
- HD95 improved for aorta, gallbladder and left kidney, but worsened for five organs.
- The critical failure was right-kidney HD95 (`+33.5680`) together with lower Dice.
- Interpretation: row-only forward/backward scanning reduced two-dimensional spatial coverage and caused a broad loss of segmentation robustness.

### E2 to E2_modify_2: restoring horizontal and vertical coverage

- Dice improved for **6/8 organs**: aorta, left kidney, right kidney, pancreas, spleen and stomach.
- The largest recoveries were stomach (`+4.9481 pp`), right kidney (`+3.1414 pp`) and spleen (`+2.1585 pp`).
- Dice decreased slightly for gallbladder (`-0.1443 pp`) and liver (`-0.1220 pp`).
- HD95 improved for right kidney, liver, pancreas, spleen and stomach.
- The strongest boundary recovery was right kidney (`-39.9566` HD95).
- Interpretation: the channel-grouped design recovered two-dimensional contextual coverage while retaining two-direction computation within each channel group.

### E2_modify_2 to E3: replacing fixed fusion with static learnable fusion

- Dice improved for **2/8 organs**: pancreas (`+3.3966 pp`) and stomach (`+0.9596 pp`).
- Dice decreased for **6/8 organs**, especially left kidney (`-2.3143 pp`), right kidney (`-1.5052 pp`) and aorta (`-1.1924 pp`).
- HD95 improved for aorta, left kidney and liver, but worsened for five organs.
- Right-kidney HD95 worsened substantially (`+24.6072`). Pancreas and stomach gained Dice but lost boundary accuracy.
- Interpretation: a single input-independent directional preference helps selected organs but does not generalize consistently across organs.

### E3 50 epochs to E3 300 epochs: convergence check

- Dice improved for all eight organs as training progressed.
- HD95 improved for aorta, gallbladder, left kidney, liver and spleen, but right kidney, pancreas and stomach remained less stable.
- This confirms that 50 epochs is useful for screening broken variants, but not sufficient for final organ-level ranking.
