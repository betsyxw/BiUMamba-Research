#!/usr/bin/env python3
"""Strict same-GPU inference, FLOPs estimate, and deployable state-dict audit.

Runs one dataset/method pair per process so Python module caches cannot mix the
E1 and E2_modify_2 repository implementations.
"""

from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import h5py
import nibabel as nib
import numpy as np
import torch
from PIL import Image
from scipy.ndimage import zoom
from thop import profile


OUTPUT_ROOT = Path("/workspace/paper_final_results_v2/efficiency/unified_benchmark_20260906")
DATA_ROOT = Path("/workspace/datasets")
FINAL_ROOT = Path("/workspace/paper_final_results_v1")

SPECS = {
    ("Synapse", "E1"): {
        "repo": Path("/workspace/repos/VM-UNet_E1_synapse_v2"),
        "checkpoint": FINAL_ROOT / "synapse/training_runs/E1_seed42/checkpoints/best_validation.pth",
        "num_classes": 9,
        "input_size": (224, 224),
        "scan_fusion": "original",
    },
    ("Synapse", "E2_modify_2"): {
        "repo": Path("/workspace/repos/VM-UNet_E2_modify_2_synapse_v2"),
        "checkpoint": FINAL_ROOT / "synapse/training_runs/E2_modify_2_seed42/checkpoints/best_validation.pth",
        "num_classes": 9,
        "input_size": (224, 224),
        "scan_fusion": "grouped_2d_bidirectional_sum",
    },
    ("ACDC", "E1"): {
        "repo": Path("/workspace/repos/VM-UNet_E1_ACDC_v1"),
        "checkpoint": FINAL_ROOT / "acdc/training_runs/e1_seed42/checkpoints/best_validation.pth",
        "num_classes": 4,
        "input_size": (192, 192),
        "scan_fusion": "original",
    },
    ("ACDC", "E2_modify_2"): {
        "repo": Path("/workspace/repos/VM-UNet_E2_modify_2_ACDC_v1"),
        "checkpoint": FINAL_ROOT / "acdc/training_runs/e2_modify_2_seed42/checkpoints/best_validation.pth",
        "num_classes": 4,
        "input_size": (192, 192),
        "scan_fusion": "grouped_2d_bidirectional_sum",
    },
    ("BUSI", "E1"): {
        "repo": Path("/workspace/repos/BUSI_v1_clean_exec_runpod"),
        "checkpoint": FINAL_ROOT / "busi/training_runs/e1_seed42/checkpoints/best_validation.pth",
        "num_classes": 1,
        "input_size": (224, 224),
        "scan_fusion": "original",
    },
    ("BUSI", "E2_modify_2"): {
        "repo": Path("/workspace/repos/BUSI_v1_clean_exec_runpod"),
        "checkpoint": FINAL_ROOT / "busi/training_runs/e2_modify_2_seed42/checkpoints/best_validation.pth",
        "num_classes": 1,
        "input_size": (224, 224),
        "scan_fusion": "grouped_2d_bidirectional_sum",
    },
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tensor_sha256(tensor: torch.Tensor) -> str:
    array = tensor.detach().cpu().contiguous().numpy()
    return hashlib.sha256(array.tobytes()).hexdigest()


def read_nonempty_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_synapse_input(input_size: tuple[int, int]) -> tuple[torch.Tensor, dict]:
    source = DATA_ROOT / "Synapse/test_vol_h5/case0001.npy.h5"
    with h5py.File(source, "r") as handle:
        image = handle["image"][:]
    z_index = int(image.shape[0] // 2)
    image_slice = np.asarray(image[z_index], dtype=np.float32)
    original_shape = tuple(int(v) for v in image_slice.shape)
    if original_shape != input_size:
        image_slice = zoom(
            image_slice,
            (input_size[0] / original_shape[0], input_size[1] / original_shape[1]),
            order=3,
        )
    tensor = torch.from_numpy(np.ascontiguousarray(image_slice)).unsqueeze(0).unsqueeze(0)
    tensor = tensor.repeat(1, 3, 1, 1).float()
    return tensor, {
        "source_file": str(source),
        "source_file_sha256": file_sha256(source),
        "case": "case0001",
        "slice_index": z_index,
        "original_shape": list(original_shape),
        "preprocessing": "cubic resize to 224x224; repeat grayscale channel to 3 channels",
    }


def load_acdc_input(input_size: tuple[int, int]) -> tuple[torch.Tensor, dict]:
    split_file = FINAL_ROOT / "acdc/frozen_protocol/splits/test_patients.txt"
    patient = read_nonempty_lines(split_file)[0]
    source = DATA_ROOT / f"ACDC_hf_preprocessed_train100/train/{patient}/{patient}_sax_ed.nii.gz"
    image = np.asarray(nib.load(str(source)).dataobj)
    z_index = int(image.shape[2] // 2)
    image_slice = np.asarray(image[:, :, z_index], dtype=np.float32)
    if tuple(image_slice.shape) != input_size:
        raise RuntimeError(f"Unexpected ACDC shape: {image_slice.shape}; expected {input_size}")
    image_slice = np.clip(image_slice, 0.0, 255.0) / 255.0
    tensor = torch.from_numpy(np.ascontiguousarray(image_slice)).unsqueeze(0).repeat(3, 1, 1).unsqueeze(0)
    return tensor.float(), {
        "source_file": str(source),
        "source_file_sha256": file_sha256(source),
        "patient": patient,
        "phase": "ed",
        "slice_index": z_index,
        "original_shape": [int(v) for v in image.shape],
        "preprocessing": "clip uint8 range to [0,255], divide by 255, repeat to 3 channels",
    }


def resize_and_pad_busi(image: Image.Image, size: int = 224) -> Image.Image:
    width, height = image.size
    scale = min(size / width, size / height)
    new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
    image = image.resize(new_size, Image.Resampling.BILINEAR)
    offset = ((size - new_size[0]) // 2, (size - new_size[1]) // 2)
    canvas = Image.new("RGB", (size, size), color=(0, 0, 0))
    canvas.paste(image, offset)
    return canvas


def load_busi_input(input_size: tuple[int, int]) -> tuple[torch.Tensor, dict]:
    if input_size != (224, 224):
        raise RuntimeError(f"BUSI frozen preprocessing requires 224x224, got {input_size}")
    protocol = FINAL_ROOT / "busi/frozen_protocol"
    group_id = read_nonempty_lines(protocol / "splits/test_groups.txt")[0]
    with (protocol / "clean_manifest.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    row = next(item for item in rows if item["group_id"] == group_id)
    source = DATA_ROOT / "Dataset_BUSI_with_GT" / row["image_relpath"]
    image = resize_and_pad_busi(Image.open(source).convert("RGB"))
    array = np.asarray(image, dtype=np.float32) / 255.0
    tensor = torch.from_numpy(np.ascontiguousarray(array.transpose(2, 0, 1))).unsqueeze(0)
    return tensor.float(), {
        "source_file": str(source),
        "source_file_sha256": file_sha256(source),
        "group_id": group_id,
        "sample_id": row["sample_id"],
        "class_name": row["class_name"],
        "preprocessing": "aspect-ratio-preserving bilinear resize and symmetric zero padding to 224x224",
    }


def load_input(dataset: str, input_size: tuple[int, int]) -> tuple[torch.Tensor, dict]:
    if dataset == "Synapse":
        return load_synapse_input(input_size)
    if dataset == "ACDC":
        return load_acdc_input(input_size)
    if dataset == "BUSI":
        return load_busi_input(input_size)
    raise ValueError(dataset)


def load_model(spec: dict) -> tuple[torch.nn.Module, dict]:
    repo = spec["repo"]
    os.chdir(repo)
    sys.path.insert(0, str(repo))
    from models.vmunet.vmunet import VMUNet

    model = VMUNet(
        num_classes=spec["num_classes"],
        input_channels=3,
        depths=[2, 2, 2, 2],
        depths_decoder=[2, 2, 2, 1],
        drop_path_rate=0.2,
        load_ckpt_path=None,
        scan_fusion=spec["scan_fusion"],
    )
    checkpoint = torch.load(spec["checkpoint"], map_location="cpu")
    if not isinstance(checkpoint, dict) or "model_state_dict" not in checkpoint:
        raise RuntimeError("Expected checkpoint dictionary containing model_state_dict")
    state_dict = checkpoint["model_state_dict"]
    if state_dict and next(iter(state_dict)).startswith("module."):
        state_dict = {key[len("module."):]: value for key, value in state_dict.items()}
    incompatible = model.load_state_dict(state_dict, strict=True)
    if incompatible.missing_keys or incompatible.unexpected_keys:
        raise RuntimeError(f"Checkpoint mismatch: {incompatible}")
    return model.cuda().eval(), checkpoint


def export_state_dict(model: torch.nn.Module, output: Path) -> dict:
    cpu_state = {key: value.detach().cpu().contiguous() for key, value in model.state_dict().items()}
    tensor_bytes = int(sum(value.numel() * value.element_size() for value in cpu_state.values()))
    output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(cpu_state, output)
    return {
        "path": str(output),
        "sha256": file_sha256(output),
        "serialized_bytes": int(output.stat().st_size),
        "serialized_mib": float(output.stat().st_size / 1024**2),
        "tensor_payload_bytes": tensor_bytes,
        "tensor_payload_mib": float(tensor_bytes / 1024**2),
        "tensor_count": len(cpu_state),
        "format": "PyTorch state_dict only; CPU tensors; optimizer and scheduler excluded",
    }


def benchmark(model: torch.nn.Module, tensor: torch.Tensor, warmups: int, iterations: int) -> tuple[dict, list[float]]:
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    tensor = tensor.cuda(non_blocking=False)
    with torch.inference_mode():
        for _ in range(warmups):
            model(tensor)
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    timings_ms: list[float] = []
    with torch.inference_mode():
        for _ in range(iterations):
            torch.cuda.synchronize()
            started = time.perf_counter_ns()
            model(tensor)
            torch.cuda.synchronize()
            timings_ms.append((time.perf_counter_ns() - started) / 1_000_000.0)
    values = np.asarray(timings_ms, dtype=np.float64)
    allocated = int(torch.cuda.max_memory_allocated())
    reserved = int(torch.cuda.max_memory_reserved())
    summary = {
        "warmup_iterations": warmups,
        "timed_iterations": iterations,
        "mean_latency_ms": float(values.mean()),
        "sample_std_latency_ms": float(values.std(ddof=1)),
        "median_latency_ms": float(np.median(values)),
        "p95_latency_ms": float(np.percentile(values, 95)),
        "min_latency_ms": float(values.min()),
        "max_latency_ms": float(values.max()),
        "throughput_images_per_second": float(1000.0 / values.mean()),
        "peak_inference_allocated_bytes": allocated,
        "peak_inference_allocated_mib": float(allocated / 1024**2),
        "peak_inference_reserved_bytes": reserved,
        "peak_inference_reserved_mib": float(reserved / 1024**2),
        "timer": "time.perf_counter_ns with torch.cuda.synchronize immediately before and after every forward",
        "amp_enabled": False,
        "gradient_enabled": False,
        "model_eval": True,
        "batch_size": 1,
        "included_scope": "model forward only",
        "excluded_scope": "data loading, host-to-device transfer, postprocessing, metric calculation, and image saving",
    }
    return summary, timings_ms


def estimate_flops(model: torch.nn.Module, tensor: torch.Tensor, method: str) -> dict:
    from models.vmunet.vmamba import SS2D, flops_selective_scan_ref

    shapes: list[dict] = []

    def capture(module, inputs):
        x = inputs[0]
        shapes.append({
            "batch": int(x.shape[0]),
            "height": int(x.shape[1]),
            "width": int(x.shape[2]),
            "d_inner": int(module.d_inner),
            "d_state": int(module.d_state),
            "dt_rank": int(module.dt_rank),
        })

    hooks = [module.register_forward_pre_hook(capture) for module in model.modules() if isinstance(module, SS2D)]
    with torch.inference_mode():
        thop_macs, thop_params = profile(model, inputs=(tensor.cuda(),), verbose=False)
    for hook in hooks:
        hook.remove()

    projection_macs = 0.0
    scan_core_macs = 0.0
    for shape in shapes:
        batch = shape["batch"]
        length = shape["height"] * shape["width"]
        directions = 4
        channels = shape["d_inner"] if method == "E1" else shape["d_inner"] // 2
        projection_macs += batch * directions * length * channels * (shape["dt_rank"] + 2 * shape["d_state"])
        projection_macs += batch * directions * length * shape["dt_rank"] * channels
        scan_core_macs += flops_selective_scan_ref(
            B=batch,
            L=length,
            D=directions * channels,
            N=shape["d_state"],
            with_D=True,
            with_Z=False,
            with_Group=True,
        )
    total_macs = float(thop_macs + projection_macs + scan_core_macs)
    return {
        "parameter_count": int(sum(parameter.numel() for parameter in model.parameters())),
        "thop_reported_parameter_count": int(thop_params),
        "thop_supported_layer_macs": float(thop_macs),
        "analytical_unregistered_projection_macs": float(projection_macs),
        "analytical_ss2d_scan_core_macs": float(scan_core_macs),
        "estimated_whole_model_macs": total_macs,
        "estimated_whole_model_flops": 2.0 * total_macs,
        "mac_to_flop_rule": "1 MAC = 2 FLOPs",
        "flops_tool": "THOP for registered layers plus analytical SS2D projection and selective-scan core",
        "ss2d_call_count": len(shapes),
        "postprocessing_included": False,
        "status": "estimated, not exact: elementwise operations and normalization are not fully counted",
    }


def write_timing_csv(path: Path, values: list[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["iteration", "latency_ms"])
        writer.writerows((index + 1, value) for index, value in enumerate(values))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=["Synapse", "ACDC", "BUSI"], required=True)
    parser.add_argument("--method", choices=["E1", "E2_modify_2"], required=True)
    parser.add_argument("--warmups", type=int, default=20)
    parser.add_argument("--iterations", type=int, default=200)
    args = parser.parse_args()
    if args.warmups < 20 or args.iterations < 100:
        raise ValueError("Strict protocol requires at least 20 warm-ups and 100 timed iterations")

    spec = SPECS[(args.dataset, args.method)]
    run_dir = OUTPUT_ROOT / "runs" / f"{args.dataset.lower()}_{args.method.lower()}_seed42"
    run_dir.mkdir(parents=True, exist_ok=False)

    torch.manual_seed(20260906)
    np.random.seed(20260906)
    gc.collect()
    torch.cuda.empty_cache()

    input_cpu, source = load_input(args.dataset, spec["input_size"])
    model, checkpoint = load_model(spec)
    deployable_path = OUTPUT_ROOT / "deployable_state_dicts" / f"{args.dataset.lower()}_{args.method.lower()}_seed42_state_dict.pth"
    state_dict_info = export_state_dict(model, deployable_path)
    benchmark_summary, timings = benchmark(model, input_cpu, args.warmups, args.iterations)
    flops = estimate_flops(model, input_cpu, args.method)

    driver_version = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"], text=True
    ).strip()
    result = {
        "protocol_name": "step19_unified_inference_v1",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataset": args.dataset,
        "method": args.method,
        "seed": 42,
        "scan_fusion": spec["scan_fusion"],
        "repo": str(spec["repo"]),
        "model_source_sha256": file_sha256(spec["repo"] / "models/vmunet/vmamba.py"),
        "checkpoint": str(spec["checkpoint"]),
        "checkpoint_sha256": file_sha256(spec["checkpoint"]),
        "checkpoint_selected_epoch": checkpoint.get("epoch"),
        "checkpoint_size_bytes": int(spec["checkpoint"].stat().st_size),
        "input_shape": list(input_cpu.shape),
        "input_tensor_sha256": tensor_sha256(input_cpu),
        "input_source": source,
        "hardware": {
            "gpu": torch.cuda.get_device_name(0),
            "gpu_total_memory_bytes": int(torch.cuda.get_device_properties(0).total_memory),
            "driver_version": driver_version,
            "pytorch": torch.__version__,
            "cuda_runtime_reported_by_pytorch": torch.version.cuda,
            "cudnn": int(torch.backends.cudnn.version()),
        },
        "benchmark": benchmark_summary,
        "theoretical_efficiency": flops,
        "deployable_state_dict": state_dict_info,
    }
    write_timing_csv(run_dir / "iteration_timings.csv", timings)
    (run_dir / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
