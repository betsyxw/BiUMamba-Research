# ACDC v1 - E1 vs E2_modify_2 - Seed 42

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

This directory archives the completed ACDC v1 seed-42 comparison between:

- E1: original VM-UNet with four-direction SS2D;
- E2_modify_2: channel-grouped horizontal/vertical bidirectional scan with fixed sum fusion.

Both runs completed 300 epochs on RunPod RTX 4090. Their best checkpoints were selected only by validation Dice, with lower validation HD95 as the tie-breaker. The isolated 20-patient test set was evaluated once using the same frozen evaluator.

## Main result

E2_modify_2 reduced total training time by 28.98%, mean epoch time by 30.19%, peak allocated GPU memory by 24.94%, and inference time by 31.80%. Its single-seed test Dice was 0.28 percentage points lower, HD95 was 0.268 mm higher, and NSD@1mm was 0.63 percentage points lower than E1. The current decision is **Yellow: efficiency-accuracy trade-off**.

## Repository safety

This GitHub archive contains only source, configuration, aggregate metrics, reports, and safe text records. It intentionally excludes datasets, patient images, qualitative medical figures, NIfTI predictions, checkpoints, pretrained weights, archives, secrets, and host credentials.

The qualitative PDF and PNG figures are delivered separately for the thesis and PPT.

