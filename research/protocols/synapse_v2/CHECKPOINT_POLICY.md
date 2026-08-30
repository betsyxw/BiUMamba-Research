# Synapse v2 Checkpoint and Test-Isolation Policy

**Author:** xuwen

## Validation checkpoint rule

After every training epoch, evaluate only the four frozen validation cases.

1. Replace the current best checkpoint when validation macro Dice increases.
2. If Dice is tied within `1e-12`, replace it only when validation macro HD95
   decreases.
3. Never use training loss to select the primary checkpoint.
4. A 300-epoch formal run must still save the final epoch as a resume and audit
   artifact, but the primary result uses `best_validation.pth`.

## Test isolation

The official 12-case test set must not be constructed, loaded, inferred, or
evaluated by the training process. It is accessed exactly once after training,
after the validation-selected checkpoint and its SHA-256 hash are frozen.

Test Dice, HD95, NSD, visual quality, or individual cases must never determine
architecture, hyperparameters, stopping, seed selection, or checkpoint choice.

## Multi-seed reporting

Run all preregistered seeds in `SEEDS.txt`. Report mean ± standard deviation;
do not select the best seed.

