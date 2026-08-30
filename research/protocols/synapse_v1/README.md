# Frozen Synapse Benchmark Protocol v1

**Research Author and Repository Maintainer:** xuwen<br>
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

This directory freezes the dataset split, checkpoint rule, and offline
evaluation procedure for all subsequent Synapse experiments in this project.
It does not retroactively change the historical E1–E4 records.

## Protocol identity

- Protocol: `synapse_v1`
- Frozen: 2026-08-30 (Asia/Tokyo)
- Training set: official 18-case / 2,211-slice split
- Test set: official 12-case volume split
- Validation set: none
- Full-run checkpoint: final state after Epoch 300
- Screening checkpoint: final state after Epoch 50
- Test access during training: prohibited
- Primary metrics: macro Mean Dice, macro Mean HD95, macro Mean NSD@1 mm

## Files

- `splits/train_cases.txt`: official training case order
- `splits/train_slice_counts.csv`: exact slice ranges for the 2,211 samples
- `splits/test_cases.txt`: official test case order
- `splits/SPLIT_MANIFEST.json`: counts and authoritative hashes
- `generate_train_list.py`: reconstructs the exact official `train.txt`
- `CHECKPOINT_POLICY.md`: prespecified checkpoint rule
- `EVALUATION_POLICY.md`: metric and aggregation definitions
- `evaluate_synapse_nifti.py`: frozen offline evaluator

## Historical compatibility

Earlier runs selected `best.pth` by minimum training loss and occasionally
evaluated `test_vol` during training. Those values remain valid historical
preliminary results, but formal cross-model tables created after this protocol
must use the prespecified final checkpoint and this offline evaluator.

No dataset, patient image, prediction, checkpoint, pretrained weight, or
credential is stored here.
