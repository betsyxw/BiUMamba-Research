# Synapse v2 Smoke Test Plan

**Author:** xuwen

Before any 50- or 300-epoch experiment:

1. Verify the 14/4/12 case split and all 2,211 development slice counts.
2. Run one real E2_modify_2 forward/backward optimizer step on frozen augmented
   Synapse training slices.
3. Run validation inference without constructing the official test dataset.
4. Verify checkpoint selection with three decisions: higher Dice wins, equal
   Dice/lower HD95 wins, and lower Dice is rejected.
5. Run the frozen offline evaluator on the isolated 12-case archived prediction
   set and verify Dice, HD95, NSD, per-case, per-organ, and input-hash outputs.
6. Record source hashes, protocol hashes, exit status, and generated-file hashes.

Passing this smoke test authorizes only the preregistered 50/300-epoch runs and
does not itself constitute a formal model result.

