#!/usr/bin/env python3
"""End-to-end BUSI v1 clean smoke test with test isolation."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch
from torch.utils.data import DataLoader


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=["E1", "E2_modify_2"], required=True)
    parser.add_argument("--seed", type=int, default=42)
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
    from experiments.BUSI_v1_clean.train_busi_v1_clean import build_model, controlled_hashes, sha256
    from experiments.BUSI_v1_clean.validation_busi_v1_clean import evaluate_validation

    args.work_dir.mkdir(parents=True, exist_ok=True)
    if (args.work_dir / "checkpoints").exists():
        raise FileExistsError(f"Refusing to reuse an existing smoke output: {args.work_dir}")
    set_seed(args.seed)
    train_dataset = BUSIV1CleanDataset(args.data_root, args.protocol_dir, "train")
    validation_dataset = BUSIV1CleanDataset(args.data_root, args.protocol_dir, "validation")
    train_loader = DataLoader(train_dataset, batch_size=2, shuffle=True, num_workers=0)
    validation_loader = DataLoader(validation_dataset, batch_size=32, shuffle=False, num_workers=0)
    batch = next(iter(train_loader))
    if tuple(batch["image"].shape[1:]) != (3, 224, 224):
        raise AssertionError(f"Unexpected image shape: {tuple(batch['image'].shape)}")
    if tuple(batch["mask"].shape[1:]) != (1, 224, 224):
        raise AssertionError(f"Unexpected mask shape: {tuple(batch['mask'].shape)}")
    if not set(torch.unique(batch["mask"]).tolist()).issubset({0.0, 1.0}):
        raise AssertionError("BUSI mask is not binary")

    model = build_model(config, args.method)
    optimizer = get_optimizer(config, model)
    scheduler = get_scheduler(config, optimizer)
    torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    model.train()
    images = batch["image"].cuda().float()
    masks = batch["mask"].cuda().float()
    optimizer.zero_grad()
    probabilities = model(images)
    loss = config.criterion(probabilities, masks)
    if not torch.isfinite(loss):
        raise RuntimeError(f"Non-finite smoke loss: {loss.item()}")
    loss.backward()
    gradient_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=float("inf"))
    optimizer.step()
    scheduler.step()

    metrics = evaluate_validation(model, validation_loader)
    hashes = controlled_hashes(args.protocol_dir)
    selector = ValidationCheckpointSelector(args.work_dir / "checkpoints" / "best_validation.pth")
    selector.update(
        epoch=1,
        metrics=metrics,
        model=model,
        optimizer=optimizer,
        scheduler=scheduler,
        protocol_hashes=hashes,
    )
    saved = torch.load(selector.path, map_location="cpu")
    reloaded = build_model(config, args.method)
    reloaded.module.load_state_dict(saved["model_state_dict"], strict=True)

    report = {
        "status": "PASS",
        "protocol": "busi_v1_clean",
        "method": args.method,
        "scope": "one optimization step, complete validation, best-checkpoint save and strict reload",
        "seed": args.seed,
        "train_group_count": len(train_dataset),
        "validation_group_count": len(validation_dataset),
        "test_dataset_constructed": False,
        "loss": float(loss.item()),
        "total_gradient_norm": float(gradient_norm.item()),
        "validation_untrained_smoke_only": metrics,
        "checkpoint_reload_strict": True,
        "checkpoint_sha256": sha256(selector.path),
        "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(),
        "peak_gpu_reserved_bytes": torch.cuda.max_memory_reserved(),
        "elapsed_seconds": time.perf_counter() - started,
        "input_shape": list(images.shape),
        "mask_values": sorted(torch.unique(masks).detach().cpu().tolist()),
        "output_shape": list(probabilities.shape),
        "output_min": float(probabilities.min().item()),
        "output_max": float(probabilities.max().item()),
        "protocol_hashes": hashes,
    }
    (args.work_dir / "smoke_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
