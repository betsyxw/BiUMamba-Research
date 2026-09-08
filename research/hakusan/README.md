# Hakusan research reports

Last updated: 20260909

## Latest verified conclusions

BiUMamba (E2_modify_2) is a memory-oriented channel-grouped bidirectional scanning design, not a universal accuracy or speed improvement.

- Peak training memory is approximately 24–25% lower than E1 in the archived cross-dataset results.
- On Synapse CT and ACDC MRI, the observed mean accuracy differences are small; paired patient-level analyses found no statistically significant differences. This does not prove equivalence or no accuracy loss.
- BUSI ultrasound shows significantly worse Dice, HD95 and NSD. This negative result must remain visible.
- The strict RTX 4090 benchmark did not show an inference speedup for the current implementation on any of the three datasets. Lower analytical scan-core workload must not be called faster inference.
- FractalDB-60 did not outperform scratch and remained below ImageNet under the frozen ACDC 25% three-seed protocol. The 50% and 100% seed-42 runs are exploratory only.

The latest correction concerns the Synapse empty-mask policy and downstream Step 20 statistics. It is a CSV aggregation correction, not a new training run or raw-mask reevaluation. ACDC/BUSI results were not recomputed in this update.

## Reports

- [Corrected Synapse report and paired statistics](STEP20_CORRECTION_REPORT_20260909.md)
- [Paper update and final-freeze checklist](PAPER_UPDATE_REPORT_20260909.md)
- [Machine-readable verification summary](VERIFICATION_20260909.json)
- Existing Slurm scripts remain in [slurm/](slurm/).

## Release status

**Candidate, not final frozen.** Corrected tables and statistical figures have been regenerated locally. The newly selected Synapse Small representative, case0038, still needs formal seed-42 E1 and E2_modify_2 prediction masks for its qualitative panel. Do not substitute predictions from a different checkpoint.

## Update history

- **20260909** — Added corrected Synapse conclusions, empty-mask/statistical audit, manuscript regeneration summary and the remaining freeze blocker. Historical reports and frozen results are preserved.

This public update contains text and aggregate statistics only. Medical image pixels, prediction masks, checkpoints, credentials and patient-identifying records are excluded.
