"""Case-level validation metrics used only for checkpoint selection.

Author: xuwen
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np
import torch
from scipy.ndimage import binary_erosion, distance_transform_edt


def _surface(mask):
    structure = np.ones((3,) * mask.ndim, dtype=bool)
    return np.logical_xor(mask, binary_erosion(mask, structure=structure, border_value=0))


def _dice_hd95(pred, gt):
    pred_count, gt_count = int(pred.sum()), int(gt.sum())
    if pred_count == 0 and gt_count == 0:
        return None, None
    if pred_count == 0 or gt_count == 0:
        return 0.0, float(np.linalg.norm(np.asarray(pred.shape) - 1))
    intersection = int(np.logical_and(pred, gt).sum())
    dice = 2.0 * intersection / (pred_count + gt_count)
    pred_surface, gt_surface = _surface(pred), _surface(gt)
    to_gt = distance_transform_edt(~gt_surface)[pred_surface]
    to_pred = distance_transform_edt(~pred_surface)[gt_surface]
    hd95 = float(np.percentile(np.concatenate([to_gt, to_pred]), 95))
    return float(dice), hd95


@torch.no_grad()
def evaluate_validation(model, loader, num_classes=9):
    model.eval()
    predictions = defaultdict(list)
    ground_truth = defaultdict(list)
    for batch in loader:
        images = batch["image"].cuda(non_blocking=True).float()
        logits = model(images)
        pred = torch.argmax(torch.softmax(logits, dim=1), dim=1).cpu().numpy()
        gt = batch["label"].numpy()
        for index, case in enumerate(batch["case_name"]):
            slice_index = int(batch["slice_index"][index])
            predictions[case].append((slice_index, pred[index]))
            ground_truth[case].append((slice_index, gt[index]))

    organ_dice = defaultdict(list)
    organ_hd95 = defaultdict(list)
    for case in sorted(predictions):
        pred_volume = np.stack([item[1] for item in sorted(predictions[case])])
        gt_volume = np.stack([item[1] for item in sorted(ground_truth[case])])
        for label in range(1, num_classes):
            dice, hd95 = _dice_hd95(pred_volume == label, gt_volume == label)
            if dice is not None:
                organ_dice[label].append(dice)
                organ_hd95[label].append(hd95)

    mean_dice = float(np.mean([np.mean(organ_dice[label]) for label in sorted(organ_dice)]))
    mean_hd95 = float(np.mean([np.mean(organ_hd95[label]) for label in sorted(organ_hd95)]))
    per_organ = {
        str(label): {
            "mean_dice": float(np.mean(organ_dice[label])),
            "mean_hd95_validation_voxels": float(np.mean(organ_hd95[label])),
        }
        for label in sorted(organ_dice)
    }
    return mean_dice, mean_hd95, per_organ

