#!/usr/bin/env python3
"""End-to-end ACDC v1 E1 smoke test (no formal training claim).

Research Author and Repository Maintainer: xuwen
Affiliation: Japan Advanced Institute of Science and Technology (JAIST)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument(
        "--data-root", type=Path, default=Path("/workspace/datasets/ACDC_hf_preprocessed_train100")
    )
    parser.add_argument("--protocol-dir", type=Path, default=Path("research/protocols/acdc_v1"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    repo_root = Path.cwd().resolve()
    sys.path.insert(0, str(repo_root))
    from utils import get_optimizer, get_scheduler, set_seed
    from experiments.E2_modify_2_acdc_v1.checkpointing import ValidationCheckpointSelector
    from experiments.E2_modify_2_acdc_v1.config_acdc_v1 import ACDCV1Config as config
    from experiments.E2_modify_2_acdc_v1.dataset_acdc_v1 import ACDCSlicesV1
    from experiments.E2_modify_2_acdc_v1.train_acdc_v1 import build_model
    from experiments.E2_modify_2_acdc_v1.validation_acdc_v1 import evaluate_validation

    args.work_dir.mkdir(parents=True, exist_ok=True)
    set_seed(args.seed)
    train_dataset = ACDCSlicesV1(args.data_root, args.protocol_dir, "train")
    val_dataset = ACDCSlicesV1(args.data_root, args.protocol_dir, "validation")
    train_loader = DataLoader(train_dataset, batch_size=2, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=16, shuffle=False, num_workers=0)

    first = next(iter(train_loader))
    label_values = sorted(torch.unique(first["label"]).tolist())
    if first["image"].shape[1:] != (3, 192, 192):
        raise AssertionError(f"Unexpected input shape: {tuple(first['image'].shape)}")
    if min(label_values) < 0 or max(label_values) > 3:
        raise AssertionError(f"Unexpected labels: {label_values}")

    model = build_model(config)
    optimizer = get_optimizer(config, model)
    scheduler = get_scheduler(config, optimizer)
    torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    model.train()
    images = first["image"].cuda().float()
    labels = first["label"].cuda().long()
    optimizer.zero_grad()
    logits = model(images)
    loss = config.criterion(logits, labels)
    if not torch.isfinite(loss):
        raise RuntimeError(f"Non-finite loss: {loss.item()}")
    loss.backward()
    grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=float("inf"))
    optimizer.step()
    scheduler.step()

    val_dice, val_hd95, per_organ = evaluate_validation(model, val_loader, config.num_classes)
    controlled = [
        args.protocol_dir / "TRAINING_CONFIG.json",
        args.protocol_dir / "SEEDS.txt",
        args.protocol_dir / "PREPROCESSING_POLICY.md",
        args.protocol_dir / "frozen_augmentation.py",
        args.protocol_dir / "splits" / "split_manifest.csv",
        args.protocol_dir / "splits" / "train_patients.txt",
        args.protocol_dir / "splits" / "validation_patients.txt",
        args.protocol_dir / "splits" / "test_patients.txt",
    ]
    protocol_hashes = {str(path): file_sha256(path) for path in controlled}
    selector = ValidationCheckpointSelector(args.work_dir / "checkpoints" / "best_validation.pth")
    selector.update(
        epoch=1,
        dice=val_dice,
        hd95=val_hd95,
        model=model,
        optimizer=optimizer,
        scheduler=scheduler,
        protocol_hashes=protocol_hashes,
    )
    saved = torch.load(selector.path, map_location="cpu")
    reloaded = build_model(config)
    reloaded.module.load_state_dict(saved["model_state_dict"], strict=True)

    # Save a non-patient-identifying numerical preview for label/prediction verification.
    preview = {
        "input_min": float(images.min().item()),
        "input_max": float(images.max().item()),
        "input_shape": list(images.shape),
        "label_values": label_values,
        "logits_shape": list(logits.shape),
        "prediction_values": sorted(torch.unique(torch.argmax(logits.detach(), dim=1)).cpu().tolist()),
    }
    report = {
        "status": "PASS",
        "scope": "one optimization step plus complete validation and checkpoint reload",
        "seed": args.seed,
        "train_patient_count": 70,
        "validation_patient_count": 10,
        "test_dataset_constructed": False,
        "train_slice_count": len(train_dataset),
        "validation_slice_count": len(val_dataset),
        "loss": float(loss.item()),
        "total_gradient_norm": float(grad_norm.item()),
        "validation_dice_untrained_smoke_only": val_dice,
        "validation_hd95_mm_untrained_smoke_only": val_hd95,
        "per_organ_untrained_smoke_only": per_organ,
        "checkpoint_reload_strict": True,
        "checkpoint_sha256": file_sha256(selector.path),
        "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(),
        "peak_gpu_reserved_bytes": torch.cuda.max_memory_reserved(),
        "elapsed_seconds": time.perf_counter() - started,
        "preview": preview,
        "protocol_hashes": protocol_hashes,
    }
    (args.work_dir / "smoke_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
