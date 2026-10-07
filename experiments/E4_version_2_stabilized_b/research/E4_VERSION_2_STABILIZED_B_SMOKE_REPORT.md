# E4_version_2_stabilized_b Smoke Report

**Research Author and Repository Maintainer:** xuwen

## Result

Status: **PASS**

- Initial maximum absolute difference from E2_modify_2 fixed equal fusion: `0.0`
- Gate temperature: `4.0`
- Equal-fusion regularization weight: `1e-3`
- Backbone learning rate: `0.001`
- Gate learning rate: `0.0001`
- Epoch 1: gate frozen, alpha `0.0`
- Epoch 6: gate trainable, alpha `0.025`
- Epoch 15: gate trainable, alpha `0.25`
- Forward, backward, finite gate gradients, and optimizer step: passed
- Unclipped global gradient norm: `1.194722`
- Peak allocated GPU memory during the persistence smoke test: `0.650 GB`

Before the 50-epoch screen, `grouped_gate_alpha` was converted from a transient
Python attribute to a persistent model buffer. The smoke test now saves a model
at alpha `0.25`, loads it into a fresh process-equivalent model instance, and
requires the reloaded alpha value to remain exactly `0.25`.

Persistence result: **PASS**, reloaded alpha values: `[0.25]`.

The smoke test verifies implementation integrity only. It does not establish
reproducibility, Dice/HD95 performance, or elimination of population-wide gate
saturation. Those questions require the matched A/A test followed by the
predeclared 50-epoch decision gate.
