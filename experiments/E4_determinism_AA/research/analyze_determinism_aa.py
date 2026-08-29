"""Generate the final comparison artifacts for the E4 A/A audit.

Research Author and Repository Maintainer: xuwen
Affiliation: Japan Advanced Institute of Science and Technology (JAIST)
"""

import argparse
import csv
import json
from pathlib import Path


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    args = parser.parse_args()
    root = Path(args.root)
    run1 = read_csv(root / "run_1/audit/epoch_audit.csv")
    run2 = read_csv(root / "run_2/audit/epoch_audit.csv")
    cp1 = {row["epoch"]: row for row in read_csv(root / "run_1/audit/checkpoint_hashes.csv")}
    cp2 = {row["epoch"]: row for row in read_csv(root / "run_2/audit/checkpoint_hashes.csv")}
    initial1 = (root / "run_1/audit/initial_model_sha256.txt").read_text().strip()
    initial2 = (root / "run_2/audit/initial_model_sha256.txt").read_text().strip()

    rows = []
    for left, right in zip(run1, run2):
        epoch = left["epoch"]
        loss1 = float(left["loss"])
        loss2 = float(right["loss"])
        rows.append({
            "epoch": epoch,
            "run1_loss": f"{loss1:.12f}",
            "run2_loss": f"{loss2:.12f}",
            "signed_loss_difference_run2_minus_run1": f"{loss2-loss1:.12f}",
            "absolute_loss_difference": f"{abs(loss2-loss1):.12f}",
            "batch_order_hash_match": str(left["batch_order_sha256"] == right["batch_order_sha256"]),
            "logical_model_hash_match": str(left["logical_model_sha256"] == right["logical_model_sha256"]),
            "checkpoint_file_hash_match": str(cp1[epoch]["checkpoint_sha256"] == cp2[epoch]["checkpoint_sha256"]),
            "run1_gate_delta_std": left["gate_delta_std"],
            "run2_gate_delta_std": right["gate_delta_std"],
            "run1_gate_delta_min": left["gate_delta_min"],
            "run1_gate_delta_max": left["gate_delta_max"],
            "run2_gate_delta_min": right["gate_delta_min"],
            "run2_gate_delta_max": right["gate_delta_max"],
            "run1_total_grad_norm_max": left["total_grad_norm_max"],
            "run2_total_grad_norm_max": right["total_grad_norm_max"],
            "run1_gate_grad_norm_max": left["gate_grad_norm_max"],
            "run2_gate_grad_norm_max": right["gate_grad_norm_max"],
            "run1_model_sha256": left["logical_model_sha256"],
            "run2_model_sha256": right["logical_model_sha256"],
        })

    comparison_path = root / "E4_DETERMINISM_AA_COMPARISON.csv"
    with comparison_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    max_row = max(rows, key=lambda row: float(row["absolute_loss_difference"]))
    all_batch_match = all(row["batch_order_hash_match"] == "True" for row in rows)
    any_model_match = any(row["logical_model_hash_match"] == "True" for row in rows)
    any_checkpoint_match = any(row["checkpoint_file_hash_match"] == "True" for row in rows)
    manifest = {
        "author": "xuwen",
        "experiment": "E4 deterministic A/A diagnostic",
        "epochs_per_run": len(rows),
        "run1_exit_code": (root / "run_1/exit_code.txt").read_text().strip(),
        "run2_exit_code": (root / "run_2/exit_code.txt").read_text().strip(),
        "initial_model_hash_match": initial1 == initial2,
        "initial_model_sha256": initial1,
        "all_epoch_batch_order_hashes_match": all_batch_match,
        "matching_epoch_model_hash_count": sum(row["logical_model_hash_match"] == "True" for row in rows),
        "matching_checkpoint_file_hash_count": sum(row["checkpoint_file_hash_match"] == "True" for row in rows),
        "maximum_absolute_loss_difference": float(max_row["absolute_loss_difference"]),
        "maximum_difference_epoch": int(max_row["epoch"]),
        "strict_mode_initial_failure": "PyTorch 1.13 CUDA nll_loss2d has no deterministic implementation",
        "diagnostic_substitution": "default CE replaced by mathematically equivalent log_softmax+gather+mean",
        "decision": "RED: same-seed A/A runs still diverge; main experiments require multiple seeds. Gate saturation also warrants a separately named stabilization ablation.",
    }
    (root / "E4_DETERMINISM_AA_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    table_lines = [
        "| Epoch | Run 1 loss | Run 2 loss | Absolute difference | Batch hash | Model hash |",
        "|---:|---:|---:|---:|:---:|:---:|",
    ]
    for row in rows:
        table_lines.append(
            f"| {row['epoch']} | {row['run1_loss']} | {row['run2_loss']} | "
            f"{row['absolute_loss_difference']} | "
            f"{'Match' if row['batch_order_hash_match']=='True' else 'Different'} | "
            f"{'Match' if row['logical_model_hash_match']=='True' else 'Different'} |"
        )

    report = f"""# E4 Deterministic A/A Audit Report

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

## Outcome

The two 12-epoch runs started from the same model hash and used identical batch
orders at every epoch, but their model and checkpoint hashes differed from the
first epoch. The maximum loss difference was
`{manifest['maximum_absolute_loss_difference']:.12f}` at Epoch
{manifest['maximum_difference_epoch']}.

This is a **Red decision** for bitwise reproducibility: strict PyTorch
determinism plus `CUBLAS_WORKSPACE_CONFIG=:4096:8` is not sufficient for the
current custom Mamba CUDA stack. The A/A runs also show rapid adaptive-gate
saturation (`tanh` reaches -1 and +1 during Epoch 1), which can amplify small
numeric differences into materially different optimization trajectories.

## Controls

- Frozen E4 Git commit: `24fa3744e56d96e5bc46b3e2abf084b58545e139`
- Original E4 architecture and gate code were not modified.
- `PYTHONHASHSEED=42`
- `CUBLAS_WORKSPACE_CONFIG=:4096:8`
- `torch.use_deterministic_algorithms(True)`
- Same seed, batch size, input size, optimizer, scheduler, data, and GPU
- Final segmentation evaluation was skipped because this was a training-path audit.
- PyTorch 1.13 rejected CUDA `nll_loss2d` in strict mode. The diagnostic only
  replaced this CE primitive with the mathematically equivalent
  `log_softmax + gather + mean`; therefore these losses are diagnostic and are
  not formal E4 performance results.

## A/A comparison

{chr(10).join(table_lines)}

## Decision

1. Do not treat the failed E4 full300 run as proof that adaptive fusion is theoretically invalid.
2. Do not rerun the unchanged E4 once and select the most favorable result.
3. Main E4 comparisons require at least three seeds and mean ± standard deviation.
4. Create a separately named E4 stabilization ablation before another full300 run:
   lower gate learning rate, gate warm-up/freeze, alpha ramp, gradient clipping,
   and a light regularizer toward equal fusion.
5. Checkpoint selection must be based on a predeclared validation metric rather
   than minimum training loss before paper-level experiments.
"""
    (root / "E4_DETERMINISM_AA_REPORT.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
