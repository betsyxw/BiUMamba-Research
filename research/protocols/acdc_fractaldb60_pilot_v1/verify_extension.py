#!/usr/bin/env python3
"""Verify the frozen 50% and 100% ACDC extension splits."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def lines(path: Path):
    return [value.strip() for value in path.read_text().splitlines() if value.strip()]


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(__file__).resolve().parent
    train25 = lines(root / "splits/train_patients_25pct.txt")
    train50 = lines(root / "splits/train_patients_50pct.txt")
    train100 = lines(root / "splits/train_patients_100pct.txt")
    val = lines(root / "splits/validation_patients.txt")
    test = lines(root / "splits/test_patients.txt")

    expected = [(train25, 18), (train50, 35), (train100, 70), (val, 10), (test, 20)]
    if any(len(values) != count or len(set(values)) != count for values, count in expected):
        raise SystemExit("Wrong split size or duplicate patient")
    if not set(train25).issubset(train50) or not set(train50).issubset(train100):
        raise SystemExit("Label-fraction training sets are not nested")
    if set(train100) & (set(val) | set(test)) or set(val) & set(test):
        raise SystemExit("Training, validation and isolated-test patients overlap")

    files = [
        root / "README.md",
        root / "EXTENSION_CONFIG.json",
        root / "splits/train_patients_25pct.txt",
        root / "splits/train_patients_50pct.txt",
        root / "splits/train_patients_100pct.txt",
        root / "splits/validation_patients.txt",
        root / "splits/test_patients.txt",
    ]
    print(
        json.dumps(
            {
                "status": "PASS",
                "counts": {"train25": 18, "train50": 35, "train100": 70, "validation": 10, "isolated_test": 20},
                "nested": True,
                "hashes": {str(path.relative_to(root)): sha256(path) for path in files},
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
