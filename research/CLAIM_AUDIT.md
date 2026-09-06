# Step 25 claim audit

Audit date: 2026-09-06  
Status: **conditional pass**

The frozen evidence package passes the claim audit. The final manuscript-level audit remains pending because the complete Abstract, Results, Discussion, and Conclusion source is not yet present in this repository.

## Passed checks

- Tables 1–7 were generated from frozen CSV inputs and 289/289 mapped numeric cells passed the cross-check.
- Formal mean ± standard deviation results use seeds 42, 3407, and 2026.
- Patient-level statistics average seeds within each independent patient/case before pairing and report the paired difference, 10,000-resample bootstrap 95% CI, p value, Holm-adjusted p value, and effect size.
- Synapse and ACDC are described as having comparable observed performance, not proven equivalence.
- BUSI is retained as a significant dataset-dependent limitation.
- Training and inference memory are reported separately from strict same-RTX-4090 latency.
- FractalDB-60 at 25% labels is a formal three-seed Red result; 50% and 100% are exploratory seed-42 results.
- E2, E2_modify_1, and fusion single-seed results are explicitly exploratory.
- nnU-Net v2 is identified as using its model-specific training protocol.
- TransUNet and Swin-Unet are identified as original-paper values not reproduced under this setting.
- Negative experiments and fixed-rule qualitative selections are retained.

## Prohibited unsupported claims

- `universally better`
- `significantly improves accuracy`
- `equivalent` or `non-inferior`
- `eliminates the domain gap`
- `especially effective with limited labels`
- `faster on all datasets`
- `generalizes across all medical image types`

## Remaining gate

Repeat the audit sentence by sentence after the complete manuscript is available. Until then, the evidence package is passed, but the final manuscript cannot be marked as fully audited.

