# Experiment design

## Directional ablation

| ID | Directional design | Fusion | Purpose | Status |
|---|---|---|---|---|
| E1 | Original VMamba four-direction cross-scan | Fixed sum | Reproduced baseline | Complete |
| E2 | Forward row-major + reverse row-major | Fixed sum | Test bidirectionality | Training |
| E3 | Same two directions | Global static learnable weights | Separate learnable weighting from input adaptation | Planned |
| E4 | Same two directions | Input-dependent adaptive gate | Test the proposed adaptive fusion | Planned |

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

## Pre-training pilot

After the directional signal is established:

1. Scratch
2. ImageNet
3. FractalDB

The first pilot uses 25% labels. Expansion to 50% and 100% labels depends on
the pilot signal.
