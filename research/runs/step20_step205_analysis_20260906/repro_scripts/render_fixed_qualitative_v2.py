#!/usr/bin/env python3
"""Render preregistered Step 20.5 qualitative cases without cherry-picking.

The selection manifests were created from three-seed patient/group means.  This
program only renders those frozen selections with seed 42 masks.  Medical images
and masks are written below a clearly marked private directory and must not be
uploaded to GitHub.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import cv2
import h5py
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
import pandas as pd
import torch
from PIL import Image
from skimage.segmentation import find_boundaries


PALETTE = np.asarray(
    [
        [0, 0, 0],
        [230, 57, 70],
        [38, 166, 91],
        [48, 126, 215],
        [255, 159, 28],
        [175, 82, 222],
        [0, 190, 200],
        [255, 214, 10],
        [255, 105, 180],
    ],
    dtype=np.float32,
) / 255.0


def normalize(image: np.ndarray) -> np.ndarray:
    values = image[np.isfinite(image)]
    if not values.size:
        return np.zeros_like(image, dtype=np.float32)
    lo, hi = np.percentile(values, [1, 99])
    if hi <= lo:
        return np.zeros_like(image, dtype=np.float32)
    return np.clip((image.astype(np.float32) - lo) / (hi - lo), 0, 1)


def color_overlay(image: np.ndarray, mask: np.ndarray, gt_boundary: np.ndarray | None = None) -> np.ndarray:
    gray = normalize(image)
    rgb = np.repeat(gray[..., None], 3, axis=2)
    for label in np.unique(mask):
        label = int(label)
        if label <= 0:
            continue
        region = mask == label
        color = PALETTE[label % len(PALETTE)]
        rgb[region] = 0.45 * rgb[region] + 0.55 * color
    if gt_boundary is not None:
        rgb[gt_boundary] = np.asarray([0.15, 1.0, 0.25])
    return rgb


def binary_prediction_overlay(image: np.ndarray, pred: np.ndarray, gt: np.ndarray) -> np.ndarray:
    gray = normalize(image)
    rgb = np.repeat(gray[..., None], 3, axis=2)
    rgb[pred] = 0.42 * rgb[pred] + 0.58 * np.asarray([0.90, 0.18, 0.18])
    rgb[find_boundaries(gt, mode="outer")] = np.asarray([0.10, 1.0, 0.20])
    return rgb


def save_panel_set(dataset: str, rows: list[dict], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    titles = {
        "Synapse": ["Input CT", "Ground Truth", "E1 – VM-UNet", "E2_modify_2"],
        "ACDC": ["Input MRI", "Ground Truth", "E1 – VM-UNet", "E2_modify_2"],
        "BUSI": ["Input ultrasound", "Ground Truth", "E1 – VM-UNet", "E2_modify_2"],
    }[dataset]
    for row in rows:
        fig, axes = plt.subplots(1, 4, figsize=(13, 3.25), constrained_layout=True)
        for ax, panel, title in zip(axes, row["panels"], titles):
            ax.imshow(panel, cmap="gray" if panel.ndim == 2 else None, interpolation="nearest")
            ax.set_title(title, fontsize=12)
            ax.axis("off")
        fig.suptitle(row["caption"], fontsize=13)
        stem = f'{row["category"]}_{row["unit_id"]}'
        fig.savefig(out_dir / f"{stem}.png", dpi=300, bbox_inches="tight")
        fig.savefig(out_dir / f"{stem}.pdf", bbox_inches="tight")
        plt.close(fig)

    fig, axes = plt.subplots(len(rows), 4, figsize=(13, 3.0 * len(rows)), constrained_layout=True)
    for i, row in enumerate(rows):
        for j, (panel, title) in enumerate(zip(row["panels"], titles)):
            ax = axes[i, j]
            ax.imshow(panel, cmap="gray" if panel.ndim == 2 else None, interpolation="nearest")
            if i == 0:
                ax.set_title(title, fontsize=13, fontweight="bold")
            if j == 0:
                ax.set_ylabel(row["row_label"], fontsize=10)
            ax.set_xticks([])
            ax.set_yticks([])
    fig.suptitle(f"{dataset}: fixed-rule qualitative cases (seed 42 shown)", fontsize=16)
    fig.savefig(out_dir / f"{dataset.lower()}_fixed_selection_seed42.png", dpi=300, bbox_inches="tight")
    fig.savefig(out_dir / f"{dataset.lower()}_fixed_selection_seed42.pdf", bbox_inches="tight")
    plt.close(fig)


def synapse(workspace: Path, root: Path) -> None:
    selection_dir = root / "qualitative_figures/fixed_selection_v2/synapse"
    manifest = pd.read_csv(selection_dir / "selection_manifest.csv")
    output = selection_dir / "medical_images_DO_NOT_UPLOAD_GITHUB"
    e1_root = workspace / "runs/formal_test_synapse_v2/E1_seed42"
    e2_root = workspace / "runs/formal_test_synapse_v2/E2_modify_2_seed42"
    rendered = []
    rows = []
    for record in manifest.to_dict("records"):
        case = record["unit_id"]
        with h5py.File(workspace / f"datasets/Synapse/test_vol_h5/{case}.npy.h5", "r") as handle:
            image_zyx = np.asarray(handle["image"], dtype=np.float32)
        gt = np.asarray(nib.load(e1_root / f"ground_truth_do_not_upload/{case}_gt.nii.gz").dataobj)
        e1 = np.asarray(nib.load(e1_root / f"predictions_do_not_upload/{case}_pred.nii.gz").dataobj)
        e2 = np.asarray(nib.load(e2_root / f"predictions_do_not_upload/{case}_pred.nii.gz").dataobj)
        areas = np.sum(gt > 0, axis=(0, 1))
        z = int(np.argmax(areas))
        image = image_zyx[z]
        gt_slice, e1_slice, e2_slice = gt[:, :, z], e1[:, :, z], e2[:, :, z]
        boundary = find_boundaries(gt_slice, mode="outer")
        panels = [normalize(image), color_overlay(image, gt_slice), color_overlay(image, e1_slice, boundary), color_overlay(image, e2_slice, boundary)]
        delta = float(record["delta_dice_e2_minus_e1"])
        caption = f'{record["category"].replace("_", " ").title()} | {case}, slice {z} | three-seed patient Dice Δ={delta:+.3f}'
        rows.append({"category": record["category"], "unit_id": case, "caption": caption, "row_label": f'{record["category"].replace("_", " ").title()}\n{case}, z={z}\nΔDice={delta:+.3f}', "panels": panels})
        rendered.append({**record, "display_seed": 42, "display_volume_id": case, "slice_index": z, "slice_rule": "Maximum total ground-truth foreground area."})
    save_panel_set("Synapse", rows, output)
    pd.DataFrame(rendered).to_csv(selection_dir / "selection_manifest_rendered.csv", index=False)


def inverse_letterbox(mask_224: np.ndarray, target_shape: tuple[int, int]) -> np.ndarray:
    height, width = target_shape
    scale = min(224 / width, 224 / height)
    new_width, new_height = max(1, round(width * scale)), max(1, round(height * scale))
    left, top = (224 - new_width) // 2, (224 - new_height) // 2
    crop = mask_224[top : top + new_height, left : left + new_width].astype(np.uint8)
    return cv2.resize(crop, (width, height), interpolation=cv2.INTER_NEAREST) > 0


def busi(workspace: Path, root: Path) -> None:
    selection_dir = root / "qualitative_figures/fixed_selection_v2/busi"
    selected = pd.read_csv(selection_dir / "selection_manifest.csv")
    protocol = pd.read_csv(workspace / "outputs/busi_v1_clean_formal_three_seed_runpod/github_safe_stage/protocol/clean_manifest.csv").set_index("group_id")
    data_root = workspace / "datasets/Dataset_BUSI_with_GT"
    pred_root = workspace / "outputs/busi_v1_clean_formal_three_seed_runpod/runs"
    output = selection_dir / "medical_images_DO_NOT_UPLOAD_GITHUB"
    rows, rendered = [], []
    for record in selected.to_dict("records"):
        group_id = record["group_id"]
        source = protocol.loc[group_id]
        image = np.asarray(Image.open(data_root / source.image_relpath).convert("L"), dtype=np.float32)
        gt = np.zeros(image.shape, dtype=bool)
        for relpath in str(source.mask_relpaths).split("|"):
            gt |= np.asarray(Image.open(data_root / relpath).convert("L")) > 0
        e1_224 = np.asarray(Image.open(pred_root / f"E1_seed42/private_do_not_upload/predictions/{group_id}.png").convert("L")) > 0
        e2_224 = np.asarray(Image.open(pred_root / f"E2_modify_2_seed42/private_do_not_upload/predictions/{group_id}.png").convert("L")) > 0
        e1, e2 = inverse_letterbox(e1_224, image.shape), inverse_letterbox(e2_224, image.shape)
        panels = [normalize(image), color_overlay(image, gt.astype(np.uint8)), binary_prediction_overlay(image, e1, gt), binary_prediction_overlay(image, e2, gt)]
        delta = float(record["delta_dice_e2_minus_e1"])
        caption = f'{record["category"].replace("_", " ").title()} | {group_id} ({record["class_name"]}) | three-seed group Dice Δ={delta:+.3f}'
        rows.append({"category": record["category"], "unit_id": group_id, "caption": caption, "row_label": f'{record["category"].replace("_", " ").title()}\n{group_id}\nΔDice={delta:+.3f}', "panels": panels})
        rendered.append({**record, "display_seed": 42, "display_volume_id": group_id, "slice_index": "2D", "slice_rule": "Entire 2D image; seed 42 masks shown."})
    save_panel_set("BUSI", rows, output)
    pd.DataFrame(rendered).to_csv(selection_dir / "selection_manifest_rendered.csv", index=False)


def import_acdc_evaluator(workspace: Path):
    path = workspace / "repos/VM-UNet_E2_modify_2_ACDC_v1/research/acdc_offline_evaluate_and_visualize.py"
    spec = importlib.util.spec_from_file_location("acdc_eval", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def acdc(workspace: Path, root: Path) -> None:
    selection_dir = root / "qualitative_figures/fixed_selection_v2/acdc"
    selected = pd.read_csv(selection_dir / "selection_manifest.csv")
    evaluator = import_acdc_evaluator(workspace)
    volumes_all = evaluator.load_test_volumes(
        workspace / "datasets/ACDC_hf_preprocessed_train100",
        root / "acdc/frozen_protocol/splits/test_patients.txt",
    )
    patient_ids = set(selected.unit_id)
    volumes = {key: value for key, value in volumes_all.items() if value["patient"] in patient_ids}
    e1_model, _ = evaluator.build_model("original", workspace / "runs/e1_acdc_v1_full300_seed42_runpod/checkpoints/best_validation.pth")
    e1_pred, _ = evaluator.infer_model(e1_model, volumes, batch_size=16)
    del e1_model
    torch.cuda.empty_cache()
    e2_model, _ = evaluator.build_model("grouped_2d_bidirectional_sum", workspace / "runs/e2_modify_2_acdc_v1_full300_seed42_runpod/checkpoints/best_validation.pth")
    e2_pred, _ = evaluator.infer_model(e2_model, volumes, batch_size=16)
    del e2_model
    torch.cuda.empty_cache()

    output = selection_dir / "medical_images_DO_NOT_UPLOAD_GITHUB"
    rows, rendered = [], []
    for record in selected.to_dict("records"):
        patient = record["unit_id"]
        candidates = [key for key, value in volumes.items() if value["patient"] == patient]
        volume_id = max(candidates, key=lambda key: int(np.sum(volumes[key]["label"] > 0)))
        volume = volumes[volume_id]
        gt = volume["label"]
        z = int(np.argmax(np.sum(gt > 0, axis=(0, 1))))
        image = volume["image"][:, :, z]
        gt_slice = gt[:, :, z]
        e1_slice, e2_slice = e1_pred[volume_id][z], e2_pred[volume_id][z]
        boundary = find_boundaries(gt_slice, mode="outer")
        panels = [np.rot90(normalize(image)), np.rot90(color_overlay(image, gt_slice)), np.rot90(color_overlay(image, e1_slice, boundary)), np.rot90(color_overlay(image, e2_slice, boundary))]
        delta = float(record["delta_dice_e2_minus_e1"])
        caption = f'{record["category"].replace("_", " ").title()} | {volume_id}, slice {z} | three-seed patient Dice Δ={delta:+.3f}'
        rows.append({"category": record["category"], "unit_id": patient, "caption": caption, "row_label": f'{record["category"].replace("_", " ").title()}\n{volume_id}, z={z}\nΔDice={delta:+.3f}', "panels": panels})
        rendered.append({**record, "display_seed": 42, "display_volume_id": volume_id, "slice_index": z, "slice_rule": "Patient phase with largest GT foreground volume, then slice with maximum GT foreground area."})
    save_panel_set("ACDC", rows, output)
    pd.DataFrame(rendered).to_csv(selection_dir / "selection_manifest_rendered.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=Path("/workspace"))
    parser.add_argument("--final-root", type=Path, default=Path("/workspace/paper_final_results_v2"))
    args = parser.parse_args()
    synapse(args.workspace, args.final_root)
    busi(args.workspace, args.final_root)
    acdc(args.workspace, args.final_root)
    summary = {
        "status": "complete",
        "selection_basis": "Frozen rules applied to three-seed patient/group means before viewing seed-42 images.",
        "display_seed": 42,
        "datasets": ["Synapse", "ACDC", "BUSI"],
        "medical_image_outputs": "medical_images_DO_NOT_UPLOAD_GITHUB",
        "github_policy": "Do not upload medical images, ground truth masks, or prediction masks.",
    }
    (args.final_root / "qualitative_figures/fixed_selection_v2/RENDER_MANIFEST.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
