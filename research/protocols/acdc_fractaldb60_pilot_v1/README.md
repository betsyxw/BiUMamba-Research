# ACDC FractalDB-60 low-label pilot v1

This protocol compares three initialization conditions for the same downstream
model, E2_modify_2, using approximately 25% of the frozen ACDC training pool.

## Fixed downstream protocol

- Model: E2_modify_2 grouped two-axis bidirectional VM-UNet.
- Seed: 42.
- Training patients: 18 patients selected once from the frozen 70-patient
  ACDC v1 training pool with Python `random.Random(42).sample` and then sorted.
- Validation patients: the unchanged 10-patient ACDC v1 validation split.
- Isolated test patients: the unchanged 20-patient ACDC v1 test split. The
  training program cannot construct or read the test dataset.
- Epochs: 300.
- Input, augmentation, optimizer, scheduler, loss and checkpoint rule: the
  same as ACDC v1.
- The only downstream variable is initialization: `scratch`, `imagenet`, or
  `fractaldb60`.

Because 25% of 70 is 17.5, this protocol uses 18 patients (25.7%) and reports
the exact count rather than calling it exactly 25%.

## FractalDB-60 pre-training

FractalDB-60 contains 60 classes with 1,000 images per class. The pilot
pre-trains the same VMamba encoder shape used by the downstream model. It does
not load an incompatible FractalDB ResNet checkpoint.

- Architecture: VMamba encoder, depths `[2, 2, 2, 2]`, original SS2D.
- Input: grayscale converted to three channels, 224 x 224.
- Epochs: 90, fixed final checkpoint (no downstream test-based selection).
- Optimizer: AdamW, learning rate 0.001, weight decay 0.01.
- Scheduler: cosine annealing.
- Seed: 42.

The downstream loader writes an initialization audit containing the source
checkpoint SHA-256, matched tensor count, matched parameter count and mirrored
decoder tensor count. A pretrained run is rejected if any encoder stage has no
matching tensors.

## Decision gate

- Green: FractalDB-60 is better than scratch and reaches or exceeds ImageNet.
- Yellow: FractalDB-60 is better than scratch but below ImageNet; retain it as
  a natural-image-free alternative.
- Red: FractalDB-60 does not improve over scratch; do not expand to 50% or
  100% labels.

This seed-42 pilot is exploratory. A positive signal must be confirmed with
seeds 3407 and 2026 before a formal claim.
