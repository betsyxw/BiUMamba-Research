# Experiment design

## Directional ablation

| ID | Directional design | Fusion | Purpose | Status |
|---|---|---|---|---|
| E1 | Original VMamba four-direction cross-scan | Fixed sum | Reproduced baseline | Complete |
| E2 | Forward row-major + reverse row-major | Fixed sum | Test bidirectionality and two-path coverage | Complete; Red |
| E2_modify_1 | Alternating-axis horizontal/vertical bidirectional blocks | Fixed sum | Restore 2D coverage across blocks | 50-epoch screen complete |
| E2_modify_2 | Channel-grouped horizontal/vertical bidirectional scan | Fixed sum | Restore 2D coverage inside every block | 50-epoch screen complete; 300-epoch run active |
| E3 | Coverage-safe design selected after convergence | Global static learnable weights | Separate learnable weighting from input adaptation | Pending E2_modify_2 decision gate |
| E4 | Coverage-safe design selected after convergence | Input-dependent adaptive gate | Test the proposed adaptive fusion | Pending E2_modify_2 decision gate |

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

## E2 decision gate and coverage-recovery screening

E2 finished with Dice 0.786080 and HD95 26.1111, versus E1 Dice 0.800488
and HD95 24.6136. The two-path implementation removed the transposed scan pair.
Because the largest degradations were organ dependent, E3/E4 must not reuse
the same two-path definition until a coordinate-level scan coverage audit is
complete.

The matched 50-epoch screen compared E2_modify_1 (alternating-axis blocks) and
E2_modify_2 (channel-grouped horizontal/vertical scanning in every block).
E2_modify_2 reached Dice `0.750737`, versus `0.725396` for E2_modify_1, and was
about `20.16%` faster per epoch. It also improved Dice in seven of eight organs.
However, its HD95 was worse (`40.415915` versus `35.579682`), indicating a
boundary-outlier risk. E2_modify_2 was therefore selected for a fresh 300-epoch
validation, but the selection remains provisional until converged Dice and
HD95 are available.

## Pre-training pilot

After the directional signal is established:

1. Scratch
2. ImageNet
3. FractalDB

The first pilot uses 25% labels. Expansion to 50% and 100% labels depends on
the pilot signal.
