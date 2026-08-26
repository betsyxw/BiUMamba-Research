# E2_modify_2 — channel-grouped 2D bidirectional scan

This version preserves the original E2 source in a separate repository and
splits the inner channels into two complementary spatial groups.

- First half of channels: horizontal forward/reverse, parameter sets `[0, 2]`
- Second half of channels: vertical forward/reverse, parameter sets `[1, 3]`
- Fusion inside each group: fixed equal-weight sum, weights `(1.0, 1.0)`
- Group outputs: concatenated, then mixed by the existing output projection
- All four half-channel scans are packed into one selective-scan call

This retains horizontal and vertical coverage in every SS2D block while the
total scanned channel volume is approximately that of two full-channel scans.

GPU smoke test: PASS. Forward, backward, loss, output shape, active/inactive
gradient slices, and peak memory were checked.

