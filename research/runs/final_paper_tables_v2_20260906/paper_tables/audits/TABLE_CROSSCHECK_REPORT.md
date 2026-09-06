# Table 1–6 cross-check report

**Overall status: PASS**

- Numeric table cells checked: 205
- Passed: 205
- Failed: 0
- Latest Step 20 present: True
- Latest Step 20.5 present: True

## Coverage by table

| Table | Cells checked | Passed | Failed |
|---|---:|---:|---:|
| Table 1a | 33 | 33 | 0 |
| Table 1b | 4 | 4 | 0 |
| Table 2 | 15 | 15 | 0 |
| Table 3 | 12 | 12 | 0 |
| Table 4 | 24 | 24 | 0 |
| Table 5 | 33 | 33 | 0 |
| Table 6 | 84 | 84 | 0 |

## Method

For every mapped numeric cell, this audit re-opens the declared source CSV, verifies its SHA-256, selects the declared row(s), re-applies the declared formatting/aggregation, and confirms that the resulting value is present in the declared target-table column.

Table 1 is intentionally split into reproduced results and original-paper reported baselines. Screen50 and Full300 results are never presented as directly comparable. Table 5 keeps validation and isolated-test results in separate rows.
