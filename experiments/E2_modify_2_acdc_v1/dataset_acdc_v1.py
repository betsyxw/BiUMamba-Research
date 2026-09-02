"""Patient-isolated ACDC v1 training and validation datasets.

Research Author and Repository Maintainer: xuwen
Affiliation: Japan Advanced Institute of Science and Technology (JAIST)
"""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np
from torch.utils.data import Dataset

from research.protocols.acdc_v1.frozen_augmentation import (
    FrozenACDCAugmentation,
    to_model_tensors,
)


def _read_patients(path: Path):
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


class ACDCSlicesV1(Dataset):
    """ED/ES axial slices for train or validation; test is deliberately rejected."""

    def __init__(self, data_root: Path, protocol_dir: Path, split: str):
        if split not in {"train", "validation"}:
            raise ValueError("Training code may only construct train or validation datasets")
        self.data_root = Path(data_root)
        self.split = split
        split_name = "train_patients.txt" if split == "train" else "validation_patients.txt"
        self.patients = _read_patients(Path(protocol_dir) / "splits" / split_name)
        expected = 70 if split == "train" else 10
        if len(self.patients) != expected:
            raise ValueError(f"{split}: expected {expected} patients, found {len(self.patients)}")

        self.volumes = {}
        self.samples = []
        for patient in self.patients:
            patient_dir = self.data_root / "train" / patient
            for phase in ("ed", "es"):
                image_path = patient_dir / f"{patient}_sax_{phase}.nii.gz"
                label_path = patient_dir / f"{patient}_sax_{phase}_gt.nii.gz"
                if not image_path.is_file() or not label_path.is_file():
                    raise FileNotFoundError(f"Missing ACDC ED/ES pair: {patient} {phase}")
                image_nii, label_nii = nib.load(str(image_path)), nib.load(str(label_path))
                image = np.asarray(image_nii.dataobj)
                label = np.asarray(label_nii.dataobj)
                if image.shape != label.shape or image.shape[:2] != (192, 192):
                    raise ValueError(f"Unexpected shape for {patient} {phase}: {image.shape}/{label.shape}")
                unique = set(np.unique(label).astype(int).tolist())
                if not unique.issubset({0, 1, 2, 3}):
                    raise ValueError(f"Unexpected labels for {patient} {phase}: {sorted(unique)}")
                volume_id = f"{patient}_{phase}"
                spacing_xyz = tuple(float(v) for v in image_nii.header.get_zooms()[:3])
                self.volumes[volume_id] = (image, label, spacing_xyz)
                for z_index in range(image.shape[2]):
                    self.samples.append((volume_id, z_index))
        self.augmentation = FrozenACDCAugmentation() if split == "train" else None

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        volume_id, z_index = self.samples[index]
        image_volume, label_volume, spacing_xyz = self.volumes[volume_id]
        image = np.asarray(image_volume[:, :, z_index])
        label = np.asarray(label_volume[:, :, z_index])
        if self.augmentation is None:
            image, label = to_model_tensors(image, label)
        else:
            image, label = self.augmentation(image, label)
        return {
            "image": image,
            "label": label,
            "volume_id": volume_id,
            "slice_index": int(z_index),
            "spacing_xyz": np.asarray(spacing_xyz, dtype=np.float32),
        }
