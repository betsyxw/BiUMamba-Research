"""GPU smoke test for E4_version_2_stabilized_b.

Research Author and Repository Maintainer: xuwen
Affiliation: Japan Advanced Institute of Science and Technology (JAIST)
"""

import json
import sys
import tempfile
from pathlib import Path

import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from configs.config_setting_synapse import setting_config
from engine_synapse import configure_stabilized_gate, equal_fusion_regularization
from models.vmunet.vmamba import SS2D
from models.vmunet.vmunet import VMUNet
from utils import get_optimizer


def main():
    torch.manual_seed(42)
    torch.cuda.manual_seed_all(42)
    device = torch.device("cuda")
    fixed = SS2D(
        d_model=16, scan_fusion="grouped_2d_bidirectional_sum"
    ).to(device).eval()
    stabilized = SS2D(
        d_model=16,
        scan_fusion="grouped_2d_adaptive_gate_v2_stabilized_b",
    ).to(device).eval()
    fixed_state = fixed.state_dict()
    compatible = {
        key: value for key, value in fixed_state.items()
        if key in stabilized.state_dict()
    }
    stabilized.load_state_dict(compatible, strict=False)
    assert isinstance(stabilized.grouped_adaptive_gate[0], torch.nn.LayerNorm)
    assert stabilized.grouped_gate_temperature == 4.0
    assert float(stabilized.grouped_gate_alpha.detach().cpu()) == 0.0

    sample = torch.randn(2, 8, 8, 16, device=device)
    with torch.no_grad():
        fixed_output = fixed(sample)
        stabilized_output = stabilized(sample)
    equivalence_error = float((fixed_output - stabilized_output).abs().max())
    assert equivalence_error <= 1e-5

    model = VMUNet(
        input_channels=3,
        num_classes=9,
        depths=[2, 2, 2, 2],
        depths_decoder=[2, 2, 2, 1],
        drop_path_rate=0.2,
        scan_fusion="grouped_2d_adaptive_gate_v2_stabilized_b",
    ).to(device)
    optimizer = get_optimizer(setting_config, model)
    lr_by_group = {
        group["group_name"]: group["lr"] for group in optimizer.param_groups
    }
    assert abs(lr_by_group["adaptive_gate"] - 0.1 * lr_by_group["backbone"]) < 1e-12
    epoch1 = configure_stabilized_gate(model, 1, setting_config)
    epoch6 = configure_stabilized_gate(model, 6, setting_config)
    epoch15 = configure_stabilized_gate(model, 15, setting_config)
    assert epoch1["frozen"] and epoch1["alpha"] == 0.0
    assert not epoch6["frozen"] and abs(epoch6["alpha"] - 0.025) < 1e-12
    assert abs(epoch15["alpha"] - 0.25) < 1e-12

    # Alpha is inference state, not an optimizer-only schedule value. Verify
    # that a fresh model receives the same alpha through state_dict reload.
    with tempfile.NamedTemporaryFile(suffix=".pth") as temporary:
        torch.save(model.state_dict(), temporary.name)
        reloaded = VMUNet(
            input_channels=3,
            num_classes=9,
            depths=[2, 2, 2, 2],
            depths_decoder=[2, 2, 2, 1],
            drop_path_rate=0.2,
            scan_fusion="grouped_2d_adaptive_gate_v2_stabilized_b",
        ).to(device)
        reloaded.load_state_dict(torch.load(temporary.name), strict=True)
        reloaded_alpha = sorted({
            float(module.grouped_gate_alpha.detach().cpu())
            for module in reloaded.modules()
            if hasattr(module, "grouped_gate_alpha")
        })
    assert reloaded_alpha == [0.25]
    del reloaded

    configure_stabilized_gate(model, 6, setting_config)
    model.train()
    inputs = torch.randn(1, 1, 64, 64, device=device)
    targets = torch.randint(0, 9, (1, 64, 64), device=device)
    torch.cuda.reset_peak_memory_stats(device)
    outputs = model(inputs)
    segmentation_loss = F.cross_entropy(outputs, targets)
    regularizer = equal_fusion_regularization(model)
    loss = segmentation_loss + setting_config.equal_fusion_reg_weight * regularizer
    loss.backward()
    unclipped_norm = torch.nn.utils.clip_grad_norm_(
        model.parameters(), setting_config.gradient_clip_norm
    )
    optimizer.step()
    torch.cuda.synchronize(device)
    gate_gradients = [
        float(parameter.grad.norm().detach().cpu())
        for name, parameter in model.named_parameters()
        if "grouped_adaptive_gate" in name and parameter.grad is not None
    ]
    assert gate_gradients and all(torch.isfinite(torch.tensor(gate_gradients)))
    print(json.dumps({
        "author": "xuwen",
        "variant": "E4_version_2_stabilized_b",
        "status": "PASS",
        "initial_equivalence_max_abs_difference": equivalence_error,
        "gate_temperature": 4.0,
        "equal_fusion_reg_weight": setting_config.equal_fusion_reg_weight,
        "lr_by_group": lr_by_group,
        "epoch1_gate_state": epoch1,
        "epoch6_gate_state": epoch6,
        "epoch15_gate_state": epoch15,
        "checkpoint_reloaded_alpha_values": reloaded_alpha,
        "loss": float(loss.detach().cpu()),
        "unclipped_global_grad_norm": float(unclipped_norm.detach().cpu()),
        "gate_gradient_norms": gate_gradients,
        "peak_allocated_mib": torch.cuda.max_memory_allocated(device) / 2**20,
    }, indent=2))


if __name__ == "__main__":
    main()
