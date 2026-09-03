#!/usr/bin/env python3
"""Aggregate the six frozen BUSI evaluations into paper-ready tables and reports."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from pathlib import Path


ROOT = Path("outputs/busi_v1_clean/formal_three_seed")
RUNS = ROOT / "runs"
TABLES = ROOT / "tables"
REPORTS = ROOT / "reports"
SEEDS = [42, 3407, 2026]
METHODS = ["E1", "E2_modify_2"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mean_std(values: list[float]) -> tuple[float, float]:
    return statistics.mean(values), statistics.stdev(values)


def pct_delta(new: float, old: float) -> float:
    return 100.0 * (new - old) / old


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_runs() -> dict[tuple[str, int], dict]:
    results = {}
    for method in METHODS:
        for seed in SEEDS:
            path = RUNS / f"{method}_seed{seed}" / "evaluation_summary.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            if data["method"] != method or int(data["seed"]) != seed:
                raise RuntimeError(f"Method/seed mismatch in {path}")
            if int(data["test_group_count"]) != 105:
                raise RuntimeError(f"Unexpected test count in {path}")
            results[(method, seed)] = data
    hashes = {data["test_list_sha256"] for data in results.values()}
    manifest_hashes = {data["clean_manifest_sha256"] for data in results.values()}
    evaluator_hashes = {data["evaluator_sha256"] for data in results.values()}
    if len(hashes) != 1 or len(manifest_hashes) != 1 or len(evaluator_hashes) != 1:
        raise RuntimeError("The six runs do not share one frozen test protocol")
    return results


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    runs = load_runs()
    complexity = {
        method: json.loads((ROOT / f"{method}_complexity.json").read_text(encoding="utf-8"))
        for method in METHODS
    }

    per_seed = []
    per_class = []
    efficiency = []
    for method in METHODS:
        for seed in SEEDS:
            data = runs[(method, seed)]
            metrics = data["metrics"]
            training = data["training_summary"]
            timing = data["timing"]
            per_seed.append({
                "method": method,
                "seed": seed,
                "dice": metrics["lesion_positive_mean_dice"],
                "hd95_px": metrics["lesion_positive_mean_hd95_px"],
                "nsd_at_2px": metrics["lesion_positive_mean_nsd_at_2px"],
                "lesion_positive_count": metrics["lesion_positive_count"],
                "normal_empty_mask_accuracy": metrics["normal_empty_mask_accuracy"],
                "normal_false_positive_area_fraction": metrics["normal_mean_false_positive_area_fraction"],
                "normal_count": metrics["normal_count"],
                "selected_epoch": data["checkpoint_selected_epoch"],
            })
            for class_name, values in metrics["per_class"].items():
                per_class.append({
                    "method": method,
                    "seed": seed,
                    "class": class_name,
                    "dice": values["mean_dice"],
                    "hd95_px": values["mean_hd95_px"],
                    "nsd_at_2px": values["mean_nsd_at_2px"],
                    "count": values["count"],
                })
            efficiency.append({
                "method": method,
                "seed": seed,
                "total_training_and_validation_seconds": training["total_training_and_validation_seconds"],
                "mean_epoch_seconds": training["mean_epoch_total_seconds"],
                "peak_training_gpu_allocated_gib": training["peak_gpu_allocated_bytes"] / 1024**3,
                "peak_training_gpu_reserved_gib": training["peak_gpu_reserved_bytes"] / 1024**3,
                "parameter_count": data["parameter_count"],
                "inference_mean_ms_batch1": timing["model_forward_mean_ms_batch1"],
                "inference_median_ms_batch1": timing["model_forward_median_ms_batch1"],
                "approx_flops_g": complexity[method]["augmented_total_flops_two_per_mac"] / 1e9,
                "selective_scan_core_macs_g": complexity[method]["analytical_selective_scan_core_macs"] / 1e9,
            })

    write_csv(TABLES / "per_seed_metrics.csv", per_seed)
    write_csv(TABLES / "per_class_per_seed.csv", per_class)
    write_csv(TABLES / "efficiency_per_seed.csv", efficiency)

    metric_fields = [
        "dice", "hd95_px", "nsd_at_2px", "normal_empty_mask_accuracy",
        "normal_false_positive_area_fraction",
    ]
    method_summary = []
    for method in METHODS:
        method_rows = [row for row in per_seed if row["method"] == method]
        row = {"method": method, "seed_count": 3, "test_groups_per_seed": 105}
        for field in metric_fields:
            mean, std = mean_std([float(item[field]) for item in method_rows])
            row[f"{field}_mean"] = mean
            row[f"{field}_std"] = std
        eff_rows = [row for row in efficiency if row["method"] == method]
        for field in [
            "total_training_and_validation_seconds", "mean_epoch_seconds",
            "peak_training_gpu_allocated_gib", "peak_training_gpu_reserved_gib",
            "inference_mean_ms_batch1", "inference_median_ms_batch1",
        ]:
            mean, std = mean_std([float(item[field]) for item in eff_rows])
            row[f"{field}_mean"] = mean
            row[f"{field}_std"] = std
        row["parameter_count"] = eff_rows[0]["parameter_count"]
        row["approx_flops_g"] = eff_rows[0]["approx_flops_g"]
        row["selective_scan_core_macs_g"] = eff_rows[0]["selective_scan_core_macs_g"]
        method_summary.append(row)
    write_csv(TABLES / "method_mean_std.csv", method_summary)

    paired = []
    for seed in SEEDS:
        e1 = next(row for row in per_seed if row["method"] == "E1" and row["seed"] == seed)
        e2 = next(row for row in per_seed if row["method"] == "E2_modify_2" and row["seed"] == seed)
        paired.append({
            "seed": seed,
            "dice_delta_e2_minus_e1": e2["dice"] - e1["dice"],
            "hd95_delta_e2_minus_e1_px": e2["hd95_px"] - e1["hd95_px"],
            "nsd_delta_e2_minus_e1": e2["nsd_at_2px"] - e1["nsd_at_2px"],
        })
    write_csv(TABLES / "paired_seed_deltas.csv", paired)

    summary_by_method = {row["method"]: row for row in method_summary}
    e1s, e2s = summary_by_method["E1"], summary_by_method["E2_modify_2"]
    efficiency_delta = [{
        "comparison": "E2_modify_2 vs E1",
        "dice_delta_points": 100.0 * (e2s["dice_mean"] - e1s["dice_mean"]),
        "hd95_delta_px": e2s["hd95_px_mean"] - e1s["hd95_px_mean"],
        "nsd_delta_points": 100.0 * (e2s["nsd_at_2px_mean"] - e1s["nsd_at_2px_mean"]),
        "training_time_delta_percent": pct_delta(e2s["total_training_and_validation_seconds_mean"], e1s["total_training_and_validation_seconds_mean"]),
        "mean_epoch_time_delta_percent": pct_delta(e2s["mean_epoch_seconds_mean"], e1s["mean_epoch_seconds_mean"]),
        "peak_allocated_memory_delta_percent": pct_delta(e2s["peak_training_gpu_allocated_gib_mean"], e1s["peak_training_gpu_allocated_gib_mean"]),
        "peak_reserved_memory_delta_percent": pct_delta(e2s["peak_training_gpu_reserved_gib_mean"], e1s["peak_training_gpu_reserved_gib_mean"]),
        "inference_time_delta_percent": pct_delta(e2s["inference_mean_ms_batch1_mean"], e1s["inference_mean_ms_batch1_mean"]),
        "approx_flops_delta_percent": pct_delta(e2s["approx_flops_g"], e1s["approx_flops_g"]),
        "selective_scan_core_macs_delta_percent": pct_delta(e2s["selective_scan_core_macs_g"], e1s["selective_scan_core_macs_g"]),
    }]
    write_csv(TABLES / "efficiency_and_metric_deltas.csv", efficiency_delta)

    ppt_rows = []
    for method in METHODS:
        s = summary_by_method[method]
        ppt_rows.append({
            "Model": "E1 (VM-UNet)" if method == "E1" else "E2_modify_2 (BiUMamba)",
            "Dice_mean_percent": 100 * s["dice_mean"],
            "Dice_std_percent": 100 * s["dice_std"],
            "HD95_mean_px": s["hd95_px_mean"],
            "HD95_std_px": s["hd95_px_std"],
            "NSD_mean_percent": 100 * s["nsd_at_2px_mean"],
            "NSD_std_percent": 100 * s["nsd_at_2px_std"],
            "Peak_memory_GiB": s["peak_training_gpu_allocated_gib_mean"],
            "Mean_epoch_seconds": s["mean_epoch_seconds_mean"],
            "Inference_ms_per_image": s["inference_mean_ms_batch1_mean"],
            "Approx_GFLOPs": s["approx_flops_g"],
            "Parameters_M": s["parameter_count"] / 1e6,
        })
    write_csv(TABLES / "ppt_table.csv", ppt_rows)

    # Select four non-overlapping seed-42 lesion-positive examples for qualitative panels.
    sample_maps = {}
    for method in METHODS:
        path = RUNS / f"{method}_seed42" / "per_sample_metrics.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            sample_maps[method] = {row["group_id"]: row for row in csv.DictReader(handle)}
    candidates = []
    for group_id, e1 in sample_maps["E1"].items():
        e2 = sample_maps["E2_modify_2"][group_id]
        if not e1["dice"] or not e2["dice"]:
            continue
        candidates.append({
            "group_id": group_id,
            "sample_id": e1["sample_id"],
            "class_name": e1["class_name"],
            "gt_area_fraction": float(e1["gt_area_fraction"]),
            "e1_dice": float(e1["dice"]),
            "e2_dice": float(e2["dice"]),
        })
    for row in candidates:
        row["mean_dice"] = (row["e1_dice"] + row["e2_dice"]) / 2.0
        row["abs_delta"] = abs(row["e2_dice"] - row["e1_dice"])
        row["e2_minus_e1"] = row["e2_dice"] - row["e1_dice"]

    selected = []
    typical_pool = [r for r in candidates if 0.01 <= r["gt_area_fraction"] <= 0.20]
    typical = max(typical_pool, key=lambda r: (min(r["e1_dice"], r["e2_dice"]), -r["abs_delta"]))
    selected.append(("Typical case", typical, "Both models have high Dice and similar boundaries."))
    remaining = [r for r in candidates if r["group_id"] != typical["group_id"]]
    small = min([r for r in remaining if min(r["e1_dice"], r["e2_dice"]) > 0.15], key=lambda r: r["gt_area_fraction"])
    selected.append(("Small-lesion case", small, "The ground-truth lesion has a small area."))
    remaining = [r for r in remaining if r["group_id"] != small["group_id"]]
    difficult_pool = [
        r for r in remaining
        if 0.20 < r["mean_dice"] < 0.55 and min(r["e1_dice"], r["e2_dice"]) > 0.20
    ]
    difficult = min(
        difficult_pool or remaining,
        key=lambda r: (r["abs_delta"], abs(r["mean_dice"] - 0.35)),
    )
    selected.append(("Difficult case", difficult, "Both methods find the lesion, but the boundary remains difficult."))
    remaining = [r for r in remaining if r["group_id"] != difficult["group_id"]]
    failure = min(remaining, key=lambda r: (r["e2_minus_e1"], r["e2_dice"]))
    selected.append(("E2 failure case", failure, "E1 finds the lesion, while E2_modify_2 has a clear segmentation error."))
    qualitative_rows = []
    for order, (category, row, reason) in enumerate(selected, start=1):
        qualitative_rows.append({
            "order": order,
            "category": category,
            "group_id": row["group_id"],
            "sample_id": row["sample_id"],
            "class_name": row["class_name"],
            "gt_area_fraction": row["gt_area_fraction"],
            "e1_seed42_dice": row["e1_dice"],
            "e2_modify_2_seed42_dice": row["e2_dice"],
            "selection_reason": reason,
        })
    write_csv(TABLES / "qualitative_selection.csv", qualitative_rows)

    d = efficiency_delta[0]
    en = f"""# BUSI E1 vs E2_modify_2 Formal Three-Seed Report

## Protocol

- Dataset: BUSI v1 clean, duplicate-cleaned image-group split.
- Split: 371 training groups, 53 validation groups, and 105 isolated test groups.
- Seeds: 42, 3407, and 2026.
- Models: E1 (original VM-UNet SS2D) and E2_modify_2 (channel-grouped two-axis bidirectional scan).
- Checkpoint rule: highest validation lesion-positive Dice; lower HD95 as the tie-breaker.
- Test metrics: lesion-positive Dice, HD95 in pixels, and NSD at a 2-pixel tolerance.

## Main results

| Model | Dice (%) | HD95 (px) | NSD (%) | Peak memory (GiB) | Mean epoch (s) | Inference (ms/image) | Approx. GFLOPs |
|---|---:|---:|---:|---:|---:|---:|---:|
| E1 | {100*e1s['dice_mean']:.2f} ± {100*e1s['dice_std']:.2f} | {e1s['hd95_px_mean']:.2f} ± {e1s['hd95_px_std']:.2f} | {100*e1s['nsd_at_2px_mean']:.2f} ± {100*e1s['nsd_at_2px_std']:.2f} | {e1s['peak_training_gpu_allocated_gib_mean']:.2f} | {e1s['mean_epoch_seconds_mean']:.2f} | {e1s['inference_mean_ms_batch1_mean']:.2f} | {e1s['approx_flops_g']:.2f} |
| E2_modify_2 | {100*e2s['dice_mean']:.2f} ± {100*e2s['dice_std']:.2f} | {e2s['hd95_px_mean']:.2f} ± {e2s['hd95_px_std']:.2f} | {100*e2s['nsd_at_2px_mean']:.2f} ± {100*e2s['nsd_at_2px_std']:.2f} | {e2s['peak_training_gpu_allocated_gib_mean']:.2f} | {e2s['mean_epoch_seconds_mean']:.2f} | {e2s['inference_mean_ms_batch1_mean']:.2f} | {e2s['approx_flops_g']:.2f} |

## Interpretation

E2_modify_2 reduced peak allocated training memory by {-d['peak_allocated_memory_delta_percent']:.2f}% and the estimated total FLOPs by {-d['approx_flops_delta_percent']:.2f}%. Its mean epoch time was {-d['mean_epoch_time_delta_percent']:.2f}% lower. However, mean Dice decreased by {-d['dice_delta_points']:.2f} percentage points, mean HD95 increased by {d['hd95_delta_px']:.2f} pixels, and mean NSD decreased by {-d['nsd_delta_points']:.2f} percentage points. Batch-1 inference was {d['inference_time_delta_percent']:.2f}% slower in the measured implementation.

The BUSI result is therefore a negative cross-dataset result: the grouped scan improved training efficiency but did not keep E1 segmentation accuracy on breast ultrasound. The main claim should remain limited to the datasets where formal multi-seed results support it.

## FLOPs note

The FLOPs values are approximate. They combine THOP-supported layers with analytical estimates for the unregistered projection einsums and selective-scan core. Elementwise and normalization operations are not fully counted. The selective-scan core MAC estimate is 50% lower for E2_modify_2 by design.
"""
    zh = f"""# BUSI E1 与 E2_modify_2 三种子正式对比报告

## 实验协议

- 数据集：BUSI v1 clean，采用去重后的图像组划分。
- 划分：371个训练组、53个验证组、105个隔离测试组。
- 固定种子：42、3407、2026。
- 模型：E1（原始VM-UNet SS2D）与E2_modify_2（通道分组的双轴双向扫描）。
- checkpoint选择：验证集病灶Dice最高；相同时选择HD95更低者。
- 测试指标：病灶阳性样本Dice、像素HD95，以及2像素容差下的NSD。

## 主要结果

| 模型 | Dice (%) | HD95 (px) | NSD (%) | 峰值显存 (GiB) | 平均epoch (s) | 推理 (ms/图) | 估算GFLOPs |
|---|---:|---:|---:|---:|---:|---:|---:|
| E1 | {100*e1s['dice_mean']:.2f} ± {100*e1s['dice_std']:.2f} | {e1s['hd95_px_mean']:.2f} ± {e1s['hd95_px_std']:.2f} | {100*e1s['nsd_at_2px_mean']:.2f} ± {100*e1s['nsd_at_2px_std']:.2f} | {e1s['peak_training_gpu_allocated_gib_mean']:.2f} | {e1s['mean_epoch_seconds_mean']:.2f} | {e1s['inference_mean_ms_batch1_mean']:.2f} | {e1s['approx_flops_g']:.2f} |
| E2_modify_2 | {100*e2s['dice_mean']:.2f} ± {100*e2s['dice_std']:.2f} | {e2s['hd95_px_mean']:.2f} ± {e2s['hd95_px_std']:.2f} | {100*e2s['nsd_at_2px_mean']:.2f} ± {100*e2s['nsd_at_2px_std']:.2f} | {e2s['peak_training_gpu_allocated_gib_mean']:.2f} | {e2s['mean_epoch_seconds_mean']:.2f} | {e2s['inference_mean_ms_batch1_mean']:.2f} | {e2s['approx_flops_g']:.2f} |

## 结果解释

与E1相比，E2_modify_2的训练峰值显存下降了{-d['peak_allocated_memory_delta_percent']:.2f}%，估算总FLOPs下降了{-d['approx_flops_delta_percent']:.2f}%，平均epoch时间缩短了{-d['mean_epoch_time_delta_percent']:.2f}%。但是，平均Dice下降{-d['dice_delta_points']:.2f}个百分点，平均HD95增加{d['hd95_delta_px']:.2f}像素，平均NSD下降{-d['nsd_delta_points']:.2f}个百分点；当前实现的batch-1推理时间增加了{d['inference_time_delta_percent']:.2f}%。

因此，BUSI属于负面的跨数据集结果：通道分组扫描提高了训练效率，但没有在乳腺超声上保持E1的分割精度。论文不能把BUSI写成普遍有效证据，应把主要结论限制在正式多种子结果能够支持的数据集上。

## FLOPs说明

FLOPs是近似值，由THOP可统计层、未注册投影einsum和选择性扫描核心的解析估算组成；逐元素运算和归一化没有完全计入。按照结构设计，E2_modify_2的选择性扫描核心MACs比E1低50%。
"""
    (REPORTS / "BUSI_E1_vs_E2_modify_2_FORMAL_REPORT_EN.md").write_text(en, encoding="utf-8")
    (REPORTS / "BUSI_E1_vs_E2_modify_2_FORMAL_REPORT_ZH.md").write_text(zh, encoding="utf-8")

    output_files = sorted(
        [path for path in TABLES.rglob("*") if path.is_file()]
        + [path for path in REPORTS.rglob("*") if path.is_file()]
    )
    manifest = {
        "protocol": "busi_v1_clean",
        "methods": METHODS,
        "seeds": SEEDS,
        "test_groups_per_run": 105,
        "test_list_sha256": next(iter({data["test_list_sha256"] for data in runs.values()})),
        "clean_manifest_sha256": next(iter({data["clean_manifest_sha256"] for data in runs.values()})),
        "evaluator_sha256": next(iter({data["evaluator_sha256"] for data in runs.values()})),
        "flops_status": complexity["E1"]["status"],
        "generated_files": {str(path.relative_to(ROOT)): sha256(path) for path in output_files},
    }
    (ROOT / "aggregate_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
