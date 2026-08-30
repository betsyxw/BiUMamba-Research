# Synapse v2 Case-Level Split

**Author:** xuwen

The official 18 development cases from `synapse_v1` were split at case level.
Four validation cases were selected once using Python
`random.Random(42).sample(official_train_case_order, 4)` and then frozen.

- Training: 14 cases, 1,798 slices
- Validation: 4 cases, 413 slices
- Test: untouched official 12 volumes

The three sets are pairwise disjoint. Slice-level random splitting is forbidden
because it would leak slices from the same patient across training and
validation.

