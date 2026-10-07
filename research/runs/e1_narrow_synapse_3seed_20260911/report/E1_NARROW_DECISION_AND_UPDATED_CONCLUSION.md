# E1-Narrow control: decision and updated paper conclusion

Updated: 20260911

## Experimental question

At approximately the same training-memory budget, is the proposed channel-grouped BiUMamba design more useful than simply reducing the internal SS2D expansion of the original four-direction E1 model?

The E1-Narrow width was selected before full training using a short four-candidate memory calibration. The selected expansion factor was 1.50. The full experiments then used the fixed seeds 42, 2026, and 3407 and the same frozen Synapse split and 12-case isolated test set. No additional seed was selected after seeing the results.

## Main results

| Method | Dice (%) | HD95 | NSD (%) | Peak training allocated | Parameters | Strict latency |
|---|---:|---:|---:|---:|---:|---:|
| E1 / VM-UNet | 76.84 ± 1.15 | 32.13 ± 4.95 | 71.59 ± 2.25 | 12.842 GB | 27.43 M | 4.955 ± 0.544 ms |
| E1-Narrow | 75.04 ± 2.82 | 33.89 ± 3.99 | 69.15 ± 2.34 | 10.168 GB | 21.36 M | 10.740 ± 0.187 ms |
| BiUMamba | 76.66 ± 1.22 | 33.12 ± 5.06 | 71.59 ± 1.73 | 9.707 GB | 27.43 M | 7.043 ± 0.832 ms |

E1-Narrow reduced E1's parameter count by about 22.1% and reduced peak allocated training memory by about 20.8%. However, compared with E1, its paired patient-level Dice decreased by 1.80 percentage points (95% bootstrap CI −2.84 to −0.93; Holm-adjusted p=0.0094) and its NSD decreased by 2.44 percentage points (95% CI −3.50 to −1.43; adjusted p=0.0030). Its HD95 increase was not statistically significant.

Compared with E1-Narrow, BiUMamba increased observed mean Dice by 1.62 percentage points and NSD by 2.44 percentage points. The Dice comparison had raw p=0.034 but did not remain significant after Holm correction (adjusted p=0.068); therefore, it must not be described as a statistically significant Dice improvement. The NSD difference remained significant after correction (adjusted p=0.011). HD95 showed no significant difference.

BiUMamba also showed lower observed seed-level variability for Dice (1.22 versus 2.82 percentage points) and NSD (1.73 versus 2.34 percentage points). Because only three fixed seeds were used, this is descriptive evidence of stability, not a formal variance test.

## Decision

The new control supports retaining BiUMamba as the proposed model. Under the near-matched training-memory setting, simple narrowing saved parameters but reduced Dice and NSD and produced greater observed seed-to-seed variation. BiUMamba used slightly less peak allocated training memory than E1-Narrow (9.707 versus 10.168 GB) while retaining the original parameter capacity. It also had lower strict inference latency than E1-Narrow (7.04 versus 10.74 ms), although original E1 remained the fastest of the three.

The evidence therefore supports an **accuracy–memory trade-off** claim, not a universal speed or accuracy claim. BiUMamba is more defensible than simple narrowing when the priority is to reduce memory while preserving Synapse segmentation performance. E1-Narrow remains attractive only when reducing parameter count is itself a deployment requirement.

## Updated paper conclusion

> Naively removing directional paths or reducing model capacity is not sufficient to preserve the accuracy–memory balance of VM-UNet. On Synapse, a preselected near-memory-matched E1-Narrow control reduced the parameter count but produced lower Dice and NSD and greater observed seed-level variability than the channel-grouped design. BiUMamba retained the original model capacity, used slightly less peak training memory than E1-Narrow, and achieved better observed Dice and NSD with lower inference latency than the narrow control. Together with the cross-dataset results, these findings support BiUMamba as a memory-efficient redesign with comparable observed performance to VM-UNet on Synapse CT and ACDC MRI, while the degradation on BUSI ultrasound defines an important dataset-dependent limitation.

## Claims that remain prohibited

- BiUMamba significantly improves Dice over E1-Narrow.
- BiUMamba is faster than E1 on all datasets.
- BiUMamba has no accuracy loss or is equivalent/non-inferior to E1.
- BiUMamba generalizes equally well to all medical image types.

## Statistical unit and correction

Each Synapse patient was first averaged across the three fixed seeds. Paired tests then used 12 independent patients. Bootstrap confidence intervals used 10,000 patient-level resamples with bootstrap seed 20260911. Dice, HD95, and NSD p-values were Holm-corrected within each model contrast.
