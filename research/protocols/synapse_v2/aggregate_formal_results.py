#!/usr/bin/env python3
"""Aggregate six frozen Synapse v2 formal test runs.

Research Author and Repository Maintainer: xuwen
Affiliation: Japan Advanced Institute of Science and Technology (JAIST)

The input JSON is a list of six records with method, seed, platform,
training_dir, and test_dir. Only metrics, manifests, summaries, and logs are
read; checkpoints and NIfTI files are never copied into the output directory.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np


METHOD_ORDER = ["E1", "E2_modify_2"]
SEED_ORDER = [42, 2026, 3407]
ORGANS = [
    "Aorta",
    "Gallbladder",
    "Left Kidney",
    "Right Kidney",
    "Liver",
    "Pancreas",
    "Spleen",
    "Stomach",
]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mean_std(values: list[float]) -> tuple[float, float]:
    if len(values) != 3:
        raise ValueError(f"Expected exactly three seeds, received {len(values)}")
    return float(np.mean(values)), float(np.std(values, ddof=1))


def fmt_percent(value: float) -> str:
    return f"{100.0 * value:.2f}%"


def fmt_mean_std(mean: float, std: float, percent: bool = False) -> str:
    if percent:
        return f"{100.0 * mean:.2f} ± {100.0 * std:.2f}"
    return f"{mean:.2f} ± {std:.2f}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-specs", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    specs = read_json(args.run_specs)
    expected = {(method, seed) for method in METHOD_ORDER for seed in SEED_ORDER}
    observed = {(item["method"], int(item["seed"])) for item in specs}
    if observed != expected or len(specs) != 6:
        raise ValueError(f"Run matrix mismatch: expected {expected}, observed {observed}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    per_seed_rows: list[dict] = []
    per_organ_seed_rows: list[dict] = []
    input_records: list[dict] = []

    for spec in sorted(
        specs,
        key=lambda item: (METHOD_ORDER.index(item["method"]), SEED_ORDER.index(int(item["seed"]))),
    ):
        method = spec["method"]
        seed = int(spec["seed"])
        training_dir = Path(spec["training_dir"])
        test_dir = Path(spec["test_dir"])
        training = read_json(training_dir / "training_summary.json")
        test = read_json(test_dir / "metrics" / "overall_metrics.json")
        inference = read_json(test_dir / "inference_manifest.json")
        organs = read_csv(test_dir / "metrics" / "per_organ_metrics.csv")
        exit_code = (test_dir / "EXIT_CODE.txt").read_text().strip()
        if exit_code != "0" or int(training["epochs"]) != 300:
            raise ValueError(f"Incomplete run: {method} seed {seed}")
        if inference["checkpoint_selected_epoch"] != training["best_validation_epoch"]:
            raise ValueError(f"Checkpoint epoch mismatch: {method} seed {seed}")

        per_seed_rows.append(
            {
                "method": method,
                "seed": seed,
                "platform": spec["platform"],
                "best_validation_epoch": training["best_validation_epoch"],
                "best_validation_dice": training["best_validation_dice"],
                "best_validation_hd95_voxels": training["best_validation_hd95_voxels"],
                "test_mean_dice": test["mean_dice"],
                "test_mean_hd95_mm": test["mean_hd95_mm"],
                "test_mean_nsd_1mm": test["mean_nsd_1mm"],
                "training_total_seconds": training["total_training_and_validation_seconds"],
                "mean_epoch_total_seconds": training["mean_epoch_total_seconds"],
                "mean_training_seconds_per_epoch": training["mean_training_seconds_per_epoch"],
                "mean_validation_seconds_per_epoch": training["mean_validation_seconds_per_epoch"],
                "peak_training_gpu_allocated_bytes": training["peak_gpu_allocated_bytes"],
                "peak_training_gpu_reserved_bytes": training["peak_gpu_reserved_bytes"],
                "parameter_count": inference["parameter_count"],
                "thop_macs": inference.get("thop_macs"),
                "thop_flops_two_per_mac": inference.get("thop_flops_two_per_mac"),
                "inference_ms_per_slice": inference["model_forward_ms_per_slice"],
                "peak_inference_gpu_allocated_bytes": inference[
                    "peak_inference_gpu_allocated_bytes"
                ],
                "cuda_device": inference["cuda_device"],
                "checkpoint_sha256": inference["checkpoint_sha256"],
                "evaluator_sha256": inference["evaluator_sha256"],
            }
        )
        for organ in organs:
            per_organ_seed_rows.append(
                {
                    "method": method,
                    "seed": seed,
                    "organ": organ["organ"],
                    "included_cases": int(organ["included_cases"]),
                    "mean_dice": float(organ["mean_dice"]),
                    "mean_hd95_mm": float(organ["mean_hd95_mm"]),
                    "mean_nsd_1mm": float(organ["mean_nsd_1mm"]),
                }
            )
        for path in [
            training_dir / "training_summary.json",
            training_dir / "validation_history.json",
            test_dir / "metrics" / "overall_metrics.json",
            test_dir / "metrics" / "per_organ_metrics.csv",
            test_dir / "inference_manifest.json",
            test_dir / "inference_timing_per_case.csv",
        ]:
            input_records.append(
                {
                    "method": method,
                    "seed": seed,
                    "file": str(path),
                    "sha256": sha256_file(path),
                }
            )

    write_csv(args.output_dir / "per_seed_summary.csv", list(per_seed_rows[0]), per_seed_rows)
    write_csv(
        args.output_dir / "per_organ_per_seed.csv",
        list(per_organ_seed_rows[0]),
        per_organ_seed_rows,
    )
    write_csv(args.output_dir / "input_file_hashes.csv", list(input_records[0]), input_records)

    metric_fields = ["test_mean_dice", "test_mean_hd95_mm", "test_mean_nsd_1mm"]
    method_rows: list[dict] = []
    method_stats: dict[str, dict[str, tuple[float, float]]] = defaultdict(dict)
    for method in METHOD_ORDER:
        selected = [row for row in per_seed_rows if row["method"] == method]
        row: dict = {"method": method, "seed_count": len(selected)}
        for field in metric_fields:
            mean, std = mean_std([float(item[field]) for item in selected])
            method_stats[method][field] = (mean, std)
            row[f"{field}_mean"] = mean
            row[f"{field}_sample_std"] = std
        method_rows.append(row)
    write_csv(args.output_dir / "method_mean_std.csv", list(method_rows[0]), method_rows)

    organ_summary_rows: list[dict] = []
    for method in METHOD_ORDER:
        for organ in ORGANS:
            selected = [
                row
                for row in per_organ_seed_rows
                if row["method"] == method and row["organ"] == organ
            ]
            row = {"method": method, "organ": organ, "seed_count": len(selected)}
            for field in ["mean_dice", "mean_hd95_mm", "mean_nsd_1mm"]:
                mean, std = mean_std([float(item[field]) for item in selected])
                row[f"{field}_mean"] = mean
                row[f"{field}_sample_std"] = std
            organ_summary_rows.append(row)
    write_csv(
        args.output_dir / "per_organ_mean_std.csv",
        list(organ_summary_rows[0]),
        organ_summary_rows,
    )

    paired_rows: list[dict] = []
    for seed in SEED_ORDER:
        e1 = next(row for row in per_seed_rows if row["method"] == "E1" and row["seed"] == seed)
        e2 = next(
            row
            for row in per_seed_rows
            if row["method"] == "E2_modify_2" and row["seed"] == seed
        )
        paired_rows.append(
            {
                "seed": seed,
                "delta_dice_e2_minus_e1": float(e2["test_mean_dice"])
                - float(e1["test_mean_dice"]),
                "delta_hd95_mm_e2_minus_e1": float(e2["test_mean_hd95_mm"])
                - float(e1["test_mean_hd95_mm"]),
                "delta_nsd_e2_minus_e1": float(e2["test_mean_nsd_1mm"])
                - float(e1["test_mean_nsd_1mm"]),
            }
        )
    write_csv(args.output_dir / "paired_seed_deltas.csv", list(paired_rows[0]), paired_rows)

    e1_dice = method_stats["E1"]["test_mean_dice"][0]
    e2_dice = method_stats["E2_modify_2"]["test_mean_dice"][0]
    e1_hd95 = method_stats["E1"]["test_mean_hd95_mm"][0]
    e2_hd95 = method_stats["E2_modify_2"]["test_mean_hd95_mm"][0]
    e1_nsd = method_stats["E1"]["test_mean_nsd_1mm"][0]
    e2_nsd = method_stats["E2_modify_2"]["test_mean_nsd_1mm"][0]
    delta_dice = e2_dice - e1_dice
    delta_hd95 = e2_hd95 - e1_hd95
    delta_nsd = e2_nsd - e1_nsd
    if delta_dice >= 0 and delta_hd95 <= 0 and delta_nsd >= 0:
        decision = "Green"
        explanation = "E2_modify_2 improves or preserves all three primary accuracy metrics."
    elif delta_dice <= -0.01 and delta_hd95 > 0 and delta_nsd < 0:
        decision = "Red"
        explanation = "E2_modify_2 loses at least 1 Dice point and both boundary metrics worsen."
    else:
        decision = "Yellow"
        explanation = "The metrics are mixed or close; report the efficiency/accuracy trade-off without claiming universal superiority."

    lines = [
        "# Synapse v2 Formal Three-Seed Comparison",
        "",
        "**Research Author and Repository Maintainer:** xuwen  ",
        "**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)",
        "",
        "All values use the frozen 14/4/12 Synapse v2 protocol. Checkpoints were selected only by validation Dice (HD95 tie-breaker), and the isolated 12-case test set was evaluated once after training.",
        "",
        "## Overall test results",
        "",
        "| Method | Dice (%) | HD95 (mm) | NSD@1 mm (%) |",
        "|---|---:|---:|---:|",
    ]
    for method in METHOD_ORDER:
        dice = method_stats[method]["test_mean_dice"]
        hd95 = method_stats[method]["test_mean_hd95_mm"]
        nsd = method_stats[method]["test_mean_nsd_1mm"]
        lines.append(
            f"| {method} | {fmt_mean_std(*dice, percent=True)} | {fmt_mean_std(*hd95)} | {fmt_mean_std(*nsd, percent=True)} |"
        )
    lines.extend(
        [
            "",
            "## Paired mean differences (E2_modify_2 − E1)",
            "",
            f"- Dice: {100.0 * delta_dice:+.2f} percentage points",
            f"- HD95: {delta_hd95:+.2f} mm (lower is better)",
            f"- NSD@1 mm: {100.0 * delta_nsd:+.2f} percentage points",
            "",
            f"## Decision: **{decision}**",
            "",
            explanation,
            "",
            "The reported standard deviation is the sample standard deviation across the preregistered seeds 42, 2026, and 3407. With only three seeds, the report does not claim statistical significance from a normality-based test.",
            "",
            "## Audit notes",
            "",
            "- Test metrics: Dice, physical HD95 in mm, and NSD at 1 mm.",
            "- Eight organs are aggregated by organ and then macro-averaged.",
            "- HAKUSAN A100 and RunPod RTX 4090 were both used for fixed-checkpoint inference. Accuracy aggregation is valid, but cross-platform timing is not used as the primary efficiency comparison.",
            "- Fair efficiency claims must use E1 and E2_modify_2 measured on the same RTX 4090 hardware.",
        ]
    )
    (args.output_dir / "FORMAL_COMPARISON_REPORT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    manifest = {
        "research_author": "xuwen",
        "affiliation": "Japan Advanced Institute of Science and Technology (JAIST)",
        "protocol": "synapse_v2",
        "methods": METHOD_ORDER,
        "seeds": SEED_ORDER,
        "sample_std_ddof": 1,
        "decision": decision,
        "delta_e2_modify_2_minus_e1": {
            "dice": delta_dice,
            "hd95_mm": delta_hd95,
            "nsd_1mm": delta_nsd,
        },
        "excluded_from_github": [
            "datasets",
            "patient images",
            "NIfTI predictions and ground truth",
            "checkpoints",
            "pretrained weights",
            "keys and credentials",
        ],
    }
    (args.output_dir / "aggregate_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
