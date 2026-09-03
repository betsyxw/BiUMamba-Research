#!/usr/bin/env python3
"""Build the frozen BUSI v1 clean manifest and stratified image-group split."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
from collections import Counter
from pathlib import Path


CLASSES = ("benign", "malignant", "normal")
EXCLUDED_OBJECTIONS = {"axilla", "multiclass", "needle"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_names(value: str) -> list[str]:
    return [item.strip() for item in value.strip().strip("{}").split("&") if item.strip()]


def numeric_key(name: str) -> tuple[str, int]:
    match = re.fullmatch(r"(benign|malignant|normal) \((\d+)\)", name)
    if not match:
        raise ValueError(f"Unexpected BUSI filename in correction table: {name!r}")
    return match.group(1), int(match.group(2))


def assign_stratified_split(rows: list[dict], seed: int) -> None:
    rng = random.Random(seed)
    by_class = {name: [] for name in CLASSES}
    for row in rows:
        by_class[row["class_name"]].append(row)
    for class_name, items in by_class.items():
        items.sort(key=lambda row: row["group_id"])
        rng.shuffle(items)
        count = len(items)
        validation_count = round(count * 0.10)
        test_count = round(count * 0.20)
        train_count = count - validation_count - test_count
        for index, row in enumerate(items):
            if index < train_count:
                row["split"] = "train"
            elif index < train_count + validation_count:
                row["split"] = "validation"
            else:
                row["split"] = "test"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--correction-csv", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--split-seed", type=int, default=42)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    split_dir = args.output_dir / "splits"
    split_dir.mkdir(exist_ok=True)

    with args.correction_csv.open(encoding="utf-8-sig", newline="") as handle:
        source_rows = list(csv.DictReader(handle, delimiter=";"))
    if len(source_rows) != 587:
        raise RuntimeError(f"Expected 587 correction groups, found {len(source_rows)}")

    manifest_rows: list[dict] = []
    excluded_rows: list[dict] = []
    seen_source_names: set[str] = set()
    for source_index, source in enumerate(source_rows, start=1):
        names = parse_names(source["Filename"])
        objections = {item for item in source["Objection"].split("&") if item}
        annotations = source["Annotation"]
        classes = {numeric_key(name)[0] for name in names}
        seen_source_names.update(names)
        base_record = {
            "group_id": f"group_{source_index:04d}",
            "source_ids": source["ID"].strip().strip("{}"),
            "source_names": "|".join(names),
            "objection": source["Objection"],
            "annotation": annotations,
        }
        if objections & EXCLUDED_OBJECTIONS or len(classes) != 1:
            excluded_rows.append({**base_record, "reason": source["Objection"] or "mixed_class"})
            continue

        class_name = next(iter(classes))
        representative = min(names, key=numeric_key)
        image_path = args.raw_root / class_name / f"{representative}.png"
        mask_paths = sorted((args.raw_root / class_name).glob(f"{representative}_mask*.png"))
        if not image_path.is_file() or not mask_paths:
            raise FileNotFoundError(f"Missing image/mask files for {representative}")
        manifest_rows.append(
            {
                **base_record,
                "sample_id": representative,
                "class_name": class_name,
                "image_relpath": str(image_path.relative_to(args.raw_root)),
                "mask_relpaths": "|".join(str(path.relative_to(args.raw_root)) for path in mask_paths),
                "duplicate_count": len(names),
                "mask_count": len(mask_paths),
                "image_sha256": sha256(image_path),
                "mask_sha256": "|".join(sha256(path) for path in mask_paths),
            }
        )

    expected_all = {
        f"{class_name} ({index})"
        for class_name, maximum in (("benign", 437), ("malignant", 210), ("normal", 133))
        for index in range(1, maximum + 1)
    }
    if seen_source_names != expected_all:
        raise RuntimeError(
            f"Correction table coverage mismatch: missing={sorted(expected_all-seen_source_names)[:10]} "
            f"extra={sorted(seen_source_names-expected_all)[:10]}"
        )
    if len(manifest_rows) != 529 or len(excluded_rows) != 58:
        raise RuntimeError(
            f"Unexpected clean counts: kept={len(manifest_rows)}, excluded={len(excluded_rows)}"
        )

    assign_stratified_split(manifest_rows, args.split_seed)
    manifest_rows.sort(key=lambda row: row["group_id"])
    fieldnames = list(manifest_rows[0])
    with (args.output_dir / "clean_manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)
    with (args.output_dir / "excluded_groups.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(excluded_rows[0]))
        writer.writeheader()
        writer.writerows(excluded_rows)

    for split in ("train", "validation", "test"):
        rows = [row for row in manifest_rows if row["split"] == split]
        (split_dir / f"{split}_groups.txt").write_text(
            "".join(f"{row['group_id']}\n" for row in rows), encoding="utf-8"
        )

    summary = {
        "protocol": "busi_v1_clean",
        "raw_image_count": 780,
        "correction_group_count": len(source_rows),
        "kept_group_count": len(manifest_rows),
        "excluded_group_count": len(excluded_rows),
        "exclusion_counts": Counter(row["reason"] for row in excluded_rows),
        "kept_class_counts": Counter(row["class_name"] for row in manifest_rows),
        "split_counts": Counter(row["split"] for row in manifest_rows),
        "split_class_counts": {
            split: Counter(row["class_name"] for row in manifest_rows if row["split"] == split)
            for split in ("train", "validation", "test")
        },
        "split_seed": args.split_seed,
        "correction_csv_sha256": sha256(args.correction_csv),
        "patient_level_split_claimed": False,
        "reason": "The public BUSI release does not expose patient identifiers.",
    }
    serializable = json.loads(json.dumps(summary, default=dict))
    (args.output_dir / "protocol_build_summary.json").write_text(
        json.dumps(serializable, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(serializable, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
