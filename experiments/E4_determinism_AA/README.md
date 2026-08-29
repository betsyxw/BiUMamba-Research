# E4 deterministic A/A diagnostic

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)  
**GitHub:** [@betsyxw](https://github.com/betsyxw)

This directory contains the diagnostic code added around the frozen
`E4_version_1` implementation. The original adaptive-gate architecture was not
changed.

## What was added

- `run_determinism_aa.py` enforces the declared seed and deterministic CUDA
  settings, then records loss, batch-order hash, total and gate gradient norms,
  gate-output statistics, logical model hash, and checkpoint-file hash at each
  epoch.
- `analyze_determinism_aa.py` compares two matched runs and generates the CSV,
  JSON manifest, and Markdown report.
- The final segmentation test was skipped because this experiment audits the
  training trajectory, not Dice or HD95.

## Diagnostic-only compatibility fix

Strict PyTorch determinism rejected CUDA `nll_loss2d` before Epoch 1. Only in
this diagnostic wrapper, default cross entropy was expressed as the
mathematically equivalent `log_softmax + gather + mean`. The Dice term,
VM-UNet/VMamba model, scan design, adaptive gate, optimizer, and scheduler were
left unchanged.

## Result

The runs began with the same model hash and used identical per-epoch batch
orders, but model and checkpoint hashes differed from Epoch 1. This is a Red
result for bitwise reproducibility. It requires multi-seed reporting and a
separately named gate-stabilization ablation; it does not by itself disprove
adaptive fusion.

Upstream VM-UNet/VMamba authorship and licensing remain unchanged. These
diagnostic additions and research records are maintained by xuwen.
