# E4_version_2_stabilized_gate

**Research Author and Repository Maintainer:** xuwen
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)
**GitHub:** [@betsyxw](https://github.com/betsyxw)

## Purpose

E4_version_1 is preserved unchanged as the original adaptive-gate ablation.
E4_version_2 is a separately named stability ablation built on the same
coverage-preserving E2_modify_2 scan and the same sample/channel gate.

## Predeclared stabilization settings

- Gate learning rate: `0.1 ×` backbone learning rate.
- Gate freeze: Epochs 1–5.
- Residual alpha: `0` while frozen, then a linear ramp over Epochs 6–15 to
  the maximum `0.25`.
- Global gradient clipping: L2 norm `1.0`.
- Equal-fusion regularizer: `1e-4 × mean(gate_delta²)`; zero represents equal
  forward/backward fusion.
- Screening seed: `42`.
- Formal seeds: `42`, `123`, and `3407`; formal results report mean ± standard
  deviation.

## Checkpoint-selection correction

The 12 official Synapse test volumes are no longer used during training.
Four cases are selected from the original 18 training cases by a predeclared
`random.Random(42)` case-level split:

`case0010`, `case0027`, `case0031`, `case0033`.

The remaining 14 cases train the model. Validation runs every 10 epochs. The
best checkpoint maximizes held-out Mean Dice; Mean HD95 is the tie-breaker.
The official test set is evaluated once after training. Because this changes
the training split, paper-level E1, E2_modify_2, and E4 comparisons must all be
rerun with the same split and checkpoint rule.

## Decision sequence

1. GPU smoke test.
2. Two independent 12-epoch deterministic A/A diagnostics.
   - Green: maximum loss difference ≤ `0.01` and unfrozen gate absolute value
     < `0.95`.
   - Yellow: maximum loss difference ≤ `0.03` and gate absolute value < `0.99`.
   - Red: batch order mismatch, larger trajectory divergence, or gate
     saturation beyond those limits.
3. Proceed to a 50-epoch screening only if both short trajectories are stable
   enough and no gate/gradient anomaly is detected.
4. Proceed to 300 epochs only after the 50-epoch Green/Yellow decision gate.

No favorable single run may be selected in place of the declared multi-seed
formal experiment.
