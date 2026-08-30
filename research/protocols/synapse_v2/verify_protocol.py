#!/usr/bin/env python3
"""Verify the frozen Synapse v2 split and protocol invariants.

Author: xuwen
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def read_cases(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-npz", type=Path)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    split_dir = root / "splits"
    train = read_cases(split_dir / "train_cases.txt")
    val = read_cases(split_dir / "validation_cases.txt")
    test = read_cases(split_dir / "test_cases.txt")
    assert len(train) == 14 and len(val) == 4 and len(test) == 12
    assert not (set(train) & set(val))
    assert not (set(train) & set(test))
    assert not (set(val) & set(test))

    expected: dict[str, tuple[str, int]] = {}
    with (split_dir / "EXPECTED_SLICE_COUNTS.csv").open(newline="") as handle:
        for row in csv.DictReader(handle):
            expected[row["case_id"]] = (row["split"], int(row["slice_count"]))
    assert sum(count for split, count in expected.values() if split == "train") == 1798
    assert sum(count for split, count in expected.values() if split == "validation") == 413

    observed = None
    if args.train_npz:
        observed = {}
        for case, (_, count) in expected.items():
            files = sorted(args.train_npz.glob(f"{case}_slice*.npz"))
            if len(files) != count:
                raise ValueError(f"{case}: expected {count} slices, found {len(files)}")
            observed[case] = len(files)

    report = {
        "protocol": "synapse_v2",
        "train_cases": len(train),
        "validation_cases": len(val),
        "test_cases": len(test),
        "train_slices": 1798,
        "validation_slices": 413,
        "pairwise_disjoint": True,
        "augmentation_sha256": sha256(root / "frozen_augmentation.py"),
        "observed_slice_counts": observed,
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

