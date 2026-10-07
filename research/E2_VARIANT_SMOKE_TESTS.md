# E2 coverage-recovery variants and GPU smoke tests

Date: 2026-08-27

The original E2 row-major forward/reverse experiment reduced mean Dice from
0.800488 to 0.786080 and increased mean HD95 from 24.613612 to 26.111135.
Two coverage-recovery variants were therefore implemented without modifying
the archived E1 or E2 sources.

## E2_modify_1 — alternating-axis bidirectional scan

- RunPod path: `/workspace/repos/VM-UNet_E2_modify_1`
- Branch: `experiment/e2b-alternating-axis`
- RunPod commit: `3d39ce6`
- Tag: `E2_modify_1_smoke_pass`
- Horizontal blocks: direction parameter sets `[0, 2]`
- Vertical blocks: direction parameter sets `[1, 3]`
- Global schedule: horizontal and vertical blocks alternate across encoder and
  decoder execution order
- Scans per block: 2
- Fusion: fixed equal-weight sum, weights `(1.0, 1.0)`
- GPU smoke test: PASS
- Input/output: `[1,1,64,64]` to `[1,9,64,64]`
- Loss: `2.3616890907`
- Peak allocated/reserved memory: `0.281 / 0.289 GB`
- Gradient audit: every block activated only its expected direction pair; all
  four direction parameter sets received gradients over the complete model
- Source archive:
  `/workspace/source_versions/E2_modify_1/VM-UNet_E2_modify_1-3d39ce6-source.tar.gz`
- Archive SHA-256:
  `36e697bf529ef1434d3fd8fab47432dd60090601a3b741812a08b34ac8a4add3`

## E2_modify_2 — channel-grouped 2D bidirectional scan

- RunPod path: `/workspace/repos/VM-UNet_E2_modify_2`
- Branch: `experiment/e2c-grouped-2d`
- RunPod commit: `62fc67c`
- Tag: `E2_modify_2_smoke_pass`
- First half of channels: horizontal parameter sets `[0, 2]`
- Second half of channels: vertical parameter sets `[1, 3]`
- All four half-channel scans are packed into one selective-scan call
- Effective scanned channel volume: approximately two full-channel scans
- Fusion: fixed equal-weight sum within each group, followed by concatenation
  and the existing output projection
- GPU smoke test: PASS
- Input/output: `[1,1,64,64]` to `[1,9,64,64]`
- Loss: `2.3616871834`
- Peak allocated/reserved memory: `0.272 / 0.281 GB`
- Gradient audit: all four intended parameter slices were non-zero in all 15
  blocks; every inactive half-channel slice was exactly zero
- Source archive:
  `/workspace/source_versions/E2_modify_2/VM-UNet_E2_modify_2-62fc67c-source.tar.gz`
- Archive SHA-256:
  `a97a41fdd5b5f3004abbff9bc183fbfc0b11fd086a2a8fdc42aab58b302b649c`

## Artifact policy

The private GitHub repository contains the modified source files, configs,
design notes, smoke-test programs, and compact test results. It does not
contain datasets, patient images, NIfTI outputs, checkpoints, pretrained
weights, archives, SSH keys, tokens, or authentication information.

E2_modify_1 subsequently completed a 50-epoch Synapse screening run with exit
code 0. It reached mean Dice `0.725396` and mean HD95 `35.579682`, using a
sampled peak of `10.901 GB` GPU memory. These are early-screening metrics, not
a converged comparison with the 300-epoch E1/E2 results. The complete report,
metrics, manifest, and text logs are stored under
`experiments/E2_modify_1/results/screen50_seed42/`.

E2_modify_2 subsequently completed the matched 50-epoch screening run with
exit code 0. It reached mean Dice `0.750737` and mean HD95 `40.415915`, with a
mean epoch time of `170.71 s` and sampled peak memory of `11.551 GB`.

Compared with E2_modify_1, E2_modify_2 improved Dice by 2.5341 percentage
points and reduced mean epoch time by 20.16%, but worsened HD95 by 4.8362. The
full matched comparison is recorded in `research/E2_MODIFY_SCREEN50_COMPARISON.md`.
E2_modify_2 was selected as the first 300-epoch candidate, with HD95 treated
as an explicit risk. A fresh 300-epoch run has now been started. No final
300-epoch metric is available yet.
