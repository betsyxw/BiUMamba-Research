# E2_modify_1: alternating-axis bidirectional scanning

Updated: 20261015. The existing archived model/config remain unchanged.
The shared VMUNet wrapper is now included locally to make model imports explicit.
The selector is `alternating_axis_sum`; encoder/decoder blocks alternate axes.

Use `python -m reproducibility.model_registry --method E2_modify_1` and the
[common training/evaluation instructions](../../reproducibility/README.md).
The historical result is a 50-epoch exploratory screen, not completed formal
three-seed 300-epoch evidence.
