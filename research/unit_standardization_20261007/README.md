# Memory unit update

Updated: 20261007

All published memory and model-file sizes use decimal GB:
`1 GB = 1,000,000,000 bytes`. The conversion factors from the previous
binary-megabyte and binary-gigabyte presentations are respectively
`1,048,576 / 1,000,000,000` and `1,073,741,824 / 1,000,000,000`.
Values and sample standard deviations are both converted. Dimensionless
percentage reductions, segmentation metrics, timing, FLOPs and parameters
are unchanged.

The pre-conversion repository snapshot is commit `ce93620`. Historical local
freeze ZIPs are unchanged. The public GitHub presentation is a new revision;
the cell-level source maps retain original source headers and source hashes
and explicitly record the conversion. Original GPU console output, training
logs and benchmark JSON/CSV records retain their native units and byte fields
as measurement provenance. They should not be read as the current presentation
tables.

Published Markdown uses three decimal places. CSV tables retain six decimal
places to avoid turning inference-memory or model-file sizes into zero.
Conversions of previously rounded numbers retain that original measurement
precision; this update does not imply new measurements.

The final table CSVs are cross-checked against the pre-conversion commit.
Updated plot coordinates are read from the converted Table 2. The audit
records affected files and their SHA-256 hashes.
