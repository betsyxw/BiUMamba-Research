#!/usr/bin/env python3
"""Render publication-ready BUSI qualitative comparisons from private test outputs."""

from __future__ import annotations

import argparse
import csv
import textwrap
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import binary_erosion


SIZE = 224
CASES = [
    ("Typical case", "group_0013"),
    ("Small-lesion case", "group_0114"),
    ("Difficult case", "group_0301"),
    ("E2 failure case", "group_0178"),
]
COLORS = {
    "gt": np.array([50, 205, 90], dtype=np.float32),
    "pred": np.array([235, 70, 70], dtype=np.float32),
}


def font(size: int, bold: bool = False):
    names = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for name in names:
        if Path(name).is_file():
            return ImageFont.truetype(name, size=size)
    return ImageFont.load_default()


def load_rows(path: Path) -> dict[str, dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return {row["group_id"]: row for row in csv.DictReader(handle)}


def union_mask(data_root: Path, row: dict) -> Image.Image:
    image = Image.open(data_root / row["image_relpath"]).convert("RGB")
    union = np.zeros((image.height, image.width), dtype=bool)
    for relpath in row["mask_relpaths"].split("|"):
        mask = Image.open(data_root / relpath).convert("L")
        if mask.size != image.size:
            raise RuntimeError(f"Image/mask mismatch for {row['sample_id']}")
        union |= np.asarray(mask) > 0
    return Image.fromarray(union.astype(np.uint8) * 255, mode="L")


def restore_prediction(prediction: Image.Image, original_size: tuple[int, int]) -> Image.Image:
    width, height = original_size
    scale = min(SIZE / width, SIZE / height)
    new_width = max(1, round(width * scale))
    new_height = max(1, round(height * scale))
    x0 = (SIZE - new_width) // 2
    y0 = (SIZE - new_height) // 2
    cropped = prediction.crop((x0, y0, x0 + new_width, y0 + new_height))
    return cropped.resize(original_size, Image.Resampling.NEAREST)


def fit_square(image: Image.Image, size: int, resample=Image.Resampling.LANCZOS) -> Image.Image:
    image = image.copy()
    image.thumbnail((size, size), resample=resample)
    canvas = Image.new("RGB", (size, size), "black")
    canvas.paste(image, ((size - image.width) // 2, (size - image.height) // 2))
    return canvas


def overlay(image: Image.Image, gt: Image.Image, pred: Image.Image | None) -> Image.Image:
    base = np.asarray(image.convert("RGB"), dtype=np.float32)
    gt_array = np.asarray(gt.convert("L")) > 0
    if pred is None:
        out = base.copy()
        out[gt_array] = 0.55 * out[gt_array] + 0.45 * COLORS["gt"]
    else:
        pred_array = np.asarray(pred.convert("L")) > 0
        out = base.copy()
        out[pred_array] = 0.58 * out[pred_array] + 0.42 * COLORS["pred"]
        boundary = np.logical_xor(gt_array, binary_erosion(gt_array, structure=np.ones((3, 3)), border_value=0))
        for _ in range(2):
            expanded = boundary.copy()
            expanded[:-1] |= boundary[1:]
            expanded[1:] |= boundary[:-1]
            expanded[:, :-1] |= boundary[:, 1:]
            expanded[:, 1:] |= boundary[:, :-1]
            boundary = expanded
        out[boundary] = COLORS["gt"]
    return Image.fromarray(out.clip(0, 255).astype(np.uint8), mode="RGB")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--e1-predictions", type=Path, required=True)
    parser.add_argument("--e2-predictions", type=Path, required=True)
    parser.add_argument("--e1-metrics", type=Path, required=True)
    parser.add_argument("--e2-metrics", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    with args.manifest.open(encoding="utf-8", newline="") as handle:
        manifest = {row["group_id"]: row for row in csv.DictReader(handle)}
    e1_metrics = load_rows(args.e1_metrics)
    e2_metrics = load_rows(args.e2_metrics)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    panels_dir = args.output_dir / "individual_panels"
    panels_dir.mkdir(exist_ok=True)

    canvas_width = 2280
    top_height = 160
    row_height = 500
    bottom_height = 110
    label_width = 390
    image_size = 410
    gap = 25
    canvas_height = top_height + row_height * len(CASES) + bottom_height
    canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((45, 24), "Qualitative Segmentation Results on BUSI", fill="#30343b", font=font(54, True))
    headers = ["Input ultrasound", "Ground Truth", "E1 - VM-UNet", "E2_modify_2"]
    for col, header in enumerate(headers):
        x = label_width + col * (image_size + gap)
        box = draw.textbbox((0, 0), header, font=font(31, True))
        draw.text((x + (image_size - (box[2] - box[0])) / 2, 108), header, fill="#30343b", font=font(31, True))

    panel_files = []
    for row_index, (category, group_id) in enumerate(CASES):
        row = manifest[group_id]
        image = Image.open(args.data_root / row["image_relpath"]).convert("RGB")
        gt = union_mask(args.data_root, row)
        e1_pred = restore_prediction(Image.open(args.e1_predictions / f"{group_id}.png").convert("L"), image.size)
        e2_pred = restore_prediction(Image.open(args.e2_predictions / f"{group_id}.png").convert("L"), image.size)
        views = [image, overlay(image, gt, None), overlay(image, gt, e1_pred), overlay(image, gt, e2_pred)]

        y = top_height + row_index * row_height
        if row_index % 2:
            draw.rectangle((0, y, canvas_width, y + row_height), fill="#f4f6f8")
        draw.text((35, y + 95), category, fill="#30343b", font=font(32, True))
        draw.text((35, y + 145), row["sample_id"], fill="#60656f", font=font(25))
        draw.text((35, y + 183), row["class_name"].capitalize(), fill="#60656f", font=font(25))

        for col, view in enumerate(views):
            x = label_width + col * (image_size + gap)
            fitted = fit_square(view, image_size)
            canvas.paste(fitted, (x, y + 24))
            ImageDraw.Draw(canvas).rectangle((x, y + 24, x + image_size, y + 24 + image_size), outline="#c8ccd2", width=2)
            if col == 2:
                score = float(e1_metrics[group_id]["dice"])
                draw.text((x + 8, y + 442), f"Dice: {score:.3f}", fill="#30343b", font=font(24, True))
            elif col == 3:
                score = float(e2_metrics[group_id]["dice"])
                draw.text((x + 8, y + 442), f"Dice: {score:.3f}", fill="#30343b", font=font(24, True))

        panel = canvas.crop((0, y, canvas_width, y + row_height))
        panel_path = panels_dir / f"{row_index + 1:02d}_{category.lower().replace(' ', '_')}_{group_id}.png"
        panel.save(panel_path, dpi=(300, 300))
        panel_files.append(panel_path)

    legend_y = top_height + row_height * len(CASES) + 28
    draw.rectangle((label_width, legend_y, label_width + 34, legend_y + 34), fill=tuple(COLORS["gt"].astype(int)))
    draw.text((label_width + 50, legend_y - 2), "Ground-truth region / boundary", fill="#30343b", font=font(25))
    draw.rectangle((label_width + 510, legend_y, label_width + 544, legend_y + 34), fill=tuple(COLORS["pred"].astype(int)))
    draw.text((label_width + 560, legend_y - 2), "Model prediction", fill="#30343b", font=font(25))
    draw.text((1610, legend_y - 2), "Seed 42; processed at 224 x 224", fill="#60656f", font=font(23))

    png_path = args.output_dir / "BUSI_E1_vs_E2_modify_2_qualitative_seed42_runpod_300dpi.png"
    pdf_path = args.output_dir / "BUSI_E1_vs_E2_modify_2_qualitative_seed42_runpod_300dpi.pdf"
    canvas.save(png_path, dpi=(300, 300))
    canvas.save(pdf_path, "PDF", resolution=300.0)
    readme = args.output_dir / "README.txt"
    readme.write_text(
        "BUSI qualitative comparison, seed 42.\n"
        "Columns: Input ultrasound | Ground Truth | E1 - VM-UNet | E2_modify_2.\n"
        "Green marks ground truth; red marks prediction.\n"
        "Patient-derived images and predictions: do not upload to GitHub.\n",
        encoding="utf-8",
    )
    zip_path = args.output_dir / "BUSI_E1_vs_E2_modify_2_qualitative_seed42_runpod.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in [png_path, pdf_path, readme, *panel_files]:
            archive.write(path, path.relative_to(args.output_dir))
    print(png_path)
    print(pdf_path)
    print(zip_path)


if __name__ == "__main__":
    main()
