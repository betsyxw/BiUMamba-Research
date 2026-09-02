#!/usr/bin/env python3
"""Frozen ACDC v1 offline test evaluation and qualitative export.

Research Author and Repository Maintainer: xuwen
Affiliation: Japan Advanced Institute of Science and Technology (JAIST)

The best checkpoints are selected only on validation data. This program reads
the isolated test list only after training has finished and evaluates E1 and
E2_modify_2 with the same code, patient list, preprocessing and metrics.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import time
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
import torch
from scipy.ndimage import binary_erosion, distance_transform_edt


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ORGAN_NAMES = {1: "right_ventricle", 2: "myocardium", 3: "left_ventricle"}
DISPLAY_NAMES = {1: "RV", 2: "MYO", 3: "LV"}
COLORS = {
    1: np.asarray([230, 57, 70], dtype=np.float32) / 255.0,
    2: np.asarray([38, 166, 91], dtype=np.float32) / 255.0,
    3: np.asarray([48, 126, 215], dtype=np.float32) / 255.0,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def surface(mask: np.ndarray) -> np.ndarray:
    structure = np.ones((3,) * mask.ndim, dtype=bool)
    return np.logical_xor(mask, binary_erosion(mask, structure=structure, border_value=0))


def metric_triplet(pred: np.ndarray, gt: np.ndarray, sampling_zyx, nsd_tolerance_mm: float):
    pred_count, gt_count = int(pred.sum()), int(gt.sum())
    if pred_count == 0 and gt_count == 0:
        return None
    if pred_count == 0 or gt_count == 0:
        physical_extent = (np.asarray(pred.shape) - 1) * np.asarray(sampling_zyx)
        return {"dice": 0.0, "hd95_mm": float(np.linalg.norm(physical_extent)), "nsd": 0.0}
    intersection = int(np.logical_and(pred, gt).sum())
    dice = 2.0 * intersection / (pred_count + gt_count)
    pred_surface, gt_surface = surface(pred), surface(gt)
    to_gt = distance_transform_edt(~gt_surface, sampling=sampling_zyx)[pred_surface]
    to_pred = distance_transform_edt(~pred_surface, sampling=sampling_zyx)[gt_surface]
    distances = np.concatenate([to_gt, to_pred])
    return {
        "dice": float(dice),
        "hd95_mm": float(np.percentile(distances, 95)),
        "nsd": float(np.mean(distances <= nsd_tolerance_mm)),
    }


def build_model(scan_fusion: str, checkpoint_path: Path):
    from models.vmunet.vmunet import VMUNet

    model = VMUNet(
        num_classes=4,
        input_channels=3,
        depths=[2, 2, 2, 2],
        depths_decoder=[2, 2, 2, 1],
        drop_path_rate=0.2,
        load_ckpt_path=None,
        scan_fusion=scan_fusion,
    ).cuda()
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    incompatible = model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    if incompatible.missing_keys or incompatible.unexpected_keys:
        raise RuntimeError(str(incompatible))
    model.eval()
    return model, checkpoint


def load_test_volumes(data_root: Path, test_list: Path):
    patients = [v.strip() for v in test_list.read_text().splitlines() if v.strip()]
    if len(patients) != 20 or len(set(patients)) != 20:
        raise RuntimeError(f"Expected 20 isolated test patients, found {len(patients)}")
    volumes = {}
    for patient in patients:
        patient_dir = data_root / "train" / patient
        for phase in ("ed", "es"):
            image_path = patient_dir / f"{patient}_sax_{phase}.nii.gz"
            label_path = patient_dir / f"{patient}_sax_{phase}_gt.nii.gz"
            image_nii, label_nii = nib.load(str(image_path)), nib.load(str(label_path))
            image = np.asarray(image_nii.dataobj)
            label = np.asarray(label_nii.dataobj).astype(np.uint8)
            if image.shape != label.shape or image.shape[:2] != (192, 192):
                raise RuntimeError(f"Unexpected volume: {patient} {phase} {image.shape}/{label.shape}")
            volume_id = f"{patient}_{phase}"
            volumes[volume_id] = {
                "patient": patient,
                "phase": phase,
                "image": image,
                "label": label,
                "image_nii": image_nii,
                "spacing_xyz": tuple(float(v) for v in image_nii.header.get_zooms()[:3]),
            }
    return volumes


def tensor_batch(image_xyz: np.ndarray, indices):
    arrays = []
    for z_index in indices:
        image = np.clip(image_xyz[:, :, z_index].astype(np.float32), 0.0, 255.0) / 255.0
        arrays.append(torch.from_numpy(image).unsqueeze(0).repeat(3, 1, 1))
    return torch.stack(arrays, dim=0)


@torch.no_grad()
def infer_model(model, volumes, batch_size: int):
    predictions = {}
    total_seconds, total_slices = 0.0, 0
    warmup_done = False
    for volume_id, volume in volumes.items():
        image = volume["image"]
        slices = []
        for start in range(0, image.shape[2], batch_size):
            indices = list(range(start, min(start + batch_size, image.shape[2])))
            batch = tensor_batch(image, indices).cuda(non_blocking=True).float()
            if not warmup_done:
                _ = model(batch)
                torch.cuda.synchronize()
                warmup_done = True
            torch.cuda.synchronize()
            started = time.perf_counter()
            pred = torch.argmax(model(batch), dim=1)
            torch.cuda.synchronize()
            total_seconds += time.perf_counter() - started
            total_slices += len(indices)
            slices.extend(pred.cpu().numpy().astype(np.uint8))
        predictions[volume_id] = np.stack(slices, axis=0)
    return predictions, {
        "total_forward_seconds": total_seconds,
        "slice_count": total_slices,
        "milliseconds_per_slice": 1000.0 * total_seconds / total_slices,
    }


def evaluate_predictions(predictions, volumes, nsd_tolerance_mm: float):
    records = []
    for volume_id in sorted(volumes):
        volume = volumes[volume_id]
        gt_zyx = volume["label"].transpose(2, 0, 1)
        pred_zyx = predictions[volume_id]
        sx, sy, sz = volume["spacing_xyz"]
        for label, name in ORGAN_NAMES.items():
            metrics = metric_triplet(
                pred_zyx == label,
                gt_zyx == label,
                sampling_zyx=(sz, sy, sx),
                nsd_tolerance_mm=nsd_tolerance_mm,
            )
            if metrics is not None:
                records.append(
                    {
                        "volume_id": volume_id,
                        "patient": volume["patient"],
                        "phase": volume["phase"],
                        "organ_label": label,
                        "organ": name,
                        **metrics,
                    }
                )
    per_organ = {}
    for label, name in ORGAN_NAMES.items():
        subset = [r for r in records if r["organ_label"] == label]
        per_organ[name] = {
            "dice": float(np.mean([r["dice"] for r in subset])),
            "hd95_mm": float(np.mean([r["hd95_mm"] for r in subset])),
            "nsd": float(np.mean([r["nsd"] for r in subset])),
            "volume_count": len(subset),
        }
    overall = {
        "mean_dice": float(np.mean([v["dice"] for v in per_organ.values()])),
        "mean_hd95_mm": float(np.mean([v["hd95_mm"] for v in per_organ.values()])),
        "mean_nsd": float(np.mean([v["nsd"] for v in per_organ.values()])),
    }
    return records, per_organ, overall


def volume_means(records):
    grouped = defaultdict(list)
    for record in records:
        grouped[record["volume_id"]].append(record)
    return {
        volume_id: {
            "dice": float(np.mean([v["dice"] for v in values])),
            "hd95_mm": float(np.mean([v["hd95_mm"] for v in values])),
            "nsd": float(np.mean([v["nsd"] for v in values])),
        }
        for volume_id, values in grouped.items()
    }


def choose_cases(e1_records, e2_records, volumes):
    e1, e2 = volume_means(e1_records), volume_means(e2_records)
    combined = {k: 0.5 * (e1[k]["dice"] + e2[k]["dice"]) for k in e1}
    median = float(np.median(list(combined.values())))
    typical = min(combined, key=lambda k: (abs(combined[k] - median), k))
    difficult = min(combined, key=lambda k: (combined[k], k))
    failure = min(combined, key=lambda k: (e2[k]["dice"] - e1[k]["dice"], k))
    thin_scores = {}
    for volume_id, volume in volumes.items():
        gt = volume["label"].transpose(2, 0, 1) == 2
        thin_scores[volume_id] = float(surface(gt).sum() / max(int(gt.sum()), 1))
    thin_myo = max(thin_scores, key=lambda k: (thin_scores[k], k))
    return {
        "typical": typical,
        "difficult": difficult,
        "e2_failure": failure,
        "thin_myocardium": thin_myo,
    }, {
        "typical": "Combined E1/E2 volume Dice closest to the test-set median.",
        "difficult": "Lowest combined E1/E2 volume Dice.",
        "e2_failure": "Most negative E2_modify_2 minus E1 volume Dice difference.",
        "thin_myocardium": "Highest ground-truth myocardium 3D surface-to-volume ratio.",
        "slice_rule": "Slice with maximum ground-truth foreground area; for thin myocardium, maximum myocardium area.",
    }


def normalize_for_display(image):
    lo, hi = np.percentile(image, [1, 99])
    if hi <= lo:
        return np.zeros_like(image, dtype=np.float32)
    return np.clip((image.astype(np.float32) - lo) / (hi - lo), 0.0, 1.0)


def overlay(image, mask):
    gray = normalize_for_display(image)
    rgb = np.repeat(gray[:, :, None], 3, axis=2)
    for label, color in COLORS.items():
        region = mask == label
        rgb[region] = 0.48 * rgb[region] + 0.52 * color
    return np.rot90(rgb)


def save_qualitative(selected, selection_rules, volumes, e1_pred, e2_pred, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"selection_rules": selection_rules, "cases": {}}
    rows = []
    for kind, volume_id in selected.items():
        volume = volumes[volume_id]
        label = volume["label"]
        if kind == "thin_myocardium":
            z_index = int(np.argmax(np.sum(label == 2, axis=(0, 1))))
        else:
            z_index = int(np.argmax(np.sum(label > 0, axis=(0, 1))))
        image_slice = volume["image"][:, :, z_index]
        gt_slice = label[:, :, z_index]
        e1_slice = e1_pred[volume_id][z_index]
        e2_slice = e2_pred[volume_id][z_index]
        panels = [
            np.rot90(normalize_for_display(image_slice)),
            overlay(image_slice, gt_slice),
            overlay(image_slice, e1_slice),
            overlay(image_slice, e2_slice),
        ]
        rows.append((kind, volume_id, z_index, panels))
        manifest["cases"][kind] = {
            "volume_id": volume_id,
            "patient": volume["patient"],
            "phase": volume["phase"],
            "slice_index": z_index,
        }

        fig, axes = plt.subplots(1, 4, figsize=(12, 3.2), constrained_layout=True)
        for ax, panel, title in zip(axes, panels, ["Input MRI", "Ground Truth", "E1", "E2_modify_2"]):
            ax.imshow(panel, cmap="gray" if panel.ndim == 2 else None, interpolation="nearest")
            ax.set_title(title, fontsize=12)
            ax.axis("off")
        fig.suptitle(f"{kind.replace('_', ' ').title()}: {volume_id}, slice {z_index}", fontsize=13)
        fig.savefig(out_dir / f"{kind}_{volume_id}_slice{z_index}.png", dpi=300, bbox_inches="tight")
        fig.savefig(out_dir / f"{kind}_{volume_id}_slice{z_index}.pdf", bbox_inches="tight")
        plt.close(fig)

    fig, axes = plt.subplots(4, 4, figsize=(12, 12), constrained_layout=True)
    for row_index, (kind, volume_id, z_index, panels) in enumerate(rows):
        for column_index, (panel, title) in enumerate(
            zip(panels, ["Input MRI", "Ground Truth", "E1", "E2_modify_2"])
        ):
            ax = axes[row_index, column_index]
            ax.imshow(panel, cmap="gray" if panel.ndim == 2 else None, interpolation="nearest")
            if row_index == 0:
                ax.set_title(title, fontsize=13)
            if column_index == 0:
                ax.set_ylabel(f"{kind.replace('_', ' ').title()}\n{volume_id}, z={z_index}", fontsize=11)
            ax.set_xticks([])
            ax.set_yticks([])
    fig.suptitle("ACDC Test Set: E1 vs E2_modify_2 (Seed 42)", fontsize=16)
    combined_png = out_dir / "ACDC_E1_vs_E2_modify_2_qualitative_seed42_runpod.png"
    combined_pdf = out_dir / "ACDC_E1_vs_E2_modify_2_qualitative_seed42_runpod.pdf"
    fig.savefig(combined_png, dpi=300, bbox_inches="tight")
    fig.savefig(combined_pdf, bbox_inches="tight")
    plt.close(fig)
    (out_dir / "QUALITATIVE_SELECTION_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return combined_png, combined_pdf, manifest


def write_csv(path: Path, rows, fieldnames):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--protocol-dir", type=Path, required=True)
    parser.add_argument("--e1-checkpoint", type=Path, required=True)
    parser.add_argument("--e2-checkpoint", type=Path, required=True)
    parser.add_argument("--e1-summary", type=Path, required=True)
    parser.add_argument("--e2-summary", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--nsd-tolerance-mm", type=float, default=1.0)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    test_list = args.protocol_dir / "splits" / "test_patients.txt"
    volumes = load_test_volumes(args.data_root, test_list)
    models = {
        "E1": ("original", args.e1_checkpoint),
        "E2_modify_2": ("grouped_2d_bidirectional_sum", args.e2_checkpoint),
    }
    all_results, all_predictions = {}, {}
    for model_name, (scan_fusion, checkpoint_path) in models.items():
        model, checkpoint = build_model(scan_fusion, checkpoint_path)
        predictions, inference = infer_model(model, volumes, args.batch_size)
        records, per_organ, overall = evaluate_predictions(
            predictions, volumes, args.nsd_tolerance_mm
        )
        result = {
            "model": model_name,
            "scan_fusion": scan_fusion,
            "checkpoint": str(checkpoint_path),
            "checkpoint_sha256": sha256(checkpoint_path),
            "best_validation_epoch": int(checkpoint["epoch"]),
            "best_validation_dice": float(checkpoint["validation_dice"]),
            "best_validation_hd95_mm": float(checkpoint["validation_hd95_mm"]),
            "strict_checkpoint_load": True,
            "test_patient_count": 20,
            "test_volume_count": len(volumes),
            "nsd_tolerance_mm": args.nsd_tolerance_mm,
            "overall": overall,
            "per_organ": per_organ,
            "inference": inference,
        }
        all_results[model_name] = result
        all_predictions[model_name] = predictions
        (args.output_dir / f"{model_name}_test_metrics.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        write_csv(
            args.output_dir / f"{model_name}_per_volume_per_organ.csv",
            records,
            ["volume_id", "patient", "phase", "organ_label", "organ", "dice", "hd95_mm", "nsd"],
        )
        del model
        torch.cuda.empty_cache()

    # csv.DictReader returns strings; reconstruct numeric records for selection.
    def numeric_records(path):
        rows = list(csv.DictReader(path.open()))
        for row in rows:
            for key in ("dice", "hd95_mm", "nsd"):
                row[key] = float(row[key])
            row["organ_label"] = int(row["organ_label"])
        return rows

    selected, selection_rules = choose_cases(
        numeric_records(args.output_dir / "E1_per_volume_per_organ.csv"),
        numeric_records(args.output_dir / "E2_modify_2_per_volume_per_organ.csv"),
        volumes,
    )
    qualitative_dir = args.output_dir / "qualitative_medical_images_DO_NOT_UPLOAD_GITHUB"
    combined_png, combined_pdf, qualitative_manifest = save_qualitative(
        selected,
        selection_rules,
        volumes,
        all_predictions["E1"],
        all_predictions["E2_modify_2"],
        qualitative_dir,
    )

    e1_summary, e2_summary = json.load(args.e1_summary.open()), json.load(args.e2_summary.open())
    comparison_rows = []
    for model_name, training in (("E1", e1_summary), ("E2_modify_2", e2_summary)):
        test = all_results[model_name]
        comparison_rows.append(
            {
                "model": model_name,
                "seed": 42,
                "best_validation_epoch": test["best_validation_epoch"],
                "test_mean_dice": test["overall"]["mean_dice"],
                "test_mean_hd95_mm": test["overall"]["mean_hd95_mm"],
                "test_mean_nsd_at_1mm": test["overall"]["mean_nsd"],
                "total_training_hours": training["total_training_and_validation_seconds"] / 3600.0,
                "mean_epoch_seconds": training["mean_epoch_total_seconds"],
                "peak_gpu_allocated_gib": training["peak_gpu_allocated_bytes"] / 1024.0**3,
                "parameter_count": training["parameter_count"],
                "inference_ms_per_slice": test["inference"]["milliseconds_per_slice"],
            }
        )
    write_csv(
        args.output_dir / "ACDC_E1_vs_E2_modify_2_overall_comparison.csv",
        comparison_rows,
        list(comparison_rows[0]),
    )
    organ_rows = []
    for model_name in ("E1", "E2_modify_2"):
        for organ, values in all_results[model_name]["per_organ"].items():
            organ_rows.append({"model": model_name, "organ": organ, **values})
    write_csv(
        args.output_dir / "ACDC_E1_vs_E2_modify_2_per_organ.csv",
        organ_rows,
        ["model", "organ", "dice", "hd95_mm", "nsd", "volume_count"],
    )

    e1, e2 = comparison_rows
    differences = {
        "dice_absolute": e2["test_mean_dice"] - e1["test_mean_dice"],
        "hd95_mm_absolute": e2["test_mean_hd95_mm"] - e1["test_mean_hd95_mm"],
        "nsd_absolute": e2["test_mean_nsd_at_1mm"] - e1["test_mean_nsd_at_1mm"],
        "training_time_percent": 100.0 * (e2["total_training_hours"] / e1["total_training_hours"] - 1.0),
        "mean_epoch_time_percent": 100.0 * (e2["mean_epoch_seconds"] / e1["mean_epoch_seconds"] - 1.0),
        "peak_memory_percent": 100.0 * (e2["peak_gpu_allocated_gib"] / e1["peak_gpu_allocated_gib"] - 1.0),
        "inference_time_percent": 100.0 * (e2["inference_ms_per_slice"] / e1["inference_ms_per_slice"] - 1.0),
    }
    if differences["dice_absolute"] >= 0 and differences["hd95_mm_absolute"] <= 0:
        decision = "Green"
    elif differences["dice_absolute"] >= -0.005 and differences["training_time_percent"] < 0:
        decision = "Yellow"
    else:
        decision = "Red"
    manifest = {
        "protocol": "acdc_v1",
        "test_list_sha256": sha256(test_list),
        "test_patient_count": 20,
        "test_volume_count": len(volumes),
        "checkpoint_selection": "Higher validation Dice; lower validation HD95 as tie-breaker; test never used.",
        "nsd_tolerance_mm": args.nsd_tolerance_mm,
        "results": all_results,
        "differences_e2_minus_e1": differences,
        "decision": decision,
        "qualitative": qualitative_manifest,
        "combined_png": str(combined_png),
        "combined_pdf": str(combined_pdf),
        "flops": "Unavailable in this evaluator; do not invent a value.",
    }
    (args.output_dir / "ACDC_EVALUATION_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
