# Results interpretation

## Scan-design evidence

The exploratory scan-design ablation separates directional coverage from resource use. E2 reduced memory by retaining only horizontal forward and backward scans, but its Dice decreased relative to E1. E2_modify_1 alternated horizontal and vertical processing between blocks and was retained only as a Screen50 exploratory result. BiUMamba assigned half of the channels to horizontal bidirectional scanning and half to vertical bidirectional scanning, so both axes remained represented within every block. Under the Full300 seed-42 development protocol, this design gave the strongest observed Dice and HD95 among the scan-design candidates, although these single-seed development results are not equivalent to the formal three-seed evidence.

## Matched-memory control

E1-Narrow was selected by short memory calibration before full training and then evaluated with seeds 42, 2026, and 3407 on the same 12-case Synapse isolated test set. E1-Narrow reduced model width and reached 9.47 GiB peak training allocated memory, close to BiUMamba at 9.04 GiB. Its seed-level Dice was 75.04 ± 2.82%, compared with 76.66 ± 1.22% for BiUMamba, and its NSD was 69.15 ± 2.34%, compared with 71.59 ± 1.73% for BiUMamba. After patient-level three-seed aggregation, E1-Narrow was significantly lower than E1 for Dice and NSD after Holm correction. BiUMamba exceeded E1-Narrow for NSD after Holm correction; the observed Dice advantage did not remain significant after correction. These results support a more favorable observed accuracy–memory trade-off for structured directional allocation than for uniform width reduction, without establishing universal superiority.

## Cross-dataset findings

On Synapse CT and ACDC MRI, BiUMamba produced small observed mean differences from E1, and the patient-level paired analyses did not identify significant differences in Dice, HD95, or NSD. Peak training allocated memory decreased from 11.96 to 9.04 GiB on Synapse and from 8.95 to 6.72 GiB on ACDC. Strict RTX 4090 inference latency was nevertheless higher for BiUMamba, so a universal speed claim is not supported.

On BUSI ultrasound, peak training allocated memory decreased from 11.91 to 8.94 GiB, but Dice and NSD were significantly lower and HD95 was significantly higher after patient/group-level paired analysis. The benefit of channel-grouped scanning is therefore dataset dependent.

## Reporting levels

Tables reporting three-seed mean ± SD summarize variation across training runs. The paired statistical table first averages the three seed results inside each independent patient/case and then compares E1 and BiUMamba. Consequently, the means in the paired table need not be numerically identical to the seed-level aggregate means. Patients, slices, and seeds are not pooled as independent observations.

