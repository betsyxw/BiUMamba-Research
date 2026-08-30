# E1 Original VM-UNet under Synapse v2

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

This experiment runs the original four-direction VM-UNet/SS2D baseline under
the exact frozen `synapse_v2` protocol used by E2_modify_2:

- identical 14-case training, 4-case validation, and isolated 12-case test;
- identical augmentation, input size, optimizer, scheduler, loss, and epochs;
- identical seeds: `42`, `3407`, and `2026`;
- validation every epoch;
- maximum validation Dice checkpoint selection, with lower validation HD95 as
  the prespecified tie-breaker;
- identical final offline Dice, physical HD95, and NSD evaluator.

The only intended architectural difference is
`scan_fusion="original"`, restoring the original four-direction SS2D scan.
