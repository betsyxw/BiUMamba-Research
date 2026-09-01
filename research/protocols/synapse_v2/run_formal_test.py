#!/usr/bin/env python3
"""Run the frozen Synapse v2 test protocol on one selected checkpoint.

Research Author and Repository Maintainer: xuwen
Affiliation: Japan Advanced Institute of Science and Technology (JAIST)

The script performs inference on the 12 isolated Synapse test volumes, writes
temporary NIfTI predictions/ground truth, and invokes the frozen synapse_v1
offline evaluator. Patient images, predictions, ground truth, and checkpoints
must remain outside GitHub.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import h5py
import numpy as np
import SimpleITK as sitk
import torch
from scipy.ndimage import zoom


METHOD_TO_SCAN_FUSION = {
    "E1": "original",
    "E2_modify_2": "grouped_2d_bidirectional_sum",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_checkpoint(model: torch.nn.Module, checkpoint_path: Path) -> dict:
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    if not isinstance(checkpoint, dict) or "model_state_dict" not in checkpoint:
        raise ValueError("Expected a Synapse v2 checkpoint with model_state_dict")
    incompatible = model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    if incompatible.missing_keys or incompatible.unexpected_keys:
        raise RuntimeError(f"Checkpoint mismatch: {incompatible}")
    return checkpoint


def predict_volume(
    model: torch.nn.Module,
    image: np.ndarray,
    input_size: tuple[int, int],
) -> tuple[np.ndarray, float, int]:
    prediction = np.zeros_like(image, dtype=np.uint8)
    forward_seconds = 0.0
    slice_count = int(image.shape[0])
    for index in range(slice_count):
        image_slice = image[index]
        original_shape = image_slice.shape
        if original_shape != input_size:
            image_slice = zoom(
                image_slice,
                (input_size[0] / original_shape[0], input_size[1] / original_shape[1]),
                order=3,
            )
        tensor = torch.from_numpy(image_slice).unsqueeze(0).unsqueeze(0).float().cuda()
        torch.cuda.synchronize()
        started = time.perf_counter()
        logits = model(tensor)
        torch.cuda.synchronize()
        forward_seconds += time.perf_counter() - started
        output = torch.argmax(torch.softmax(logits, dim=1), dim=1).squeeze(0)
        output_array = output.cpu().numpy()
        if original_shape != input_size:
            output_array = zoom(
                output_array,
                (original_shape[0] / input_size[0], original_shape[1] / input_size[1]),
                order=0,
            )
        prediction[index] = output_array.astype(np.uint8)
    return prediction, forward_seconds, slice_count


def save_nifti(array: np.ndarray, path: Path, z_spacing: float) -> None:
    image = sitk.GetImageFromArray(array)
    image.SetSpacing((1.0, 1.0, float(z_spacing)))
    sitk.WriteImage(image, str(path))


def estimate_complexity(model: torch.nn.Module, input_size: tuple[int, int]) -> dict:
    result = {
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "trainable_parameter_count": sum(
            parameter.numel() for parameter in model.parameters() if parameter.requires_grad
        ),
        "thop_status": "not_available",
        "thop_macs": None,
        "thop_flops_two_per_mac": None,
    }
    try:
        from thop import profile

        dummy = torch.randn(1, 1, input_size[0], input_size[1], device="cuda")
        macs, _ = profile(model, inputs=(dummy,), verbose=False)
        result.update(
            {
                "thop_status": "ok_custom_ops_may_be_undercounted",
                "thop_macs": float(macs),
                "thop_flops_two_per_mac": float(2.0 * macs),
            }
        )
    except Exception as exc:  # profiling must not invalidate medical metrics
        result["thop_status"] = f"failed: {type(exc).__name__}: {exc}"
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=sorted(METHOD_TO_SCAN_FUSION), required=True)
    parser.add_argument("--seed", type=int, choices=[42, 2026, 3407], required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--test-volume-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--case-list",
        type=Path,
        default=Path("research/protocols/synapse_v2/splits/test_cases.txt"),
    )
    parser.add_argument(
        "--evaluator",
        type=Path,
        default=Path("research/protocols/synapse_v1/evaluate_synapse_nifti.py"),
    )
    parser.add_argument("--input-size", type=int, nargs=2, default=(224, 224))
    parser.add_argument("--z-spacing", type=float, default=1.0)
    args = parser.parse_args()

    repo_root = Path.cwd().resolve()
    sys.path.insert(0, str(repo_root))
    from configs.config_setting_synapse import setting_config
    from models.vmunet.vmunet import VMUNet

    cases = [line.strip() for line in args.case_list.read_text().splitlines() if line.strip()]
    if len(cases) != 12 or len(set(cases)) != 12:
        raise ValueError("The frozen Synapse v2 test list must contain 12 unique cases")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    prediction_dir = args.output_dir / "predictions_do_not_upload"
    ground_truth_dir = args.output_dir / "ground_truth_do_not_upload"
    metrics_dir = args.output_dir / "metrics"
    prediction_dir.mkdir(exist_ok=True)
    ground_truth_dir.mkdir(exist_ok=True)
    metrics_dir.mkdir(exist_ok=True)

    model_config = dict(setting_config.model_config)
    model = VMUNet(
        num_classes=model_config["num_classes"],
        input_channels=model_config["input_channels"],
        depths=model_config["depths"],
        depths_decoder=model_config["depths_decoder"],
        drop_path_rate=model_config["drop_path_rate"],
        load_ckpt_path=None,
        scan_fusion=METHOD_TO_SCAN_FUSION[args.method],
    ).cuda()
    checkpoint = load_checkpoint(model, args.checkpoint)
    model.eval()

    complexity = estimate_complexity(model, tuple(args.input_size))
    torch.cuda.reset_peak_memory_stats()
    case_rows: list[dict] = []
    total_started = time.perf_counter()
    with torch.no_grad():
        for case in cases:
            volume_path = args.test_volume_dir / f"{case}.npy.h5"
            if not volume_path.is_file():
                raise FileNotFoundError(volume_path)
            case_started = time.perf_counter()
            with h5py.File(volume_path, "r") as handle:
                image = handle["image"][:]
                label = handle["label"][:]
            prediction, forward_seconds, slice_count = predict_volume(
                model, image, tuple(args.input_size)
            )
            save_nifti(prediction, prediction_dir / f"{case}_pred.nii.gz", args.z_spacing)
            save_nifti(label.astype(np.uint8), ground_truth_dir / f"{case}_gt.nii.gz", args.z_spacing)
            end_to_end_seconds = time.perf_counter() - case_started
            case_rows.append(
                {
                    "case": case,
                    "slice_count": slice_count,
                    "model_forward_seconds": f"{forward_seconds:.10f}",
                    "model_forward_ms_per_slice": f"{1000.0 * forward_seconds / slice_count:.10f}",
                    "end_to_end_seconds": f"{end_to_end_seconds:.10f}",
                }
            )
    total_seconds = time.perf_counter() - total_started

    write_csv(
        args.output_dir / "inference_timing_per_case.csv",
        [
            "case",
            "slice_count",
            "model_forward_seconds",
            "model_forward_ms_per_slice",
            "end_to_end_seconds",
        ],
        case_rows,
    )
    total_slices = sum(int(row["slice_count"]) for row in case_rows)
    total_forward = sum(float(row["model_forward_seconds"]) for row in case_rows)
    manifest = {
        "research_author": "xuwen",
        "affiliation": "Japan Advanced Institute of Science and Technology (JAIST)",
        "protocol": "synapse_v2",
        "method": args.method,
        "scan_fusion": METHOD_TO_SCAN_FUSION[args.method],
        "seed": args.seed,
        "case_count": len(cases),
        "slice_count": total_slices,
        "checkpoint_path": str(args.checkpoint.resolve()),
        "checkpoint_sha256": sha256_file(args.checkpoint),
        "checkpoint_selected_epoch": checkpoint.get("epoch"),
        "checkpoint_validation_dice": checkpoint.get("validation_dice"),
        "checkpoint_validation_hd95_voxels": checkpoint.get("validation_hd95"),
        "case_list_sha256": sha256_file(args.case_list),
        "evaluator_sha256": sha256_file(args.evaluator),
        "model_source_sha256": sha256_file(repo_root / "models/vmunet/vmamba.py"),
        "model_wrapper_sha256": sha256_file(repo_root / "models/vmunet/vmunet.py"),
        "input_size": list(args.input_size),
        "z_spacing_mm": args.z_spacing,
        "model_forward_seconds_total": total_forward,
        "model_forward_ms_per_slice": 1000.0 * total_forward / total_slices,
        "end_to_end_seconds_total": total_seconds,
        "peak_inference_gpu_allocated_bytes": torch.cuda.max_memory_allocated(),
        "peak_inference_gpu_reserved_bytes": torch.cuda.max_memory_reserved(),
        "cuda_device": torch.cuda.get_device_name(0),
        **complexity,
    }
    (args.output_dir / "inference_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    subprocess.run(
        [
            sys.executable,
            str(args.evaluator),
            "--prediction-dir",
            str(prediction_dir),
            "--ground-truth-dir",
            str(ground_truth_dir),
            "--case-list",
            str(args.case_list),
            "--output-dir",
            str(metrics_dir),
        ],
        check=True,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
