# E4 Deterministic A/A Audit Report

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

## Outcome

The two 12-epoch runs started from the same model hash and used identical batch
orders at every epoch, but their model and checkpoint hashes differed from the
first epoch. The maximum loss difference was
`0.042850100568` at Epoch
11.

This is a **Red decision** for bitwise reproducibility: strict PyTorch
determinism plus `CUBLAS_WORKSPACE_CONFIG=:4096:8` is not sufficient for the
current custom Mamba CUDA stack. The A/A runs also show rapid adaptive-gate
saturation (`tanh` reaches -1 and +1 during Epoch 1), which can amplify small
numeric differences into materially different optimization trajectories.

## Controls

- Frozen E4 Git commit: `24fa3744e56d96e5bc46b3e2abf084b58545e139`
- Original E4 architecture and gate code were not modified.
- `PYTHONHASHSEED=42`
- `CUBLAS_WORKSPACE_CONFIG=:4096:8`
- `torch.use_deterministic_algorithms(True)`
- Same seed, batch size, input size, optimizer, scheduler, data, and GPU
- Final segmentation evaluation was skipped because this was a training-path audit.
- PyTorch 1.13 rejected CUDA `nll_loss2d` in strict mode. The diagnostic only
  replaced this CE primitive with the mathematically equivalent
  `log_softmax + gather + mean`; therefore these losses are diagnostic and are
  not formal E4 performance results.

## A/A comparison

| Epoch | Run 1 loss | Run 2 loss | Absolute difference | Batch hash | Model hash |
|---:|---:|---:|---:|:---:|:---:|
| 1 | 1.247936112540 | 1.247936076777 | 0.000000035763 | Match | Different |
| 2 | 1.065291879007 | 1.065187347787 | 0.000104531220 | Match | Different |
| 3 | 0.959755766392 | 0.952619676079 | 0.007136090313 | Match | Different |
| 4 | 0.895218649932 | 0.889098786456 | 0.006119863476 | Match | Different |
| 5 | 0.815887922049 | 0.818462446758 | 0.002574524709 | Match | Different |
| 6 | 0.709088472809 | 0.708331717764 | 0.000756755045 | Match | Different |
| 7 | 0.588388437884 | 0.602773354735 | 0.014384916851 | Match | Different |
| 8 | 0.527874466351 | 0.517303989615 | 0.010570476736 | Match | Different |
| 9 | 0.464619884321 | 0.460322819012 | 0.004297065309 | Match | Different |
| 10 | 0.420451592548 | 0.406894988673 | 0.013556603875 | Match | Different |
| 11 | 0.373551170741 | 0.416401271309 | 0.042850100568 | Match | Different |
| 12 | 0.385938543507 | 0.383686248745 | 0.002252294762 | Match | Different |

## Decision

1. Do not treat the failed E4 full300 run as proof that adaptive fusion is theoretically invalid.
2. Do not rerun the unchanged E4 once and select the most favorable result.
3. Main E4 comparisons require at least three seeds and mean ± standard deviation.
4. Create a separately named E4 stabilization ablation before another full300 run:
   lower gate learning rate, gate warm-up/freeze, alpha ramp, gradient clipping,
   and a light regularizer toward equal fusion.
5. Checkpoint selection must be based on a predeclared validation metric rather
   than minimum training loss before paper-level experiments.
