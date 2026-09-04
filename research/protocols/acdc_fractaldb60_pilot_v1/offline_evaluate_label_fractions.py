#!/usr/bin/env python3
"""Evaluate the nine validation-selected FractalDB pilot/extension checkpoints.

The isolated ACDC test split is loaded only by this post-training program. All
models use the same test volumes, preprocessing, physical-distance metrics and
NSD tolerance.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import torch

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from research.protocols.acdc_v1.offline_evaluate_and_visualize import (
        build_model,
        evaluate_predictions,
        infer_model,
        load_test_volumes,
        sha256,
        write_csv,
    )
except ModuleNotFoundError:
    # The training checkout stores the frozen evaluator directly under research/.
    from research.acdc_offline_evaluate_and_visualize import (
        build_model,
        evaluate_predictions,
        infer_model,
        load_test_volumes,
        sha256,
        write_csv,
    )


CONDITIONS = ("scratch", "imagenet", "fractaldb60")
FRACTIONS = (25, 50, 100)


def run_directory(fraction: int, condition: str, pilot_root: Path, extension_root: Path) -> Path:
    if fraction == 25:
        return pilot_root / f"downstream_full300_{condition}"
    return extension_root / f"downstream_{fraction}pct_full300_{condition}"


def write_report(path: Path, rows: list[dict], decisions: dict[str, str], language: str) -> None:
    if language == "zh":
        title = "# ACDC FractalDB-60 标签比例隔离测试报告"
        intro = (
            "所有checkpoint仅由验证集Dice选择（HD95用于平分时决胜）。"
            "随后在同一组20名隔离测试患者（40个ED/ES体积）上评估一次。"
        )
        header = "| 标签比例 | 初始化 | Dice (%) ↑ | HD95 (mm) ↓ | NSD@1 mm (%) ↑ | 最佳epoch |"
        conclusion = "## 各标签比例结论"
    else:
        title = "# ACDC FractalDB-60 label-fraction isolated-test report"
        intro = (
            "Every checkpoint was selected only by validation Dice (HD95 tie-breaker), then "
            "evaluated once on the same 20 isolated-test patients (40 ED/ES volumes)."
        )
        header = "| Labels | Initialization | Dice (%) ↑ | HD95 (mm) ↓ | NSD@1 mm (%) ↑ | Best epoch |"
        conclusion = "## Decision by label fraction"
    lines = [title, "", intro, "", header, "|---:|---|---:|---:|---:|---:|"]
    for row in rows:
        lines.append(
            f"| {row['label_fraction_percent']}% | {row['condition']} | "
            f"{100 * row['test_mean_dice']:.2f} | {row['test_mean_hd95_mm']:.3f} | "
            f"{100 * row['test_mean_nsd_at_1mm']:.2f} | {row['best_validation_epoch']} |"
        )
    lines.extend(["", conclusion, ""])
    for fraction in FRACTIONS:
        lines.append(f"- {fraction}%: **{decisions[str(fraction)]}**")
    lines.extend(
        [
            "",
            "Green: FractalDB-60 Dice > Scratch and ≥ ImageNet.  ",
            "Yellow: FractalDB-60 Dice > Scratch but < ImageNet.  ",
            "Red: FractalDB-60 Dice ≤ Scratch.",
            "",
            "These are seed-42 results and are not a multi-seed statistical claim.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--protocol-dir", type=Path, required=True)
    parser.add_argument("--pilot-root", type=Path, required=True)
    parser.add_argument("--extension-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--nsd-tolerance-mm", type=float, default=1.0)
    args = parser.parse_args()

    if args.output_dir.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {args.output_dir}")
    args.output_dir.mkdir(parents=True)

    test_list = args.protocol_dir / "splits" / "test_patients.txt"
    volumes = load_test_volumes(args.data_root, test_list)
    overall_rows: list[dict] = []
    organ_rows: list[dict] = []
    manifest_runs: dict[str, dict] = {}

    for fraction in FRACTIONS:
        for condition in CONDITIONS:
            run_dir = run_directory(fraction, condition, args.pilot_root, args.extension_root)
            checkpoint_path = run_dir / "checkpoints" / "best_validation.pth"
            summary_path = run_dir / "training_summary.json"
            if not checkpoint_path.is_file() or not summary_path.is_file():
                raise FileNotFoundError(f"Incomplete run: {run_dir}")
            summary = json.loads(summary_path.read_text())
            if int(summary["epochs"]) != 300 or int(summary["seed"]) != 42:
                raise RuntimeError(f"Unexpected training summary: {summary_path}")

            model, checkpoint = build_model("grouped_2d_bidirectional_sum", checkpoint_path)
            predictions, inference = infer_model(model, volumes, args.batch_size)
            records, per_organ, overall = evaluate_predictions(
                predictions, volumes, args.nsd_tolerance_mm
            )
            del model, predictions
            torch.cuda.empty_cache()

            key = f"{fraction}pct_{condition}"
            row = {
                "label_fraction_percent": fraction,
                "condition": condition,
                "seed": 42,
                "best_validation_epoch": int(checkpoint["epoch"]),
                "best_validation_dice": float(checkpoint["validation_dice"]),
                "best_validation_hd95_mm": float(checkpoint["validation_hd95_mm"]),
                "test_mean_dice": overall["mean_dice"],
                "test_mean_hd95_mm": overall["mean_hd95_mm"],
                "test_mean_nsd_at_1mm": overall["mean_nsd"],
                "total_training_hours": summary["total_training_and_validation_seconds"] / 3600.0,
                "mean_epoch_seconds": summary["mean_epoch_total_seconds"],
                "peak_gpu_allocated_gib": summary["peak_gpu_allocated_bytes"] / 1024.0**3,
                "parameter_count": summary["parameter_count"],
                "inference_ms_per_slice": inference["milliseconds_per_slice"],
            }
            overall_rows.append(row)
            for organ, values in per_organ.items():
                organ_rows.append(
                    {
                        "label_fraction_percent": fraction,
                        "condition": condition,
                        "organ": organ,
                        **values,
                    }
                )
            write_csv(
                args.output_dir / f"{key}_per_volume_per_organ.csv",
                records,
                ["volume_id", "patient", "phase", "organ_label", "organ", "dice", "hd95_mm", "nsd"],
            )
            manifest_runs[key] = {
                "run_dir": str(run_dir),
                "checkpoint": str(checkpoint_path),
                "checkpoint_sha256": sha256(checkpoint_path),
                "training_summary_sha256": sha256(summary_path),
                "strict_checkpoint_load": True,
                "overall": overall,
                "per_organ": per_organ,
                "inference": inference,
            }

    write_csv(args.output_dir / "ACDC_FRACTALDB_LABEL_FRACTIONS_OVERALL.csv", overall_rows, list(overall_rows[0]))
    write_csv(
        args.output_dir / "ACDC_FRACTALDB_LABEL_FRACTIONS_PER_ORGAN.csv",
        organ_rows,
        ["label_fraction_percent", "condition", "organ", "dice", "hd95_mm", "nsd", "volume_count"],
    )

    by_fraction = {
        fraction: {row["condition"]: row for row in overall_rows if row["label_fraction_percent"] == fraction}
        for fraction in FRACTIONS
    }
    decisions = {}
    for fraction, values in by_fraction.items():
        fractal = values["fractaldb60"]["test_mean_dice"]
        scratch = values["scratch"]["test_mean_dice"]
        imagenet = values["imagenet"]["test_mean_dice"]
        decisions[str(fraction)] = "Green" if fractal > scratch and fractal >= imagenet else (
            "Yellow" if fractal > scratch else "Red"
        )

    trends = {}
    for condition in CONDITIONS:
        condition_rows = {row["label_fraction_percent"]: row for row in overall_rows if row["condition"] == condition}
        trends[condition] = {
            f"{start}_to_{end}": {
                "dice_percentage_points": 100 * (condition_rows[end]["test_mean_dice"] - condition_rows[start]["test_mean_dice"]),
                "hd95_mm": condition_rows[end]["test_mean_hd95_mm"] - condition_rows[start]["test_mean_hd95_mm"],
                "nsd_percentage_points": 100 * (condition_rows[end]["test_mean_nsd_at_1mm"] - condition_rows[start]["test_mean_nsd_at_1mm"]),
            }
            for start, end in ((25, 50), (50, 100), (25, 100))
        }

    manifest = {
        "protocol": "acdc_fractaldb60_label_fraction_seed42",
        "checkpoint_selection": "Maximum validation Dice; minimum validation HD95 tie-breaker; test never used.",
        "test_list": str(test_list),
        "test_list_sha256": sha256(test_list),
        "test_patient_count": 20,
        "test_volume_count": len(volumes),
        "nsd_tolerance_mm": args.nsd_tolerance_mm,
        "decisions": decisions,
        "trends": trends,
        "runs": manifest_runs,
    }
    (args.output_dir / "ACDC_FRACTALDB_LABEL_FRACTIONS_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_report(args.output_dir / "REPORT_EN.md", overall_rows, decisions, "en")
    write_report(args.output_dir / "REPORT_ZH.md", overall_rows, decisions, "zh")
    print(json.dumps({"decisions": decisions, "overall": overall_rows, "trends": trends}, indent=2))


if __name__ == "__main__":
    main()
