#!/usr/bin/env python3
"""Train E2_modify_2 on the fixed 18-patient ACDC pilot split."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

import torch
from torch.cuda.amp import GradScaler
from torch.utils.data import DataLoader


def sha256(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_key(key: str):
    for prefix in ("module.", "vmunet.", "backbone."):
        if key.startswith(prefix):
            key = key[len(prefix) :]
    return key


def load_audited_initialization(model, condition: str, checkpoint_path: Optional[Path]):
    if condition == "scratch":
        return {
            "condition": condition,
            "checkpoint": None,
            "matched_encoder_tensors": 0,
            "matched_encoder_parameters": 0,
            "mirrored_decoder_tensors": 0,
        }
    if checkpoint_path is None or not checkpoint_path.is_file():
        raise FileNotFoundError(f"Missing {condition} checkpoint: {checkpoint_path}")

    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    source = checkpoint.get("model", checkpoint.get("state_dict", checkpoint))
    source = {normalize_key(k): v for k, v in source.items()}
    target = model.vmunet.state_dict()
    matched = {
        k: v
        for k, v in source.items()
        if (k.startswith("patch_embed.") or k.startswith("layers."))
        and k in target
        and target[k].shape == v.shape
    }
    stage_counts = {
        stage: sum(k.startswith(f"layers.{stage}.") for k in matched)
        for stage in range(4)
    }
    if not matched or any(count == 0 for count in stage_counts.values()):
        raise RuntimeError(f"Incomplete {condition} encoder load: stages={stage_counts}")
    target.update(matched)

    mirrored = {}
    layer_map = {"layers.0": "layers_up.3", "layers.1": "layers_up.2", "layers.2": "layers_up.1", "layers.3": "layers_up.0"}
    for key, value in matched.items():
        for source_prefix, target_prefix in layer_map.items():
            if key.startswith(source_prefix):
                candidate = key.replace(source_prefix, target_prefix, 1)
                if candidate in target and target[candidate].shape == value.shape:
                    mirrored[candidate] = value
                break
    target.update(mirrored)
    model.vmunet.load_state_dict(target)
    return {
        "condition": condition,
        "checkpoint": str(checkpoint_path),
        "checkpoint_sha256": sha256(checkpoint_path),
        "source_tensor_count": len(source),
        "matched_encoder_tensors": len(matched),
        "matched_encoder_parameters": sum(v.numel() for v in matched.values()),
        "matched_encoder_stage_tensors": stage_counts,
        "mirrored_decoder_tensors": len(mirrored),
        "mirrored_decoder_parameters": sum(v.numel() for v in mirrored.values()),
    }


class Config:
    network = "vmunet"
    num_classes = 4
    input_channels = 3
    input_size_h = 192
    input_size_w = 192
    batch_size = 32
    num_workers = 0
    amp = False
    print_interval = 10
    opt = "AdamW"
    lr = 0.001
    betas = (0.9, 0.999)
    eps = 1e-8
    weight_decay = 1e-2
    amsgrad = False
    sch = "CosineAnnealingLR"
    T_max = 100
    eta_min = 0.00001
    last_epoch = -1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--condition", choices=["scratch", "imagenet", "fractaldb60"], required=True)
    parser.add_argument("--epochs", type=int, required=True)
    parser.add_argument("--seed", type=int, default=42, choices=[42])
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, default=Path("/workspace/datasets/ACDC_hf_preprocessed_train100"))
    parser.add_argument("--protocol-dir", type=Path, default=Path("research/protocols/acdc_fractaldb60_pilot_v1"))
    parser.add_argument("--imagenet-checkpoint", type=Path)
    parser.add_argument("--fractaldb60-checkpoint", type=Path)
    args = parser.parse_args()

    repo_root = Path.cwd().resolve()
    sys.path.insert(0, str(repo_root))
    from engine_synapse import train_one_epoch
    from models.vmunet.vmunet import VMUNet
    from research.protocols.acdc_fractaldb60_pilot_v1.dataset_acdc25 import ACDC25Slices
    from research.protocols.acdc_v1.checkpointing import ValidationCheckpointSelector
    from research.protocols.acdc_v1.validation_acdc_v1 import evaluate_validation
    from utils import CeDiceLoss, get_logger, get_optimizer, get_scheduler, set_seed

    Config.criterion = CeDiceLoss(Config.num_classes, [1, 1])
    Config.seed = args.seed
    Config.epochs = args.epochs
    Config.work_dir = str(args.work_dir) + "/"
    set_seed(args.seed)
    args.work_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir = args.work_dir / "checkpoints"
    checkpoint_dir.mkdir(exist_ok=True)
    logger = get_logger(f"acdc25_{args.condition}_seed{args.seed}", str(args.work_dir / "log"))

    model = VMUNet(
        num_classes=4,
        input_channels=3,
        depths=[2, 2, 2, 2],
        depths_decoder=[2, 2, 2, 1],
        drop_path_rate=0.2,
        load_ckpt_path=None,
        scan_fusion="grouped_2d_bidirectional_sum",
    )
    source_path = {
        "scratch": None,
        "imagenet": args.imagenet_checkpoint,
        "fractaldb60": args.fractaldb60_checkpoint,
    }[args.condition]
    load_report = load_audited_initialization(model, args.condition, source_path)
    (args.work_dir / "initialization_audit.json").write_text(
        json.dumps(load_report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    model = torch.nn.DataParallel(model.cuda(), device_ids=[0], output_device=0)

    train_dataset = ACDC25Slices(args.data_root, args.protocol_dir, "train")
    val_dataset = ACDC25Slices(args.data_root, args.protocol_dir, "validation")
    generator = torch.Generator().manual_seed(args.seed)
    train_loader = DataLoader(
        train_dataset,
        batch_size=Config.batch_size,
        shuffle=True,
        pin_memory=True,
        num_workers=Config.num_workers,
        generator=generator,
    )
    val_loader = DataLoader(val_dataset, batch_size=Config.batch_size, shuffle=False, pin_memory=True, num_workers=0)

    optimizer = get_optimizer(Config, model)
    scheduler = get_scheduler(Config, optimizer)
    scaler = GradScaler()
    controlled_files = [
        args.protocol_dir / "PILOT_CONFIG.json",
        args.protocol_dir / "README.md",
        args.protocol_dir / "splits" / "train_patients_25pct.txt",
        args.protocol_dir / "splits" / "validation_patients.txt",
        args.protocol_dir / "splits" / "test_patients.txt",
        Path("research/protocols/acdc_v1/frozen_augmentation.py"),
    ]
    protocol_hashes = {str(path): sha256(path) for path in controlled_files}
    (args.work_dir / "protocol_hashes.json").write_text(
        json.dumps(protocol_hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    selector = ValidationCheckpointSelector(checkpoint_dir / "best_validation.pth")
    history = []
    torch.cuda.reset_peak_memory_stats()
    started_unix, started_perf = time.time(), time.perf_counter()
    for epoch in range(1, args.epochs + 1):
        epoch_started = time.perf_counter()
        training_started = time.perf_counter()
        loss = train_one_epoch(train_loader, model, Config.criterion, optimizer, scheduler, epoch, logger, Config, scaler=scaler)
        training_seconds = time.perf_counter() - training_started
        validation_started = time.perf_counter()
        val_dice, val_hd95, per_organ = evaluate_validation(model, val_loader, Config.num_classes)
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
        logger.info("acdc_fractaldb60_pilot_validation " + json.dumps(record, sort_keys=True))
        (args.work_dir / "validation_history.json").write_text(json.dumps(history, indent=2) + "\n", encoding="utf-8")
        torch.save(
            {
                "epoch": epoch,
                "model_state_dict": model.module.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "scheduler_state_dict": scheduler.state_dict(),
                "protocol_hashes": protocol_hashes,
                "initialization_audit": load_report,
            },
            checkpoint_dir / "latest_resume.pth",
        )

    os.replace(checkpoint_dir / "latest_resume.pth", checkpoint_dir / f"final_epoch_{args.epochs}.pth")
    summary = {
        "protocol": "acdc_fractaldb60_pilot_v1",
        "condition": args.condition,
        "model_reference": "E2_modify_2_grouped_2d_bidirectional_sum",
        "seed": args.seed,
        "epochs": args.epochs,
        "train_patient_count": 18,
        "validation_patient_count": 10,
        "isolated_test_patient_count": 20,
        "train_slice_count": len(train_dataset),
        "validation_slice_count": len(val_dataset),
        "best_validation_epoch": selector.best_epoch,
        "best_validation_dice": selector.best_dice,
        "best_validation_hd95_mm": selector.best_hd95,
        "test_access_during_training": False,
        "initialization_audit": load_report,
        "protocol_hashes": protocol_hashes,
        "parameter_count": sum(p.numel() for p in model.parameters()),
        "run_started_unix": started_unix,
        "total_training_and_validation_seconds": time.perf_counter() - started_perf,
        "mean_epoch_total_seconds": sum(v["epoch_total_seconds"] for v in history) / len(history),
        "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(),
        "peak_gpu_reserved_bytes": torch.cuda.max_memory_reserved(),
        "cuda_device": torch.cuda.get_device_name(0),
    }
    (args.work_dir / "training_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
