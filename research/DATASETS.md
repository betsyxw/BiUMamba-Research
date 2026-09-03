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

- FractalDB-60: first low-cost pre-training pilot (60 classes x 1,000 images).
- FractalDB-1k: optional expansion only after the FractalDB-60 decision gate.

FractalDB-60, ImageNet and scratch comparisons use the same downstream split,
label fraction, seed, model and evaluation protocol. The first pilot uses a
fixed 18/70-patient ACDC training subset; see
`research/protocols/acdc_fractaldb60_pilot_v1/`.
