#!/usr/bin/env python3
"""Frozen paired augmentation for BUSI v1 clean."""

from __future__ import annotations

import random

import numpy as np
import torch
from PIL import Image


SIZE = 224


def resize_and_pad(image: Image.Image, mask: Image.Image) -> tuple[Image.Image, Image.Image]:
    width, height = image.size
    scale = min(SIZE / width, SIZE / height)
    new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
    image = image.resize(new_size, Image.Resampling.BILINEAR)
    mask = mask.resize(new_size, Image.Resampling.NEAREST)
    offset = ((SIZE - new_size[0]) // 2, (SIZE - new_size[1]) // 2)
    image_canvas = Image.new("RGB", (SIZE, SIZE), color=(0, 0, 0))
    mask_canvas = Image.new("L", (SIZE, SIZE), color=0)
    image_canvas.paste(image, offset)
    mask_canvas.paste(mask, offset)
    return image_canvas, mask_canvas


def to_tensors(image: Image.Image, mask: Image.Image) -> tuple[torch.Tensor, torch.Tensor]:
    image_array = np.asarray(image, dtype=np.float32) / 255.0
    mask_array = (np.asarray(mask, dtype=np.uint8) > 0).astype(np.float32)
    image_tensor = torch.from_numpy(image_array.transpose(2, 0, 1).copy())
    mask_tensor = torch.from_numpy(mask_array[None, ...].copy())
    return image_tensor, mask_tensor


class FrozenBUSIAugmentation:
    def __call__(self, image: Image.Image, mask: Image.Image):
        if random.random() < 0.5:
            image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            mask = mask.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if random.random() < 0.5:
            angle = random.uniform(-15.0, 15.0)
            image = image.rotate(angle, resample=Image.Resampling.BILINEAR, fillcolor=(0, 0, 0))
            mask = mask.rotate(angle, resample=Image.Resampling.NEAREST, fillcolor=0)
        return to_tensors(image, mask)
