# Manuscript tables and figures update

Last updated: 20260909

## Completed and checked

- Tables 1–7 regenerated together from corrected source CSVs.
- 289 mapped numerical cells passed source/value cross-checks; zero failures.
- Tables 4 and 7 and Supplementary Tables S1–S3 contain the corrected Synapse aggregation. Table 1 numerical results were already correct; reproduced-Synapse metric headers were clarified to avoid unsupported physical-mm wording.
- Patient-level forest plots, paired-difference distributions and the Synapse organ Dice forest plot regenerated.
- Publication table PNG/PDF outputs and qualitative publication/PPT-ready outputs regenerated.
- Synapse typical-case selection updated to case0001.
- The versioned local delivery ZIP was verified against file SHA-256 values for 114 included files.
- Existing v2 frozen files were not overwritten.

Generated local delivery: BiUMamba_Paper_Update_20260909_v3_candidate.zip. This is an update package, not the complete final raw-data archive, and is not uploaded here because it includes medical image pixels. No original manuscript or PPTX was edited in place; the replacement assets are supplied separately.

## Remaining freeze blocker

Corrected fixed-rule selections changed the Synapse typical, Small and Large representatives. The newly selected Small representative is case0038. Its formal seed-42 E1 and E2_modify_2 prediction masks are not available in the checked local archive; the previous RunPod endpoint was unavailable during the check.

The supplied four-row Synapse publication figure therefore explicitly labels its retained small-organ panel as a PRIOR anatomical example. It must not be presented as the corrected fixed-rule Small representative. The complete corrected seven-category selection image remains pending.

Status: CANDIDATE_NOT_FROZEN. Complete the missing formal panel, regenerate its selection/rendering manifests and hashes, and verify the full archive before final freeze.

## Manuscript wording

Use: "small observed mean differences" and "no statistically significant difference in the paired analysis."

Do not use: "equivalent", "non-inferior", "no accuracy loss", "universally better" or "faster on all datasets" without the required evidence.

Retain BUSI's negative accuracy result, separate training from inference memory, and report FractalDB 50%/100% seed-42 results as exploratory. FractalDB's negative result is specific to this study and is not evidence of misconduct in the original FractalDB work.

## Public upload boundary

This folder update contains reports and aggregate verification only. No CT/MRI/ultrasound pixels, Ground Truth or prediction volumes, weights, large data ZIPs or credentials are published.
