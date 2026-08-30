# E2_modify_2 Synapse v2 Source Provenance

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

- Parent E2_modify_2 commit: `62fc67c2839f225bc86edcba9f3f108bdfb99beb`
- Parent method: channel-grouped 2D bidirectional scan with fixed sum
- Independent RunPod repository:
  `/workspace/repos/VM-UNet_E2_modify_2_synapse_v2`
- Branch: `experiment/e2c-synapse-v2-protocol`
- Initial protocol/trainer commit:
  `cb966820827d342cb815864c52f20888dc7a8bfa`

The model architecture is unchanged from the frozen E2_modify_2 parent. This
version changes only experimental governance and data flow: case-level
train/validation isolation, per-epoch validation, validation-selected
checkpointing, formal seeds, frozen augmentation, and complete test isolation
during training.

Before the first formal run, non-invasive instrumentation was added to record
parameter counts, total and per-epoch training/validation time, and PyTorch
peak allocated/reserved GPU memory. It does not modify the model forward pass,
loss, optimizer, scheduler, data split, augmentation, or checkpoint rule.
