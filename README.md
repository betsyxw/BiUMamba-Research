# BiUMamba Research


[English](#english) | [日本語](#日本語)


**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)  
**GitHub:** [@betsyxw](https://github.com/betsyxw)


Research-specific designs, experiment implementations, ablation records,
evaluation reports, and reproducibility documentation in this repository are
maintained by **xuwen**. The original VM-UNet/VMamba code remains attributed to
its upstream authors under the retained license. See [`AUTHORS.md`](AUTHORS.md).


## English


Private research repository for the master's project:


> **BiUMamba: Bidirectional Selective Scan with Adaptive Fusion and
> Natural-Image-Free Pre-training for Medical Image Segmentation**


Current experimental status:


- E1: original four-direction VM-UNet baseline — completed.
- E2: forward/reverse row-major scan with fixed sum — completed; below E1.
- E2_modify_1: alternating-axis bidirectional scan — 50-epoch screening completed.
- E2_modify_2: channel-grouped 2D bidirectional scan — 300-epoch validation completed; it recovered E2's lost accuracy and passed the Strong Green decision gate.
- E3: static learnable fusion on E2_modify_2 — smoke test passed and 50-epoch screening is in progress.
- E4: input-adaptive fusion on the same coverage-preserving structure — pending the E3 screening result.
- Datasets: Synapse first, ACDC second; FractalDB pre-training pilot follows the directional ablation.


### Training story and current evidence


E2 reduced the original four SS2D directions to row-major forward/reverse scans.
It reduced mean epoch time and peak memory, but Dice decreased from `80.05%` to
`78.61%` and HD95 worsened from `24.61` to `26.11`. This negative control
suggested that bidirectionality alone was insufficient because the transposed
vertical scan pair had been removed.


Two coverage-recovery variants were therefore implemented and tested under a
matched 50-epoch Synapse screening protocol (seed 42, batch size 32, 224x224
input, and the same initialization and optimization settings):


| Variant | Design | Mean Dice | Mean HD95 | Final loss | Mean epoch time | Peak memory |
|---|---|---:|---:|---:|---:|---:|
| E2_modify_1 | Alternating horizontal/vertical bidirectional blocks | 72.54% | **35.58** | 0.1478 | 213.81 s | **10,396 MiB** |
| E2_modify_2 | Channel-grouped horizontal/vertical bidirectional scan in every block | **75.07%** | 40.42 | **0.1307** | **170.71 s** | 11,016 MiB |


E2_modify_2 was selected for the first full 300-epoch validation because it
improved Dice by `2.53` percentage points, improved Dice in seven of eight
organs, reduced final loss, and trained about `20.16%` faster per epoch than
