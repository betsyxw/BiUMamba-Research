# E4_version_1: Coverage-Preserving Adaptive Residual Fusion

**Research Author and Repository Maintainer:** xuwen
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

E4_version_1 changes only the fusion rule of E2_modify_2. Horizontal and
vertical channel grouping, all four directional parameter slices, the packed
selective-scan call, preprocessing, optimizer and training data remain fixed.

For each spatial axis, the fusion is:

`y = y_forward + y_backward + alpha * delta(x) * (y_forward - y_backward)`

where `alpha = 0.25` and `delta(x) = tanh(MLP(context(x)))`. The context is
formed by global-average pooling the horizontal-forward, horizontal-backward,
vertical-forward and vertical-backward outputs. The gate produces one value
per sample, channel and axis, but not per spatial token.

The final gate layer is initialized to zero. Therefore `delta(x) = 0` at
initialization and E4_version_1 is mathematically identical to E2_modify_2's
fixed sum. The bounded residual limits each directional weight to
`[1 - alpha, 1 + alpha]`, so both directions remain active.

The 50-epoch run is a screening experiment. It does not establish final
superiority and must be compared only with matched 50-epoch results.
