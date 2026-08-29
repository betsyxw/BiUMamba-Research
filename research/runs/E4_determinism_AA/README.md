# E4 deterministic A/A audit archive

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)  
**GitHub:** [@betsyxw](https://github.com/betsyxw)

## Purpose

The E4 50-epoch screening and 300-epoch full run showed sharply different
training trajectories despite matching logged settings. This archive tests
whether two short runs with the same frozen source, initialization, seed,
batch order, configuration, and GPU follow the same optimization path.

## Main findings

| Check | Result |
|---|---|
| Initial model hash | Match |
| Batch-order hash | Match in all 12 epochs |
| Logical model hash | Different in all 12 epochs |
| Checkpoint-file hash | Different in all 12 epochs |
| Maximum loss difference | `0.042850100568` at Epoch 11 |
| Gate range in Epoch 1 | `-1.0` to `+1.0` |
| Decision | Red for bitwise reproducibility |

The evidence indicates that strict high-level deterministic settings are not
sufficient for the current custom Mamba CUDA training stack. Rapid adaptive-
gate saturation may amplify small numerical differences. The audit does not
identify one individual CUDA kernel as the sole cause, and it does not establish
that adaptive fusion is theoretically invalid.

## Consequence for the research plan

1. Preserve `E4_version_1` as the recorded negative/inconsistent ablation.
2. Do not cherry-pick a favorable single rerun.
3. Report formal E4 results with at least three seeds and mean ± standard
   deviation.
4. Test a separately named `E4_version_2_stabilized_gate`: gate learning rate
   `0.1×` backbone, 5–10 epoch gate warm-up/freeze, residual-alpha ramp from
   `0` to `0.25`, gradient clipping at `1.0`, and a light equal-fusion
   regularizer.
5. Select checkpoints with a predeclared validation metric rather than minimum
   training loss.

## Included and excluded files

Included: diagnostic scripts, aggregate epoch metrics, hashes, exit codes,
source hashes, report, CSV, and manifest. Excluded: datasets, patient images,
NIfTI predictions, batch-level case lists, checkpoints, pretrained weights,
archives, credentials, and full server logs.
