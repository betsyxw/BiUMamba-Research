#!/usr/bin/env python3
"""Formal BUSI v1 clean trainer for E1 and E2_modify_2."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader


METHOD_TO_SCAN = {
    "E1": "original",
    "E2_modify_2": "grouped_2d_bidirectional_sum",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def controlled_hashes(protocol_dir: Path) -> dict:
    files = [
        protocol_dir / "TRAINING_CONFIG.json",
        protocol_dir / "SEEDS.txt",
        protocol_dir / "PREPROCESSING_POLICY.md",
        protocol_dir / "frozen_augmentation.py",
        protocol_dir / "clean_manifest.csv",
        protocol_dir / "excluded_groups.csv",
        protocol_dir / "dataset_comment_list.csv",
        protocol_dir / "splits" / "train_groups.txt",
        protocol_dir / "splits" / "validation_groups.txt",
        protocol_dir / "splits" / "test_groups.txt",
    ]
    return {str(path): sha256(path) for path in files}


def build_model(config, method: str):
    from models.vmunet.vmunet import VMUNet

    model_cfg = dict(config.model_config)
    model = VMUNet(
        num_classes=model_cfg["num_classes"],
        input_channels=model_cfg["input_channels"],
        depths=model_cfg["depths"],
        depths_decoder=model_cfg["depths_decoder"],
        drop_path_rate=model_cfg["drop_path_rate"],
        load_ckpt_path=model_cfg["load_ckpt_path"],
        scan_fusion=METHOD_TO_SCAN[method],
    )
    model.load_from()
    return torch.nn.DataParallel(model.cuda(), device_ids=[0], output_device=0)


def train_one_epoch(model, loader, criterion, optimizer, epoch: int, print_interval: int) -> float:
    model.train()
    losses = []
    for iteration, batch in enumerate(loader):
        images = batch["image"].cuda(non_blocking=True).float()
        masks = batch["mask"].cuda(non_blocking=True).float()
        optimizer.zero_grad()
        probabilities = model(images)
        loss = criterion(probabilities, masks)
        if not torch.isfinite(loss):
            raise RuntimeError(f"Non-finite loss at epoch={epoch}, iteration={iteration}: {loss.item()}")
        loss.backward()
        optimizer.step()
        losses.append(float(loss.item()))
        if iteration % print_interval == 0:
            print(
                f"train epoch={epoch} iter={iteration}/{len(loader)} "
                f"loss={np.mean(losses):.6f} lr={optimizer.param_groups[0]['lr']:.8g}",
                flush=True,
            )
    return float(np.mean(losses))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=sorted(METHOD_TO_SCAN), required=True)
    parser.add_argument("--epochs", type=int, choices=[300], required=True)
    parser.add_argument("--seed", type=int, choices=[42, 3407, 2026], required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--protocol-dir", type=Path, required=True)
    args = parser.parse_args()

    repo_root = Path.cwd().resolve()
    sys.path.insert(0, str(repo_root))
    from utils import get_optimizer, get_scheduler, set_seed
    from experiments.BUSI_v1_clean.checkpointing import ValidationCheckpointSelector
    from experiments.BUSI_v1_clean.config_busi_v1_clean import BUSIV1CleanConfig as config
    from experiments.BUSI_v1_clean.dataset_busi_v1_clean import BUSIV1CleanDataset
    from experiments.BUSI_v1_clean.validation_busi_v1_clean import evaluate_validation

    config.seed, config.epochs = args.seed, args.epochs
    set_seed(args.seed)
    args.work_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir = args.work_dir / "checkpoints"
    if checkpoint_dir.exists():
        raise FileExistsError(f"Refusing to reuse an existing training output: {args.work_dir}")
    checkpoint_dir.mkdir()

    train_dataset = BUSIV1CleanDataset(args.data_root, args.protocol_dir, "train")
    validation_dataset = BUSIV1CleanDataset(args.data_root, args.protocol_dir, "validation")
    train_generator = torch.Generator().manual_seed(args.seed)
    train_loader = DataLoader(
        train_dataset,
        batch_size=config.batch_size,
        shuffle=True,
        generator=train_generator,
        pin_memory=True,
        num_workers=config.num_workers,
    )
    validation_loader = DataLoader(
        validation_dataset,
        batch_size=config.batch_size,
        shuffle=False,
        pin_memory=True,
        num_workers=config.num_workers,
    )

    model = build_model(config, args.method)
    parameter_count = sum(parameter.numel() for parameter in model.parameters())
    trainable_parameter_count = sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)
    optimizer = get_optimizer(config, model)
    scheduler = get_scheduler(config, optimizer)
    hashes = controlled_hashes(args.protocol_dir)
    (args.work_dir / "protocol_hashes.json").write_text(
        json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    selector = ValidationCheckpointSelector(checkpoint_dir / "best_validation.pth")
    history = []
    torch.cuda.reset_peak_memory_stats()
    started_unix, started_perf = time.time(), time.perf_counter()

    for epoch in range(1, args.epochs + 1):
        epoch_started = time.perf_counter()
        training_started = time.perf_counter()
        training_loss = train_one_epoch(model, train_loader, config.criterion, optimizer, epoch, config.print_interval)
        training_seconds = time.perf_counter() - training_started
        scheduler.step()
        validation_started = time.perf_counter()
        metrics = evaluate_validation(model, validation_loader)
        validation_seconds = time.perf_counter() - validation_started
        improved = selector.update(
            epoch=epoch,
            metrics=metrics,
            model=model,
            optimizer=optimizer,
            scheduler=scheduler,
            protocol_hashes=hashes,
        )
        record = {
            "epoch": epoch,
            "training_loss": training_loss,
            "learning_rate": float(optimizer.param_groups[0]["lr"]),
            "checkpoint_updated": improved,
            "validation": metrics,
            "training_seconds": training_seconds,
            "validation_seconds": validation_seconds,
            "epoch_total_seconds": time.perf_counter() - epoch_started,
            "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(),
            "peak_gpu_reserved_bytes": torch.cuda.max_memory_reserved(),
        }
        history.append(record)
        print("busi_v1_clean_validation " + json.dumps(record, sort_keys=True), flush=True)
        (args.work_dir / "validation_history.json").write_text(
            json.dumps(history, indent=2) + "\n", encoding="utf-8"
        )
        torch.save(
            {
                "epoch": epoch,
                "method": args.method,
                "model_state_dict": model.module.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "scheduler_state_dict": scheduler.state_dict(),
                "protocol_hashes": hashes,
            },
            checkpoint_dir / "latest_resume.pth",
        )

    os.replace(checkpoint_dir / "latest_resume.pth", checkpoint_dir / f"final_epoch_{args.epochs}.pth")
    elapsed = time.perf_counter() - started_perf
    summary = {
        "protocol": "busi_v1_clean",
        "method": args.method,
        "scan_fusion": METHOD_TO_SCAN[args.method],
        "seed": args.seed,
        "epochs": args.epochs,
        "train_group_count": len(train_dataset),
        "validation_group_count": len(validation_dataset),
        "test_group_count": 105,
        "test_dataset_constructed": False,
        "best_validation_epoch": selector.best_epoch,
        "best_validation_lesion_positive_dice": selector.best_dice,
        "best_validation_lesion_positive_hd95_px": selector.best_hd95,
        "parameter_count": parameter_count,
        "trainable_parameter_count": trainable_parameter_count,
        "run_started_unix": started_unix,
        "total_training_and_validation_seconds": elapsed,
        "mean_epoch_total_seconds": float(np.mean([row["epoch_total_seconds"] for row in history])),
        "mean_training_seconds_per_epoch": float(np.mean([row["training_seconds"] for row in history])),
        "mean_validation_seconds_per_epoch": float(np.mean([row["validation_seconds"] for row in history])),
        "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(),
        "peak_gpu_reserved_bytes": torch.cuda.max_memory_reserved(),
        "protocol_hashes": hashes,
    }
    (args.work_dir / "training_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
