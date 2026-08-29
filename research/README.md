# Research record

This directory stores lightweight, reproducible experiment metadata. Large or
restricted artifacts remain outside GitHub.

- `EXPERIMENTS.md`: E1-E4 definitions and decision gates.
- `RESULTS.md`: verified quantitative results only.
- `DATASETS.md`: expected dataset layout without dataset files.
- `manifests/`: launch and smoke-test records.
- `metrics/`: small CSV result tables.
- `environment/`: frozen package versions used on RunPod.
- `runs/e2_synapse_seed42/`: complete E2 report, CSV metrics, manifests, and
  text logs. Checkpoints and NIfTI outputs are excluded.
- `runs/e1_synapse_seed42/`: archived E1 baseline report and metrics.
- `runs/e2_modify_2_synapse_seed42/`: converged grouped-2D fixed-fusion report,
  overall/per-organ comparisons, and manifest.
- `runs/E3_fusion_50_epochs/`: E3 static-fusion 50-epoch screening record.
- `runs/E3_fusion_300_epochs/`: E3 full-run archive, five-experiment overall
  and per-organ comparisons, manifest, and trilingual PPT summary.
- `runs/E4_version_1_full300/`: E4 full-run archive, six-experiment overall
  comparison, eight-organ comparison, metrics, and structured manifest.
- `runs/E4_determinism_AA/`: frozen-source deterministic A/A audit, aggregate
  epoch metrics, model/checkpoint hashes, compatibility finding, and decision
  record. Datasets, case lists, checkpoints, weights, and server logs are
  excluded.

The authoritative E2 source snapshot was created from RunPod branch
`experiment/e2-bidirectional-fixed-sum`, commit
`4ef87e068c084a16e0cd4f1fe669bfc08530c423`.
