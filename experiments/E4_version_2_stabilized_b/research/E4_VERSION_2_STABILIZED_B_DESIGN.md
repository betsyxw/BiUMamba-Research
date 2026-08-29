# E4_version_2_stabilized_b Design

**Research Author and Repository Maintainer:** xuwen

## Evidence gate

The independent V2 population probe evaluated 4,905,024 gate values per run
over 433 deterministic held-out Synapse slices. The fractions with
`|gate_delta| >= 0.99` were 59.90% and 54.25%. Both exceed the predeclared 10%
threshold, confirming population-wide rather than isolated saturation.

## Targeted changes from V2

1. Preserve the V2 gate LR multiplier (`0.1`), five frozen epochs, alpha ramp
   from `0` to `0.25`, and global gradient clipping (`1.0`).
2. Apply `LayerNorm` to the concatenated four-direction gate context.
3. Use temperature-scaled output: `delta = tanh(logits / 4.0)`.
4. Increase the equal-fusion regularizer from `1e-4` to `1e-3`.
5. Preserve zero initialization of the final gate layer, so the initial model
   remains exactly equivalent to E2_modify_2 fixed equal fusion.
6. Store `grouped_gate_alpha` as a persistent model buffer so standalone
   checkpoint evaluation reproduces the trained adaptive-fusion strength.

This is a new ablation version. It does not replace or overwrite E4 V1 or V2.

## Decision sequence

1. Initial-equivalence and forward/backward smoke test.
2. Two matched 12-epoch A/A runs with population saturation statistics.
3. Only if both trajectories are acceptable and population saturation is no
   longer broad: run a 50-epoch screen.
4. A 300-epoch formal experiment requires the 50-epoch validation decision and
   later three seeds with mean ± standard deviation.
