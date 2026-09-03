#!/usr/bin/env python3
"""Pre-train the downstream-compatible VMamba encoder on FractalDB-60."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms


def sha256(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


class VMambaEncoderClassifier(nn.Module):
    """Classification wrapper containing only the encoder used downstream."""

    def __init__(self, num_classes: int = 60):
        super().__init__()
        from models.vmunet.vmamba import VSSM

        source = VSSM(
            in_chans=3,
            num_classes=num_classes,
            depths=[2, 2, 2, 2],
            depths_decoder=[2, 2, 2, 1],
            drop_path_rate=0.2,
            scan_fusion="original",
        )
        self.patch_embed = source.patch_embed
        self.pos_drop = source.pos_drop
        self.layers = source.layers
        self.norm = nn.LayerNorm(source.num_features)
        self.head = nn.Linear(source.num_features, num_classes)

    def forward(self, x):
        x = self.pos_drop(self.patch_embed(x))
        for layer in self.layers:
            x = layer(x)
        x = self.norm(x.mean(dim=(1, 2)))
        return self.head(x)

    def encoder_state_dict(self):
        return {
            key: value.detach().cpu()
            for key, value in self.state_dict().items()
            if key.startswith("patch_embed.") or key.startswith("layers.")
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=90)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--num-workers", type=int, default=8)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-samples", type=int, default=0)
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required")
    set_seed(args.seed)
    args.work_dir.mkdir(parents=True, exist_ok=True)

    transform = transforms.Compose(
        [
            transforms.Grayscale(num_output_channels=3),
            transforms.RandomResizedCrop(224, scale=(0.7, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
        ]
    )
    dataset = datasets.ImageFolder(str(args.data_root), transform=transform)
    if len(dataset.classes) != 60:
        raise ValueError(f"Expected 60 FractalDB classes, found {len(dataset.classes)}")
    full_sample_count = len(dataset)
    if full_sample_count != 60000:
        raise ValueError(f"Expected 60000 FractalDB images, found {full_sample_count}")
    if args.max_samples:
        generator = torch.Generator().manual_seed(args.seed)
        indices = torch.randperm(len(dataset), generator=generator)[: args.max_samples].tolist()
        dataset = Subset(dataset, indices)

    loader_generator = torch.Generator().manual_seed(args.seed)
    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=True,
        persistent_workers=args.num_workers > 0,
        generator=loader_generator,
    )
    model = VMambaEncoderClassifier().cuda()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-2)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=1e-5)
    criterion = nn.CrossEntropyLoss()
    history = []
    started = time.perf_counter()
    torch.cuda.reset_peak_memory_stats()

    for epoch in range(1, args.epochs + 1):
        model.train()
        epoch_started = time.perf_counter()
        loss_total = 0.0
        correct = 0
        seen = 0
        for images, labels in loader:
            images = images.cuda(non_blocking=True)
            labels = labels.cuda(non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            logits = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            count = labels.numel()
            loss_total += float(loss.detach()) * count
            correct += int((logits.argmax(1) == labels).sum())
            seen += count
        scheduler.step()
        record = {
            "epoch": epoch,
            "loss": loss_total / seen,
            "accuracy": correct / seen,
            "learning_rate": optimizer.param_groups[0]["lr"],
            "seconds": time.perf_counter() - epoch_started,
        }
        history.append(record)
        (args.work_dir / "pretraining_history.json").write_text(
            json.dumps(history, indent=2) + "\n", encoding="utf-8"
        )
        checkpoint = {
            "model": model.encoder_state_dict(),
            "epoch": epoch,
            "optimizer": optimizer.state_dict(),
            "scheduler": scheduler.state_dict(),
            "protocol": "acdc_fractaldb60_pilot_v1",
            "source_dataset": "FractalDB-60",
        }
        torch.save(checkpoint, args.work_dir / "latest_resume.pth")
        print(json.dumps(record, sort_keys=True), flush=True)

    final_path = args.work_dir / f"fractaldb60_vmamba_encoder_epoch{args.epochs}.pth"
    (args.work_dir / "latest_resume.pth").replace(final_path)
    summary = {
        "protocol": "acdc_fractaldb60_pilot_v1",
        "seed": args.seed,
        "epochs": args.epochs,
        "full_dataset_sample_count": full_sample_count,
        "used_sample_count": len(dataset),
        "classes": len(dataset.dataset.classes) if isinstance(dataset, Subset) else len(dataset.classes),
        "total_seconds": time.perf_counter() - started,
        "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(),
        "checkpoint": str(final_path),
        "checkpoint_sha256": sha256(final_path),
        "final_loss": history[-1]["loss"],
        "final_accuracy": history[-1]["accuracy"],
        "cuda_device": torch.cuda.get_device_name(0),
        "torch_version": torch.__version__,
    }
    (args.work_dir / "pretraining_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
