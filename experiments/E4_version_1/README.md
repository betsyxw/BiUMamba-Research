# E4: grouped-axis adaptive residual gate, version 1

Updated: 20261015. Restored model, config, design and smoke-test source from the
user's read-only Hakusan execution-code archive copied to Mac. This is **v1**,
not stabilized v2-B. Selector: `grouped_2d_adaptive_gate_v1`.

For each axis the design is `forward + backward + alpha * delta * (forward -
backward)`, alpha 0.25, delta from a sample/channel gate. The last gate layer
starts at zero. The shared VMUNet wrapper is included locally.

Use `python -m reproducibility.model_registry --method E4` and the
[common training/evaluation instructions](../../reproducibility/README.md).
Historical v1 performance was negative and showed stability/reproducibility
concerns; do not substitute stabilized v2-B or select favorable retries.

The recovered snapshot's model hash differs from the historical A/A audit's
listed model hash. Therefore neither the original full300 nor A/A source tree
is claimed byte-identical. The archived implementation is provided with this
explicit limitation. Original smoke scripts are preserved; use the common
entry point for unambiguous model loading.
