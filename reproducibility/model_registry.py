"""Resolve each experiment to its own source, never a shared default branch.

Metadata inspection uses only the standard library. PyTorch and CUDA extensions
are imported only when a caller explicitly builds a model.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = {
    "E1": ("E1", "original", "Original four-direction baseline"),
    "E2": ("E2", "bidirectional_sum", "Horizontal forward/reverse only"),
    "E2_modify_1": ("E2_modify_1", "alternating_axis_sum", "Alternating axes between blocks"),
    "E2_modify_2": ("E2_modify_2", "grouped_2d_bidirectional_sum", "BiUMamba: grouped axes, fixed sum"),
    "E3": ("E3_static_fusion", "grouped_2d_static_fusion", "Grouped axes, static learned fusion"),
    "E4": ("E4_version_1", "grouped_2d_adaptive_gate_v1", "Grouped axes, adaptive residual gate v1"),
}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def describe(method):
    if method not in VARIANTS:
        raise ValueError("Unknown method {!r}; choose {}".format(method, ", ".join(VARIANTS)))
    directory, fusion, description = VARIANTS[method]
    base = Path("experiments") / directory
    paths = [base / "models/vmunet/vmamba.py", base / "models/vmunet/vmunet.py",
             base / "configs/config_setting_synapse.py"]
    for relative in paths:
        if not (ROOT / relative).is_file():
            raise FileNotFoundError(ROOT / relative)
    return {"method": method, "description": description, "scan_fusion": fusion,
            "model_source": paths[0].as_posix(), "wrapper_source": paths[1].as_posix(),
            "config_source": paths[2].as_posix(),
            "source_sha256": {p.as_posix(): sha256(ROOT / p) for p in paths},
            "historical_training_commit_recovered": False}


def model_class(method):
    """Load a unique package so six vmamba.py files cannot shadow one another."""
    info = describe(method)
    package_name = "_biumamba_release_" + method
    if package_name not in sys.modules:
        package = types.ModuleType(package_name)
        package.__path__ = [str((ROOT / info["model_source"]).parent)]
        sys.modules[package_name] = package
        try:
            for name, key in [("vmamba", "model_source"), ("vmunet", "wrapper_source")]:
                fullname = package_name + "." + name
                spec = importlib.util.spec_from_file_location(fullname, ROOT / info[key])
                if spec is None or spec.loader is None:
                    raise ImportError("Cannot load " + fullname)
                module = importlib.util.module_from_spec(spec)
                sys.modules[fullname] = module
                spec.loader.exec_module(module)
        except Exception:
            for name in [package_name + ".vmunet", package_name + ".vmamba", package_name]:
                sys.modules.pop(name, None)
            raise
    return sys.modules[package_name + ".vmunet"].VMUNet


def build_model(method, **kwargs):
    info = describe(method)
    if "scan_fusion" in kwargs and kwargs["scan_fusion"] != info["scan_fusion"]:
        raise ValueError("Wrong scan_fusion for {}: expected {}".format(method, info["scan_fusion"]))
    kwargs["scan_fusion"] = info["scan_fusion"]
    model = model_class(method)(**kwargs)
    assert_model_identity(model, method)
    return model


def assert_model_identity(model, method):
    info = describe(method)
    blocks = [m for m in model.modules() if m.__class__.__name__ == "SS2D"]
    if not blocks or any(getattr(m, "scan_fusion", None) != info["scan_fusion"] for m in blocks):
        raise RuntimeError("Model does not implement the requested scan mode: " + method)
    if method == "E2_modify_1":
        axes = {getattr(m, "scan_axis", None) for m in blocks}
        if axes != {"horizontal", "vertical"}:
            raise RuntimeError("Alternating-axis model is missing one axis")
    return len(blocks)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", choices=list(VARIANTS))
    args = parser.parse_args()
    methods = [args.method] if args.method else list(VARIANTS)
    print(json.dumps([describe(m) for m in methods], indent=2))


if __name__ == "__main__":
    main()
