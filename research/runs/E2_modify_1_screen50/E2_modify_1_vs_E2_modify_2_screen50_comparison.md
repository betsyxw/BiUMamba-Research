# E2 coverage-recovery 50-epoch screening comparison

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

Both variants used the same Synapse split, seed 42, batch size 32, 224x224 input, pretrained initialization, optimizer, scheduler, and 50-epoch budget.

| Metric | E2_modify_1: alternating axis | E2_modify_2: channel-grouped 2D | Difference (2 - 1) |
|---|---:|---:|---:|
| Mean Dice | 0.725396 | **0.750737** | **+0.025341 (+2.5341 pp)** |
| Mean HD95 | **35.579682** | 40.415915 | +4.836232 (worse) |
| Final loss | 0.1478 | **0.1307** | -0.0171 |
| Mean epoch time | 213.81 s | **170.71 s** | -43.10 s (-20.16%) |
| Peak GPU memory | **10,396 MiB** | 11,016 MiB | +620 MiB (+5.96%) |

## Organ-level change from E2_modify_1 to E2_modify_2

| Organ | Dice change | HD95 change | Interpretation |
|---|---:|---:|---|
| Aorta | +0.011290 | -1.872809 | both improved |
| Gallbladder | +0.020508 | +18.334871 | Dice improved, boundary worsened |
| Left kidney | +0.021082 | +21.151046 | Dice improved, boundary worsened |
| Right kidney | +0.029946 | +2.357919 | Dice improved, boundary worsened |
| Liver | +0.005259 | -2.263834 | both improved |
| Pancreas | +0.095188 | -4.108395 | strong improvement |
| Spleen | +0.021425 | +8.891114 | Dice improved, boundary worsened |
| Stomach | -0.001970 | -3.800053 | essentially tied Dice, better boundary |

## Decision

The original green criterion (higher Dice and lower HD95) was not fully met. E2_modify_2 nevertheless shows the stronger screening signal: Dice improved in seven of eight organs, pancreas improved substantially, and training was about 20% faster. Its HD95 risk is concentrated in several organ/case outliers and must be checked after convergence.

**Decision: E2_modify_2 was selected as the first 300-epoch candidate, with HD95 as an explicit stop/review criterion.** Keep E2_modify_1 archived as the simpler fallback. A fresh 300-epoch E2_modify_2 run has now been started; its final Dice/HD95 are not yet available and must not be inferred from the 50-epoch screen.
