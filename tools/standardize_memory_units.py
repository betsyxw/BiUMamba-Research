#!/usr/bin/env python3
"""Convert published memory tables to decimal GB without changing measurements.

Original device logs and machine-readable benchmark records remain in their
native units. Published CSVs, Markdown reports and workbook cells are converted.
Run with --apply to update a clean checkout; the default is a dry run.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FACTORS = {"MiB": 2**20 / 10**9, "GiB": 2**30 / 10**9}
NUMBER = r"[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
NUM_RE = re.compile(NUMBER)
UNIT_RE = re.compile(r"MiB|GiB")
INLINE_RE = re.compile(
    rf"(?P<values>{NUMBER}(?:\s*(?:/|±|to|versus|and|–|→)\s*{NUMBER})*)\s+(?P<unit>MiB|GiB)"
)


def scale(value: str, factor: float, decimals: int = 6) -> str:
    """Scale a number, an uncertainty, or a slash-separated memory pair."""
    clean = value.strip().strip('`*')
    if not re.fullmatch(rf"{NUMBER}(?:\s*(?:±|/|to|versus|and|–|→)\s*{NUMBER})*", clean):
        return value
    return NUM_RE.sub(lambda m: f"{float(m[0].replace(',', '')) * factor:.{decimals}f}", value)


def inline(text: str) -> str:
    return INLINE_RE.sub(lambda m: scale(m['values'], FACTORS[m['unit']], 3) + " GB", text)


def markdown(text: str) -> str:
    lines = text.splitlines(keepends=True)
    columns: dict[int, float] = {}
    out = []
    for line in lines:
        if line.lstrip().startswith('|'):
            cells = line.split('|')
            header = {i: FACTORS[u[0]] for i, c in enumerate(cells) if (u := UNIT_RE.search(c)) and not INLINE_RE.search(c)}
            if header:
                columns = header
                line = UNIT_RE.sub('GB', line)
            elif columns and not re.match(r'^\s*\|[\s:|\-]+$', line):
                for i, factor in columns.items():
                    if i < len(cells) and not UNIT_RE.search(cells[i]):
                        cells[i] = scale(cells[i], factor, 3)
                line = '|'.join(cells)
        else:
            columns = {}
        out.append(inline(line))
    return ''.join(out)


def csv_text(text: str, path: str) -> str:
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return text
    header = rows[0]
    if 'target_column' in header and 'target_value' in header:
        ci, vi = header.index('target_column'), header.index('target_value')
        ti = header.index('transformation')
        for row in rows[1:]:
            if u := UNIT_RE.search(row[ci]):
                row[vi] = scale(row[vi], FACTORS[u[0]])
                row[ci] = UNIT_RE.sub('GB', row[ci])
                row[ti] += f"; decimal GB conversion (source value x {FACTORS[u[0]]:.12f}); source snapshot ce93620"
    else:
        columns = {i: FACTORS[u[0]] for i, c in enumerate(header) if (u := UNIT_RE.search(c))}
        for row in rows[1:]:
            for i, factor in columns.items():
                if i < len(row):
                    row[i] = scale(row[i], factor)
        rows[0] = [UNIT_RE.sub('GB', h) for h in header]
        # Some comparison tables store units in metric rows, not headers.
        if 'metric' in header:
            mi = header.index('metric')
            for row in rows[1:]:
                if u := UNIT_RE.search(row[mi]):
                    factor = FACTORS[u[0]]
                    row[mi] = UNIT_RE.sub('GB', row[mi])
                    for i, h in enumerate(header):
                        if i != mi and 'percent' not in h and i < len(row):
                            row[i] = scale(row[i], factor)
    stream = io.StringIO(newline='')
    csv.writer(stream, lineterminator='\n').writerows(rows)
    return stream.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    updates = []
    for rel in tracked:
        p = ROOT / rel
        if '/ablations/fusion/' in rel:
            continue  # Frozen source CSVs, not presentation tables.
        if p.suffix not in {'.md', '.csv'} or not p.is_file():
            continue
        old = p.read_text(encoding='utf-8-sig')
        if not UNIT_RE.search(old):
            continue
        new = markdown(old) if p.suffix == '.md' else csv_text(old, rel)
        if old == new:
            continue
        updates.append({'path': rel, 'original_sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                        'updated_sha256': hashlib.sha256(new.encode()).hexdigest()})
        if args.apply:
            p.write_text(new, encoding='utf-8')
    print(json.dumps({'updated_files': len(updates), 'files': updates}, indent=2))


if __name__ == '__main__':
    main()
