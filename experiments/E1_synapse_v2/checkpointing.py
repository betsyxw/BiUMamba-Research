"""Validation Dice/HD95 checkpoint selection for Synapse v2.

Author: xuwen
"""

from __future__ import annotations

import os
from pathlib import Path

import torch


class ValidationCheckpointSelector:
    def __init__(self, path: Path, dice_tolerance: float = 1e-12):
        self.path = Path(path)
        self.dice_tolerance = float(dice_tolerance)
        self.best_dice = float("-inf")
        self.best_hd95 = float("inf")
        self.best_epoch = None

    def is_better(self, dice: float, hd95: float) -> bool:
        if dice > self.best_dice + self.dice_tolerance:
            return True
        return abs(dice - self.best_dice) <= self.dice_tolerance and hd95 < self.best_hd95

    def update(self, *, epoch, dice, hd95, model, optimizer, scheduler, protocol_hashes):
        dice, hd95 = float(dice), float(hd95)
        if not self.is_better(dice, hd95):
            return False
        state = {
            "epoch": int(epoch),
            "validation_dice": dice,
            "validation_hd95": hd95,
            "selection_rule": "max_validation_dice_then_min_validation_hd95",
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

