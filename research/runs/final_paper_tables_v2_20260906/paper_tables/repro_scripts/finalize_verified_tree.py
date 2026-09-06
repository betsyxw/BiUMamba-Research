#!/usr/bin/env python3
"""Finalize the post-Step20/20.5/table v2 tree with complete hashes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path


OUTPUT_NAMES = {
    "FILE_MANIFEST_V2_VERIFIED_20260906.tsv",
    "SHA256SUMS_V2_VERIFIED_20260906.txt",
    "SHA256_VERIFY_V2_VERIFIED_20260906.txt",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("build_workbook_script", type=Path)
    args = ap.parse_args()
    root = args.root.resolve()
    tables = root / "paper_tables"
    manifests = root / "manifests"
    manifests.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.build_workbook_script.resolve(), tables / "repro_scripts/build_workbook.mjs")
    shutil.copy2(Path(__file__).resolve(), tables / "repro_scripts/finalize_verified_tree.py")

    audit = json.loads((tables / "audits/TABLE_CROSSCHECK_REPORT.json").read_text(encoding="utf-8"))
    table_csvs = sorted((tables / "csv").glob("*.csv"))
    image_files = [p for p in (root / "qualitative_figures/fixed_selection_v2").rglob("*") if p.is_file() and p.suffix.lower() in {".png", ".pdf"}]
    completion = {
        "generated_date": "2026-09-06",
        "status": "complete" if audit["overall_status"] == "PASS" else "failed",
        "latest_step20_merged": (root / "statistics/step20_paper_table.csv").exists(),
        "latest_step20_5_merged": (root / "qualitative_figures/error_analysis/analysis_manifest_v2_complete.json").exists(),
        "fixed_rule_qualitative_png_pdf_files": len(image_files),
        "table_csv_panels": [p.relative_to(root).as_posix() for p in table_csvs],
        "workbook": "paper_tables/workbook/BiUMamba_Final_Paper_Tables_v2.xlsx",
        "numeric_cells_cross_checked": audit["mapped_numeric_cells"],
        "numeric_cells_failed": audit["failed"],
        "table_crosscheck_status": audit["overall_status"],
        "notes": [
            "Table 1 has reproduced and reported-baseline panels.",
            "Source map records the frozen source CSV, selector, source columns, transformation, and source SHA-256 for every reported numeric cell.",
            "Medical qualitative images are present in this local verified tree and must not be uploaded to public GitHub.",
        ],
    }
    completion_path = manifests / "TABLES_AND_STEP20_MERGE_20260906.json"
    completion_path.write_text(json.dumps(completion, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    excluded = {manifests / name for name in OUTPUT_NAMES}
    files = sorted(p for p in root.rglob("*") if p.is_file() and p not in excluded)
    manifest_path = manifests / "FILE_MANIFEST_V2_VERIFIED_20260906.tsv"
    sums_path = manifests / "SHA256SUMS_V2_VERIFIED_20260906.txt"
    records: list[tuple[str, int, str]] = []
    for p in files:
        records.append((p.relative_to(root).as_posix(), p.stat().st_size, sha256(p)))
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["relative_path", "size_bytes", "sha256"])
        w.writerows(records)
    sums_path.write_text("".join(f"{digest}  {rel}\n" for rel, _, digest in records), encoding="utf-8")

    failures = []
    for rel, size, digest in records:
        p = root / rel
        actual_size = p.stat().st_size if p.exists() else -1
        actual_hash = sha256(p) if p.exists() else "MISSING"
        if actual_size != size or actual_hash != digest:
            failures.append({"path": rel, "expected_size": size, "actual_size": actual_size, "expected_sha256": digest, "actual_sha256": actual_hash})
    verify_path = manifests / "SHA256_VERIFY_V2_VERIFIED_20260906.txt"
    verify_path.write_text(
        f"STATUS={'PASS' if not failures else 'FAIL'}\nFILES_VERIFIED={len(records)}\nFAILURES={len(failures)}\n"
        + (json.dumps(failures, indent=2) + "\n" if failures else ""),
        encoding="utf-8",
    )
    print(json.dumps({"status": "PASS" if not failures else "FAIL", "files": len(records), "bytes": sum(x[1] for x in records), "verification_failures": len(failures)}))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
