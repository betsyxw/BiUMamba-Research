# Final manuscript Tables 1–6 (2026-09-06)

This directory is the public, self-contained table release derived from the local verified `paper_final_results_v2` archive.

## Contents

- `paper_tables/csv/`: final Table 1–6 CSV files. Table 1 is separated into reproduced and original-paper panels.
- `paper_tables/workbook/`: formatted Excel workbook.
- `paper_tables/source_map/`: cell-level mapping from every reported numeric value to its frozen source CSV, selector, source column(s), transformation, and SHA-256.
- `paper_tables/audits/`: Table 1–6 cross-check report; 205/205 numeric cells passed.
- `paper_tables/repro_scripts/`: table generation, checking, and workbook scripts.
- The remaining folders contain only the frozen CSV inputs required to reproduce the tables.

## Interpretation limits

- Table 1a uses the frozen Synapse evaluator's macro-organ aggregate. Table 4 uses patient-level means for paired statistical interpretation.
- TransUNet and Swin-Unet values are reported by the original papers and were not reproduced under this study's setting.
- Screen50 and Full300 ablations are not directly comparable.
- The formal 25% FractalDB result is a three-seed validation result. The 25%, 50%, and 100% isolated-test rows are exploratory seed-42 results.
- Whole-model FLOPs are estimated, not exact.
- E2_modify_2 reduces memory and estimated operations, but the strict benchmark measured higher inference latency on Synapse, ACDC, and BUSI.

## Public-data policy

No medical images, ground-truth masks, prediction masks, patient-identifiable information, checkpoints, or optimizer states are included. Qualitative medical figures remain only in the private professor/local archive.

Run the table audit from this directory with:

```bash
python paper_tables/repro_scripts/audit_final_tables.py .
```
