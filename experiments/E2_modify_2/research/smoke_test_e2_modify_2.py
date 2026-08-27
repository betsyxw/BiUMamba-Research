"""GPU smoke test for E2_modify_2 channel-grouped 2D bidirectional SS2D."""

# Author: xuwen
# Project: BiUMamba Research

import json
import sys
from pathlib import Path

import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models.vmunet.vmamba import SS2D
from models.vmunet.vmunet import VMUNet


def main():
    torch.manual_seed(42)
    torch.cuda.manual_seed_all(42)
    device = torch.device("cuda")
    model = VMUNet(
        input_channels=3,
        num_classes=9,
        depths=[2, 2, 2, 2],
        depths_decoder=[2, 2, 2, 1],
        drop_path_rate=0.2,
        scan_fusion="grouped_2d_bidirectional_sum",
    ).to(device)
    model.train()

    inputs = torch.randn(1, 1, 64, 64, device=device)
    targets = torch.randint(0, 9, (1, 64, 64), device=device)
    torch.cuda.reset_peak_memory_stats(device)
    outputs = model(inputs)
    loss = F.cross_entropy(outputs, targets)
    loss.backward()
    torch.cuda.synchronize(device)

    blocks = [module for module in model.modules() if isinstance(module, SS2D)]
    checked_blocks = []
    for block in blocks:
        gradient = block.x_proj_weight.grad
        assert gradient is not None
        midpoint = block.d_inner // 2
        slice_norms = {
            "d0_horizontal": float(gradient[0, :, :midpoint].abs().sum()),
            "d0_inactive": float(gradient[0, :, midpoint:].abs().sum()),
            "d1_inactive": float(gradient[1, :, :midpoint].abs().sum()),
            "d1_vertical": float(gradient[1, :, midpoint:].abs().sum()),
            "d2_horizontal": float(gradient[2, :, :midpoint].abs().sum()),
            "d2_inactive": float(gradient[2, :, midpoint:].abs().sum()),
            "d3_inactive": float(gradient[3, :, :midpoint].abs().sum()),
            "d3_vertical": float(gradient[3, :, midpoint:].abs().sum()),
        }
        for name in ("d0_horizontal", "d1_vertical", "d2_horizontal", "d3_vertical"):
            assert slice_norms[name] > 0.0, (name, slice_norms)
        for name in ("d0_inactive", "d1_inactive", "d2_inactive", "d3_inactive"):
            assert slice_norms[name] == 0.0, (name, slice_norms)
        checked_blocks.append(slice_norms)

    result = {
        "variant": "E2_modify_2_grouped_2d",
        "status": "PASS",
        "input_shape": list(inputs.shape),
        "output_shape": list(outputs.shape),
        "loss": float(loss.detach()),
        "block_count": len(blocks),
        "checked_block_gradient_slices": checked_blocks,
        "peak_allocated_mib": torch.cuda.max_memory_allocated(device) / 2**20,
        "peak_reserved_mib": torch.cuda.max_memory_reserved(device) / 2**20,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
