"""Deterministic preprocessing for held-out Synapse training cases.

Research Author and Repository Maintainer: xuwen
Affiliation: Japan Advanced Institute of Science and Technology (JAIST)
"""

import numpy as np
import torch
from scipy.ndimage import zoom


class ValidationGenerator(object):
    """Resize the image while retaining the original-resolution label."""

    def __init__(self, output_size):
        self.output_size = output_size

    def __call__(self, sample):
        image, label = sample['image'], sample['label']
        x, y = image.shape
        if x != self.output_size[0] or y != self.output_size[1]:
            image = zoom(
                image,
                (self.output_size[0] / x, self.output_size[1] / y),
                order=3,
            )
        image = torch.from_numpy(image.astype(np.float32)).unsqueeze(0)
        label = torch.from_numpy(label.astype(np.int64))
        return {
            'image': image,
            'label': label,
            'original_shape': torch.tensor([x, y], dtype=torch.long),
        }
