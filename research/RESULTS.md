# Verified results

Only completed measurements are recorded here. Ongoing experiments are never
filled with estimates.

## E1 — VM-UNet Synapse baseline

- Best checkpoint: epoch 286
- Mean Dice: 0.800488 (80.0488%)
- Mean HD95: 24.6136
- Training duration: approximately 15 h 49 min
- Peak GPU memory: approximately 14.3 GB
- Test volumes: 12
- Qualitative exports: 36 NIfTI files (not stored in GitHub)

| Organ | Dice (%) | HD95 |
|---|---:|---:|
| Aorta | 85.7881 | 22.7990 |
| Gallbladder | 68.2824 | 26.3341 |
| Left Kidney | 85.0418 | 36.0768 |
| Right Kidney | 78.9200 | 37.9346 |
| Liver | 93.8822 | 23.3211 |
| Pancreas | 60.9000 | 9.9068 |
| Spleen | 87.8004 | 22.7226 |
| Stomach | 79.7755 | 17.8141 |

## E2 — bidirectional fixed sum

Status: complete (seed 42, 300 epochs, exit status 0).

- Mean Dice: 0.786080 (78.6080%)
- Mean HD95: 26.1111
- Wall-clock duration: 14 h 30 min 11 s
- Mean training time per epoch: 164.48 s
- Peak sampled device memory: 10,747 MiB
- Relative to E1: Dice -1.4408 percentage points; HD95 +1.4975
- Decision: Red — audit lost transposed/vertical coverage before E3/E4

The complete report, per-organ comparison, manifests, and logs are stored in
[`runs/e2_synapse_seed42/`](runs/e2_synapse_seed42/).

## E2_modify_2 — grouped 2D bidirectional fixed sum

Status: complete (seed 42, 300 epochs, exit status 0).

- Checkpoint epoch: 297
- Mean Dice: 0.802540 (80.2540%)
- Mean HD95: 21.9206
- Mean training time per epoch: 157.06 s
- Peak sampled device memory: 11,016 MiB
- Relative to E1: Dice +0.2052 percentage points; HD95 -2.6931
- Decision: Strong Green — preserve grouped horizontal/vertical coverage for E3/E4

The archive and comparisons are stored in
[`runs/e2_modify_2_synapse_seed42/`](runs/e2_modify_2_synapse_seed42/).

## E3 — static learnable fusion screening

Status: complete (seed 42, 50 epochs, exit status 0).

- Checkpoint epoch: 48
- Mean Dice: 0.756773 (75.6773%)
- Mean HD95: 36.0624
- Mean training time per epoch: 152.66 s
- Peak sampled device memory: 12,958 MiB
- Matched E2_modify_2 50-epoch result: Dice 75.0737%, HD95 40.4159
- Matched change: Dice +0.6035 percentage points; HD95 -4.3535
- Decision: passes the short-screening gate; a matched 300-epoch run is justified

This screening result must not be ranked directly against the 300-epoch rows.
The report and overall/per-organ CSV files are stored in
[`runs/E3_fusion_50_epochs/`](runs/E3_fusion_50_epochs/).

## E3 — static learnable fusion full run

Status: complete (seed 42, 300 epochs, exit status 0).

- Checkpoint epoch: 286
- Mean Dice: 0.800049 (80.0049%)
- Mean HD95: 25.5669
- Training-only duration: 11 h 35 min 28 s
- Mean training time per epoch: 139.09 s
- Peak sampled device memory: 12,958 MiB
- Relative to E2_modify_2: Dice -0.2491 percentage points; HD95 +3.6464
- Per-organ Dice: improved for pancreas and stomach; decreased for six organs
- Decision: E3 does not replace E2_modify_2; retain as a negative/neutral ablation

The full archive, five-experiment comparison, per-organ CSV, manifest and
trilingual presentation summary are stored in
[`runs/E3_fusion_300_epochs/`](runs/E3_fusion_300_epochs/).

## E4 Version 1 — constrained adaptive gate full run

Status: complete (seed 42, 300 epochs, exit status 0; Red decision).

- Checkpoint epoch: 285, selected by minimum training loss
- Mean Dice: 0.709089 (70.9089%)
- Mean HD95: 35.3190
- Training-only duration: 9 h 49 min 34 s
- Mean training time per epoch: 117.91 s
- Peak sampled device memory: 13,534 MiB
- Relative to E2_modify_2: Dice -9.3451 percentage points; HD95 +13.3985
- Per-organ Dice: decreased for all eight evaluated organs
- Reproducibility warning: Epoch-50 loss was 0.7409 in the full run versus
  0.1146 in the screening run despite matching logged settings
- Decision: retain E4 as a negative ablation; audit the screen/full mismatch
  before another full run

The E4 archive, six-experiment overall comparison, eight-organ comparison,
metrics and structured manifest are stored in
[`runs/E4_version_1_full300/`](runs/E4_version_1_full300/).

## E4 Version 2-B — stabilized adaptive gate screening

Status: complete (seed 42, 50 epochs, exit status 0; negative/inconclusive
accuracy decision).

- Checkpoint epoch: 50, selected by held-out validation Dice with HD95 tie-break
- Mean Dice: 0.749931 (74.9931%)
- Mean HD95: 37.9087
- Training-only duration: 1 h 21 min 30 s
- End-to-end wall time: 1 h 48 min 29 s
- Mean training time per epoch: 97.81 s
- Peak allocated GPU memory: 11,499.30 MiB
- Peak reserved GPU memory: 12,578 MiB
- Final training loss: 0.1046
- Stabilization changes: `0.1x` gate learning rate, five frozen gate epochs,
  alpha ramp `0 -> 0.25`, gradient clipping `1.0`, equal-fusion regularization,
  context normalization, temperature scaling, and persistent alpha checkpoints
- Decision: the engineering stabilization succeeded, but the accuracy result
  does not justify a 300-epoch extension; E2_modify_2 remains the main model

Protocol warning: this run trained on 1,778 slices and reserved 433 slices for
held-out validation. Earlier E1-E4 runs trained on all 2,211 slices, so E4
Version 2-B is not a controlled architecture comparison against those runs.
The seven-experiment table is provided for traceability and is explicitly
marked as protocol-confounded.

The archive report, overall and per-organ CSV files, verified workbook,
manifest, and negative-ablation/stability analysis are stored in
[`runs/E4_v2_stabilized_b_epoch50/`](runs/E4_v2_stabilized_b_epoch50/).
