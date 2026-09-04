# ACDC FractalDB-60 label-fraction isolated test (seed 42)

All nine E2_modify_2 checkpoints were selected only by validation Dice, with
lower validation HD95 as the tie-breaker. They were then evaluated once on the
same frozen 20-patient isolated ACDC test set (40 ED/ES volumes). The test set
was not read during training or checkpoint selection.

| Labels | Initialization | Dice (%) ↑ | HD95 (mm) ↓ | NSD@1 mm (%) ↑ |
|---:|---|---:|---:|---:|
| 25% | Scratch | 86.77 | 5.671 | 83.98 |
| 25% | ImageNet | 89.50 | 4.105 | 88.51 |
| 25% | FractalDB-60 | 86.39 | 6.665 | 83.43 |
| 50% | Scratch | 85.39 | 6.083 | 83.04 |
| 50% | ImageNet | 90.31 | 3.045 | 90.30 |
| 50% | FractalDB-60 | 87.83 | 5.135 | 86.20 |
| 100% | Scratch | 89.90 | 3.220 | 89.84 |
| 100% | ImageNet | 90.33 | 3.678 | 90.02 |
| 100% | FractalDB-60 | 90.06 | 3.144 | 89.96 |

Decision by the frozen primary Dice rule:

- 25%: **Red** — FractalDB-60 did not exceed Scratch.
- 50%: **Yellow** — FractalDB-60 exceeded Scratch but remained below ImageNet.
- 100%: **Yellow** — FractalDB-60 slightly exceeded Scratch and was close to ImageNet.

From 25% to 100%, FractalDB-60 improved Dice by 3.67 percentage points,
reduced HD95 by 3.52 mm, and improved NSD by 6.53 percentage points. This is
the opposite of the planned low-label advantage hypothesis: the current signal
became stronger as more labels were provided. The non-monotonic Scratch result
at 50% also shows why this single-seed comparison must not be treated as a
statistically stable conclusion.

Remote complete package:
`/workspace/outputs/acdc_fractaldb60_label_fraction_seed42_isolated_test_runpod.zip`

Package SHA-256:
`b9447944250171880f48d40e7f03c4063f543c37fc11d31684675fe9889770c9`

