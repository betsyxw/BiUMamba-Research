# E1: original four-direction VM-UNet baseline

Updated: 20261015. This explicit source snapshot selects `original` and uses
all channels in each of four directions. The files were copied from the public
shared implementation; they are not a recovered original training Git tree.

Use `python -m reproducibility.model_registry --method E1` and the
[common training/evaluation instructions](../../reproducibility/README.md).
The existing `E1_synapse_v2` directory preserves the formal trainer/provenance.
Root-config defaults must not be mistaken for the E1 model selector.
