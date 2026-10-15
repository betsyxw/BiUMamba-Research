# E1--E4 source and reproduction entry points

Updated: **20261015**

This release makes model identity explicit and restores the E3 and E4-v1
implementation snapshots missing from the public repository. It does not
claim that all original training Git objects have been recovered or that
training has been numerically reproduced in this release.

## Select the model, not a similarly named fusion flag

| CLI method | Source directory under `experiments/` | Required scan mode |
|---|---|---|
| `E1` | `E1` | `original` |
| `E2` | `E2` | `bidirectional_sum` |
| `E2_modify_1` | `E2_modify_1` | `alternating_axis_sum` |
| `E2_modify_2` | `E2_modify_2` | `grouped_2d_bidirectional_sum` |
| `E3` | `E3_static_fusion` | `grouped_2d_static_fusion` |
| `E4` | `E4_version_1` | `grouped_2d_adaptive_gate_v1` |

**BiUMamba is E2_modify_2, not `bidirectional_sum`.** E4 here is the original
adaptive residual-gate experiment, not the separately archived stabilized v2-B.
The registry imports each model in a unique package so an unrelated root-level
`vmamba.py` cannot silently replace the requested implementation. Conflicting
scan-mode overrides fail explicitly. These six variants do not include E5.

## Clean-clone inspection (standard library only)

```bash
git clone https://github.com/betsyxw/BiUMamba-Research.git
cd BiUMamba-Research
python -m reproducibility.model_registry
python -m reproducibility.verify_release
python -m unittest discover -s reproducibility/tests -v
```

These commands verify files, syntax, model/config identities and hashes; they
are not CUDA numerical validation. See `SOURCE_MANIFEST.json` and
`SOURCE_RECOVERY_AUDIT.md` for the release's evidence limits.

## Environment and external inputs

Training requires Linux/NVIDIA CUDA and compatible selective-scan extensions.
The historical target was Python 3.8, PyTorch 1.13.0+cu117, torchvision
0.14.0+cu117, timm 0.4.12, mamba-ssm 1.0.1 and causal-conv1d 1.0.0.
See `requirements-core.txt` for Python dependencies and the original
[`requirements-runpod-e1.txt`](../research/environment/requirements-runpod-e1.txt)
for the fuller historical environment. Its local wheel URLs are provenance
records, not downloadable dependencies. Obtain compatible extensions from
their official projects or use your institution's verified installation;
do not copy private credentials or use an arbitrary binary wheel.

The repository does **not** contain datasets or trained/pretrained weights.
Obtain the Synapse data through its authorized source and prepare the existing
slice/volume format described in [`data/README.md`](../data/README.md) and
[`synapse_v2`](../research/protocols/synapse_v2/README.md). Obtain
`vmamba_small_e238_ema.pth` from the upstream
[VM-UNet](https://github.com/JCruan519/VM-UNet) /
[VMamba](https://github.com/MzeroMiko/VMamba) instructions and record its hash.
Only load trusted checkpoints: historical PyTorch checkpoint loading uses pickle.

The frozen v2 development set has **14 training cases / 1,798 slices** and
**4 validation cases / 413 slices**. The 2,211 development slices are the
combined pool, not the number used for v2 training. There are 12 isolated test
volumes. Run the protocol verifier before training:

```bash
python research/protocols/synapse_v2/verify_protocol.py --train-npz /path/to/train_npz
```

GPU smoke check, one method at a time (only on an allocated compute node):

```bash
python -m reproducibility.smoke --method E2_modify_2
```

## Maintained training interface

```bash
PYTHONHASHSEED=42 python -m reproducibility.train_synapse \
  --method E2_modify_2 --seed 42 --epochs 300 \
  --train-npz /path/to/train_npz \
  --pretrained /path/to/vmamba_small_e238_ema.pth \
  --work-dir /path/to/new_run_directory
```

Replace `--method` with any of the six table entries; repeat with seeds 2026
and 3407 when the experiment plan calls for three runs. This command is an
example, not an instruction to automatically launch six models or GPU jobs.
`--describe-only` prints the selected source without importing torch or reading
datasets. Existing output directories are refused.

This is a **new maintained common Synapse-v2 runner**, using the archived
train-only engine, augmentation, validation implementation and checkpoint
selector. It is not the missing historical commit. It reads train/validation
data only; hashing the test case list for integrity does read its bytes.
Optimizer: AdamW lr 0.001/wd 0.01; batch 32; input 224; AMP off;
CosineAnnealingLR T_max=100/eta_min=1e-5 for 300 epochs, without scheduler
restarts. Best checkpoint maximizes validation Dice with HD95 tie-breaker.
Logs include source/config hashes, model identity and pretrained load messages.

Do not relabel historical E2, alternating-axis or E3/E4 preliminary results as
new common-protocol results. Old runs include different data usage, epoch
budgets and minimum-training-loss checkpoint selection. E1/E2_modify_2 formal
trainers remain unchanged under their existing experiment directories, but
their root-config dependencies must be inspected; the explicit interface above
avoids inheriting the root config's default `bidirectional_sum` accidentally.

## Validation and isolated test evaluation

```bash
python -m reproducibility.evaluate_synapse \
  --method E2_modify_2 --checkpoint /path/to/best_validation.pth \
  --split validation --train-npz /path/to/train_npz \
  --output-dir /path/to/new_validation_output
```

Use the exact model that trained the checkpoint. A strict load verifies names
and shapes, not functional equivalence. The runner only removes a common
DataParallel `module.` prefix, records that operation and otherwise uses strict
loading; it never substitutes another model or drops mismatched keys.

Only after model selection is fixed, explicitly request isolated-test access:

```bash
python -m reproducibility.evaluate_synapse \
  --method E2_modify_2 --checkpoint /path/to/best_validation.pth \
  --split test --test-volume-dir /path/to/test_vol_h5 \
  --output-dir /path/to/new_isolated_test_output
```

This maintained evaluator reuses the existing predictor and binary metric
implementation, includes single-empty penalties and excludes undefined
both-empty pairs. It records processed cases/slices, per-case/per-organ CSVs,
checkpoint/source hashes, Dice, HD95 and NSD. Validation is in resized 224
space; test predictions are restored to the stored volume grid. Both use
spacing `(1,1,1)` and NSD tolerance 1 **protocol unit**, not verified CT mm.
Do not mix the two spaces. Metrics are macro averages of organ means over valid
cases. This script is not an exact historical logging/serialization replay.

## What was and was not verified for this release

- Verified: all six source/config mappings, Python syntax, package dispatch
  tests, source hashes, and files present in a clean local clone.
- Not performed here: CUDA forward/backward, data-dependent inference,
  retraining, benchmark measurement, or full numerical result reproduction.
- Original `f720144...` BiUMamba formal-training Git object remains missing.
  Existing independently reported grouped validation agreement does not prove
  byte-identical recovery of the original training source.

No existing frozen results, checkpoints or scientific metrics are changed by
this source-completeness release. See the source audit for archive provenance.
