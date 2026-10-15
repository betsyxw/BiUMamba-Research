# Source-completeness audit, 20261015

## Why this release was necessary

Previous public updates included shared model branches, some per-experiment
snapshots, metrics and provenance references. They did not provide a complete,
unambiguous six-model entry point. E3 static-fusion and E4-v1 model snapshots
were missing from the checked public main tree. Recording a RunPod commit ID
without copying its Git object does not preserve that source tree.

## What has been restored or made explicit

| Method | Action | Provenance limitation |
|---|---|---|
| E1 | Dedicated model/wrapper/config snapshot; original four-direction mode | Consolidated from the current public shared implementation, not the old RunPod Git tree |
| E2 | Dedicated model/wrapper/config snapshot; horizontal-only mode | Consolidated implementation; not claimed byte-identical to the old tarball |
| E2_modify_1 | Existing model/config retained, local wrapper and entry point added | Existing archive, not a newly recovered historical training commit |
| E2_modify_2 | Existing model/config/frozen records retained; local wrapper and enforced grouped selector | Formal training commit f720144... still not recovered |
| E3 | Model/config/design/smoke source restored from local read-only Hakusan execution archive | Historical training commit 25bde91e... not recovered; no independent old model hash verified |
| E4 | Version-1 model/config/design/smoke source restored from same archive | Historical A/A model hash differs; byte-identical full300/A/A source recovery is not claimed |

The recovered source archive's own note says it was copied from Hakusan
`E2_modify_2_synapse_v2_exec` on 20261015, parent HEAD `ff97fe28`, without Git,
weights, datasets or results. This is a later execution snapshot, not evidence
that the original formal-training Git commit now exists. E3/E4 model/config/
design/smoke files were copied without editing their contents. The common
VMUNet wrapper is separately copied from the public shared implementation.

The full original BiUMamba formal-training identifier recorded in old runs is
`f720144086661dcabb6128f46069a2c40abeebc3`. It remains a provenance gap. Grouped
validation metric agreement, reported separately, is supportive evidence of
checkpoint compatibility, not proof of historical source equivalence.

Historical E3 full300 records point to
`25bde91e5a6b5f55432b62eb0b1e760ea29c437c` in a separate RunPod repository.
E4 A/A records list model-file SHA-256
`b1f69f712d5513fdda479e19531b413eaa4bd5a830632edf81e105f4b376bdbe`;
the later recovered E4-v1 snapshot instead has
`7abdf44bd7bb47fa0ad4d0642452ba48c8f9d941b5cb3caa982e175c22c85b5e`.
This difference is disclosed rather than silently explained as comments only.

## Maintained interfaces versus historical results

The new registry, smoke, common trainer and evaluator are maintained tooling
added on 20261015. Existing experiment sources, result records and frozen
protocols are not rewritten. The common runner enables explicit experiments;
it does not turn single-seed/short historical ablations into formally matched
three-seed experiments. E5 is outside this release.

The root Synapse config still selects `bidirectional_sum` for historical
reasons. Do not use that default for E2_modify_2. The new entry point checks the
method/config pair and loads the selected local snapshot in a unique package.

## Verification and remaining work

Standard-library audits check six mappings, model/config syntax, source-file
hashes, CLI dry descriptions and import-package isolation. A clean-clone check
must also pass before handoff. Mac release verification has no PyTorch/CUDA
stack; CUDA smoke, pretrained loading on GPU, data-dependent inference and
retraining have **not** been performed as part of this repair.

No result CSVs, historical source-hash records, protocols or checkpoints are
modified. Original data/weights/private paths are not uploaded. The source
manifest supports integrity checking of this release; it does not certify
the original training environment or guarantee identical scores after retraining.

Further work, if exact historical recovery is needed: locate original source
tarballs/Git bundles or authorized RunPod disk archives, compare actual source
content and environment, and run allocated GPU numerical checks. Missing items
must remain declared rather than reconstructed and relabeled as originals.
