#!/usr/bin/env python3
"""Real-data training and checkpoint smoke test for Synapse v2.

Author: xuwen
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import torch
from torch.utils.data import DataLoader, Subset


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--train-npz", type=Path, required=True)
    parser.add_argument("--protocol-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    os.chdir(args.repo_root)
    sys.path.insert(0, str(args.repo_root))

    from configs.config_setting_synapse import setting_config as config
    from experiments.E1_synapse_v2.checkpointing import ValidationCheckpointSelector
    from experiments.E1_synapse_v2.dataset_synapse_v2 import SynapseSlicesV2
    from models.vmunet.vmunet import VMUNet
    from utils import set_seed

    args.output_dir.mkdir(parents=True, exist_ok=True)
    set_seed(42)
    train_dataset = SynapseSlicesV2(args.train_npz, args.protocol_dir, "train")
    validation_dataset = SynapseSlicesV2(args.train_npz, args.protocol_dir, "validation")
    assert len(train_dataset) == 1798 and len(validation_dataset) == 413

    loader = DataLoader(Subset(train_dataset, [0, 1]), batch_size=2, shuffle=False)
    batch = next(iter(loader))
    model_cfg = dict(config.model_config)
    model_cfg["scan_fusion"] = "original"
    model = VMUNet(
        num_classes=model_cfg["num_classes"],
        input_channels=model_cfg["input_channels"],
        depths=model_cfg["depths"],
        depths_decoder=model_cfg["depths_decoder"],
        drop_path_rate=model_cfg["drop_path_rate"],
        load_ckpt_path=model_cfg["load_ckpt_path"],
        scan_fusion=model_cfg.get("scan_fusion", "original"),
    )
    model.load_from()
    model = model.cuda().train()
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=0.001, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.01
    )
    images = batch["image"].cuda().float()
    labels = batch["label"].cuda().long()
    optimizer.zero_grad()
    logits = model(images)
    loss = config.criterion(logits, labels)
    loss.backward()
    optimizer.step()
    assert torch.isfinite(loss)

    validation_loader = DataLoader(
        Subset(validation_dataset, [0, 1]), batch_size=2, shuffle=False
    )
    validation_batch = next(iter(validation_loader))
    model.eval()
    with torch.no_grad():
        validation_logits = model(validation_batch["image"].cuda().float())
    assert tuple(validation_logits.shape[:2]) == (2, config.num_classes)

    toy = torch.nn.Linear(2, 2).cuda()
    toy_optimizer = torch.optim.AdamW(toy.parameters(), lr=0.001)
    toy_scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(toy_optimizer, T_max=100)
    selector = ValidationCheckpointSelector(args.output_dir / "checkpoint_rule_smoke.pth")
    decisions = [
        selector.update(epoch=1, dice=0.80, hd95=20.0, model=toy,
                        optimizer=toy_optimizer, scheduler=toy_scheduler, protocol_hashes={}),
        selector.update(epoch=2, dice=0.80, hd95=18.0, model=toy,
                        optimizer=toy_optimizer, scheduler=toy_scheduler, protocol_hashes={}),
        selector.update(epoch=3, dice=0.79, hd95=1.0, model=toy,
                        optimizer=toy_optimizer, scheduler=toy_scheduler, protocol_hashes={}),
    ]
    assert decisions == [True, True, False]
    assert selector.best_epoch == 2

    result = {
        "protocol": "synapse_v2",
        "model_reference": "E1_original_four_direction_ss2d",
        "train_slice_count": len(train_dataset),
        "validation_slice_count": len(validation_dataset),
        "real_batch_forward_backward": "pass",
        "real_batch_loss": float(loss.detach().cpu()),
        "output_shape": list(logits.shape),
        "validation_batch_inference": "pass",
        "validation_output_shape": list(validation_logits.shape),
        "checkpoint_decisions": decisions,
        "selected_checkpoint_epoch": selector.best_epoch,
        "selected_checkpoint_dice": selector.best_dice,
        "selected_checkpoint_hd95": selector.best_hd95,
        "test_dataset_constructed": False,
        "augmentation_sha256": sha256(args.protocol_dir / "frozen_augmentation.py"),
    }
    (args.output_dir / "training_checkpoint_smoke.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
