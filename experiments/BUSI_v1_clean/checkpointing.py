"""Validation-only checkpoint selection for BUSI v1 clean."""

from __future__ import annotations

import os
from pathlib import Path

import torch


class ValidationCheckpointSelector:
    def __init__(self, path: Path, tolerance: float = 1e-12):
        self.path = Path(path)
        self.tolerance = float(tolerance)
        self.best_dice = float("-inf")
        self.best_hd95 = float("inf")
        self.best_epoch = None

    def update(self, *, epoch, metrics, model, optimizer, scheduler, protocol_hashes):
        dice = float(metrics["lesion_positive_mean_dice"])
        hd95 = float(metrics["lesion_positive_mean_hd95_px"])
        better = dice > self.best_dice + self.tolerance or (
            abs(dice - self.best_dice) <= self.tolerance and hd95 < self.best_hd95
        )
        if not better:
            return False
        state = {
            "epoch": int(epoch),
            "validation_metrics": dict(metrics),
            "selection_rule": "max_lesion_positive_validation_Dice_then_min_HD95_px",
            "model_state_dict": model.module.state_dict() if hasattr(model, "module") else model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scheduler_state_dict": scheduler.state_dict(),
            "protocol_hashes": dict(protocol_hashes),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        torch.save(state, temporary)
        os.replace(temporary, self.path)
        self.best_dice, self.best_hd95, self.best_epoch = dice, hd95, int(epoch)
        return True
