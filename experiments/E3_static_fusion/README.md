# E3: grouped-axis static learnable fusion

Updated: 20261015. Restored model, config, design and original smoke-test source
from the user's read-only Hakusan execution-code archive copied to Mac.
The selector is `grouped_2d_static_fusion`. Each axis learns two static logits;
`2 * softmax(logits)` gives initial weights `[1, 1]` for zero logits.

The VMUNet wrapper is copied from the shared repository implementation.
Use `python -m reproducibility.model_registry --method E3` and the
[common training/evaluation instructions](../../reproducibility/README.md).

The historical report references commit `25bde91e...`; that Git object and
an independent historical model-file hash have not been recovered here.
These files are an archived implementation snapshot, not claimed byte-exact
recovery of the full300 run. Keep historical exploratory metrics separate from
any new common-protocol experiment. Original smoke scripts are archived as-is;
use the common explicit smoke entry point to avoid path shadowing.
