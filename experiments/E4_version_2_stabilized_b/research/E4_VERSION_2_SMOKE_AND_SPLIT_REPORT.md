# E4_version_2 smoke and data-split verification

**Research Author and Repository Maintainer:** xuwen
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

## GPU smoke test

Status: **PASS**

- Initial maximum difference from E2_modify_2 equal-sum fusion: `0.0`.
- Backbone learning rate: `0.001`.
- Adaptive-gate learning rate: `0.0001` (`0.1×`).
- Epoch 1: gate frozen, alpha `0.0`.
- Epoch 6: gate trainable, alpha `0.025`.
- Epoch 15: gate trainable, alpha `0.25`.
- Forward, backward, equal-fusion regularizer, and global gradient clipping
  completed without NaN/Inf.
- Unclipped global gradient norm in the synthetic smoke batch: `1.1947223`;
  configured clip threshold: `1.0`.
- Peak allocated GPU memory in the synthetic smoke batch: `0.529 GB`.

## Fixed case-level split

Status: **PASS**

- Training cases: 14.
- Held-out validation cases: 4.
- Training slices: 1,778.
- Validation slices: 433.
- Validation cases: `case0010`, `case0027`, `case0031`, `case0033`.
- Validation model input: `1 × 224 × 224`.
- Validation label retained at original resolution: `512 × 512`.
- The 12 official Synapse test cases are not used for checkpoint selection.

This smoke test checks implementation integrity only. It is not a Dice/HD95
performance result and does not authorize a 300-epoch run.
