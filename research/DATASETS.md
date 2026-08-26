# Dataset setup

Dataset files are excluded from this repository.

## Synapse

Expected paths:

```text
data/Synapse/
├── train_npz/
├── test_vol_h5/
└── lists/lists_Synapse/
```

## ACDC

ACDC will be integrated after the Synapse E1-E4 screening. The split and
preprocessing manifest must be frozen before the first full run.

## FractalDB

Compressed archives are stored outside GitHub:

- FractalDB-60: pipeline smoke testing only.
- FractalDB-1k: formal natural-image-free pre-training experiments.

FractalDB-1k, ImageNet and scratch comparisons must use the same downstream
split, label fraction and evaluation protocol.
