"""Strict deterministic A/A audit for E4_version_2_stabilized_gate.

Research Author and Repository Maintainer: xuwen
Affiliation: Japan Advanced Institute of Science and Technology (JAIST)

This diagnostic runner does not change the E4 architecture. It records the
sample order, loss, gradient norms, adaptive-gate statistics, logical model
hash, and the SHA-256 hash of each latest checkpoint.
"""

import argparse
import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch

# The runner lives under research/, while the VM-UNet modules live one level
# above it. Make the frozen diagnostic repository importable regardless of how
# the script is launched.
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def logical_model_hash(model):
    module = model.module if hasattr(model, "module") else model
    digest = hashlib.sha256()
    for name, tensor in sorted(module.state_dict().items()):
        value = tensor.detach().contiguous().cpu()
        digest.update(name.encode("utf-8"))
        digest.update(str(value.dtype).encode("ascii"))
        digest.update(str(tuple(value.shape)).encode("ascii"))
        digest.update(value.numpy().tobytes())
    return digest.hexdigest()


def append_csv(path, fieldnames, row):
    path = Path(path)
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow(row)
        stream.flush()
        os.fsync(stream.fileno())


def gate_values(model):
    values = []
    for module in model.modules():
        value = getattr(module, "_last_grouped_gate_delta", None)
        if value is not None:
            values.append(value.detach().float().reshape(-1))
    if not values:
        return None
    return torch.cat(values)


def gradient_norms(model):
    total_sq = 0.0
    gate_sq = 0.0
    for name, parameter in model.named_parameters():
        if parameter.grad is None:
            continue
        norm = parameter.grad.detach().float().norm(2).item()
        total_sq += norm * norm
        if "grouped_adaptive_gate" in name:
            gate_sq += norm * norm
    return total_sq ** 0.5, gate_sq ** 0.5


def make_audit_train_one_epoch(audit_dir):
    from torch.cuda.amp import autocast
    from engine_synapse import (
        configure_stabilized_gate,
        equal_fusion_regularization,
    )

    metrics_path = audit_dir / "epoch_audit.csv"
    batch_path = audit_dir / "batch_order.txt"
    fields = [
        "epoch", "loss", "segmentation_loss", "regularization_loss",
        "seconds", "backbone_learning_rate", "gate_learning_rate",
        "gate_frozen", "gate_alpha", "batch_count",
        "sample_count", "batch_order_sha256", "total_grad_norm_mean",
        "total_grad_norm_max", "gate_grad_norm_mean", "gate_grad_norm_max",
        "gate_delta_mean", "gate_delta_std", "gate_delta_min",
        "gate_delta_max", "logical_model_sha256",
    ]

    def train_one_epoch(train_loader, model, criterion, optimizer, scheduler,
                        epoch, logger, config, scaler=None):
        start = time.time()
        model.train()
        gate_state = configure_stabilized_gate(model, epoch, config)
        reg_weight = float(config.equal_fusion_reg_weight)
        clip_norm = float(config.gradient_clip_norm)
        losses = []
        segmentation_losses = []
        regularization_losses = []
        total_grad_norms = []
        gate_grad_norms = []
        gate_sum = 0.0
        gate_sum_sq = 0.0
        gate_count = 0
        gate_min = float("inf")
        gate_max = float("-inf")
        ordered_samples = []

        with batch_path.open("a", encoding="utf-8") as batch_log:
            for iteration, data in enumerate(train_loader):
                optimizer.zero_grad()
                case_names = [str(item) for item in data.get("case_name", [])]
                ordered_samples.extend(case_names)
                batch_log.write(
                    f"epoch={epoch},batch={iteration},samples="
                    + "|".join(case_names) + "\n"
                )

                images = data["image"].cuda(non_blocking=True).float()
                targets = data["label"].cuda(non_blocking=True).float()
                if config.amp:
                    with autocast():
                        output = model(images)
                        segmentation_loss = criterion(output, targets)
                        gate_regularizer = equal_fusion_regularization(model)
                        regularization_loss = (
                            gate_regularizer * reg_weight
                            if gate_regularizer is not None
                            else segmentation_loss.new_zeros(())
                        )
                        loss = segmentation_loss + regularization_loss
                    scaler.scale(loss).backward()
                    scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(model.parameters(), clip_norm)
                    total_norm, gate_norm = gradient_norms(model)
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    output = model(images)
                    segmentation_loss = criterion(output, targets)
                    gate_regularizer = equal_fusion_regularization(model)
                    regularization_loss = (
                        gate_regularizer * reg_weight
                        if gate_regularizer is not None
                        else segmentation_loss.new_zeros(())
                    )
                    loss = segmentation_loss + regularization_loss
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), clip_norm)
                    total_norm, gate_norm = gradient_norms(model)
                    optimizer.step()

                values = gate_values(model)
                if values is not None:
                    gate_sum += values.sum().item()
                    gate_sum_sq += (values * values).sum().item()
                    gate_count += values.numel()
                    gate_min = min(gate_min, values.min().item())
                    gate_max = max(gate_max, values.max().item())

                losses.append(loss.item())
                segmentation_losses.append(segmentation_loss.item())
                regularization_losses.append(regularization_loss.item())
                total_grad_norms.append(total_norm)
                gate_grad_norms.append(gate_norm)
                learning_rates = {
                    group.get("group_name", f"group_{index}"): group["lr"]
                    for index, group in enumerate(optimizer.param_groups)
                }
                if iteration % config.print_interval == 0:
                    message = (
                        f"train: epoch {epoch}, iter:{iteration}, "
                        f"loss: {loss.item():.4f}, lr: {learning_rates}, "
                        f"gate_alpha: {gate_state['alpha']:.6f}, "
                        f"gate_frozen: {gate_state['frozen']}"
                    )
                    print(message, flush=True)
                    logger.info(message)

            batch_log.flush()
            os.fsync(batch_log.fileno())

        scheduler.step()
        mean_loss = float(np.mean(losses))
        elapsed = time.time() - start
        if gate_count:
            gate_mean = gate_sum / gate_count
            gate_variance = max(gate_sum_sq / gate_count - gate_mean ** 2, 0.0)
            gate_std = gate_variance ** 0.5
        else:
            gate_mean = gate_std = gate_min = gate_max = float("nan")

        order_hash = hashlib.sha256(
            "\n".join(ordered_samples).encode("utf-8")
        ).hexdigest()
        row = {
            "epoch": epoch,
            "loss": f"{mean_loss:.12f}",
            "segmentation_loss": f"{np.mean(segmentation_losses):.12f}",
            "regularization_loss": f"{np.mean(regularization_losses):.12f}",
            "seconds": f"{elapsed:.6f}",
            "backbone_learning_rate": f"{learning_rates['backbone']:.16g}",
            "gate_learning_rate": f"{learning_rates['adaptive_gate']:.16g}",
            "gate_frozen": gate_state["frozen"],
            "gate_alpha": f"{gate_state['alpha']:.12f}",
            "batch_count": len(losses),
            "sample_count": len(ordered_samples),
            "batch_order_sha256": order_hash,
            "total_grad_norm_mean": f"{np.mean(total_grad_norms):.12f}",
            "total_grad_norm_max": f"{np.max(total_grad_norms):.12f}",
            "gate_grad_norm_mean": f"{np.mean(gate_grad_norms):.12f}",
            "gate_grad_norm_max": f"{np.max(gate_grad_norms):.12f}",
            "gate_delta_mean": f"{gate_mean:.12f}",
            "gate_delta_std": f"{gate_std:.12f}",
            "gate_delta_min": f"{gate_min:.12f}",
            "gate_delta_max": f"{gate_max:.12f}",
            "logical_model_sha256": logical_model_hash(model),
        }
        append_csv(metrics_path, fields, row)
        message = (
            f"Finish one epoch train: epoch {epoch}, loss: {mean_loss:.4f}, "
            f"time(s): {elapsed:.2f}, model_sha256: {row['logical_model_sha256']}"
        )
        print(message, flush=True)
        logger.info(message)
        return mean_loss

    return train_one_epoch


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--work-dir", required=True)
    parser.add_argument("--epochs", type=int, default=12)
    args = parser.parse_args()

    required = {
        "PYTHONHASHSEED": "42",
        "CUBLAS_WORKSPACE_CONFIG": ":4096:8",
    }
    for name, expected in required.items():
        actual = os.environ.get(name)
        if actual != expected:
            raise RuntimeError(f"{name} must be {expected!r}; received {actual!r}")

    work_dir = Path(args.work_dir).resolve()
    audit_dir = work_dir / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True

    import train_synapse
    from configs.config_setting_synapse import setting_config
    from models.vmunet.vmunet import VMUNet

    class DeterministicCrossEntropy2d(torch.nn.Module):
        """Mathematically equivalent default CE without CUDA nll_loss2d."""

        def forward(self, prediction, target):
            log_probabilities = torch.log_softmax(prediction, dim=1)
            selected = torch.gather(
                log_probabilities, 1, target.long().unsqueeze(1)
            ).squeeze(1)
            return -selected.mean()

    # PyTorch 1.13 reports that its CUDA nll_loss2d kernel has no strict
    # deterministic implementation. Replace only that CE primitive in this
    # diagnostic copy; the Dice term and all model/gate code remain unchanged.
    setting_config.criterion.celoss = DeterministicCrossEntropy2d()

    original_load_from = VMUNet.load_from

    def audited_load_from(model):
        result = original_load_from(model)
        initial_hash = logical_model_hash(model)
        (audit_dir / "initial_model_sha256.txt").write_text(
            initial_hash + "\n", encoding="utf-8"
        )
        print(f"INITIAL_MODEL_SHA256={initial_hash}", flush=True)
        return result

    VMUNet.load_from = audited_load_from
    train_synapse.train_one_epoch = make_audit_train_one_epoch(audit_dir)

    # Testing is irrelevant for the A/A training-trajectory audit and would
    # add approximately ten minutes per run. Keep training untouched and
    # replace only the final evaluation with a recorded no-op.
    def audit_noop_validation(*unused_args, **unused_kwargs):
        print("A/A audit: final segmentation evaluation intentionally skipped.")
        return float("nan"), float("nan")

    train_synapse.val_heldout_training_cases = audit_noop_validation
    train_synapse.val_one_epoch = audit_noop_validation

    original_save = torch.save
    checkpoint_fields = ["epoch", "path", "size_bytes", "checkpoint_sha256"]

    def audited_save(obj, path, *save_args, **save_kwargs):
        result = original_save(obj, path, *save_args, **save_kwargs)
        if os.path.basename(str(path)) == "latest.pth":
            append_csv(
                audit_dir / "checkpoint_hashes.csv",
                checkpoint_fields,
                {
                    "epoch": obj.get("epoch", "") if isinstance(obj, dict) else "",
                    "path": str(path),
                    "size_bytes": os.path.getsize(path),
                    "checkpoint_sha256": sha256_file(path),
                },
            )
        return result

    torch.save = audited_save

    setting_config.epochs = args.epochs
    setting_config.work_dir = str(work_dir) + "/"
    setting_config.selection_val_interval = args.epochs + 1

    try:
        git_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception:
        git_commit = "unknown"
    manifest = {
        "run_id": args.run_id,
        "author": "xuwen",
        "epochs": args.epochs,
        "seed": setting_config.seed,
        "work_dir": str(work_dir),
        "git_commit": git_commit,
        "python": sys.version,
        "platform": platform.platform(),
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
        "cudnn": torch.backends.cudnn.version(),
        "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
        "cudnn_deterministic": torch.backends.cudnn.deterministic,
        "cudnn_benchmark": torch.backends.cudnn.benchmark,
        "environment": {name: os.environ.get(name) for name in required},
        "scan_fusion": setting_config.model_config.get("scan_fusion"),
        "gate_lr_multiplier": setting_config.gate_lr_multiplier,
        "gate_freeze_epochs": setting_config.gate_freeze_epochs,
        "gate_alpha_ramp_epochs": setting_config.gate_alpha_ramp_epochs,
        "gate_alpha_max": setting_config.gate_alpha_max,
        "gradient_clip_norm": setting_config.gradient_clip_norm,
        "equal_fusion_reg_weight": setting_config.equal_fusion_reg_weight,
        "diagnostic_loss_substitution": (
            "CrossEntropyLoss -> log_softmax+gather+mean because PyTorch 1.13 "
            "CUDA nll_loss2d is rejected by strict deterministic mode"
        ),
    }
    (audit_dir / "runtime_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    try:
        train_synapse.main(setting_config)
    except Exception:
        import traceback

        error = traceback.format_exc()
        (audit_dir / "strict_determinism_error.txt").write_text(
            error, encoding="utf-8"
        )
        print(error, file=sys.stderr, flush=True)
        raise


if __name__ == "__main__":
    main()
