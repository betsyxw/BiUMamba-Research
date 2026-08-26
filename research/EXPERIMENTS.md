# Experiment design

## Directional ablation

| ID | Directional design | Fusion | Purpose | Status |
|---|---|---|---|---|
| E1 | Original VMamba four-direction cross-scan | Fixed sum | Reproduced baseline | Complete |
| E2 | Forward row-major + reverse row-major | Fixed sum | Test bidirectionality and two-path coverage | Complete; Red |
| E2b | Horizontal and vertical bidirectional coverage | Fixed sum | Restore 2D coverage before testing fusion | Coverage audit required |
| E3 | Coverage-safe bidirectional design | Global static learnable weights | Separate learnable weighting from input adaptation | Blocked by audit |
| E4 | Coverage-safe bidirectional design | Input-dependent adaptive gate | Test the proposed adaptive fusion | Blocked by audit |

The initially proposed E3 `average` is not scheduled for a full 300-epoch run
until an equivalence test is completed. Because fusion is followed immediately
by LayerNorm, `LN(0.5 * x)` is approximately equal to `LN(x)`. The smoke test
will record maximum and mean absolute differences before E3 is finalized.

## Controlled variables

- Dataset split and preprocessing
- Input size: 224 x 224
- Optimizer and learning-rate schedule
- Epochs: 300
- Batch size: 32
- Seed: 42 for initial screening
- Pretrained VMamba checkpoint
- Evaluation pipeline

Promising comparisons will be expanded to three matched seeds and ACDC.

## E2 decision gate

E2 finished with Dice 0.786080 and HD95 26.1111, versus E1 Dice 0.800488
and HD95 24.6136. The two-path implementation removed the transposed scan pair.
Because the largest degradations were organ dependent, E3/E4 must not reuse
the same two-path definition until a coordinate-level scan coverage audit is
complete. The audit will determine whether E2b should restore horizontal and
vertical bidirectional pairs before fusion ablations resume.

## Pre-training pilot

After the directional signal is established:

1. Scratch
2. ImageNet
3. FractalDB

The first pilot uses 25% labels. Expansion to 50% and 100% labels depends on
the pilot signal.
