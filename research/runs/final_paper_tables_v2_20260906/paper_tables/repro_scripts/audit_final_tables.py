#!/usr/bin/env python3
"""Re-read every mapped source cell and cross-check manuscript Tables 1–6."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import statistics
from collections import Counter, defaultdict
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fmt_num(value: float, decimals: int) -> str:
    return f"{value:.{decimals}f}"


def transform_value(rows: list[dict[str, str]], columns: list[str], transform: str) -> str:
    name, decimals_s = transform.split(":")
    decimals = int(decimals_s)
    if not rows:
        raise ValueError("No source rows matched selector")
    if name.startswith("aggregate_"):
        vals = [float(r[columns[0]]) for r in rows]
        mean, std = statistics.mean(vals), statistics.stdev(vals)
        if name == "aggregate_mean_std_percent":
            mean, std = mean * 100, std * 100
        return f"{fmt_num(mean, decimals)} ± {fmt_num(std, decimals)}"

    r = rows[0]
    if name == "identity_number":
        return fmt_num(float(r[columns[0]]), decimals)
    if name == "identity_percent":
        return fmt_num(float(r[columns[0]]) * 100, decimals)
    if name == "divide_1e6_number":
        return fmt_num(float(r[columns[0]]) / 1e6, decimals)
    if name in ("mean_std_number", "mean_std_percent"):
        mean = float(r[columns[0]])
        raw_std = r[columns[1]] if len(columns) > 1 else ""
        std = float(raw_std) if raw_std not in ("", "None", "nan", "NaN") else math.nan
        if name == "mean_std_percent":
            mean *= 100
            std *= 100
        if math.isnan(std):
            return fmt_num(mean, decimals)
        return f"{fmt_num(mean, decimals)} ± {fmt_num(std, decimals)}"
    raise ValueError(f"Unknown transformation: {transform}")


def target_cell_exists(table_rows: list[dict[str, str]], column: str, value: str) -> bool:
    return any(r.get(column) == value for r in table_rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    args = ap.parse_args()
    root = args.root.resolve()
    out = root / "paper_tables"
    source_map_path = out / "source_map/table_cell_source_map.csv"
    maps = read_csv(source_map_path)
    results: list[dict[str, object]] = []
    cache: dict[Path, list[dict[str, str]]] = {}
    table_cache: dict[Path, list[dict[str, str]]] = {}

    for idx, item in enumerate(maps, start=1):
        source_path = root / item["source_csv"]
        target_path = root / item["target_csv"]
        selector = json.loads(item["source_selector_json"])
        columns = item["source_columns"].split(";")
        errors: list[str] = []
        actual_hash = sha256(source_path) if source_path.exists() else "MISSING"
        hash_ok = actual_hash == item["source_sha256"]
        if not hash_ok:
            errors.append("source hash mismatch")
        try:
            rows = cache.setdefault(source_path, read_csv(source_path))
            selected = [r for r in rows if all(str(r.get(k)) == str(v) for k, v in selector.items())]
            computed = transform_value(selected, columns, item["transformation"])
        except Exception as exc:  # report every failure rather than aborting early
            computed = "ERROR"
            errors.append(str(exc))
        value_ok = computed == item["target_value"]
        if not value_ok:
            errors.append(f"computed {computed!r} != target {item['target_value']!r}")
        try:
            table_rows = table_cache.setdefault(target_path, read_csv(target_path))
            target_ok = target_cell_exists(table_rows, item["target_column"], item["target_value"])
        except Exception as exc:
            target_ok = False
            errors.append(f"target table read failed: {exc}")
        if not target_ok:
            errors.append("target value not found in declared target column")
        results.append({
            "id": idx,
            "table": item["table"],
            "target_csv": item["target_csv"],
            "target_row_key": item["target_row_key"],
            "target_column": item["target_column"],
            "target_value": item["target_value"],
            "computed_value": computed,
            "source_csv": item["source_csv"],
            "selector": selector,
            "source_columns": columns,
            "transformation": item["transformation"],
            "source_hash_ok": hash_ok,
            "source_to_target_value_ok": value_ok,
            "target_cell_present": target_ok,
            "status": "PASS" if not errors else "FAIL",
            "errors": errors,
        })

    counts = Counter(r["status"] for r in results)
    by_table: dict[str, Counter] = defaultdict(Counter)
    for r in results:
        by_table[str(r["table"])][str(r["status"])] += 1

    csv_files = sorted((out / "csv").glob("*.csv"))
    report = {
        "schema_version": 1,
        "overall_status": "PASS" if counts["FAIL"] == 0 else "FAIL",
        "mapped_numeric_cells": len(results),
        "passed": counts["PASS"],
        "failed": counts["FAIL"],
        "tables": {k: dict(v) for k, v in sorted(by_table.items())},
        "table_csv_sha256": {p.name: sha256(p) for p in csv_files},
        "step20_present": (root / "statistics/step20_paper_table.csv").exists(),
        "step20_5_present": (root / "qualitative_figures/error_analysis/analysis_manifest_v2_complete.json").exists(),
        "checks": results,
    }
    audit_dir = out / "audits"
    audit_dir.mkdir(parents=True, exist_ok=True)
    json_path = audit_dir / "TABLE_CROSSCHECK_REPORT.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Table 1–6 cross-check report",
        "",
        f"**Overall status: {report['overall_status']}**",
        "",
        f"- Numeric table cells checked: {len(results)}",
        f"- Passed: {counts['PASS']}",
        f"- Failed: {counts['FAIL']}",
        f"- Latest Step 20 present: {report['step20_present']}",
        f"- Latest Step 20.5 present: {report['step20_5_present']}",
        "",
        "## Coverage by table",
        "",
        "| Table | Cells checked | Passed | Failed |",
        "|---|---:|---:|---:|",
    ]
    for table, c in sorted(by_table.items()):
        lines.append(f"| {table} | {sum(c.values())} | {c['PASS']} | {c['FAIL']} |")
    lines += [
        "",
        "## Method",
        "",
        "For every mapped numeric cell, this audit re-opens the declared source CSV, verifies its SHA-256, selects the declared row(s), re-applies the declared formatting/aggregation, and confirms that the resulting value is present in the declared target-table column.",
        "",
        "Table 1 is intentionally split into reproduced results and original-paper reported baselines. Screen50 and Full300 results are never presented as directly comparable. Table 5 keeps validation and isolated-test results in separate rows.",
    ]
    failures = [r for r in results if r["status"] == "FAIL"]
    if failures:
        lines += ["", "## Failures", ""]
        for r in failures:
            lines.append(f"- {r['table']} / {r['target_row_key']} / {r['target_column']}: {'; '.join(r['errors'])}")
    (audit_dir / "TABLE_CROSSCHECK_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    script_copy = out / "repro_scripts" / Path(__file__).name
    if Path(__file__).resolve() != script_copy.resolve():
        shutil.copy2(Path(__file__), script_copy)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
