# E2: full-channel horizontal forward/reverse scans

Updated: 20261015. This explicit source snapshot selects `bidirectional_sum`.
It is the horizontal-only ablation, **not** E2_modify_2/BiUMamba. Files were
copied from the shared implementation and config; this is not a recovered
original training Git tree. A historical E2 source tarball also exists locally,
but this maintained entry point is explicitly identified by its release hashes.

Use `python -m reproducibility.model_registry --method E2` and the
[common training/evaluation instructions](../../reproducibility/README.md).
Historical E2 results were exploratory and do not become Synapse-v2 three-seed
results merely because a common runner is now provided.
