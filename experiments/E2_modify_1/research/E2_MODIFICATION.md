# E2_modify_1 — alternating-axis bidirectional scan

This version preserves the original E2 source in a separate repository and
changes only the scan coverage policy.

- Even global block index: horizontal forward/reverse, parameter sets `[0, 2]`
- Odd global block index: vertical forward/reverse, parameter sets `[1, 3]`
- Fusion inside each block: fixed equal-weight sum, weights `(1.0, 1.0)`
- Number of scans per block: 2
- Encoder and decoder share one continuous alternating block schedule

The vertical pair is derived from the original SS2D H/W-transposed sequence
construction and is restored to the original HxW coordinates before fusion.

GPU smoke test: PASS. Forward, backward, loss, output shape, axis schedule,
direction-specific gradients, and peak memory were checked.

