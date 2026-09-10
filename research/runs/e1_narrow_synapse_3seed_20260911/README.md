# E1-Narrow Synapse three-seed control

Updated: 20260911

## Purpose

This experiment tests whether BiUMamba's memory result can be reproduced by
simply narrowing the original four-direction E1 model. Four SS2D expansion
candidates received short memory-only calibration. Expansion `1.50` was fixed
before full training.

The formal control used seeds `42`, `2026` and `3407`, 300 epochs, the frozen
Synapse split and the same 12-case isolated test set as E1 and BiUMamba. All
three runs completed successfully. Seed 3407 was valid and no additional seed
was introduced after observing the results.

## Results

| Method | Dice (%) | HD95 | NSD (%) | Peak training allocated | Parameters | Strict latency |
|---|---:|---:|---:|---:|---:|---:|
| E1 | 76.84 ± 1.15 | 32.13 ± 4.95 | 71.59 ± 2.25 | 11.96 GiB | 27.43 M | 4.955 ± 0.544 ms |
| E1-Narrow | 75.04 ± 2.82 | 33.89 ± 3.99 | 69.15 ± 2.34 | 9.47 GiB | 21.36 M | 10.740 ± 0.187 ms |
| BiUMamba | 76.66 ± 1.22 | 33.12 ± 5.06 | 71.59 ± 1.73 | 9.04 GiB | 27.43 M | 7.043 ± 0.832 ms |

Patient-level statistics first average each patient across the three seeds.
BiUMamba minus E1-Narrow was `+1.62` percentage points for Dice and `+2.44`
percentage points for NSD. Dice did not remain significant after Holm
correction (`p=0.0683`), while NSD did (`p=0.0111`). HD95 was not significant.

## Interpretation

The experiment supports BiUMamba as the stronger observed accuracy-memory
trade-off. E1-Narrow saved parameters but reduced Dice and NSD and showed
greater observed seed-level variation. BiUMamba used slightly less training
memory and had lower inference latency than E1-Narrow while retaining the
original model capacity.

This does not establish Dice superiority after multiple-comparison correction,
equivalence to E1, or a universal runtime speedup. E1-Narrow was evaluated only
on Synapse and is not cross-dataset evidence.

## Contents

- `statistics/`: per-seed results, per-patient three-seed averages and paired tests.
- `efficiency/`: strict RTX 4090 benchmark summary and 200 timed iterations.
- `tables/`: updated manuscript Tables 2, 4 and 6 in CSV format.
- `report/`: statistical report and updated paper conclusion.

Checkpoints, source medical images and prediction masks are not included in
this GitHub-safe folder.
