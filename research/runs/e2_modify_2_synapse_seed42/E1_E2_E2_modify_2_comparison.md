# E1, E2, and E2_modify_2 Comparison

All three results use the same Synapse split, seed 42, batch size 32, 224 × 224 input, pretrained initialization family, optimizer, scheduler, and 300-epoch budget.

## Overall results

| Metric | E1: 4-direction SS2D | E2: row-only F/B | E2_modify_2: grouped horizontal/vertical F/B |
|---|---:|---:|---:|
| Mean Dice | 80.0488% | 78.6080% | **80.2540%** |
| Mean HD95 | 24.6136 | 26.1111 | **21.9206** |
| Checkpoint epoch | 286 | 299 | 297 |
| Mean epoch time | 177.86 s | 164.48 s | **157.06 s** |
| Training-only time | 14.82 h | 13.71 h | **13.09 h** |
| Wall time | 15.82 h | 14.50 h | **13.87 h** |
| Peak sampled GPU memory | 15.377 GB | **11.269 GB** | 11.551 GB |

## Main findings

1. **E2 confirms the coverage problem.** Reducing SS2D to row-major forward/reverse lowers resource use but loses accuracy and worsens HD95.
2. **E2_modify_2 recovers the lost signal.** Channel grouping preserves horizontal and vertical information inside every block.
3. **E2_modify_2 exceeds E1 in this seed.** Dice improves by 0.2052 percentage points and HD95 decreases by 2.6931.
4. **Efficiency also improves over E1.** Mean epoch time decreases by 11.69% and sampled peak memory decreases by 24.88%.
5. **The result is not uniformly better for every organ.** Gallbladder and pancreas Dice remain below E1, and stomach Dice remains slightly below E1. Multi-seed confirmation and qualitative inspection are required.

## Decision

E2_modify_2 passes the predeclared **Strong Green** gate. The next justified step is to implement the static learnable fusion control and the input-adaptive gate on the coverage-preserving grouped-2D structure, first with a smoke test and short screening run.

The current result is single-seed evidence and must not yet be presented as a statistically established improvement.
