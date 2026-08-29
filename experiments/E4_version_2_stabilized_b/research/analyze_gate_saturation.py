"""Measure adaptive-gate saturation over deterministic Synapse validation slices.

Research Author and Repository Maintainer: xuwen
Affiliation: Japan Advanced Institute of Science and Technology (JAIST)
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import torch
from torch.utils.data import DataLoader, Subset
from torchvision import transforms

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from configs.config_setting_synapse import setting_config
from datasets.dataset import Synapse_dataset
from datasets.validation import ValidationGenerator
from models.vmunet.vmunet import VMUNet


THRESHOLDS = (0.90, 0.95, 0.99, 0.999)


def make_validation_loader():
    dataset = Synapse_dataset(
        base_dir=setting_config.data_path,
        list_dir=setting_config.list_dir,
        split="train",
        transform=transforms.Compose([
            ValidationGenerator(
                output_size=[
                    setting_config.input_size_h,
                    setting_config.input_size_w,
                ]
            )
        ]),
    )
    validation_cases = set(setting_config.validation_cases)
    indices = [
        index
        for index, sample_name in enumerate(dataset.sample_list)
        if sample_name.strip().split("_slice")[0] in validation_cases
    ]
    return DataLoader(
        Subset(dataset, indices),
        batch_size=setting_config.validation_batch_size,
        shuffle=False,
        pin_memory=True,
        num_workers=setting_config.num_workers,
    ), len(indices)


def load_model(checkpoint_path):
    cfg = setting_config.model_config
    model = VMUNet(
        num_classes=cfg["num_classes"],
        input_channels=cfg["input_channels"],
        depths=cfg["depths"],
        depths_decoder=cfg["depths_decoder"],
        drop_path_rate=cfg["drop_path_rate"],
        load_ckpt_path=None,
        scan_fusion=cfg["scan_fusion"],
    )
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    return model.cuda().eval(), int(checkpoint["epoch"])


def empty_stats():
    return {
        "count": 0,
        "sum": 0.0,
        "sum_abs": 0.0,
        "sum_sq": 0.0,
        "min": float("inf"),
        "max": float("-inf"),
        "threshold_counts": {str(value): 0 for value in THRESHOLDS},
    }


def update_stats(stats, values):
    values = values.detach().float().reshape(-1)
    absolute = values.abs()
    stats["count"] += values.numel()
    stats["sum"] += values.sum().item()
    stats["sum_abs"] += absolute.sum().item()
    stats["sum_sq"] += values.square().sum().item()
    stats["min"] = min(stats["min"], values.min().item())
    stats["max"] = max(stats["max"], values.max().item())
    for threshold in THRESHOLDS:
        stats["threshold_counts"][str(threshold)] += int(
            (absolute >= threshold).sum().item()
        )


def finalize(stats):
    count = stats["count"]
    mean = stats["sum"] / count
    variance = max(stats["sum_sq"] / count - mean * mean, 0.0)
    result = {
        "count": count,
        "mean": mean,
        "mean_absolute": stats["sum_abs"] / count,
        "std": variance ** 0.5,
        "min": stats["min"],
        "max": stats["max"],
    }
    for threshold in THRESHOLDS:
        key = str(threshold)
        result[f"fraction_abs_ge_{key}"] = (
            stats["threshold_counts"][key] / count
        )
    return result


def probe(checkpoint_path, loader):
    model, epoch = load_model(checkpoint_path)
    overall = empty_stats()
    per_module = defaultdict(empty_stats)
    alpha_values = set()
    with torch.no_grad():
        for batch in loader:
            model(batch["image"].cuda(non_blocking=True).float())
            for name, module in model.named_modules():
                values = getattr(module, "_last_grouped_gate_delta", None)
                if values is None:
                    continue
                update_stats(overall, values)
                update_stats(per_module[name], values)
                alpha_values.add(float(module.grouped_gate_alpha))
    overall_result = finalize(overall)
    module_results = [
        {"module": name, **finalize(stats)}
        for name, stats in sorted(per_module.items())
    ]
    del model
    torch.cuda.empty_cache()
    return {
        "checkpoint": str(checkpoint_path),
        "epoch": epoch,
        "alpha_values": sorted(alpha_values),
        "overall": overall_result,
        "modules": module_results,
    }


def saturation_classification(run_results):
    # Predeclared population-based definition. An isolated min/max cannot
    # trigger BROAD saturation.
    broad_each_run = [
        result["overall"]["fraction_abs_ge_0.99"] >= 0.10
        or result["overall"]["fraction_abs_ge_0.95"] >= 0.25
        for result in run_results
    ]
    localized_each_run = [
        any(module["fraction_abs_ge_0.99"] >= 0.25 for module in result["modules"])
        for result in run_results
    ]
    if all(broad_each_run):
        return "BROAD", "both runs exceed the predeclared population threshold"
    if any(broad_each_run) or all(localized_each_run):
        return "LOCALIZED_OR_INCONSISTENT", (
            "global saturation is not confirmed in both runs, but at least one "
            "run or module exceeds a population threshold"
        )
    return "LIMITED", "extreme values exist, but saturation is not population-wide"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    run_root = Path(args.run_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)

    loader, slice_count = make_validation_loader()
    results = []
    for run_name in ("run_1", "run_2"):
        checkpoint = run_root / run_name / "checkpoints/latest.pth"
        result = probe(checkpoint, loader)
        result["run"] = run_name
        results.append(result)

    classification, reason = saturation_classification(results)
    manifest = {
        "author": "xuwen",
        "experiment": "E4 V2 gate saturation population probe",
        "validation_cases": list(setting_config.validation_cases),
        "validation_slice_count": slice_count,
        "thresholds": list(THRESHOLDS),
        "broad_definition": (
            "both runs: overall fraction |delta|>=0.99 is at least 10%, "
            "or overall fraction |delta|>=0.95 is at least 25%"
        ),
        "localized_definition": "any module has at least 25% with |delta|>=0.99",
        "classification": classification,
        "reason": reason,
        "runs": results,
    }
    (output_dir / "E4_V2_GATE_SATURATION_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    fields = [
        "run", "scope", "module", "count", "mean", "mean_absolute", "std",
        "min", "max", *[f"fraction_abs_ge_{value}" for value in THRESHOLDS],
    ]
    with (output_dir / "E4_V2_GATE_SATURATION.csv").open(
        "w", newline="", encoding="utf-8"
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for result in results:
            writer.writerow({
                "run": result["run"], "scope": "overall", "module": "ALL",
                **result["overall"],
            })
            for module in result["modules"]:
                writer.writerow({
                    "run": result["run"], "scope": "module", **module,
                })

    lines = [
        "# E4 V2 Gate Saturation Population Report",
        "",
        "**Research Author and Repository Maintainer:** xuwen",
        "",
        f"**Classification:** {classification}",
        "",
        reason,
        "",
        "| Run | |delta|>=0.95 | |delta|>=0.99 | |delta|>=0.999 | Mean |delta| |",
        "|---|---:|---:|---:|---:|",
    ]
    for result in results:
        overall = result["overall"]
        lines.append(
            f"| {result['run']} | {overall['fraction_abs_ge_0.95']:.4%} | "
            f"{overall['fraction_abs_ge_0.99']:.4%} | "
            f"{overall['fraction_abs_ge_0.999']:.4%} | "
            f"{overall['mean_absolute']:.6f} |"
        )
    (output_dir / "E4_V2_GATE_SATURATION_REPORT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "classification": classification,
        "reason": reason,
        "overall": {r["run"]: r["overall"] for r in results},
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
