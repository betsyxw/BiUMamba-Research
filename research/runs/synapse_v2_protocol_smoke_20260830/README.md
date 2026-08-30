# Synapse v2 Protocol Smoke-Test Report

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

## Decision

**PASS.** The frozen `synapse_v2` protocol is ready for formal multi-seed
experiments. The existing `synapse_v1` protocol was not modified or replaced.

## Frozen data flow

- Training: 14 cases / 1,798 slices
- Validation: 4 cases / 413 slices
- Official test: 12 cases, pairwise isolated from training and validation
- Validation cases: `case0005`, `case0031`, `case0033`, `case0037`
- Formal seeds: `42`, `2026`, `3407`
- Validation runs after every epoch.
- Checkpoint rule: maximize validation macro Dice; when tied within `1e-12`,
  minimize validation macro HD95.
- The training process does not construct or load a test dataset.

## Training and checkpoint smoke test

- RunPod source commit: `e570e93e67b2db59ed9908cb417d847292442ab2`
- Real E2_modify_2 forward/backward/optimizer step: PASS
- Real batch loss: `3.583573341369629`
- Output shape: `[2, 9, 224, 224]`
- Real validation-batch inference: PASS
- Validation output shape: `[2, 9, 224, 224]`
- Checkpoint decisions: `[save, save, reject]`
- Selected synthetic checkpoint: epoch 2, Dice `0.8`, HD95 `18.0`
- `test_dataset_constructed`: `false`
- Frozen augmentation SHA-256:
  `d7ddcf526f7acf71289ac855c817f29cbc64fc8130318447654bd50f7a6752e4`
- Process exit code: `0`

## Offline evaluation smoke test

The exact frozen `synapse_v1` NIfTI evaluator is intentionally reused by
`synapse_v2`, so all formal experiments retain the same Dice, physical HD95,
and NSD implementation. The smoke test used an already completed historical
prediction set only to verify the evaluation pipeline; these values are not a
new `synapse_v2` training result.

- Evaluated official test cases: `12`
- Organs: `8`
- Mean Dice: `0.7921235710125001`
- Mean HD95: `27.54872302965 mm`
- Mean NSD@1 mm: `0.7466564990375`
- Evaluator SHA-256:
  `7b7f40f76b57155139005ba08815d2c99bcdc454e00303b4e1b2fe6c63b4dacb`
- Test-case-list SHA-256:
  `6976606c015c8bd4188faf6ee3d120fd8a481f260ec940e8a2ad90706967cab3`
- Process exit code: `0`

## Artifact hashes

```text
d23b9f060a30c5c181c9e096c375a56a5ff8dcd2bb3e7a0e71f6144a59d8d605  training_checkpoint_smoke.json
59ac081e3c4c3c20b1795350cc2dc528089e4ac42a83993a2b474d5716f9a31c  offline_overall_metrics.json
739436c3fd8178d6b7e4a063fe44b993fd7431a3366516637f8290ec2da487c0  remote per_case_metrics.csv
8bf9a6b46707db725c4efd3431a14b830a3949c12c44779f64c6a61c7cd5a9a3  remote per_organ_metrics.csv
```

The patient-level CSV files remain on RunPod; no NIfTI volumes, predictions,
checkpoints, datasets, or credentials are committed to GitHub.

## Formal-run gate

The required gate is satisfied. Formal runs may now start under `synapse_v2`,
but every compared model must use this same split, checkpoint rule, evaluator,
augmentation hash, and all three preregistered seeds. The official test set may
only be evaluated after the validation-selected checkpoint is frozen.
