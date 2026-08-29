"""Formal 50-epoch Synapse screening entry for stabilized B.

Research Author and Repository Maintainer: xuwen
Affiliation: Japan Advanced Institute of Science and Technology (JAIST)
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import train_synapse
from configs.config_setting_synapse import setting_config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-dir", required=True)
    args = parser.parse_args()
    work_dir = Path(args.work_dir).resolve()
    if work_dir.exists():
        raise FileExistsError(f"Refusing to overwrite screening directory: {work_dir}")

    setting_config.epochs = 50
    setting_config.seed = 42
    setting_config.work_dir = str(work_dir) + "/"
    setting_config.selection_val_interval = 10
    setting_config.only_test_and_save_figs = False

    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()
    manifest = {
        "author": "xuwen",
        "experiment": "E4_version_2_stabilized_b Synapse screen50",
        "source_commit": commit,
        "epochs": setting_config.epochs,
        "seed": setting_config.seed,
        "batch_size": setting_config.batch_size,
        "input_size": [setting_config.input_size_h, setting_config.input_size_w],
        "validation_cases": list(setting_config.validation_cases),
        "selection_val_interval": setting_config.selection_val_interval,
        "checkpoint_selection": "maximum held-out validation Dice; HD95 tie-break",
        "scan_fusion": setting_config.model_config["scan_fusion"],
        "gate_lr_multiplier": setting_config.gate_lr_multiplier,
        "gate_freeze_epochs": setting_config.gate_freeze_epochs,
        "gate_alpha_ramp_epochs": setting_config.gate_alpha_ramp_epochs,
        "gate_alpha_max": setting_config.gate_alpha_max,
        "gradient_clip_norm": setting_config.gradient_clip_norm,
        "equal_fusion_reg_weight": setting_config.equal_fusion_reg_weight,
    }
    work_dir.mkdir(parents=True, exist_ok=False)
    (work_dir / "SCREEN50_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    torch.cuda.reset_peak_memory_stats()
    train_synapse.main(setting_config)
    torch.cuda.synchronize()
    peak = {
        "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
        "peak_reserved_bytes": torch.cuda.max_memory_reserved(),
        "peak_allocated_mib": torch.cuda.max_memory_allocated() / 2**20,
        "peak_reserved_mib": torch.cuda.max_memory_reserved() / 2**20,
    }
    (work_dir / "GPU_MEMORY.json").write_text(
        json.dumps(peak, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(peak, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
