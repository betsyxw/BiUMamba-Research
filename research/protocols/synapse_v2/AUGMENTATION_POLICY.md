# Synapse v2 Frozen Augmentation Policy

**Author:** xuwen

Training augmentation is frozen in `frozen_augmentation.py`:

- First branch: with probability 0.5, rotate by `k × 90°`, where
  `k ∈ {0,1,2,3}`, then flip along axis 0 or 1 with equal probability.
- Second branch: if the first branch is not selected, perform an independent
  probability-0.5 check; when selected, rotate by an integer angle sampled
  uniformly from `[-20°, 19°]`.
- Effective probabilities are 0.50 rotation/flip, 0.25 small rotation, and
  0.25 no random geometric augmentation.
- Images are resized to 224×224 with order-3 interpolation.
- Labels are resized with nearest-neighbour/order-0 interpolation.
- No augmentation is applied to validation or test data.

Changing this file or its hash requires a new protocol version.

