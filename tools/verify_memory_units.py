#!/usr/bin/env python3
"""Check presentation-unit changes against the pre-conversion Git snapshot."""
from __future__ import annotations
import csv
import io
import json
import re
import subprocess
from pathlib import Path
from standardize_memory_units import FACTORS, UNIT_RE, scale

ROOT = Path(__file__).resolve().parents[1]
BASE = 'ce93620'
failures = []
changed_cells = 0
unchanged_cells = 0
files = subprocess.check_output(['git', 'diff', '--name-only', BASE], cwd=ROOT, text=True).splitlines()
for name in files:
    if not name.endswith('.csv'):
        continue
    old_text = subprocess.check_output(['git', 'show', f'{BASE}:{name}'], cwd=ROOT, text=True)
    old = list(csv.reader(io.StringIO(old_text)))
    new = list(csv.reader(io.StringIO((ROOT/name).read_text(encoding='utf-8-sig'))))
    if len(old) != len(new):
        failures.append([name, 'row count changed'])
        continue
    columns = {i: FACTORS[m[0]] for i, h in enumerate(old[0]) if (m := UNIT_RE.search(h))}
    is_map = 'target_column' in old[0]
    for ri, (a, b) in enumerate(zip(old, new)):
        if len(a) != len(b):
            failures.append([name, ri, 'column count changed'])
            continue
        metric_unit = UNIT_RE.search(a[old[0].index('metric')]) if ri and 'metric' in old[0] else None
        for ci, (before, after) in enumerate(zip(a, b)):
            expected = before
            if is_map and ri:
                tc = old[0].index('target_column')
                unit = UNIT_RE.search(a[tc])
                if unit and ci == tc:
                    expected = UNIT_RE.sub('GB', before)
                elif unit and old[0][ci] == 'target_value':
                    expected = scale(before, FACTORS[unit[0]])
                elif unit and old[0][ci] == 'transformation':
                    expected = before + f'; decimal GB conversion (source value x {FACTORS[unit[0]]:.12f}); source snapshot ce93620'
            elif ri == 0:
                expected = UNIT_RE.sub('GB', before)
            elif ci in columns:
                expected = scale(before, columns[ci])
            elif metric_unit:
                if old[0][ci] == 'metric':
                    expected = UNIT_RE.sub('GB', before)
                elif 'percent' not in old[0][ci]:
                    expected = scale(before, FACTORS[metric_unit[0]])
            if expected != after:
                failures.append([name, ri+1, ci+1, before, after, expected])
            elif before != after:
                changed_cells += 1
            else:
                unchanged_cells += 1

# Check the final cell-level source map against the actual converted CSVs.
bundle = ROOT / 'research/paper_evidence_20260912'
with (bundle/'paper_tables/source_map/table_cell_source_map.csv').open() as handle:
    mappings = list(csv.DictReader(handle))
cached = {}
mapped_cells = 0
for row in mappings:
    p = bundle/row['target_csv']
    if p not in cached:
        cached[p] = list(csv.reader(p.open()))
    match = re.fullmatch(r'R(\d+)C(\d+)', row['target_cell'])
    if not match:
        continue
    ri, ci = [int(x)-1 for x in match.groups()]
    actual = cached[p][ri][ci]
    if actual != row['target_value']:
        failures.append([str(p.relative_to(ROOT)), row['target_cell'], 'source map value mismatch'])
    mapped_cells += 1

report = {'updated': '20261007', 'baseline_commit': BASE,
          'converted_csv_cells': changed_cells, 'unchanged_csv_cells': unchanged_cells,
          'source_map_cells_checked': mapped_cells, 'failures': failures,
          'status': 'PASS' if not failures else 'FAIL'}
print(json.dumps(report, indent=2))
if failures:
    raise SystemExit(1)
