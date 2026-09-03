"""Duplicate-cleaned BUSI train/validation dataset with test isolation."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from PIL import Image
from torch.utils.data import Dataset

from research.protocols.busi_v1_clean.frozen_augmentation import (
    FrozenBUSIAugmentation,
    resize_and_pad,
    to_tensors,
)


class BUSIV1CleanDataset(Dataset):
    def __init__(self, data_root: Path, protocol_dir: Path, split: str):
        if split not in {"train", "validation"}:
            raise ValueError("Training code may only construct train or validation BUSI datasets")
        self.data_root = Path(data_root)
        self.protocol_dir = Path(protocol_dir)
        self.split = split
        split_groups = {
            line.strip()
            for line in (self.protocol_dir / "splits" / f"{split}_groups.txt").read_text().splitlines()
            if line.strip()
        }
        with (self.protocol_dir / "clean_manifest.csv").open(encoding="utf-8", newline="") as handle:
            all_rows = list(csv.DictReader(handle))
        self.rows = [row for row in all_rows if row["group_id"] in split_groups]
        if {row["group_id"] for row in self.rows} != split_groups:
            raise RuntimeError(f"{split}: split list and clean manifest do not match")
        expected = 371 if split == "train" else 53
        if len(self.rows) != expected:
            raise RuntimeError(f"{split}: expected {expected} groups, found {len(self.rows)}")
        if any(row["split"] != split for row in self.rows):
            raise RuntimeError(f"{split}: manifest contains a conflicting split assignment")
        self.augmentation = FrozenBUSIAugmentation() if split == "train" else None

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int):
        row = self.rows[index]
        image = Image.open(self.data_root / row["image_relpath"]).convert("RGB")
        masks = [Image.open(self.data_root / relpath).convert("L") for relpath in row["mask_relpaths"].split("|")]
        union = np.zeros((image.height, image.width), dtype=np.uint8)
        for mask in masks:
            if mask.size != image.size:
                raise RuntimeError(f"Image/mask size mismatch for {row['sample_id']}")
            union |= (np.asarray(mask, dtype=np.uint8) > 0).astype(np.uint8) * 255
        mask = Image.fromarray(union, mode="L")
        image, mask = resize_and_pad(image, mask)
        if self.augmentation is None:
            image_tensor, mask_tensor = to_tensors(image, mask)
        else:
            image_tensor, mask_tensor = self.augmentation(image, mask)
        return {
            "image": image_tensor,
            "mask": mask_tensor,
            "group_id": row["group_id"],
            "sample_id": row["sample_id"],
            "class_name": row["class_name"],
            "is_normal": row["class_name"] == "normal",
        }
