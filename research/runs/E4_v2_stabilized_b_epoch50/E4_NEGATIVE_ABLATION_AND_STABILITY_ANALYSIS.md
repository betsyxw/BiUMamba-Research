# E4 Negative Ablation and Stability Analysis

**Research Author and Repository Maintainer:** xuwen
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

## E4 Version 1: negative ablation

E4 Version 1 introduced a sample- and channel-dependent constrained adaptive
gate on the coverage-preserving grouped-2D structure. Its full 300-epoch run
reached `70.9089%` Mean Dice and `35.3190` Mean HD95. Relative to
E2_modify_2, Dice decreased by `9.3451` points, HD95 worsened by `13.3985`, and
all eight organs lost Dice. The large mismatch between its favorable 50-epoch
screen and full-run trajectory prevented a clean theoretical conclusion.

## Determinism and saturation diagnosis

The matched A/A audit found identical initial model hashes and batch order but
non-bitwise-identical CUDA trajectories. More importantly, population analysis
showed widespread gate saturation in the first stabilized implementation. This
motivated a separately named stabilization ablation instead of silently
replacing E4 Version 1.

## E4 Version 2 Stabilized B

Version 2-B reduced the gate learning rate, froze and ramped the gate, clipped
gradients, regularized toward equal fusion, normalized gate context and applied
temperature scaling. Checkpoint persistence of `alpha` was fixed and verified.
The resulting 50-epoch run completed normally with final training loss
`0.1046`, Mean Dice `74.9931%`, and Mean HD95 `37.9087`.

This establishes an engineering result: the training instability can be
controlled. It does not establish an accuracy contribution. Compared with the
old E3 50-epoch screen, Dice was `0.6842` points lower and HD95 was `1.8463`
higher. That comparison remains diagnostic because Version 2-B trained on
1,778 slices after reserving 433 slices for validation, whereas the old runs
used all 2,211 training slices.

## Publication-safe conclusion

> Adaptive gating was investigated through a negative full-run ablation,
> determinism and saturation audits, and an independently named stabilization
> variant. Stabilization improved optimization reliability but did not provide
> sufficient evidence of an accuracy gain under the pilot protocol.

E2_modify_2 therefore remains the main model. A future gate claim requires a
common train/validation/test protocol, identical checkpoint selection, and at
least three seeds. No E4_v2-B 300-epoch run is planned under the current
unmatched protocol.
