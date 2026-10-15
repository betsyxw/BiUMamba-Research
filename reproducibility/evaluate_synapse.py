"""Evaluate one explicitly selected model/checkpoint; default is validation.

This maintained evaluator reports protocol-space distances, never unverified
physical millimetres. Isolated test access requires --split test explicitly.
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import time

from .model_registry import ROOT, VARIANTS, build_model, describe, sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", choices=list(VARIANTS), required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--split", choices=["validation", "test"], default="validation")
    parser.add_argument("--train-npz", type=Path)
    parser.add_argument("--test-volume-dir", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--protocol-dir", type=Path, default=ROOT / "research/protocols/synapse_v2")
    args = parser.parse_args()
    if Path.cwd().resolve() != ROOT:
        raise RuntimeError("Run from the repository root")
    if args.output_dir.exists():
        raise FileExistsError("Refusing to reuse evaluation output")
    if args.split == "validation" and (args.train_npz is None or args.test_volume_dir is not None):
        parser.error("validation requires --train-npz and forbids --test-volume-dir")
    if args.split == "test" and args.test_volume_dir is None:
        parser.error("explicit isolated test requires --test-volume-dir")
    import h5py
    import numpy as np
    import torch
    from torch.utils.data import DataLoader
    from experiments.E2_modify_2_synapse_v2.dataset_synapse_v2 import SynapseSlicesV2
    from research.protocols.synapse_v1.evaluate_synapse_nifti import evaluate_binary, ORGANS, write_csv
    from research.protocols.synapse_v2.run_formal_test import predict_volume
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA selective-scan environment required")
    identity = describe(args.method)
    model = build_model(args.method, num_classes=9, input_channels=3,
                        depths=[2, 2, 2, 2], depths_decoder=[2, 2, 2, 1],
                        drop_path_rate=0.2, load_ckpt_path=None).cuda().eval()
    # Only load trusted local checkpoints; PyTorch 1.13 uses pickle here.
    checkpoint = torch.load(args.checkpoint, map_location="cpu")
    if not isinstance(checkpoint, dict):
        raise ValueError("Expected checkpoint dictionary or plain state_dict")
    if checkpoint.get("method") is not None and checkpoint["method"] != args.method:
        raise ValueError("Checkpoint method metadata disagrees with --method")
    if checkpoint.get("scan_fusion") is not None and checkpoint["scan_fusion"] != identity["scan_fusion"]:
        raise ValueError("Checkpoint scan mode disagrees with --method")
    state_key = next((k for k in ["model_state_dict", "state_dict", "model"]
                      if isinstance(checkpoint.get(k), dict)), None)
    state = checkpoint[state_key] if state_key else checkpoint
    stripped = bool(state) and all(k.startswith("module.") for k in state)
    if stripped:
        state = {k[len("module."):]: v for k, v in state.items()}
    model.load_state_dict(state, strict=True)
    cases, volumes, processed_slices = [], {}, 0
    split_file = args.protocol_dir / "splits" / ("validation_cases.txt" if args.split == "validation" else "test_cases.txt")
    cases = [line.strip() for line in split_file.read_text().splitlines() if line.strip()]
    expected_cases = 4 if args.split == "validation" else 12
    if len(cases) != expected_cases or len(set(cases)) != expected_cases:
        raise ValueError("Unexpected frozen case list")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    with torch.no_grad():
        if args.split == "validation":
            data = SynapseSlicesV2(args.train_npz, args.protocol_dir, "validation")
            loader = DataLoader(data, batch_size=32, shuffle=False, num_workers=0)
            for batch in loader:
                logits = model(batch["image"].cuda().float())
                prediction = torch.argmax(torch.softmax(logits, dim=1), dim=1).cpu().numpy()
                for i, case in enumerate(batch["case_name"]):
                    volumes.setdefault(case, []).append((int(batch["slice_index"][i]), prediction[i], batch["label"][i].numpy()))
                    processed_slices += 1
            if processed_slices != len(data):
                raise RuntimeError("Validation slice coverage incomplete")
        else:
            for case in cases:
                with h5py.File(args.test_volume_dir / (case + ".npy.h5"), "r") as handle:
                    image, label = handle["image"][:], handle["label"][:]
                prediction, _, count = predict_volume(model, image, (224, 224))
                volumes[case] = [(i, prediction[i], label[i]) for i in range(count)]
                processed_slices += count
    if set(volumes) != set(cases):
        raise RuntimeError("Missing or unexpected evaluated cases")
    rows, case_rows, organ_rows = [], [], []
    def mean(values):
        clean = [float(v) for v in values if v is not None]
        return float(np.mean(clean)) if clean else None
    for case in cases:
        items = sorted(volumes[case], key=lambda item: item[0])
        pred = np.stack([r[1] for r in items])
        gt = np.stack([r[2] for r in items])
        for label, organ in ORGANS.items():
            dice, hd95, nsd, status = evaluate_binary(pred == label, gt == label, (1.0, 1.0, 1.0))
            rows.append({"case": case, "organ_id": label, "organ": organ, "dice": dice,
                         "hd95_protocol_units": hd95, "nsd_at_1_protocol_unit": nsd, "status": status})
        subset = [r for r in rows if r["case"] == case]
        case_rows.append({"case": case, "slice_count": len(items), **{
            metric: mean(r[metric] for r in subset) for metric in
            ["dice", "hd95_protocol_units", "nsd_at_1_protocol_unit"]}})
    for label, organ in ORGANS.items():
        subset = [r for r in rows if r["organ_id"] == label]
        organ_rows.append({"organ_id": label, "organ": organ, **{
            metric: mean(r[metric] for r in subset) for metric in
            ["dice", "hd95_protocol_units", "nsd_at_1_protocol_unit"]}})
    for filename, records in [("per_case_per_organ.csv", rows), ("per_case.csv", case_rows), ("per_organ.csv", organ_rows)]:
        write_csv(args.output_dir / filename, list(records[0]), records)
    summary = {**identity, "split": args.split, "case_count": len(cases), "slice_count": processed_slices,
               "aggregation": "mean_of_organ_means_across_valid_cases", "spacing_zyx": [1, 1, 1],
               "nsd_tolerance_protocol_units": 1.0, "test_data_access": args.split == "test",
               "checkpoint_sha256": sha256(args.checkpoint), "checkpoint_state_key": state_key,
               "stripped_module_prefix": stripped, "case_list_sha256": sha256(split_file),
               "torch": torch.__version__, "cuda": torch.version.cuda,
               "gpu": torch.cuda.get_device_name(0), "elapsed_seconds": time.perf_counter() - start,
               "evaluator_sha256": sha256(ROOT / "research/protocols/synapse_v1/evaluate_synapse_nifti.py"),
               "runner_sha256": sha256(Path(__file__)), **{
                   metric: mean(r[metric] for r in organ_rows) for metric in
                   ["dice", "hd95_protocol_units", "nsd_at_1_protocol_unit"]}}
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
