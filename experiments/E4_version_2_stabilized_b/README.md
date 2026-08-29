# E4 Version 2 — Stabilized Adaptive Gate B

**Research Author and Repository Maintainer:** xuwen
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

This source snapshot is an independent E4 stabilization ablation built on the
coverage-preserving channel-grouped 2D scan of `E2_modify_2`. It does not
overwrite E4 Version 1.

The stabilization changes are:

- gate learning rate set to `0.1 ×` the backbone learning rate;
- gate frozen for the first 5 epochs;
- persistent checkpointed `alpha`, ramped from 0 to 0.25 over 10 epochs;
- gradient clipping at 1.0;
- an equal-fusion regularizer with weight `0.001`;
- LayerNorm on directional gate context and temperature 4.0 to limit `tanh`
  saturation;
- fixed case-level held-out validation and Dice-first checkpoint selection.

The 50-epoch screening run completed normally, establishing that the
engineering stabilization removed the previous catastrophic trajectory
failure. It did not establish an accuracy advantage. See
[`../../research/runs/E4_v2_stabilized_b_epoch50/`](../../research/runs/E4_v2_stabilized_b_epoch50/).

Upstream VM-UNet/VMamba authorship and the Apache-2.0 license remain retained.
Only the research modifications listed above are maintained by xuwen.
