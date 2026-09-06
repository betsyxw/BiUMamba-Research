#!/usr/bin/env python3
"""Aggregate unified inference runs and existing training histories for Step 19."""

from __future__ import annotations

import csv
import hashlib
import json
import statistics
import time
from collections import defaultdict
from pathlib import Path


SOURCE_ROOT = Path("/workspace/paper_final_results_v1")
FINAL_ROOT = Path("/workspace/paper_final_results_v2")
OUTPUT_ROOT = FINAL_ROOT / "efficiency/unified_benchmark_20260906"
STABLE_START_EPOCH = 21


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"No rows for {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mean_std(values: list[float]) -> tuple[float, str]:
    mean = statistics.mean(values)
    std = statistics.stdev(values) if len(values) > 1 else ""
    return mean, std


def aggregate_inference() -> None:
    rows = []
    for path in sorted((OUTPUT_ROOT / "runs").glob("*/summary.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        bench = data["benchmark"]
        theory = data["theoretical_efficiency"]
        deploy = data["deployable_state_dict"]
        rows.append({
            "dataset": data["dataset"],
            "method": data["method"],
            "seed": data["seed"],
            "hardware": data["hardware"]["gpu"],
            "input_shape": "x".join(str(v) for v in data["input_shape"]),
            "amp_enabled": bench["amp_enabled"],
            "warmup_iterations": bench["warmup_iterations"],
            "timed_iterations": bench["timed_iterations"],
            "mean_latency_ms": bench["mean_latency_ms"],
            "sample_std_latency_ms": bench["sample_std_latency_ms"],
            "median_latency_ms": bench["median_latency_ms"],
            "p95_latency_ms": bench["p95_latency_ms"],
            "throughput_images_per_second": bench["throughput_images_per_second"],
            "peak_inference_allocated_mib": bench["peak_inference_allocated_mib"],
            "peak_inference_reserved_mib": bench["peak_inference_reserved_mib"],
            "parameter_count": theory["parameter_count"],
            "estimated_whole_model_macs_g": theory["estimated_whole_model_macs"] / 1e9,
            "estimated_whole_model_flops_g": theory["estimated_whole_model_flops"] / 1e9,
            "analytical_ss2d_scan_core_macs_g": theory["analytical_ss2d_scan_core_macs"] / 1e9,
            "analytical_ss2d_scan_core_flops_g": 2.0 * theory["analytical_ss2d_scan_core_macs"] / 1e9,
            "flops_status": theory["status"],
            "deployable_state_dict_mib": deploy["serialized_mib"],
            "checkpoint_mib": data["checkpoint_size_bytes"] / 1024**2,
            "postprocessing_included": theory["postprocessing_included"],
            "summary_sha256": file_sha256(path),
        })
    if len(rows) != 6:
        raise RuntimeError(f"Expected six unified inference summaries, found {len(rows)}")
    write_csv(OUTPUT_ROOT / "step19_unified_inference_and_theory.csv", rows)

    by_dataset = defaultdict(dict)
    for row in rows:
        by_dataset[row["dataset"]][row["method"]] = row
    delta_rows = []
    for dataset in sorted(by_dataset):
        e1, e2 = by_dataset[dataset]["E1"], by_dataset[dataset]["E2_modify_2"]
        def change(column: str) -> float:
            return 100.0 * (float(e2[column]) - float(e1[column])) / float(e1[column])
        delta_rows.append({
            "dataset": dataset,
            "mean_latency_change_pct": change("mean_latency_ms"),
            "median_latency_change_pct": change("median_latency_ms"),
            "p95_latency_change_pct": change("p95_latency_ms"),
            "throughput_change_pct": change("throughput_images_per_second"),
            "peak_inference_allocated_change_pct": change("peak_inference_allocated_mib"),
            "peak_inference_reserved_change_pct": change("peak_inference_reserved_mib"),
            "estimated_whole_model_flops_change_pct": change("estimated_whole_model_flops_g"),
            "ss2d_scan_core_flops_change_pct": change("analytical_ss2d_scan_core_flops_g"),
            "deployable_state_dict_change_pct": change("deployable_state_dict_mib"),
        })
    write_csv(OUTPUT_ROOT / "step19_unified_e2_vs_e1_changes.csv", delta_rows)


def run_specs() -> list[tuple[str, str, int, Path]]:
    specs = []
    for dataset, base in (("ACDC", SOURCE_ROOT / "acdc/training_runs"), ("BUSI", SOURCE_ROOT / "busi/training_runs")):
        for method, prefix in (("E1", "e1"), ("E2_modify_2", "e2_modify_2")):
            for seed in (42, 3407, 2026):
                specs.append((dataset, method, seed, base / f"{prefix}_seed{seed}"))
    synapse = SOURCE_ROOT / "synapse/training_runs"
    specs.append(("Synapse", "E1", 42, synapse / "E1_seed42"))
    for seed in (42, 3407, 2026):
        specs.append(("Synapse", "E2_modify_2", seed, synapse / f"E2_modify_2_seed{seed}"))
    return specs


def aggregate_training() -> None:
    per_run = []
    for dataset, method, seed, run_dir in run_specs():
        summary = json.loads((run_dir / "training_summary.json").read_text(encoding="utf-8"))
        history = json.loads((run_dir / "validation_history.json").read_text(encoding="utf-8"))
        stable = [row for row in history if int(row["epoch"]) >= STABLE_START_EPOCH]
        if len(history) != 300 or len(stable) != 300 - STABLE_START_EPOCH + 1:
            raise RuntimeError(f"Unexpected history length for {run_dir}")

        def avg(rows, key):
            return statistics.mean(float(row[key]) for row in rows)

        full_overhead = [float(row["epoch_total_seconds"]) - float(row["training_seconds"]) - float(row["validation_seconds"]) for row in history]
        stable_overhead = [float(row["epoch_total_seconds"]) - float(row["training_seconds"]) - float(row["validation_seconds"]) for row in stable]
        per_run.append({
            "dataset": dataset,
            "method": method,
            "seed": seed,
            "hardware_scope": "RTX 4090" if not (dataset == "Synapse" and method == "E1" and seed != 42) else "not included",
            "epochs": len(history),
            "stable_epoch_definition": f"epochs {STABLE_START_EPOCH}-300 inclusive",
            "mean_epoch_total_s_full": avg(history, "epoch_total_seconds"),
            "mean_epoch_total_s_stable": avg(stable, "epoch_total_seconds"),
            "std_epoch_total_s_stable": statistics.stdev(float(row["epoch_total_seconds"]) for row in stable),
            "mean_training_s_full": avg(history, "training_seconds"),
            "mean_training_s_stable": avg(stable, "training_seconds"),
            "mean_validation_s_full": avg(history, "validation_seconds"),
            "mean_validation_s_stable": avg(stable, "validation_seconds"),
            "mean_other_overhead_s_full": statistics.mean(full_overhead),
            "mean_other_overhead_s_stable": statistics.mean(stable_overhead),
            "wall_clock_training_and_validation_h": float(summary["total_training_and_validation_seconds"]) / 3600.0,
            "peak_training_allocated_gib": float(summary["peak_gpu_allocated_bytes"]) / 1024**3,
            "peak_training_reserved_gib": float(summary["peak_gpu_reserved_bytes"]) / 1024**3,
            "timing_scope_note": "epoch_total includes training, validation, checkpoint decision/save, logging, and loop overhead",
        })
    write_csv(OUTPUT_ROOT / "step19_training_efficiency_per_run.csv", per_run)

    grouped = defaultdict(list)
    for row in per_run:
        grouped[(row["dataset"], row["method"])].append(row)
    aggregate_rows = []
    metrics = [
        "mean_epoch_total_s_full",
        "mean_epoch_total_s_stable",
        "mean_training_s_stable",
        "mean_validation_s_stable",
        "mean_other_overhead_s_stable",
        "wall_clock_training_and_validation_h",
        "peak_training_allocated_gib",
        "peak_training_reserved_gib",
    ]
    for (dataset, method), rows in sorted(grouped.items()):
        result = {
            "dataset": dataset,
            "method": method,
            "n_same_rtx4090_seeds": len(rows),
            "seeds": ",".join(str(row["seed"]) for row in sorted(rows, key=lambda item: item["seed"])),
            "stable_epoch_definition": f"epochs {STABLE_START_EPOCH}-300 inclusive",
            "scope_note": (
                "Same-RTX-4090 training efficiency uses seed 42 only; segmentation accuracy remains three-seed"
                if dataset == "Synapse"
                else "Three seeds measured on RTX 4090 for both methods"
            ),
        }
        for metric in metrics:
            mean, std = mean_std([float(row[metric]) for row in rows])
            result[f"{metric}_mean"] = mean
            result[f"{metric}_sample_std"] = std
        aggregate_rows.append(result)
    write_csv(OUTPUT_ROOT / "step19_training_efficiency_aggregate.csv", aggregate_rows)


def write_manifest() -> None:
    files = sorted(path for path in OUTPUT_ROOT.rglob("*") if path.is_file() and path.name not in {"SHA256SUMS.txt", "MANIFEST.json"})
    checksums = [f"{file_sha256(path)}  {path.relative_to(OUTPUT_ROOT)}" for path in files]
    (OUTPUT_ROOT / "SHA256SUMS.txt").write_text("\n".join(checksums) + "\n", encoding="utf-8")
    manifest = {
        "protocol": "step19_unified_inference_v1",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "benchmark_pairs": 6,
        "inference_seed": 42,
        "warmup_iterations": 20,
        "timed_iterations": 200,
        "training_stable_epoch_definition": f"epochs {STABLE_START_EPOCH}-300 inclusive",
        "training_efficiency_scope": {
            "ACDC": "three RTX 4090 seeds for E1 and E2_modify_2",
            "BUSI": "three RTX 4090 seeds for E1 and E2_modify_2",
            "Synapse": "same-RTX-4090 comparison uses seed 42 only; no retraining performed",
        },
        "flops_scope": "estimated whole-model FLOPs: THOP registered layers plus analytical SS2D projection and scan core; 1 MAC = 2 FLOPs; postprocessing excluded",
        "file_count_excluding_manifest_and_checksum": len(files),
    }
    (OUTPUT_ROOT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    aggregate_inference()
    aggregate_training()
    write_manifest()
    print(f"Finalized Step 19 at {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
