# ACDC v1 Formal Three-Seed Evaluation

This archive contains the GitHub-safe records for E1 and E2_modify_2 on the frozen ACDC v1 protocol.

- Seeds: 42, 3407, 2026.
- Split: 70 training, 10 validation, 20 isolated test patients.
- Test set: 40 ED/ES volumes.
- Checkpoint selection: higher validation Dice; lower validation HD95 as tie-breaker.
- Final metrics: Dice, physical HD95 in millimetres, and NSD at 1 mm.
- Decision: Yellow / efficiency-oriented.

E2_modify_2 keeps nearly the same three-seed mean Dice as E1 while reducing training time, mean epoch time, peak GPU memory, and inference time. Mean HD95 and NSD are slightly worse, so the result supports an accuracy-efficiency trade-off rather than a universal accuracy improvement.

Patient images, prediction masks, NIfTI files, checkpoints, pretrained weights, medical-image PDFs/PNGs, ZIP archives, and credentials are intentionally excluded.
