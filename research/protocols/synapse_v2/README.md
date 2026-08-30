# Frozen Synapse Formal Protocol v2

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

`synapse_v2` is the formal protocol for future E2_modify_2-derived experiments.
It is independent of, and does not overwrite, the frozen `synapse_v1` protocol.

## Prespecified design

- Original 18 development cases are split at patient/case level into 14 training
  cases and 4 validation cases.
- The official 12 test volumes remain isolated until the selected checkpoint is
  frozen.
- Full training is 300 epochs; screening is 50 epochs.
- Validation is run after every epoch.
- The best checkpoint maximizes validation macro Dice. If Dice is exactly tied
  within `1e-12`, the lower validation macro HD95 is selected.
- Formal runs use seeds `42`, `2026`, and `3407` and report mean ± standard
  deviation. No best-seed selection is allowed.
- Final test metrics are computed offline with the frozen `synapse_v1`
  NIfTI evaluator: Dice, physical HD95 in mm, and NSD@1 mm.

## Frozen files

- `splits/`: case- and slice-level train/validation lists plus the untouched
  official test-case list.
- `TRAINING_CONFIG.json`: input, optimization, epoch, validation, and
  checkpoint settings.
- `SEEDS.txt`: preregistered formal seed list.
- `frozen_augmentation.py`: exact training augmentation implementation.
- `CHECKPOINT_POLICY.md`: validation selection and test-isolation rules.
- `AUGMENTATION_POLICY.md`: augmentation probabilities and interpolation.
- `PROTOCOL_SHA256SUMS.txt`: integrity record for protocol-controlled files.

Historical E1–E4 results keep their original labels and must not be silently
converted into `synapse_v2` results.

