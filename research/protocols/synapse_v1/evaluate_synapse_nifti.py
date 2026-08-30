#!/usr/bin/env python3
"""Frozen offline evaluator for Synapse segmentation predictions.

Author: xuwen
Affiliation: Japan Advanced Institute of Science and Technology (JAIST)
Protocol: synapse_v1
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np
import SimpleITK as sitk
from scipy.ndimage import binary_erosion, distance_transform_edt

PROTOCOL = "synapse_v1"
NSD_TOLERANCE_MM = 1.0
ORGANS = {
    1: "Aorta",
    2: "Gallbladder",
    3: "Left Kidney",
    4: "Right Kidney",
    5: "Liver",
    6: "Pancreas",
    7: "Spleen",
    8: "Stomach",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def surface(mask: np.ndarray) -> np.ndarray:
    structure = np.ones((3,) * mask.ndim, dtype=bool)
    return np.logical_xor(mask, binary_erosion(mask, structure=structure, border_value=0))


def surface_distances(
    pred: np.ndarray, gt: np.ndarray, spacing_zyx: tuple[float, ...]
) -> tuple[np.ndarray, np.ndarray]:
    pred_surface = surface(pred)
    gt_surface = surface(gt)
    distance_to_gt = distance_transform_edt(~gt_surface, sampling=spacing_zyx)
    distance_to_pred = distance_transform_edt(~pred_surface, sampling=spacing_zyx)
    return distance_to_gt[pred_surface], distance_to_pred[gt_surface]


def evaluate_binary(
    pred: np.ndarray,
    gt: np.ndarray,
    spacing_zyx: tuple[float, ...],
) -> tuple[float | None, float | None, float | None, str]:
    pred_count = int(pred.sum())
    gt_count = int(gt.sum())
    if pred_count == 0 and gt_count == 0:
        return None, None, None, "both_empty"

    if pred_count == 0 or gt_count == 0:
        extent = (np.asarray(pred.shape) - 1) * np.asarray(spacing_zyx)
        diagonal_mm = float(np.linalg.norm(extent))
        status = "prediction_empty" if pred_count == 0 else "ground_truth_empty"
        return 0.0, diagonal_mm, 0.0, status

    intersection = int(np.logical_and(pred, gt).sum())
    dice = 2.0 * intersection / (pred_count + gt_count)
    pred_to_gt, gt_to_pred = surface_distances(pred, gt, spacing_zyx)
    distances = np.concatenate([pred_to_gt, gt_to_pred])
    hd95 = float(np.percentile(distances, 95))
    nsd = float(
        (
            np.count_nonzero(pred_to_gt <= NSD_TOLERANCE_MM)
            + np.count_nonzero(gt_to_pred <= NSD_TOLERANCE_MM)
        )
        / (pred_to_gt.size + gt_to_pred.size)
    )
    return float(dice), hd95, nsd, "ok"


def finite_mean(values: Iterable[float | None]) -> float:
    clean = [float(value) for value in values if value is not None and math.isfinite(value)]
    if not clean:
        raise ValueError("No finite values available for aggregation")
    return float(np.mean(clean))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prediction-dir", type=Path, required=True)
    parser.add_argument("--ground-truth-dir", type=Path, required=True)
    parser.add_argument(
        "--case-list",
        type=Path,
        default=Path(__file__).resolve().parent / "splits" / "test_cases.txt",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--pred-pattern", default="{case}_pred.nii.gz")
    parser.add_argument("--gt-pattern", default="{case}_gt.nii.gz")
    args = parser.parse_args()

    cases = [line.strip() for line in args.case_list.read_text().splitlines() if line.strip()]
    if len(cases) != 12 or len(set(cases)) != len(cases):
        raise ValueError("synapse_v1 requires exactly 12 unique test cases")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    case_rows: list[dict] = []
    input_rows: list[dict] = []
    for case in cases:
        pred_path = args.prediction_dir / args.pred_pattern.format(case=case)
        gt_path = args.ground_truth_dir / args.gt_pattern.format(case=case)
        if not pred_path.is_file() or not gt_path.is_file():
            raise FileNotFoundError(f"Missing prediction or GT for {case}")

        pred_image = sitk.ReadImage(str(pred_path))
        gt_image = sitk.ReadImage(str(gt_path))
        pred = sitk.GetArrayFromImage(pred_image)
        gt = sitk.GetArrayFromImage(gt_image)
        if pred.shape != gt.shape:
            raise ValueError(f"Shape mismatch for {case}: {pred.shape} != {gt.shape}")
        if not np.allclose(pred_image.GetSpacing(), gt_image.GetSpacing(), atol=1e-6):
            raise ValueError(f"Spacing mismatch for {case}")
        spacing_zyx = tuple(float(value) for value in reversed(gt_image.GetSpacing()))

        input_rows.append(
            {
                "case": case,
                "prediction": pred_path.name,
                "prediction_sha256": sha256_file(pred_path),
                "ground_truth": gt_path.name,
                "ground_truth_sha256": sha256_file(gt_path),
            }
        )
        for label, organ in ORGANS.items():
            dice, hd95, nsd, status = evaluate_binary(pred == label, gt == label, spacing_zyx)
            case_rows.append(
                {
                    "case": case,
                    "label": label,
                    "organ": organ,
                    "dice": "" if dice is None else f"{dice:.10f}",
                    "hd95_mm": "" if hd95 is None else f"{hd95:.10f}",
                    "nsd_1mm": "" if nsd is None else f"{nsd:.10f}",
                    "status": status,
                }
            )

    organ_rows: list[dict] = []
    for label, organ in ORGANS.items():
        selected = [row for row in case_rows if row["label"] == label]
        included = [row for row in selected if row["status"] != "both_empty"]
        organ_rows.append(
            {
                "label": label,
                "organ": organ,
                "included_cases": len(included),
                "excluded_both_empty": len(selected) - len(included),
                "mean_dice": f"{finite_mean(float(row['dice']) for row in included):.10f}",
                "mean_hd95_mm": f"{finite_mean(float(row['hd95_mm']) for row in included):.10f}",
                "mean_nsd_1mm": f"{finite_mean(float(row['nsd_1mm']) for row in included):.10f}",
            }
        )

    overall = {
        "protocol": PROTOCOL,
        "case_count": len(cases),
        "organ_count": len(ORGANS),
        "mean_dice": finite_mean(float(row["mean_dice"]) for row in organ_rows),
        "mean_hd95_mm": finite_mean(float(row["mean_hd95_mm"]) for row in organ_rows),
        "mean_nsd_1mm": finite_mean(float(row["mean_nsd_1mm"]) for row in organ_rows),
        "nsd_tolerance_mm": NSD_TOLERANCE_MM,
        "case_list_sha256": sha256_file(args.case_list),
        "evaluator_sha256": sha256_file(Path(__file__).resolve()),
    }

    write_csv(
        args.output_dir / "per_case_metrics.csv",
        ["case", "label", "organ", "dice", "hd95_mm", "nsd_1mm", "status"],
        case_rows,
    )
    write_csv(
        args.output_dir / "per_organ_metrics.csv",
        [
            "label",
            "organ",
            "included_cases",
            "excluded_both_empty",
            "mean_dice",
            "mean_hd95_mm",
            "mean_nsd_1mm",
        ],
        organ_rows,
    )
    write_csv(
        args.output_dir / "input_hashes.csv",
        ["case", "prediction", "prediction_sha256", "ground_truth", "ground_truth_sha256"],
        input_rows,
    )
    (args.output_dir / "overall_metrics.json").write_text(
        json.dumps(overall, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(overall, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
