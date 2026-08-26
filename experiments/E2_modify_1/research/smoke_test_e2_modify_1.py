"""GPU smoke test for E2_modify_1 alternating-axis bidirectional SS2D."""

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
        scan_fusion="alternating_axis_sum",
    ).to(device)
    model.train()

    blocks = [module for module in model.modules() if isinstance(module, SS2D)]
    axes = [module.scan_axis for module in blocks]
    expected_axes = [
        "horizontal" if index % 2 == 0 else "vertical"
        for index in range(len(blocks))
    ]
    assert axes == expected_axes, (axes, expected_axes)

    inputs = torch.randn(1, 1, 64, 64, device=device)
    targets = torch.randint(0, 9, (1, 64, 64), device=device)
    torch.cuda.reset_peak_memory_stats(device)
    outputs = model(inputs)
    loss = F.cross_entropy(outputs, targets)
    loss.backward()
    torch.cuda.synchronize(device)

    direction_gradients = [0.0, 0.0, 0.0, 0.0]
    checked_blocks = []
    for block in blocks:
        gradient = block.x_proj_weight.grad
        assert gradient is not None
        norms = [float(gradient[index].abs().sum()) for index in range(4)]
        active = [index for index, norm in enumerate(norms) if norm > 0.0]
        expected = [0, 2] if block.scan_axis == "horizontal" else [1, 3]
        assert active == expected, {
            "axis": block.scan_axis,
            "active": active,
            "expected": expected,
        }
        checked_blocks.append({"axis": block.scan_axis, "active": active})
        for index, norm in enumerate(norms):
            direction_gradients[index] += norm

    result = {
        "variant": "E2_modify_1_alternating_axis",
        "status": "PASS",
        "input_shape": list(inputs.shape),
        "output_shape": list(outputs.shape),
        "loss": float(loss.detach()),
        "block_count": len(blocks),
        "axis_schedule": axes,
        "checked_blocks": checked_blocks,
        "aggregate_direction_gradient_l1": direction_gradients,
        "peak_allocated_mib": torch.cuda.max_memory_allocated(device) / 2**20,
        "peak_reserved_mib": torch.cuda.max_memory_reserved(device) / 2**20,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
