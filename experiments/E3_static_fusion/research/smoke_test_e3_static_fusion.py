"""GPU smoke test for E3 grouped-2D static learnable fusion."""

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

    # Mathematical-equivalence check at initialization.
    fixed = SS2D(
        d_model=16, scan_fusion="grouped_2d_bidirectional_sum"
    ).to(device).eval()
    static = SS2D(
        d_model=16, scan_fusion="grouped_2d_static_fusion"
    ).to(device).eval()
    incompatible = static.load_state_dict(fixed.state_dict(), strict=False)
    assert incompatible.missing_keys == ["grouped_static_logits"]
    assert incompatible.unexpected_keys == []
    equivalence_input = torch.randn(2, 8, 8, 16, device=device)
    with torch.no_grad():
        fixed_output = fixed(equivalence_input)
        static_output = static(equivalence_input)
    max_initial_difference = float(
        (fixed_output - static_output).abs().max().cpu()
    )
    assert max_initial_difference <= 1e-5, max_initial_difference

    model = VMUNet(
        input_channels=3,
        num_classes=9,
        depths=[2, 2, 2, 2],
        depths_decoder=[2, 2, 2, 1],
        drop_path_rate=0.2,
        scan_fusion="grouped_2d_static_fusion",
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
    fusion_weights = []
    fusion_gradient_norms = []
    active_direction_gradient_norms = []
    for block in blocks:
        gradient = block.grouped_static_logits.grad
        assert gradient is not None
        assert torch.isfinite(gradient).all()
        gradient_norm = float(gradient.abs().sum().detach().cpu())
        assert gradient_norm > 0.0
        weights = 2.0 * torch.softmax(
            block.grouped_static_logits.detach().float(), dim=-1
        )
        assert torch.allclose(weights, torch.ones_like(weights))
        fusion_weights.append(weights.cpu().tolist())
        fusion_gradient_norms.append(gradient_norm)

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
        "variant": "E3_grouped_2d_static_fusion",
        "status": "PASS",
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
        "static_fusion_parameter_count": sum(
            block.grouped_static_logits.numel() for block in blocks
        ),
        "initial_fusion_weights": fusion_weights,
        "fusion_gradient_l1_norms": fusion_gradient_norms,
        "active_direction_gradient_l1_norms": (
            active_direction_gradient_norms
        ),
        "peak_allocated_mib": torch.cuda.max_memory_allocated(device) / 2**20,
        "peak_reserved_mib": torch.cuda.max_memory_reserved(device) / 2**20,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
