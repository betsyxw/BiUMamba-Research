#!/usr/bin/env python3
"""Formal ACDC v1 E1 trainer with validation-only checkpoint selection.

Research Author and Repository Maintainer: xuwen
Affiliation: Japan Advanced Institute of Science and Technology (JAIST)

The test-patient list is controlled and hashed, but it is never read by this
program and the test dataset cannot be constructed here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
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


def build_model(config):
    from models.vmunet.vmunet import VMUNet

    model_cfg = dict(config.model_config)
    model = VMUNet(
        num_classes=model_cfg["num_classes"],
        input_channels=model_cfg["input_channels"],
        depths=model_cfg["depths"],
        depths_decoder=model_cfg["depths_decoder"],
        drop_path_rate=model_cfg["drop_path_rate"],
        load_ckpt_path=model_cfg["load_ckpt_path"],
        scan_fusion="grouped_2d_bidirectional_sum",
    )
    model.load_from()
    return torch.nn.DataParallel(model.cuda(), device_ids=[0], output_device=0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, choices=[50, 300], required=True)
    parser.add_argument("--seed", type=int, choices=[42, 2026, 3407], required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("/workspace/datasets/ACDC_hf_preprocessed_train100"),
    )
    parser.add_argument("--protocol-dir", type=Path, default=Path("research/protocols/acdc_v1"))
    args = parser.parse_args()

    repo_root = Path.cwd().resolve()
    sys.path.insert(0, str(repo_root))
    from engine_synapse import train_one_epoch
    from utils import get_logger, get_optimizer, get_scheduler, set_seed
    from experiments.E2_modify_2_acdc_v1.checkpointing import ValidationCheckpointSelector
    from experiments.E2_modify_2_acdc_v1.config_acdc_v1 import ACDCV1Config as config
    from experiments.E2_modify_2_acdc_v1.dataset_acdc_v1 import ACDCSlicesV1
    from experiments.E2_modify_2_acdc_v1.validation_acdc_v1 import evaluate_validation

    config.seed, config.epochs = args.seed, args.epochs
    config.work_dir = str(args.work_dir) + "/"
    set_seed(args.seed)
    args.work_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir = args.work_dir / "checkpoints"
    checkpoint_dir.mkdir(exist_ok=True)
    logger = get_logger(f"train_acdc_v1_seed{args.seed}", str(args.work_dir / "log"))

    train_dataset = ACDCSlicesV1(args.data_root, args.protocol_dir, "train")
    val_dataset = ACDCSlicesV1(args.data_root, args.protocol_dir, "validation")
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

    model = build_model(config)
    parameter_count = sum(p.numel() for p in model.parameters())
    trainable_parameter_count = sum(p.numel() for p in model.parameters() if p.requires_grad)
    optimizer = get_optimizer(config, model)
    scheduler = get_scheduler(config, optimizer)
    scaler = GradScaler()

    controlled_files = [
        args.protocol_dir / "TRAINING_CONFIG.json",
        args.protocol_dir / "SEEDS.txt",
        args.protocol_dir / "PREPROCESSING_POLICY.md",
        args.protocol_dir / "frozen_augmentation.py",
        args.protocol_dir / "splits" / "split_manifest.csv",
        args.protocol_dir / "splits" / "train_patients.txt",
        args.protocol_dir / "splits" / "validation_patients.txt",
        args.protocol_dir / "splits" / "test_patients.txt",
    ]
    protocol_hashes = {str(path): sha256(path) for path in controlled_files}
    (args.work_dir / "protocol_hashes.json").write_text(
        json.dumps(protocol_hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    selector = ValidationCheckpointSelector(checkpoint_dir / "best_validation.pth")
    history = []
    torch.cuda.reset_peak_memory_stats()
    run_started_at, run_started_perf = time.time(), time.perf_counter()

    for epoch in range(1, args.epochs + 1):
        epoch_started = time.perf_counter()
        training_started = time.perf_counter()
        loss = train_one_epoch(
            train_loader, model, config.criterion, optimizer, scheduler, epoch, logger, config, scaler=scaler
        )
        training_seconds = time.perf_counter() - training_started
        validation_started = time.perf_counter()
        val_dice, val_hd95, per_organ = evaluate_validation(model, val_loader, config.num_classes)
        validation_seconds = time.perf_counter() - validation_started
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
            "validation_hd95_mm": val_hd95,
            "checkpoint_updated": improved,
            "per_organ": per_organ,
            "training_seconds": training_seconds,
            "validation_seconds": validation_seconds,
            "epoch_total_seconds": time.perf_counter() - epoch_started,
            "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(),
            "peak_gpu_reserved_bytes": torch.cuda.max_memory_reserved(),
        }
        history.append(record)
        logger.info("acdc_v1_validation " + json.dumps(record, sort_keys=True))
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
    total_seconds = time.perf_counter() - run_started_perf
    summary = {
        "protocol": "acdc_v1",
        "model_reference": "E2_modify_2_grouped_2d_bidirectional_sum",
        "dataset_source_limitation": "HF derivative uses LV-mask-centred crop; see PREPROCESSING_POLICY.md",
        "seed": args.seed,
        "epochs": args.epochs,
        "train_patient_count": 70,
        "validation_patient_count": 10,
        "test_patient_count": 20,
        "train_slice_count": len(train_dataset),
        "validation_slice_count": len(val_dataset),
        "best_validation_epoch": selector.best_epoch,
        "best_validation_dice": selector.best_dice,
        "best_validation_hd95_mm": selector.best_hd95,
        "test_access_during_training": False,
        "protocol_hashes": protocol_hashes,
        "parameter_count": parameter_count,
        "trainable_parameter_count": trainable_parameter_count,
        "run_started_unix": run_started_at,
        "total_training_and_validation_seconds": total_seconds,
        "mean_epoch_total_seconds": sum(v["epoch_total_seconds"] for v in history) / len(history),
        "mean_training_seconds_per_epoch": sum(v["training_seconds"] for v in history) / len(history),
        "mean_validation_seconds_per_epoch": sum(v["validation_seconds"] for v in history) / len(history),
        "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(),
        "peak_gpu_reserved_bytes": torch.cuda.max_memory_reserved(),
    }
    (args.work_dir / "training_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
