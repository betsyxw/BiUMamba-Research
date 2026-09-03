"""Frozen 2D BUSI validation metrics."""

from __future__ import annotations

from collections import defaultdict

import numpy as np
import torch
from scipy.ndimage import binary_erosion, distance_transform_edt


NSD_TOLERANCE_PX = 2.0


def _surface(mask: np.ndarray) -> np.ndarray:
    return np.logical_xor(mask, binary_erosion(mask, structure=np.ones((3, 3)), border_value=0))


def _positive_metrics(pred: np.ndarray, gt: np.ndarray) -> tuple[float, float, float]:
    pred_count, gt_count = int(pred.sum()), int(gt.sum())
    if gt_count == 0:
        raise ValueError("Positive-lesion metrics require a non-empty ground truth")
    if pred_count == 0:
        diagonal = float(np.linalg.norm(np.asarray(gt.shape, dtype=float) - 1.0))
        return 0.0, diagonal, 0.0
    intersection = int(np.logical_and(pred, gt).sum())
    dice = 2.0 * intersection / (pred_count + gt_count)
    pred_surface, gt_surface = _surface(pred), _surface(gt)
    pred_to_gt = distance_transform_edt(~gt_surface)[pred_surface]
    gt_to_pred = distance_transform_edt(~pred_surface)[gt_surface]
    distances = np.concatenate([pred_to_gt, gt_to_pred])
    hd95 = float(np.percentile(distances, 95))
    nsd = float(
        (np.count_nonzero(pred_to_gt <= NSD_TOLERANCE_PX) + np.count_nonzero(gt_to_pred <= NSD_TOLERANCE_PX))
        / (len(pred_to_gt) + len(gt_to_pred))
    )
    return float(dice), hd95, nsd


@torch.no_grad()
def evaluate_validation(model, loader, threshold: float = 0.5) -> dict:
    model.eval()
    positive = defaultdict(lambda: defaultdict(list))
    normal_empty_correct = []
    normal_false_positive_fraction = []
    for batch in loader:
        probabilities = model(batch["image"].cuda(non_blocking=True).float())
        predictions = probabilities[:, 0].cpu().numpy() >= threshold
        ground_truth = batch["mask"][:, 0].numpy() >= 0.5
        for index, class_name in enumerate(batch["class_name"]):
            pred, gt = predictions[index], ground_truth[index]
            if gt.any():
                dice, hd95, nsd = _positive_metrics(pred, gt)
                positive[class_name]["dice"].append(dice)
                positive[class_name]["hd95"].append(hd95)
                positive[class_name]["nsd"].append(nsd)
            else:
                normal_empty_correct.append(float(not pred.any()))
                normal_false_positive_fraction.append(float(pred.mean()))

    if sorted(positive) != ["benign", "malignant"] or not normal_empty_correct:
        raise RuntimeError("Validation split must contain benign, malignant and normal groups")
    all_dice = positive["benign"]["dice"] + positive["malignant"]["dice"]
    all_hd95 = positive["benign"]["hd95"] + positive["malignant"]["hd95"]
    all_nsd = positive["benign"]["nsd"] + positive["malignant"]["nsd"]
    return {
        "lesion_positive_mean_dice": float(np.mean(all_dice)),
        "lesion_positive_mean_hd95_px": float(np.mean(all_hd95)),
        "lesion_positive_mean_nsd_at_2px": float(np.mean(all_nsd)),
        "lesion_positive_count": len(all_dice),
        "normal_empty_mask_accuracy": float(np.mean(normal_empty_correct)),
        "normal_mean_false_positive_area_fraction": float(np.mean(normal_false_positive_fraction)),
        "normal_count": len(normal_empty_correct),
        "per_class": {
            class_name: {
                "mean_dice": float(np.mean(values["dice"])),
                "mean_hd95_px": float(np.mean(values["hd95"])),
                "mean_nsd_at_2px": float(np.mean(values["nsd"])),
                "count": len(values["dice"]),
            }
            for class_name, values in sorted(positive.items())
        },
    }
