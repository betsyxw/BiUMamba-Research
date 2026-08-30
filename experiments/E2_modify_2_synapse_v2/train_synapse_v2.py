#!/usr/bin/env python3
"""Formal Synapse v2 trainer with validation-only checkpoint selection.

Author: xuwen
Affiliation: Japan Advanced Institute of Science and Technology (JAIST)

This process never constructs or reads the official Synapse test set.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import torch
from torch.cuda.amp import GradScaler
from torch.utils.data import DataLoader


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, choices=[50, 300], required=True)
    parser.add_argument("--seed", type=int, choices=[42, 2026, 3407], required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--train-npz", type=Path, default=Path("data/Synapse/train_npz"))
    parser.add_argument(
        "--protocol-dir",
        type=Path,
        default=Path("research/protocols/synapse_v2"),
    )
    args = parser.parse_args()

    repo_root = Path.cwd().resolve()
    sys.path.insert(0, str(repo_root))
    from configs.config_setting_synapse import setting_config as config
    from engine_synapse import train_one_epoch
    from models.vmunet.vmunet import VMUNet
    from utils import get_logger, get_optimizer, get_scheduler, set_seed
    from experiments.E2_modify_2_synapse_v2.checkpointing import ValidationCheckpointSelector
    from experiments.E2_modify_2_synapse_v2.dataset_synapse_v2 import SynapseSlicesV2
    from experiments.E2_modify_2_synapse_v2.validation import evaluate_validation

    config.seed = args.seed
    config.epochs = args.epochs
    config.val_interval = 1
    config.work_dir = str(args.work_dir) + "/"
    set_seed(args.seed)

    args.work_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir = args.work_dir / "checkpoints"
    checkpoint_dir.mkdir(exist_ok=True)
    logger = get_logger("train", str(args.work_dir / "log"))

    train_dataset = SynapseSlicesV2(args.train_npz, args.protocol_dir, "train")
    val_dataset = SynapseSlicesV2(args.train_npz, args.protocol_dir, "validation")
    train_loader = DataLoader(
        train_dataset,
        batch_size=config.batch_size,
        shuffle=True,
        pin_memory=True,
        num_workers=config.num_workers,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=config.batch_size,
        shuffle=False,
        pin_memory=True,
        num_workers=config.num_workers,
    )

    model_cfg = config.model_config
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
    model = torch.nn.DataParallel(model.cuda(), device_ids=[0], output_device=0)
    optimizer = get_optimizer(config, model)
    scheduler = get_scheduler(config, optimizer)
    scaler = GradScaler()

    controlled_files = [
        args.protocol_dir / "TRAINING_CONFIG.json",
        args.protocol_dir / "SEEDS.txt",
        args.protocol_dir / "frozen_augmentation.py",
        args.protocol_dir / "splits" / "train_cases.txt",
        args.protocol_dir / "splits" / "validation_cases.txt",
        args.protocol_dir / "splits" / "test_cases.txt",
    ]
    protocol_hashes = {str(path): sha256(path) for path in controlled_files}
    selector = ValidationCheckpointSelector(checkpoint_dir / "best_validation.pth")
    history = []

    for epoch in range(1, args.epochs + 1):
        loss = train_one_epoch(
            train_loader,
            model,
            config.criterion,
            optimizer,
            scheduler,
            epoch,
            logger,
            config,
            scaler=scaler,
        )
        val_dice, val_hd95, per_organ = evaluate_validation(model, val_loader, config.num_classes)
        improved = selector.update(
            epoch=epoch,
            dice=val_dice,
            hd95=val_hd95,
            model=model,
            optimizer=optimizer,
            scheduler=scheduler,
            protocol_hashes=protocol_hashes,
        )
        record = {
            "epoch": epoch,
            "training_loss": float(loss),
            "validation_dice": val_dice,
            "validation_hd95_voxels": val_hd95,
            "checkpoint_updated": improved,
            "per_organ": per_organ,
        }
        history.append(record)
        logger.info("synapse_v2_validation " + json.dumps(record, sort_keys=True))
        (args.work_dir / "validation_history.json").write_text(
            json.dumps(history, indent=2) + "\n", encoding="utf-8"
        )
        torch.save(
            {
                "epoch": epoch,
                "model_state_dict": model.module.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "scheduler_state_dict": scheduler.state_dict(),
                "protocol_hashes": protocol_hashes,
            },
            checkpoint_dir / "latest_resume.pth",
        )

    os.replace(checkpoint_dir / "latest_resume.pth", checkpoint_dir / f"final_epoch_{args.epochs}.pth")
    summary = {
        "protocol": "synapse_v2",
        "seed": args.seed,
        "epochs": args.epochs,
        "best_validation_epoch": selector.best_epoch,
        "best_validation_dice": selector.best_dice,
        "best_validation_hd95_voxels": selector.best_hd95,
        "test_access_during_training": False,
        "protocol_hashes": protocol_hashes,
    }
    (args.work_dir / "training_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

