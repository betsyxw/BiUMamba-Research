# E2_modify_2: BiUMamba, grouped axes with fixed-sum fusion

Updated: 20261015. Each block assigns half its inner channels to horizontal
forward/reverse scans and half to vertical forward/reverse scans. The correct
selector is **`grouped_2d_bidirectional_sum`**, not `bidirectional_sum`.

The existing archived model/config and frozen metadata remain unchanged; a
local copy of the shared VMUNet wrapper is added. Use
`python -m reproducibility.model_registry --method E2_modify_2` and the
[common training/evaluation instructions](../../reproducibility/README.md).

The old `frozen/` record describes the preliminary source lineage and result.
It does not recover the later formal-training commit `f720144...`. Read the
release source audit before claiming exact historical source recovery.
