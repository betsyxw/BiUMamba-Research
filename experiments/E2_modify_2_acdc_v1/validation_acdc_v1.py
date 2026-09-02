"""Volume-level ACDC validation metrics for checkpoint selection.

Research Author and Repository Maintainer: xuwen
Affiliation: Japan Advanced Institute of Science and Technology (JAIST)
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np
import torch
from scipy.ndimage import binary_erosion, distance_transform_edt


ORGAN_NAMES = {1: "right_ventricle", 2: "myocardium", 3: "left_ventricle"}


def _surface(mask):
    structure = np.ones((3,) * mask.ndim, dtype=bool)
    return np.logical_xor(mask, binary_erosion(mask, structure=structure, border_value=0))


def _dice_hd95_mm(pred, gt, sampling_zyx):
    pred_count, gt_count = int(pred.sum()), int(gt.sum())
    if pred_count == 0 and gt_count == 0:
        return None, None
    if pred_count == 0 or gt_count == 0:
        physical_extent = (np.asarray(pred.shape) - 1) * np.asarray(sampling_zyx)
        return 0.0, float(np.linalg.norm(physical_extent))
    intersection = int(np.logical_and(pred, gt).sum())
    dice = 2.0 * intersection / (pred_count + gt_count)
    pred_surface, gt_surface = _surface(pred), _surface(gt)
    to_gt = distance_transform_edt(~gt_surface, sampling=sampling_zyx)[pred_surface]
    to_pred = distance_transform_edt(~pred_surface, sampling=sampling_zyx)[gt_surface]
    hd95 = float(np.percentile(np.concatenate([to_gt, to_pred]), 95))
    return float(dice), hd95


@torch.no_grad()
def evaluate_validation(model, loader, num_classes=4):
    model.eval()
    predictions, ground_truth = defaultdict(list), defaultdict(list)
    spacing_by_volume = {}
    for batch in loader:
        images = batch["image"].cuda(non_blocking=True).float()
        pred = torch.argmax(model(images), dim=1).cpu().numpy()
        gt = batch["label"].numpy()
        spacing = batch["spacing_xyz"].numpy()
        for index, volume_id in enumerate(batch["volume_id"]):
            slice_index = int(batch["slice_index"][index])
            predictions[volume_id].append((slice_index, pred[index]))
            ground_truth[volume_id].append((slice_index, gt[index]))
            spacing_by_volume[volume_id] = tuple(float(v) for v in spacing[index])

    organ_dice, organ_hd95 = defaultdict(list), defaultdict(list)
    for volume_id in sorted(predictions):
        pred_volume = np.stack([v for _, v in sorted(predictions[volume_id])], axis=0)
        gt_volume = np.stack([v for _, v in sorted(ground_truth[volume_id])], axis=0)
        sx, sy, sz = spacing_by_volume[volume_id]
        for label in range(1, num_classes):
            dice, hd95 = _dice_hd95_mm(
                pred_volume == label,
                gt_volume == label,
                sampling_zyx=(sz, sy, sx),
            )
            if dice is not None:
                organ_dice[label].append(dice)
                organ_hd95[label].append(hd95)

    if sorted(organ_dice) != list(range(1, num_classes)):
        raise RuntimeError(f"Missing validation organ metrics: {sorted(organ_dice)}")
    per_organ = {
        str(label): {
            "name": ORGAN_NAMES[label],
            "mean_dice": float(np.mean(organ_dice[label])),
            "mean_hd95_mm": float(np.mean(organ_hd95[label])),
            "volume_count": len(organ_dice[label]),
        }
        for label in range(1, num_classes)
    }
    mean_dice = float(np.mean([per_organ[str(label)]["mean_dice"] for label in range(1, num_classes)]))
    mean_hd95 = float(np.mean([per_organ[str(label)]["mean_hd95_mm"] for label in range(1, num_classes)]))
    return mean_dice, mean_hd95, per_organ
