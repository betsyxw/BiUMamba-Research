"""Explicit CUDA forward/backward test; never launched by release validation."""

from __future__ import annotations
import argparse
import json
from .model_registry import VARIANTS, assert_model_identity, build_model, describe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", choices=list(VARIANTS), required=True)
    parser.add_argument("--size", type=int, default=64)
    args = parser.parse_args()
    import torch
    import torch.nn.functional as F
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA selective-scan environment is required; no silent CPU fallback")
    torch.manual_seed(42)
    model = build_model(args.method, input_channels=3, num_classes=9,
                        depths=[2, 2, 2, 2], depths_decoder=[2, 2, 2, 1],
                        drop_path_rate=0.2, load_ckpt_path=None).cuda().train()
    image = torch.randn(1, 1, args.size, args.size, device="cuda")
    target = torch.randint(0, 9, (1, args.size, args.size), device="cuda")
    output = model(image)
    assert output.shape == (1, 9, args.size, args.size)
    assert torch.isfinite(output).all()
    loss = F.cross_entropy(output, target)
    loss.backward()
    grads = [p.grad for p in model.parameters() if p.grad is not None]
    assert grads and all(torch.isfinite(g).all() for g in grads)
    model.load_state_dict(model.state_dict(), strict=True)
    print(json.dumps({**describe(args.method), "blocks": assert_model_identity(model, args.method),
                      "parameter_count": sum(p.numel() for p in model.parameters()),
                      "loss": float(loss.detach()), "status": "PASS_CUDA_FORWARD_BACKWARD"}, indent=2))


if __name__ == "__main__":
    main()
