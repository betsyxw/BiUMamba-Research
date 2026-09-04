"""Patient-isolated ACDC dataset for the FractalDB-60 low-label pilot."""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np
from torch.utils.data import Dataset

from research.protocols.acdc_v1.frozen_augmentation import (
    FrozenACDCAugmentation,
    to_model_tensors,
)


def read_patients(path: Path):
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


class ACDCLabelFractionSlices(Dataset):
    """ED/ES slices for a frozen ACDC label fraction or the fixed validation split."""

    def __init__(self, data_root: Path, protocol_dir: Path, split: str, label_fraction: int = 25):
        if split not in {"train", "validation"}:
            raise ValueError("Training code may construct only train or validation data")
        if label_fraction not in {25, 50, 100}:
            raise ValueError(f"Unsupported label fraction: {label_fraction}")
        self.data_root = Path(data_root)
        self.split = split
        train_splits = {
            25: ("train_patients_25pct.txt", 18),
            50: ("train_patients_50pct.txt", 35),
            100: ("train_patients_100pct.txt", 70),
        }
        split_name, expected = train_splits[label_fraction] if split == "train" else ("validation_patients.txt", 10)
        self.patients = read_patients(Path(protocol_dir) / "splits" / split_name)
        if len(self.patients) != expected or len(set(self.patients)) != expected:
            raise ValueError(f"{split}: expected {expected} unique patients, found {len(self.patients)}")

        self.volumes = {}
        self.samples = []
        for patient in self.patients:
            patient_dir = self.data_root / "train" / patient
            for phase in ("ed", "es"):
                image_path = patient_dir / f"{patient}_sax_{phase}.nii.gz"
                label_path = patient_dir / f"{patient}_sax_{phase}_gt.nii.gz"
                if not image_path.is_file() or not label_path.is_file():
                    raise FileNotFoundError(f"Missing ACDC pair: {patient} {phase}")
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
                self.samples.extend((volume_id, z) for z in range(image.shape[2]))
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


class ACDC25Slices(ACDCLabelFractionSlices):
    """Backward-compatible name for the original fixed 18-patient pilot dataset."""

    def __init__(self, data_root: Path, protocol_dir: Path, split: str):
        super().__init__(data_root, protocol_dir, split, label_fraction=25)
