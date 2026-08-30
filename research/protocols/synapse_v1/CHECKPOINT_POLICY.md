# Frozen Checkpoint Policy — Synapse v1

**Author:** xuwen

## Main rule

The checkpoint is selected before test evaluation and without observing test
metrics.

- 300-epoch formal experiment: use the model state after Epoch 300.
- 50-epoch screening experiment: use the model state after Epoch 50.
- Interrupted runs are ineligible until resumed to the prespecified epoch.
- `best.pth` selected by minimum training loss may be retained for diagnostics,
  but it must not supply the primary result table.
- `latest.pth` is a resume artifact and must not be reported unless it is exactly
  the prespecified final epoch.

## Test isolation

The 12 Synapse test volumes must not be evaluated during training. They are
evaluated once after the final checkpoint is frozen. Hyperparameters, stopping
rules, and architecture decisions must not be adjusted using those test results.

## Seeds

Each seed produces one final checkpoint under the same rule. Publication tables
report the mean and standard deviation across the prespecified seeds; they must
not select the best seed.

## Historical results

E1–E4 results produced before this policy may retain their original
minimum-training-loss labels. When included beside protocol-v1 results, they
must be marked `historical` and must not be silently relabelled as protocol-v1.
