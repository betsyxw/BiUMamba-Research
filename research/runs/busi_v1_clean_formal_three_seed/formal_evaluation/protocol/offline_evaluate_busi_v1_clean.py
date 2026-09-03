#!/usr/bin/env python3
"""Frozen isolated-test evaluation for BUSI v1 clean.

This program is separate from the training dataset implementation so the
isolated test split cannot be constructed during training. Predictions and
processed medical images are written below ``private_do_not_upload`` and must
never be committed to GitHub.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from scipy.ndimage import binary_erosion, distance_transform_edt
from torch.utils.data import DataLoader, Dataset


METHOD_TO_SCAN = {
    "E1": "original",
    "E2_modify_2": "grouped_2d_bidirectional_sum",
}
NSD_TOLERANCE_PX = 2.0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def surface(mask: np.ndarray) -> np.ndarray:
    return np.logical_xor(mask, binary_erosion(mask, structure=np.ones((3, 3)), border_value=0))


def positive_metrics(pred: np.ndarray, gt: np.ndarray) -> tuple[float, float, float]:
    pred_count, gt_count = int(pred.sum()), int(gt.sum())
    if gt_count == 0:
        raise ValueError("Positive-lesion metrics require non-empty ground truth")
    if pred_count == 0:
        diagonal = float(np.linalg.norm(np.asarray(gt.shape, dtype=float) - 1.0))
        return 0.0, diagonal, 0.0
    intersection = int(np.logical_and(pred, gt).sum())
    dice = 2.0 * intersection / (pred_count + gt_count)
    pred_surface, gt_surface = surface(pred), surface(gt)
    pred_to_gt = distance_transform_edt(~gt_surface)[pred_surface]
    gt_to_pred = distance_transform_edt(~pred_surface)[gt_surface]
    distances = np.concatenate([pred_to_gt, gt_to_pred])
    hd95 = float(np.percentile(distances, 95))
    nsd = float(
        (np.count_nonzero(pred_to_gt <= NSD_TOLERANCE_PX)
         + np.count_nonzero(gt_to_pred <= NSD_TOLERANCE_PX))
        / (len(pred_to_gt) + len(gt_to_pred))
    )
    return float(dice), hd95, nsd


class BUSITestDataset(Dataset):
    def __init__(self, data_root: Path, protocol_dir: Path):
        from research.protocols.busi_v1_clean.frozen_augmentation import resize_and_pad, to_tensors

        self.data_root = Path(data_root)
        self.protocol_dir = Path(protocol_dir)
        self.resize_and_pad = resize_and_pad
        self.to_tensors = to_tensors
        split_groups = [
            line.strip()
            for line in (self.protocol_dir / "splits" / "test_groups.txt").read_text().splitlines()
            if line.strip()
        ]
        if len(split_groups) != 105 or len(set(split_groups)) != 105:
            raise RuntimeError("Frozen BUSI test split must contain 105 unique groups")
        with (self.protocol_dir / "clean_manifest.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        by_group = {row["group_id"]: row for row in rows}
        if set(split_groups) - set(by_group):
            raise RuntimeError("Test split includes groups missing from clean_manifest.csv")
        self.rows = [by_group[group_id] for group_id in split_groups]
        if any(row["split"] != "test" for row in self.rows):
            raise RuntimeError("Test list and manifest split assignments do not match")

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int):
        row = self.rows[index]
        image = Image.open(self.data_root / row["image_relpath"]).convert("RGB")
        masks = [
            Image.open(self.data_root / relpath).convert("L")
            for relpath in row["mask_relpaths"].split("|")
        ]
        union = np.zeros((image.height, image.width), dtype=np.uint8)
        for mask in masks:
            if mask.size != image.size:
                raise RuntimeError(f"Image/mask size mismatch for {row['sample_id']}")
            union |= (np.asarray(mask, dtype=np.uint8) > 0).astype(np.uint8) * 255
        image, mask = self.resize_and_pad(image, Image.fromarray(union, mode="L"))
        image_tensor, mask_tensor = self.to_tensors(image, mask)
        return {
            "image": image_tensor,
            "mask": mask_tensor,
            "group_id": row["group_id"],
            "sample_id": row["sample_id"],
            "class_name": row["class_name"],
        }


def build_model(method: str):
    from experiments.BUSI_v1_clean.config_busi_v1_clean import BUSIV1CleanConfig as config
    from models.vmunet.vmunet import VMUNet

    model_cfg = dict(config.model_config)
    model = VMUNet(
        num_classes=model_cfg["num_classes"],
        input_channels=model_cfg["input_channels"],
        depths=model_cfg["depths"],
        depths_decoder=model_cfg["depths_decoder"],
        drop_path_rate=model_cfg["drop_path_rate"],
        load_ckpt_path=None,
        scan_fusion=METHOD_TO_SCAN[method],
    ).cuda()
    return model


def load_checkpoint(model: torch.nn.Module, checkpoint_path: Path) -> dict:
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    if not isinstance(checkpoint, dict) or "model_state_dict" not in checkpoint:
        raise ValueError("Expected checkpoint dictionary with model_state_dict")
    state_dict = checkpoint["model_state_dict"]
    if state_dict and next(iter(state_dict)).startswith("module."):
        state_dict = {key.removeprefix("module."): value for key, value in state_dict.items()}
    incompatible = model.load_state_dict(state_dict, strict=True)
    if incompatible.missing_keys or incompatible.unexpected_keys:
        raise RuntimeError(f"Checkpoint mismatch: {incompatible}")
    return checkpoint


def aggregate(positive: dict, normals: dict) -> dict:
    if sorted(positive) != ["benign", "malignant"] or not normals["empty_correct"]:
        raise RuntimeError("Test split must contain benign, malignant, and normal groups")
    all_dice = positive["benign"]["dice"] + positive["malignant"]["dice"]
    all_hd95 = positive["benign"]["hd95"] + positive["malignant"]["hd95"]
    all_nsd = positive["benign"]["nsd"] + positive["malignant"]["nsd"]
    return {
        "lesion_positive_mean_dice": float(np.mean(all_dice)),
        "lesion_positive_mean_hd95_px": float(np.mean(all_hd95)),
        "lesion_positive_mean_nsd_at_2px": float(np.mean(all_nsd)),
        "lesion_positive_count": len(all_dice),
        "normal_empty_mask_accuracy": float(np.mean(normals["empty_correct"])),
        "normal_mean_false_positive_area_fraction": float(np.mean(normals["false_positive_fraction"])),
        "normal_count": len(normals["empty_correct"]),
        "per_class": {
            name: {
                "mean_dice": float(np.mean(values["dice"])),
                "mean_hd95_px": float(np.mean(values["hd95"])),
                "mean_nsd_at_2px": float(np.mean(values["nsd"])),
                "count": len(values["dice"]),
            }
            for name, values in sorted(positive.items())
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=sorted(METHOD_TO_SCAN), required=True)
    parser.add_argument("--seed", type=int, choices=[42, 3407, 2026], required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--training-summary", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--protocol-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()

    repo_root = Path.cwd().resolve()
    sys.path.insert(0, str(repo_root))
    args.output_dir.mkdir(parents=True, exist_ok=False)
    private_root = args.output_dir / "private_do_not_upload"
    prediction_dir = private_root / "predictions"
    source_dir = private_root / "processed_input_and_ground_truth"
    prediction_dir.mkdir(parents=True)
    source_dir.mkdir(parents=True)

    dataset = BUSITestDataset(args.data_root, args.protocol_dir)
    loader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=0, pin_memory=True)
    model = build_model(args.method)
    checkpoint = load_checkpoint(model, args.checkpoint)
    model.eval()
    training_summary = json.loads(args.training_summary.read_text(encoding="utf-8"))
    if training_summary.get("method") != args.method or int(training_summary.get("seed")) != args.seed:
        raise RuntimeError("Training summary method/seed does not match requested evaluation")
    if checkpoint.get("protocol_hashes") != training_summary.get("protocol_hashes"):
        raise RuntimeError("Checkpoint and training summary protocol hashes do not match")

    first = dataset[0]["image"].unsqueeze(0).cuda()
    with torch.no_grad():
        for _ in range(10):
            model(first)
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()

    positive = defaultdict(lambda: defaultdict(list))
    normals = defaultdict(list)
    rows: list[dict] = []
    inference_ms: list[float] = []
    evaluation_started = time.perf_counter()
    with torch.no_grad():
        for batch in loader:
            image_gpu = batch["image"].cuda(non_blocking=True).float()
            torch.cuda.synchronize()
            started = time.perf_counter()
            probabilities = model(image_gpu)
            torch.cuda.synchronize()
            elapsed_ms = 1000.0 * (time.perf_counter() - started)
            inference_ms.append(elapsed_ms)

            pred = probabilities[0, 0].detach().cpu().numpy() >= args.threshold
            gt = batch["mask"][0, 0].numpy() >= 0.5
            group_id = batch["group_id"][0]
            sample_id = batch["sample_id"][0]
            class_name = batch["class_name"][0]
            row = {
                "method": args.method,
                "seed": args.seed,
                "group_id": group_id,
                "sample_id": sample_id,
                "class_name": class_name,
                "gt_area_fraction": float(gt.mean()),
                "pred_area_fraction": float(pred.mean()),
                "inference_ms_batch1": elapsed_ms,
                "dice": "",
                "hd95_px": "",
                "nsd_at_2px": "",
                "normal_empty_correct": "",
            }
            if gt.any():
                dice, hd95, nsd = positive_metrics(pred, gt)
                positive[class_name]["dice"].append(dice)
                positive[class_name]["hd95"].append(hd95)
                positive[class_name]["nsd"].append(nsd)
                row.update({"dice": dice, "hd95_px": hd95, "nsd_at_2px": nsd})
            else:
                empty_correct = float(not pred.any())
                false_positive_fraction = float(pred.mean())
                normals["empty_correct"].append(empty_correct)
                normals["false_positive_fraction"].append(false_positive_fraction)
                row["normal_empty_correct"] = empty_correct
            rows.append(row)

            Image.fromarray(pred.astype(np.uint8) * 255, mode="L").save(prediction_dir / f"{group_id}.png")
            if not (source_dir / f"{group_id}_input.png").exists():
                image = (batch["image"][0].numpy().transpose(1, 2, 0) * 255.0).round().clip(0, 255).astype(np.uint8)
                Image.fromarray(image, mode="RGB").save(source_dir / f"{group_id}_input.png")
                Image.fromarray(gt.astype(np.uint8) * 255, mode="L").save(source_dir / f"{group_id}_gt.png")

    metrics = aggregate(positive, normals)
    total_seconds = time.perf_counter() - evaluation_started
    timing = {
        "warmup_iterations": 10,
        "timed_image_count": len(inference_ms),
        "model_forward_mean_ms_batch1": float(np.mean(inference_ms)),
        "model_forward_std_ms_batch1": float(np.std(inference_ms, ddof=1)),
        "model_forward_median_ms_batch1": float(np.median(inference_ms)),
        "model_forward_total_seconds": float(np.sum(inference_ms) / 1000.0),
        "evaluation_end_to_end_seconds": total_seconds,
    }
    result = {
        "protocol": "busi_v1_clean",
        "method": args.method,
        "scan_fusion": METHOD_TO_SCAN[args.method],
        "seed": args.seed,
        "test_group_count": len(dataset),
        "threshold": args.threshold,
        "nsd_tolerance_pixels": NSD_TOLERANCE_PX,
        "checkpoint_path": str(args.checkpoint.resolve()),
        "checkpoint_sha256": sha256(args.checkpoint),
        "checkpoint_selected_epoch": checkpoint.get("epoch"),
        "checkpoint_validation_metrics": checkpoint.get("validation_metrics"),
        "test_list_sha256": sha256(args.protocol_dir / "splits" / "test_groups.txt"),
        "clean_manifest_sha256": sha256(args.protocol_dir / "clean_manifest.csv"),
        "evaluator_sha256": sha256(Path(__file__)),
        "model_source_sha256": sha256(repo_root / "models" / "vmunet" / "vmamba.py"),
        "model_wrapper_sha256": sha256(repo_root / "models" / "vmunet" / "vmunet.py"),
        "cuda_device": torch.cuda.get_device_name(0),
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "trainable_parameter_count": sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad),
        "peak_inference_gpu_allocated_bytes": torch.cuda.max_memory_allocated(),
        "peak_inference_gpu_reserved_bytes": torch.cuda.max_memory_reserved(),
        "flops_status": "not_measured_in_this_run; custom selective-scan FLOPs require a registered profiler",
        "timing": timing,
        "metrics": metrics,
        "training_summary": training_summary,
    }
    write_csv(args.output_dir / "per_sample_metrics.csv", list(rows[0]), rows)
    (args.output_dir / "evaluation_summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.output_dir / "FINISHED_UTC.txt").write_text(
        time.strftime("%Y-%m-%dT%H:%M:%SZ\n", time.gmtime()), encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
