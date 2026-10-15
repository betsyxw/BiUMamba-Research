"""GPU smoke test for E4_version_1 grouped-2D adaptive fusion."""

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

    fixed = SS2D(
        d_model=16, scan_fusion="grouped_2d_bidirectional_sum"
    ).to(device).eval()
    adaptive = SS2D(
        d_model=16, scan_fusion="grouped_2d_adaptive_gate_v1"
    ).to(device).eval()
    incompatible = adaptive.load_state_dict(fixed.state_dict(), strict=False)
    expected_missing = {
        "grouped_adaptive_gate.0.weight",
        "grouped_adaptive_gate.0.bias",
        "grouped_adaptive_gate.2.weight",
        "grouped_adaptive_gate.2.bias",
    }
    assert set(incompatible.missing_keys) == expected_missing
    assert incompatible.unexpected_keys == []

    equivalence_input = torch.randn(2, 8, 8, 16, device=device)
    with torch.no_grad():
        fixed_output = fixed(equivalence_input)
        adaptive_output = adaptive(equivalence_input)
    max_initial_difference = float(
        (fixed_output - adaptive_output).abs().max().cpu()
    )
    assert max_initial_difference <= 1e-5, max_initial_difference

    model = VMUNet(
        input_channels=3,
        num_classes=9,
        depths=[2, 2, 2, 2],
        depths_decoder=[2, 2, 2, 1],
        drop_path_rate=0.2,
        scan_fusion="grouped_2d_adaptive_gate_v1",
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
    gate_final_gradient_norms = []
    initial_gate_delta_max_abs = []
    active_direction_gradient_norms = []
    adaptive_parameter_count = 0
    for block in blocks:
        gate = block.grouped_adaptive_gate
        final_gradient = gate[-1].weight.grad
        assert final_gradient is not None
        assert torch.isfinite(final_gradient).all()
        gradient_norm = float(final_gradient.abs().sum().detach().cpu())
        assert gradient_norm > 0.0
        gate_final_gradient_norms.append(gradient_norm)

        delta = block._last_grouped_gate_delta
        assert delta is not None
        assert torch.isfinite(delta).all()
        delta_max_abs = float(delta.abs().max().cpu())
        assert delta_max_abs <= 1e-7, delta_max_abs
        initial_gate_delta_max_abs.append(delta_max_abs)

        adaptive_parameter_count += sum(
            parameter.numel() for parameter in gate.parameters()
        )

        direction_gradient = block.x_proj_weight.grad
        assert direction_gradient is not None
        midpoint = block.d_inner // 2
        slice_norms = {
            "horizontal_forward": float(
                direction_gradient[0, :, :midpoint].abs().sum().cpu()
            ),
            "vertical_forward": float(
                direction_gradient[1, :, midpoint:].abs().sum().cpu()
            ),
            "horizontal_backward": float(
                direction_gradient[2, :, :midpoint].abs().sum().cpu()
            ),
            "vertical_backward": float(
                direction_gradient[3, :, midpoint:].abs().sum().cpu()
            ),
        }
        assert all(value > 0.0 for value in slice_norms.values())
        active_direction_gradient_norms.append(slice_norms)

    result = {
        "variant": "E4_version_1_grouped_2d_adaptive_gate",
        "status": "PASS",
        "gate_scope": "sample_and_channel",
        "gate_alpha": 0.25,
        "initial_equivalence_max_abs_difference": max_initial_difference,
        "input_shape": list(inputs.shape),
        "output_shape": list(outputs.shape),
        "loss": float(loss.detach().cpu()),
        "block_count": len(blocks),
        "trainable_parameter_count": sum(
            parameter.numel()
            for parameter in model.parameters()
            if parameter.requires_grad
        ),
        "adaptive_gate_parameter_count": adaptive_parameter_count,
        "initial_gate_delta_max_abs": initial_gate_delta_max_abs,
        "gate_final_gradient_l1_norms": gate_final_gradient_norms,
        "active_direction_gradient_l1_norms": (
            active_direction_gradient_norms
        ),
        "peak_allocated_mib": torch.cuda.max_memory_allocated(device) / 2**20,
        "peak_reserved_mib": torch.cuda.max_memory_reserved(device) / 2**20,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
