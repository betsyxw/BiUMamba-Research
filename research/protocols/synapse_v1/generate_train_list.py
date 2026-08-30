#!/usr/bin/env python3
"""Reconstruct and verify the frozen Synapse v1 train.txt.

Author: xuwen
Affiliation: Japan Advanced Institute of Science and Technology (JAIST)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

EXPECTED_SHA256 = "2a3afc3b126f560d023c09e9a943e31c9ab95cea544afa69bf6b39f80ade59f5"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    protocol_dir = Path(__file__).resolve().parent
    counts_path = protocol_dir / "splits" / "train_slice_counts.csv"
    lines: list[str] = []
    with counts_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            count = int(row["slice_count"])
            first = int(row["first_slice"])
            last = int(row["last_slice"])
            if last - first + 1 != count:
                raise ValueError(f"Non-contiguous range for {row['case_id']}")
            lines.extend(
                f"{row['case_id']}_slice{index:03d}" for index in range(first, last + 1)
            )

    payload = ("\n".join(lines) + "\n").encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    if len(lines) != 2211 or digest != EXPECTED_SHA256:
        raise RuntimeError(
            f"Frozen split verification failed: lines={len(lines)}, sha256={digest}"
        )
    args.output.write_bytes(payload)
    print(f"Wrote {len(lines)} entries; sha256={digest}")


if __name__ == "__main__":
    main()
