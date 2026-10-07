# E4_v2 Stabilized Gate B — 50-Epoch Screening

**Research Author and Repository Maintainer:** xuwen
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

Status: completed, seed 42, 50/50 epochs, exit status 0.

## Verified result

- Validation-selected checkpoint: Epoch 50
- Official test Mean Dice: `0.7499307646` (`74.9931%`)
- Official test Mean HD95: `37.9087007654`
- Training-only time: `4,890.43 s` (`1.3585 h`)
- Mean epoch time: `97.81 s`
- End-to-end time including validation and test: `6,509 s`
- Peak allocated/reserved memory: `12.058 / 13.189 GB`
- Training/held-out validation slices: `1,778 / 433`
- Source commit on RunPod: `814fc52834dde99dd5ae1fd656fdf4908414fd58`

## Decision

This experiment is retained as a **negative/inconclusive accuracy ablation and
a positive engineering-stability result**. It completed without the E4
Version-1 trajectory failure, but it did not show a strong early accuracy
signal. A 300-epoch extension is not justified under the current unmatched
protocol.

The numerical ranking is confounded because this run reserved 433 of the 2,211
training slices for model selection, while the earlier E1–E4v1 runs used all
2,211 slices and a different checkpoint-selection protocol. Consequently, the
reported gap must not be presented as a controlled proof that the gate is
inferior.

Datasets, case-level images, NIfTI predictions, checkpoints, pretrained
weights, raw server logs and credentials are intentionally excluded.
