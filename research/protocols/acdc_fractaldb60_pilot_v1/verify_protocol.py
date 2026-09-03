#!/usr/bin/env python3
"""Verify frozen patient lists and report protocol hashes."""

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
    train = lines(root / "splits/train_patients_25pct.txt")
    val = lines(root / "splits/validation_patients.txt")
    test = lines(root / "splits/test_patients.txt")
    if (len(train), len(val), len(test)) != (18, 10, 20):
        raise SystemExit(f"Wrong split sizes: {len(train)}/{len(val)}/{len(test)}")
    if len(set(train + val + test)) != 48:
        raise SystemExit("Pilot train, validation and test lists overlap or contain duplicates")
    files = [
        root / "README.md",
        root / "PILOT_CONFIG.json",
        root / "splits/train_patients_25pct.txt",
        root / "splits/validation_patients.txt",
        root / "splits/test_patients.txt",
    ]
    report = {
        "status": "PASS",
        "counts": {"train": 18, "validation": 10, "isolated_test": 20},
        "hashes": {str(path.relative_to(root)): sha256(path) for path in files},
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
