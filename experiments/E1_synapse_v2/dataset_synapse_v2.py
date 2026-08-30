"""Case-isolated Synapse training and validation datasets.

Author: xuwen
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import numpy as np
import torch
from scipy.ndimage import zoom
from torch.utils.data import Dataset

from research.protocols.synapse_v2.frozen_augmentation import FrozenRandomGenerator


SLICE_RE = re.compile(r"^(case\d+)_slice(\d+)$")


def _read_cases(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def _expected_counts(path: Path) -> dict[str, int]:
    with path.open(newline="") as handle:
        return {row["case_id"]: int(row["slice_count"]) for row in csv.DictReader(handle)}


class SynapseSlicesV2(Dataset):
    def __init__(self, npz_dir: Path, protocol_dir: Path, split: str, output_size=(224, 224)):
        if split not in {"train", "validation"}:
            raise ValueError("Training code may only construct train or validation datasets")
        self.npz_dir = Path(npz_dir)
        self.split = split
        self.output_size = tuple(output_size)
        split_file = "train_cases.txt" if split == "train" else "validation_cases.txt"
        cases = _read_cases(protocol_dir / "splits" / split_file)
        expected = _expected_counts(protocol_dir / "splits" / "EXPECTED_SLICE_COUNTS.csv")
        self.samples: list[tuple[Path, str, int]] = []
        for case in cases:
            files = sorted(self.npz_dir.glob(f"{case}_slice*.npz"))
            if len(files) != expected[case]:
                raise ValueError(f"{case}: expected {expected[case]} slices, found {len(files)}")
            for path in files:
                match = SLICE_RE.match(path.stem)
                if not match:
                    raise ValueError(f"Unexpected Synapse slice name: {path.name}")
                self.samples.append((path, case, int(match.group(2))))
        expected_total = 1798 if split == "train" else 413
        if len(self.samples) != expected_total:
            raise ValueError(f"{split}: expected {expected_total} slices, found {len(self.samples)}")
        self.augmentation = FrozenRandomGenerator(self.output_size) if split == "train" else None

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        path, case, slice_index = self.samples[index]
        data = np.load(path)
        image, label = data["image"], data["label"]
        if self.augmentation is not None:
            sample = self.augmentation({"image": image, "label": label})
        else:
            x, y = image.shape
            if (x, y) != self.output_size:
                image = zoom(image, (self.output_size[0] / x, self.output_size[1] / y), order=3)
                label = zoom(label, (self.output_size[0] / x, self.output_size[1] / y), order=0)
            sample = {
                "image": torch.from_numpy(image.astype(np.float32)).unsqueeze(0),
                "label": torch.from_numpy(label.astype(np.int64)),
            }
        sample.update({"case_name": case, "slice_index": slice_index})
        return sample

