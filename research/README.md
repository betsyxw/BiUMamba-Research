# Research record
Research Author and Repository Maintainer: xuwen
Affiliation: Japan Advanced Institute of Science and Technology (JAIST)
GitHub: @betsyxw

Research-specific designs, experiment implementations, ablation records, evaluation reports, and reproducibility documentation in this repository are maintained by xuwen. The original VM-UNet/VMamba code remains attributed to its upstream authors under the retained license. See AUTHORS.md.


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

The authoritative E2 source snapshot was created from RunPod branch
`experiment/e2-bidirectional-fixed-sum`, commit
`4ef87e068c084a16e0cd4f1fe669bfc08530c423`.
