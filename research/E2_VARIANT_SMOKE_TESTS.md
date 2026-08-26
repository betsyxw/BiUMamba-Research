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
- Peak allocated/reserved memory: `267.67 / 276.00 MiB`
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
- Peak allocated/reserved memory: `259.53 / 268.00 MiB`
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

No full training run has been started for either variant. E2_modify_1 is the
recommended first screening candidate because it changes fewer components and
provides the clearest test of whether E2 degraded because vertical coverage
was removed.

