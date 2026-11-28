# Synapse v2 validation results

Compiled: 2026-11-28 10:15 JST (Asia/Tokyo).
Read-only harvest of finished runs. No test-set file was opened for metrics. No existing file was changed.

## Scope

This table is for the Synapse v2 protocol only: 14 training cases, 4 validation cases, and 12 isolated test cases; 300 epochs; ImageNet VMamba-S initialization. All numbers below are **validation** macro Dice and validation macro HD95. The isolated test set was not used to select a checkpoint, a seed, or a model.

Seeds 42, 3407 and 2026 were fixed in advance and are never swapped by score. Mean ± std is the sample standard deviation with `n = 3` and `ddof = 1`. A 3-seed mean is reported only when all three seeds have finished. Missing values are written as `missing`. Unfinished Phase 2 seeds are marked `running` or `pending` from the Slurm state at 2026-11-28 10:07 JST.

## Results

| Model | Seed 42 Dice | Seed 42 HD95 | Seed 42 epoch | Seed 3407 Dice | Seed 3407 HD95 | Seed 3407 epoch | Seed 2026 Dice | Seed 2026 HD95 | Seed 2026 epoch | Dice mean ± sd (n=3) | HD95 mean ± sd (n=3) | Scan budget | Train peak allocated / reserved (GB = bytes/10^9) | GPU |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| E1 (VM-UNet, `original`) | 0.79126 | 8.252 | 242 | 0.80681 | 7.882 | 209 | 0.80034 | 9.009 | 263 | 0.79947 ± 0.00781 | 8.381 ± 0.574 | 4 routes (H+, H-, V+, V-); per-route channel share 1; theoretical workload 4HWC | seed 42: 12.846 / 13.749; seeds 3407 and 2026: 12.959 / 13.673. These two groups are not comparable. | seed 42: RunPod RTX 4090; seeds 3407 and 2026: Hakusan A100 40GB |
| BiUMamba (E2_modify_2, `grouped_2d_bidirectional_sum`) | 0.77179 | 12.565 | 271 | 0.80004 | 11.342 | 225 | 0.79149 | 9.556 | 265 | 0.78777 ± 0.01449 | 11.154 ± 1.513 | 2 groups, 2 routes each (H+/H- and V+/V-); per-route channel share 1/2; theoretical workload 2HWC | 9.707 / 10.303 (identical on all 3 seeds) | RunPod RTX 4090 (all 3 seeds) |
| E5 candidate (legacy C01, r=0.25) | 0.79940 | 11.263 | 242 | 0.79072 | 8.579 | 257 | 0.79229 | 9.915 | 246 | 0.79413 ± 0.00463 | 9.919 ± 1.342 | mixed r=0.25: 4-direction share 1/4, bidirectional H and V share 3/8 each; theoretical workload 2.5HWC | 11.174 / 12.210 (identical on all 3 seeds) | Hakusan A100 40GB (all 3 seeds) |
| G4-Single (`grouped_4_single`), incomplete | 0.79560 | 10.917 | 242 | 0.79054 | 9.290 | 193 | running | running | running | missing (2/3 seeds finished) | missing (2/3 seeds finished) | 4 groups, 1 route each (H+, H-, V+, V-); per-route channel share 1/4; theoretical workload HWC | 8.294 / 9.171 (identical on the 2 finished seeds); seed 2026: missing | Hakusan A100 40GB; seed 2026 still running (job 1082044) |
| G4-Paired (`grouped_4_paired`), incomplete | running | running | running | pending | pending | pending | pending | pending | pending | missing (0/3 seeds finished) | missing (0/3 seeds finished) | 4 groups, 2 routes each, pairs (H+,V+), (H-,V-), (H+,V-), (H-,V+); per-route channel share 1/4; theoretical workload 2HWC | missing | Hakusan A100 40GB planned; seed 42 running (job 1082045); seeds 3407 and 2026 pending (jobs 1082046, 1082047) |

HD95 units: voxels (unit spacing), as stored in `best_validation_hd95_voxels`. Markdown values are rounded (Dice to 5 decimals, HD95 to 3 decimals, means and sd to the same). Exact values are in `RESULTS_TABLE_VAL.csv` and in the source `training_summary.json` files listed in `SOURCES.txt`.

## Table notes

1. **Sources and jobs.** E1 seed 42 and all three BiUMamba seeds come from the paper_final_results_v2 archive, imported on Hakusan and also verified on the Mac. The Hakusan and Mac `training_summary.json` files have identical SHA-256 hashes. E1 seeds 3407 and 2026 are Hakusan jobs 644012 and 644013. E5 seeds 42, 3407 and 2026 are Hakusan jobs 814143, 822106 and 822107. Finished G4-Single seeds 42 and 3407 are Hakusan jobs 1082042 and 1082043. See `SOURCES.txt` for the path and SHA-256 of every source file.

2. **GPU labels.** E1 seeds 3407/2026, all E5 seeds, and the finished G4-Single seeds have a per-run `gpu_info.txt` that names `NVIDIA A100-PCIE-40GB`. E1 seed 42 and the three BiUMamba seeds have no per-run `gpu_info.txt`. They are labelled RunPod RTX 4090 from the import path `imported_baselines_seed42_runpod`, the paper package README ("RunPod checkpoints"), and the package environment snapshot `gpu_summary.csv` / `nvidia_smi_q.txt` (`NVIDIA GeForce RTX 4090`).

3. **Checkpoint rule.** The same rule is used for every row: select the epoch with the highest validation macro Dice; if Dice values differ by at most `1e-12`, select the lower validation macro HD95. This is written in the Synapse v2 `CHECKPOINT_POLICY.md`, in the Phase 2 `FREEZE.md`, and in `ValidationCheckpointSelector` (`experiments/E2_modify_2_synapse_v2/checkpointing.py`). E1, BiUMamba, E5/C01 and Phase 2 trainers all call this selector. I recomputed the selected epoch from each 300-entry `validation_history.json`. Every history matched its `training_summary.json` exactly. No history had NaN or Inf. In every finished run, the best Dice appeared at only one epoch, so the tie-break was not used.

4. **Standard deviation.** Mean ± std uses the sample standard deviation (`statistics.stdev`, `ddof=1`) over the three pre-registered seeds. It is not a standard error. For G4 rows the 3-seed mean is `missing` because the seed set is incomplete. A 2-seed mean is not reported.

5. **G4 rows are incomplete.** At 10:07 JST on 2026-11-28, job 1082044 (G4-Single seed 2026) and job 1082045 (G4-Paired seed 42) were running. Jobs 1082046 and 1082047 were pending (`QOSMaxJobsPerUserLimit`). These rows must not be treated as finished 3-seed results.

6. **Memory is not comparable across GPUs.** Training peak memory is the `peak_gpu_allocated_bytes` and `peak_gpu_reserved_bytes` recorded in each training summary, converted with GB = bytes / 10^9. E1 mixes RTX 4090 (seed 42) and A100 (seeds 3407 and 2026), so those memory figures must not be averaged or compared with each other. BiUMamba memory is RTX 4090 only. E5 and finished G4-Single memory is A100 only. Cross-GPU memory comparison is not valid.

7. **E5 seed 42 is the selection seed.** The E5 seed-42 summary is labelled `EXPLORATORY_seed42_only`. Seeds 3407 and 2026 are labelled `confirmation_replicate`. All three seeds are listed because they exist, but seed 42 was used to choose this candidate. E5 used the C01 trainer (commit `198473c`, `scan_ratio=0.25`) and the same Synapse v2 protocol hashes as the other rows (training config, seeds file, augmentation, train split, and validation split).

8. **Scan budget.** E1, BiUMamba and E5 descriptions come from `forward_corev0`, `forward_core_grouped_2d`, and `ss2d_ratio.py` (`split_channels` at r=0.25). G4 descriptions come from Phase 2 `FREEZE.md` and `forward_core_grouped_4`. Workload is the theoretical scan cost in units of HWC.

9. **Protocol checks.** Every finished summary has `protocol=synapse_v2` and `test_access_during_training=false`. The train-split, validation-split, training-config and seeds-file hashes match across E1, BiUMamba, E5 and G4-Single.

## Chinese summary

这张表只报告 Synapse v2 验证集结果。验证集有 4 个病例。三个 seed（42、3407、2026）是预先固定的，没有按分数更换，也没有使用测试集。

在验证集 Dice 上，E1（VM-UNet）的 3-seed 均值最高，为 0.79947 ± 0.00781。E5 候选是 0.79413 ± 0.00463，略低于 E1。BiUMamba 是 0.78777 ± 0.01449，低于 E1，而且三个 seed 之间的波动更大。HD95 同样是 E1 更好（数值更低）：E1 为 8.381 ± 0.574，E5 为 9.919 ± 1.342，BiUMamba 为 11.154 ± 1.513。在全部三个 seed 上，BiUMamba 的验证 Dice 都不高于同 seed 的 E1，HD95 也不低于同 seed 的 E1。

E5 只在用来挑选方案的 seed 42 上，Dice 高于 E1（0.79940 对 0.79126）。在两个确认 seed（3407 和 2026）上，E5 的 Dice 都低于 E1。因此不能把 seed 42 的优势当成已经确认的提升。

BiUMamba 明确更好的地方是扫描预算，以及在同一块 RTX 4090 上记录的训练显存。它的理论扫描量是 2HWC，E1 是 4HWC。它的训练峰值 allocated 是 9.707 GB，E1 的 seed 42 是 12.846 GB。E1 的另外两个 seed 是在 A100 上训练的，显存不能和 4090 直接比较。

G4-Single 目前只完成了 seed 42 和 3407，还不能计算 3-seed 均值。G4-Paired 还没有完成的 seed。这两行不完整，现在不能下结论。

验证集只有 4 个病例，三个 seed 之间的差别有可能仍在噪声范围内。这里不做“显著更好”或 SOTA 的判断。
