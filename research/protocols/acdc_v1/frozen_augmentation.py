#!/usr/bin/env python3
"""Frozen ACDC v1 training augmentation.

Research Author and Repository Maintainer: xuwen
Affiliation: Japan Advanced Institute of Science and Technology (JAIST)

Only geometric transforms are applied jointly to image and label. Validation
and test data are never augmented. Images are then scaled from uint8 to
float32 [0, 1] and repeated to three channels for the pretrained VM-UNet.
"""

from __future__ import annotations

import random

import numpy as np
import torch
from scipy import ndimage


def _random_rot_flip(image: np.ndarray, label: np.ndarray):
    k = np.random.randint(0, 4)
    axis = np.random.randint(0, 2)
    return (
        np.flip(np.rot90(image, k), axis=axis).copy(),
        np.flip(np.rot90(label, k), axis=axis).copy(),
    )


def _random_rotate(image: np.ndarray, label: np.ndarray):
    angle = int(np.random.randint(-20, 20))
    return (
        ndimage.rotate(image, angle, order=3, reshape=False, mode="constant", cval=0),
        ndimage.rotate(label, angle, order=0, reshape=False, mode="constant", cval=0),
    )


def to_model_tensors(image: np.ndarray, label: np.ndarray):
    image = np.clip(image.astype(np.float32), 0.0, 255.0) / 255.0
    image = torch.from_numpy(image).unsqueeze(0).repeat(3, 1, 1)
    label = torch.from_numpy(label.astype(np.int64))
    return image, label


class FrozenACDCAugmentation:
    """The exact training-time transform frozen for all ACDC comparisons."""

    def __call__(self, image: np.ndarray, label: np.ndarray):
        first_draw = random.random()
        if first_draw > 0.5:
            image, label = _random_rot_flip(image, label)
        elif random.random() > 0.5:
            image, label = _random_rotate(image, label)
        return to_model_tensors(image, label)
