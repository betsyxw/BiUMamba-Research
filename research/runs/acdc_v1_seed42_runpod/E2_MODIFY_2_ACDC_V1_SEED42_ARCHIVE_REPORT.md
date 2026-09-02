# E2_modify_2 ACDC v1 Seed 42 Archive Report

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

- Model: VM-UNet with grouped horizontal/vertical bidirectional scan and fixed sum
- Platform: RunPod RTX 4090
- Source commit: `cf8ccfacf7931666c11971dc5ab3431d38863fa5`
- Exit code: 0
- Completed epochs: 300
- Best validation epoch: 242
- Best validation Dice: 0.901558
- Best validation HD95: 2.417425 mm
- Isolated-test Mean Dice: 0.905536
- Isolated-test Mean HD95: 2.982069 mm
- Isolated-test Mean NSD@1mm: 0.904357
- Total training and validation time: 3080.018 s (0.856 h)
- Mean epoch time: 9.617 s
- Peak allocated GPU memory: 6.716 GiB
- Parameters: 27,427,636
- Inference: 1.273 ms/slice
- Checkpoint SHA-256: `cadec1fbc1939e661b28cb1a1bcf72f62cc9b05dcee8890eb92a6a8f7b926e4f`
- Test data were not accessed during training or checkpoint selection.

