"""Maintained six-model Synapse-v2 runner; not a recovered historical trainer.

Run from the repository root: python -m reproducibility.train_synapse --help
This runner uses the existing train-only engine, frozen data pipeline and
validation checkpoint selector. It does not run isolated-test evaluation.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

from .model_registry import ROOT, VARIANTS, assert_model_identity, build_model, describe, sha256


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", choices=list(VARIANTS), required=True)
    parser.add_argument("--seed", type=int, choices=[42, 2026, 3407], required=True)
    parser.add_argument("--epochs", type=int, choices=[50, 300], required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--train-npz", type=Path, required=True)
    parser.add_argument("--pretrained", type=Path, required=True)
    parser.add_argument("--protocol-dir", type=Path, default=ROOT / "research/protocols/synapse_v2")
    parser.add_argument("--describe-only", action="store_true", help="No torch import or data access")
    return parser.parse_args()


def main():
    args = arguments()
    identity = describe(args.method)
    if args.describe_only:
        print(json.dumps({**identity, "seed": args.seed, "epochs": args.epochs,
                          "runner": "maintained_synapse_v2", "test_data_access": False}, indent=2))
        return
    if Path.cwd().resolve() != ROOT:
        raise RuntimeError("Run from the repository root")
    if args.work_dir.exists():
        raise FileExistsError("Refusing to reuse output directory: " + str(args.work_dir))
    if not args.pretrained.is_file():
        raise FileNotFoundError(args.pretrained)
    import torch
    from torch.cuda.amp import GradScaler
    from torch.utils.data import DataLoader
    from engine_synapse import train_one_epoch
    from utils import get_logger, get_optimizer, get_scheduler, set_seed
    from experiments.E2_modify_2_synapse_v2.checkpointing import ValidationCheckpointSelector
    from experiments.E2_modify_2_synapse_v2.dataset_synapse_v2 import SynapseSlicesV2
    from experiments.E2_modify_2_synapse_v2.validation import evaluate_validation

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA and the compatible selective-scan extension are required")
    spec = importlib.util.spec_from_file_location("_release_config_" + args.method,
                                                 ROOT / identity["config_source"])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    config = module.setting_config
    config.seed, config.epochs, config.val_interval = args.seed, args.epochs, 1
    config.work_dir = str(args.work_dir) + "/"
    config.model_config = dict(config.model_config)
    config.model_config["load_ckpt_path"] = str(args.pretrained.resolve())
    if config.model_config["scan_fusion"] != identity["scan_fusion"]:
        raise RuntimeError("Archived config disagrees with the explicit model registry")
    protocol = json.loads((args.protocol_dir / "TRAINING_CONFIG.json").read_text())
    expected = (protocol["batch_size"], protocol["optimizer"]["learning_rate"],
                protocol["optimizer"]["weight_decay"], protocol["scheduler"]["T_max"],
                protocol["scheduler"]["eta_min"])
    observed = (config.batch_size, config.lr, config.weight_decay, config.T_max, config.eta_min)
    if (expected != observed or config.amp or config.distributed
            or config.opt != "AdamW" or config.sch != "CosineAnnealingLR"
            or config.num_workers != protocol["num_workers"]
            or [config.input_size_h, config.input_size_w] != protocol["input_size"]):
        raise RuntimeError("Configuration is not the maintained single-GPU Synapse-v2 recipe")
    set_seed(args.seed)
    train_data = SynapseSlicesV2(args.train_npz, args.protocol_dir, "train")
    val_data = SynapseSlicesV2(args.train_npz, args.protocol_dir, "validation")
    train_loader = DataLoader(train_data, batch_size=config.batch_size, shuffle=True,
                              pin_memory=True, num_workers=config.num_workers)
    val_loader = DataLoader(val_data, batch_size=config.batch_size, shuffle=False,
                            pin_memory=True, num_workers=config.num_workers)
    model = build_model(args.method, **config.model_config)
    # Use the archived initialization procedure; its loaded/not-loaded key lists
    # are printed by load_from and should be retained by the job's stdout log.
    model.load_from()
    block_count = assert_model_identity(model, args.method)
    model = torch.nn.DataParallel(model.cuda(), device_ids=[0], output_device=0)
    optimizer = get_optimizer(config, model)
    scheduler = get_scheduler(config, optimizer)
    scaler = GradScaler()
    args.work_dir.mkdir(parents=True, exist_ok=False)
    logger = get_logger("train", str(args.work_dir / "log"))
    checkpoints = args.work_dir / "checkpoints"
    selector = ValidationCheckpointSelector(checkpoints / "best_validation.pth")
    controlled = [args.protocol_dir / "TRAINING_CONFIG.json", args.protocol_dir / "SEEDS.txt",
                  args.protocol_dir / "frozen_augmentation.py"]
    controlled += [args.protocol_dir / "splits" / n for n in
                   ["train_cases.txt", "validation_cases.txt", "test_cases.txt", "EXPECTED_SLICE_COUNTS.csv"]]
    hashes = {str(p): sha256(p) for p in controlled}
    runtime_files = [Path(__file__), ROOT / "reproducibility/model_registry.py",
                     ROOT / "engine_synapse.py", ROOT / "utils.py"]
    runtime_files += [ROOT / "experiments/E2_modify_2_synapse_v2" / n for n in
                      ["checkpointing.py", "dataset_synapse_v2.py", "validation.py"]]
    manifest = {**identity, "runner": "maintained_synapse_v2_not_historical_replay",
                "seed": args.seed, "epochs": args.epochs, "ss2d_blocks": block_count,
                "train_slices": len(train_data), "validation_slices": len(val_data),
                "test_data_access": False, "test_case_list_hashed": True,
                "protocol_hashes": hashes, "pretrained_sha256": sha256(args.pretrained),
                "runtime_source_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in runtime_files},
                "python": sys.version, "torch": torch.__version__, "cuda": torch.version.cuda,
                "gpu": torch.cuda.get_device_name(0), "amp": config.amp,
                "command": sys.argv, "pythonhashseed": os.environ.get("PYTHONHASHSEED"),
                "model_config": config.model_config,
                "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                "git_status": subprocess.check_output(["git", "status", "--porcelain"], text=True)}
    (args.work_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (args.work_dir / "source_diff.patch").write_bytes(subprocess.check_output(["git", "diff", "HEAD"]))
    history, started = [], time.perf_counter()
    torch.cuda.reset_peak_memory_stats()
    for epoch in range(1, args.epochs + 1):
        epoch_started = time.perf_counter()
        lr = optimizer.param_groups[0]["lr"]
        loss = train_one_epoch(train_loader, model, config.criterion, optimizer,
                               scheduler, epoch, logger, config, scaler=scaler)
        training_seconds = time.perf_counter() - epoch_started
        validation_started = time.perf_counter()
        dice, hd95, organs = evaluate_validation(model, val_loader, config.num_classes)
        validation_seconds = time.perf_counter() - validation_started
        if not all(math.isfinite(float(v)) for v in [loss, dice, hd95]):
            raise RuntimeError("Non-finite loss or validation metric")
        improved = selector.update(epoch=epoch, dice=dice, hd95=hd95, model=model,
                                   optimizer=optimizer, scheduler=scheduler, protocol_hashes=hashes)
        history.append({"epoch": epoch, "training_loss": float(loss), "learning_rate_used": lr,
                        "validation_dice": dice, "validation_hd95_voxels": hd95,
                        "checkpoint_updated": improved, "per_organ": organs,
                        "training_seconds": training_seconds, "validation_seconds": validation_seconds,
                        "epoch_total_seconds": time.perf_counter() - epoch_started})
        (args.work_dir / "validation_history.json").write_text(json.dumps(history, indent=2) + "\n")
        torch.save({"method": args.method, "scan_fusion": identity["scan_fusion"], "epoch": epoch,
                    "model_state_dict": model.module.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "scheduler_state_dict": scheduler.state_dict(), "protocol_hashes": hashes},
                   checkpoints / "latest_resume.pth")
    os.replace(checkpoints / "latest_resume.pth", checkpoints / ("final_epoch_%d.pth" % args.epochs))
    summary = {"method": args.method, "seed": args.seed, "epochs": len(history),
               "best_validation_epoch": selector.best_epoch, "best_validation_dice": selector.best_dice,
               "best_validation_hd95_voxels": selector.best_hd95,
               "best_checkpoint_sha256": sha256(selector.path), "test_data_access": False,
               "total_seconds": time.perf_counter() - started,
               "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
               "peak_reserved_bytes": torch.cuda.max_memory_reserved()}
    (args.work_dir / "training_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
