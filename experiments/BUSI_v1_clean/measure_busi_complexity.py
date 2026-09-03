#!/usr/bin/env python3
"""Measure supported-layer THOP MACs and add the unregistered SS2D core analytically."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
from thop import profile


METHOD_TO_SCAN = {
    "E1": "original",
    "E2_modify_2": "grouped_2d_bidirectional_sum",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=sorted(METHOD_TO_SCAN), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    repo_root = Path.cwd().resolve()
    sys.path.insert(0, str(repo_root))
    from experiments.BUSI_v1_clean.config_busi_v1_clean import BUSIV1CleanConfig as config
    from models.vmunet.vmamba import SS2D, flops_selective_scan_ref
    from models.vmunet.vmunet import VMUNet

    cfg = dict(config.model_config)
    model = VMUNet(
        num_classes=cfg["num_classes"],
        input_channels=cfg["input_channels"],
        depths=cfg["depths"],
        depths_decoder=cfg["depths_decoder"],
        drop_path_rate=cfg["drop_path_rate"],
        load_ckpt_path=None,
        scan_fusion=METHOD_TO_SCAN[args.method],
    ).cuda().eval()

    ss2d_shapes: list[dict] = []

    def capture(module, inputs):
        x = inputs[0]
        if x.ndim != 4:
            raise RuntimeError(f"Unexpected SS2D input shape: {tuple(x.shape)}")
        ss2d_shapes.append(
            {
                "batch": int(x.shape[0]),
                "height": int(x.shape[1]),
                "width": int(x.shape[2]),
                "d_model": int(module.d_model),
                "d_inner": int(module.d_inner),
                "d_state": int(module.d_state),
                "dt_rank": int(module.dt_rank),
            }
        )

    hooks = [module.register_forward_pre_hook(capture) for module in model.modules() if isinstance(module, SS2D)]
    dummy = torch.randn(1, 3, 224, 224, device="cuda")
    with torch.no_grad():
        thop_macs, thop_params = profile(model, inputs=(dummy,), verbose=False)
    for hook in hooks:
        hook.remove()

    missing_projection_macs = 0.0
    selective_scan_core_macs = 0.0
    for shape in ss2d_shapes:
        batch = shape["batch"]
        length = shape["height"] * shape["width"]
        directions = 4
        channel_per_direction = shape["d_inner"] if args.method == "E1" else shape["d_inner"] // 2
        missing_projection_macs += (
            batch
            * directions
            * length
            * channel_per_direction
            * (shape["dt_rank"] + 2 * shape["d_state"])
        )
        missing_projection_macs += (
            batch
            * directions
            * length
            * shape["dt_rank"]
            * channel_per_direction
        )
        selective_scan_core_macs += flops_selective_scan_ref(
            B=batch,
            L=length,
            D=directions * channel_per_direction,
            N=shape["d_state"],
            with_D=True,
            with_Z=False,
            with_Group=True,
        )

    augmented_macs = float(thop_macs + missing_projection_macs + selective_scan_core_macs)
    result = {
        "method": args.method,
        "scan_fusion": METHOD_TO_SCAN[args.method],
        "input_shape": [1, 3, 224, 224],
        "parameter_count": int(sum(p.numel() for p in model.parameters())),
        "thop_parameter_count": int(thop_params),
        "thop_supported_layer_macs": float(thop_macs),
        "analytical_unregistered_projection_macs": float(missing_projection_macs),
        "analytical_selective_scan_core_macs": float(selective_scan_core_macs),
        "augmented_total_macs": augmented_macs,
        "augmented_total_flops_two_per_mac": 2.0 * augmented_macs,
        "ss2d_call_count": len(ss2d_shapes),
        "status": "approximate: THOP supported layers plus analytical einsum and selective-scan core; elementwise and normalization operations are not fully counted",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
