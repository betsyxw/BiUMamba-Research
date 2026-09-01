# Synapse v2 Formal Test Correction Audit

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

## Detected issue

The first E2_modify_2 formal-test attempt instantiated the checkpoint with
`bidirectional_sum`. E2_modify_2 was trained with
`grouped_2d_bidirectional_sum`. The checkpoint loaded strictly because the two
variants have the same parameter names, but the forward computation was wrong.
The invalid seed-42 attempt produced a mean Dice of 0.0266 and must not be used.

## Corrective action

1. The running test process was stopped; no training job or checkpoint was
   interrupted or modified.
2. All affected outputs were moved to a directory explicitly marked
   `invalid_20260901_wrong_scan_fusion`.
3. The formal-test mapping was corrected to
   `E2_modify_2 -> grouped_2d_bidirectional_sum`.
4. The corrected script SHA-256 is
   `acb564931bec61e2d99d7e748e3370fb41bbb7b2ed6c450b866709cbb8a76ca3`.
5. All three E2_modify_2 checkpoints are being re-evaluated from scratch.

## Data-use decision

No value from the invalid attempt will be included in per-seed summaries,
three-seed statistics, Excel/PPT tables, or manuscript conclusions. The audit
record is retained for reproducibility.

