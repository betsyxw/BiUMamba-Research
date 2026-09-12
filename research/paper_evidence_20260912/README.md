# BiUMamba paper evidence update

**Updated: 20260912**

This GitHub-safe package reorganizes the final paper evidence around a
training-memory trade-off rather than an unsupported accuracy-improvement or
universal-speed claim.

It contains:

- primary-source differentiation from VM-UNet, GroupMamba, LocalMamba and
  EfficientVMamba;
- the `4HWC -> 2HWC` analytical directional scan-core derivation;
- Tables 1–7 and the Synapse E1-Narrow matched-memory statistics;
- the cell-level table source map and cross-check report;
- manuscript-ready Results, Discussion and Limitations text;
- the claim audit and reproducibility scripts.

The public figures are stored in
[`../result_img/paper_evidence_20260912/`](../result_img/paper_evidence_20260912/).
Fixed-rule qualitative medical-image panels and the complete freeze ZIP are
intentionally excluded from GitHub.

## Evidence-supported conclusion

BiUMamba retains horizontal and vertical bidirectional modeling in every block
and reduces the analytical directional scan-core workload from `4HWC` to
`2HWC`. It reduced peak training allocated memory on Synapse, ACDC and BUSI.
The observed mean performance remained close to E1 on Synapse CT and ACDC MRI,
whereas BUSI ultrasound showed a significant performance decrease.

The Synapse E1-Narrow control provides the central matched-memory comparison.
At a similar memory level, simple narrowing reduced Dice and NSD and showed
higher seed-level variability. BiUMamba retained the original model width and
provided a more favorable observed accuracy-memory balance. The corrected Dice
comparison between BiUMamba and E1-Narrow was not statistically significant;
the NSD comparison remained significant.

The current implementation was slower than E1 in the strict RTX 4090 inference
benchmark. Therefore, the supported claim is **training-memory efficiency with
dataset-dependent segmentation behavior**, not universal runtime acceleration.
