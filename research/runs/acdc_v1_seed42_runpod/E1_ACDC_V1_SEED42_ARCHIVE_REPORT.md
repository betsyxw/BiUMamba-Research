# E1 ACDC v1 Seed 42 Archive Report

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

- Model: original VM-UNet with four-direction SS2D
- Platform: RunPod RTX 4090
- Source commit: `d151646082d3f4f1a7b3995fb174f3e0a65cb92f`
- Exit code: 0
- Completed epochs: 300
- Best validation epoch: 230
- Best validation Dice: 0.899855
- Best validation HD95: 2.390185 mm
- Isolated-test Mean Dice: 0.908328
- Isolated-test Mean HD95: 2.713670 mm
- Isolated-test Mean NSD@1mm: 0.910623
- Total training and validation time: 4336.890 s (1.205 h)
- Mean epoch time: 13.776 s
- Peak allocated GPU memory: 9.607 GB
- Parameters: 27,427,636
- Inference: 1.866 ms/slice
- Checkpoint SHA-256: `a0f1cdff672725705762026aaaac1a1965f2095fff2e93ec5ab8e490c900b2c3`
- Test data were not accessed during training or checkpoint selection.

