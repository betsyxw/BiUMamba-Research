# E2_modify_2 Frozen Source and Configuration

**Research Author and Repository Maintainer:** xuwen<br>
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

## Freeze status

E2_modify_2 is frozen as the reference implementation used for the completed
Synapse 300-epoch, seed-42 experiment. Future E3, E4, dataset ports, and
pretraining experiments must be developed in separate source versions and must
not overwrite this directory.

Freeze date: 2026-08-30 (Asia/Tokyo)

## Authoritative RunPod provenance

- Repository: `/workspace/repos/VM-UNet_E2_modify_2`
- Branch: `experiment/e2c-grouped-2d`
- Git commit: `62fc67c2839f225bc86edcba9f3f108bdfb99beb`
- Git tag: `E2_modify_2_smoke_pass`
- Source snapshot: `/workspace/source_versions/E2_modify_2/VM-UNet_E2_modify_2_full300_62fc67c_source.tar.gz`
- Snapshot SHA-256: `571c80f0dfa57210a1023c0a5d2489a9bfaae2e3b89c93b21b0142ddd0f17109`

At verification time, the RunPod Git working tree had no modified tracked
files. The only untracked entries were the local Synapse data link and
pretrained-weight files; they are explicitly excluded from this archive.

## Frozen implementation

- Model family: VM-UNet / VMamba SS2D
- Method: channel-grouped 2D bidirectional scan with fixed sum
- Horizontal channel group: horizontal forward and reverse scans
- Vertical channel group: vertical forward and reverse scans
- Fusion inside each group: fixed equal-weight sum `(1.0, 1.0)`
- Group merge: channel concatenation followed by the existing output projection
- Configuration selector: `grouped_2d_bidirectional_sum`

The executable archival files are:

- `../models/vmunet/vmamba.py`
- `../configs/config_setting_synapse.py`
- `../research/E2_MODIFICATION.md`
- `../research/smoke_test_e2_modify_2.py`

Their authoritative RunPod hashes and the hashes of the repository copies are
recorded in `SOURCE_SHA256SUMS.txt`. Repository copies include authorship headers
and normalized line endings, so their byte-level hashes differ from RunPod while
the research implementation and configuration remain functionally unchanged.

## Frozen experiment identity

- Experiment: `E2_modify_2_full300_seed42_20260827_vmunetenv`
- Dataset: Synapse
- Completed epochs: 300
- Seed: 42
- Batch size: 32
- Input size: 224 × 224
- Official checkpoint-selection rule: minimum training loss
- Official checkpoint label: epoch 297
- Official checkpoint Mean Dice: 0.8025402376811894
- Official checkpoint Mean HD95: 21.92055602481082
- Status: completed, single-seed preliminary result

See `../../../research/runs/e2_modify_2_synapse_seed42/manifest.json` for the
full run manifest and archived metrics.

## Reproducibility rule

Any result described as E2_modify_2 must resolve to the authoritative RunPod
commit above, use the configuration in `CONFIG_FROZEN.json`, and match the
source hashes in `SOURCE_SHA256SUMS.txt`. Any structural or optimization change
requires a new experiment name and a new Git commit.

No dataset, patient image, NIfTI prediction, checkpoint, pretrained weight,
credential, or authentication information is included in this frozen record.
