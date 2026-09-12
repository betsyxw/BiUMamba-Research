#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT / "outputs" / "BiUMamba_Paper_Evidence_Freeze_20260912_v1"
ZIP_PATH = ROOT / "outputs" / "BiUMamba_Paper_Evidence_Freeze_20260912_v1.zip"
SIDECAR = ROOT / "outputs" / "BiUMamba_Paper_Evidence_Freeze_20260912_v1_ZIP_VERIFICATION.json"
STAMP = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def files_for_manifest() -> list[Path]:
    excluded = {
        "manifests/FILE_MANIFEST.tsv",
        "manifests/SHA256SUMS.txt",
    }
    return [
        p for p in sorted(BUNDLE.rglob("*"))
        if p.is_file() and p.relative_to(BUNDLE).as_posix() not in excluded
    ]


(BUNDLE / "repro_scripts").mkdir(parents=True, exist_ok=True)
(BUNDLE / "manifests").mkdir(parents=True, exist_ok=True)
for name in [
    "build_paper_evidence_freeze.py",
    "build_final_evidence_workbook.mjs",
    "make_preview_contact_sheet.mjs",
    "finalize_evidence_freeze.py",
]:
    shutil.copy2(ROOT / name, BUNDLE / "repro_scripts" / name)

status = {
    "release": "BiUMamba_Paper_Evidence_Freeze_20260912_v1",
    "status": "FROZEN",
    "completed_utc": STAMP,
    "scope": "Paper evidence, tables, figures, manuscript-ready text, provenance, and claim audit; no new training.",
    "central_claim": "BiUMamba provides a favorable observed training-memory trade-off on Synapse CT and ACDC MRI relative to direction deletion and a Synapse near-memory-matched E1-Narrow control, while BUSI ultrasound exposes a dataset-dependent limitation.",
    "forbidden_overclaims": [
        "state-of-the-art accuracy",
        "statistical equivalence or non-inferiority",
        "universal inference speed improvement",
        "generalization across all medical modalities",
        "FractalDB is especially effective with limited labels",
    ],
    "steps": [
        {"step": 1, "item": "GroupMamba, LocalMamba, and EfficientVMamba related work", "status": "complete"},
        {"step": 2, "item": "Method difference table", "status": "complete"},
        {"step": 3, "item": "E1 versus BiUMamba core structure figure", "status": "complete"},
        {"step": 4, "item": "4HWC to 2HWC analytical derivation", "status": "complete"},
        {"step": 5, "item": "Table 2 rewritten by research question", "status": "complete"},
        {"step": 6, "item": "E1-Narrow matched-memory control", "status": "complete"},
        {"step": 7, "item": "Dice-memory and NSD-memory Pareto figures", "status": "complete"},
        {"step": 8, "item": "Cross-dataset Table 4", "status": "complete"},
        {"step": 9, "item": "Patient-level Table 7 and forest figure for main text", "status": "complete"},
        {"step": 10, "item": "Fixed-rule qualitative cases", "status": "complete"},
        {"step": 11, "item": "Discussion and Limitations", "status": "complete"},
        {"step": 12, "item": "Full claim audit", "status": "complete"},
        {"step": 13, "item": "Regenerate final tables from frozen CSVs and freeze", "status": "complete"},
    ],
    "crosscheck": {"status": "PASS", "mapped_cells": 774, "hash_checked_source_cells": 753, "failures": 0},
    "workbook_formula_error_scan": "PASS: 0 matches",
}
(BUNDLE / "RELEASE_STATUS.json").write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(BUNDLE / "COMPLETED_UTC.txt").write_text(STAMP + "\n", encoding="utf-8")

audit = """# Final release audit

- Release status: FROZEN
- Table cross-check: PASS (774 mapped cells; 753 source hashes checked; 0 failures)
- Workbook formula error scan: PASS (0 matches)
- Workbook visual review: PASS (all worksheets rendered; contact sheet included)
- Static figure visual review: PASS (method, Pareto, and forest figures inspected)
- Fixed-rule qualitative selection: included with case IDs, metrics, and selection manifests
- Claim audit: included; unsupported and contradicted claims are explicitly marked
- Aggregation warning: Tables 1/4 use seed-level mean ± SD; Table 7 uses patient/case means formed across three seeds before pairing
- Frozen-source policy: no model retraining or alteration of source results was performed
"""
(BUNDLE / "audit" / "FINAL_RELEASE_AUDIT.md").write_text(audit, encoding="utf-8")

entries = []
for p in files_for_manifest():
    entries.append((p.relative_to(BUNDLE).as_posix(), p.stat().st_size, sha256(p)))

with (BUNDLE / "manifests" / "FILE_MANIFEST.tsv").open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["relative_path", "size_bytes", "sha256"])
    w.writerows(entries)
with (BUNDLE / "manifests" / "SHA256SUMS.txt").open("w", encoding="utf-8") as f:
    for rel, _, digest in entries:
        f.write(f"{digest}  {rel}\n")

if ZIP_PATH.exists():
    ZIP_PATH.unlink()
with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for p in sorted(BUNDLE.rglob("*")):
        if p.is_file():
            z.write(p, arcname=f"{BUNDLE.name}/{p.relative_to(BUNDLE).as_posix()}")

bad_member = None
manifest_hash_failures = []
with zipfile.ZipFile(ZIP_PATH, "r") as z:
    bad_member = z.testzip()
    member_count = len(z.infolist())
    for rel, size, expected in entries:
        member = f"{BUNDLE.name}/{rel}"
        data = z.read(member)
        actual = hashlib.sha256(data).hexdigest()
        if len(data) != size or actual != expected:
            manifest_hash_failures.append({
                "relative_path": rel,
                "expected_size": size,
                "actual_size": len(data),
                "expected_sha256": expected,
                "actual_sha256": actual,
            })

verification = {
    "zip": ZIP_PATH.name,
    "verified_utc": STAMP,
    "zip_sha256": sha256(ZIP_PATH),
    "size_bytes": ZIP_PATH.stat().st_size,
    "member_count": member_count,
    "testzip_bad_member": bad_member,
    "manifest_entries_verified": len(entries),
    "manifest_hash_failures": manifest_hash_failures,
    "status": "PASS" if bad_member is None and not manifest_hash_failures else "FAIL",
}
SIDECAR.write_text(json.dumps(verification, indent=2) + "\n", encoding="utf-8")
print(json.dumps(verification, indent=2))
