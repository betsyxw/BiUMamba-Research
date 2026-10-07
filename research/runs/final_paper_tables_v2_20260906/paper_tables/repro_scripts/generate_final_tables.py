#!/usr/bin/env python3
"""Generate manuscript Tables 1–6 and a cell-level provenance map.

All table values are read from the verified paper result tree.  The script never
reads PPT text or hard-codes measured results; only design descriptions and
interpretation labels are authored here.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import statistics
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    from standardize_memory_units import csv_text
    original = path.read_text(encoding="utf-8-sig")
    path.write_text(csv_text(original, str(path)), encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def one(rows: list[dict[str, str]], **selector: object) -> dict[str, str]:
    hits = [r for r in rows if all(str(r[k]) == str(v) for k, v in selector.items())]
    if len(hits) != 1:
        raise ValueError(f"Expected one row for {selector}, found {len(hits)}")
    return hits[0]


def fmt_pct(mean: float, std: float | None = None, decimals: int = 2) -> str:
    if std is None or math.isnan(std):
        return f"{mean * 100:.{decimals}f}"
    return f"{mean * 100:.{decimals}f} ± {std * 100:.{decimals}f}"


def fmt_num(mean: float, std: float | None = None, decimals: int = 2) -> str:
    if std is None or math.isnan(std):
        return f"{mean:.{decimals}f}"
    return f"{mean:.{decimals}f} ± {std:.{decimals}f}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    args = ap.parse_args()
    root = args.root.resolve()
    out = root / "paper_tables"
    csv_dir = out / "csv"
    src_dir = out / "source_inputs"
    audit_dir = out / "audits"
    script_dir = out / "repro_scripts"
    for d in (csv_dir, src_dir, audit_dir, script_dir, out / "workbook"):
        d.mkdir(parents=True, exist_ok=True)

    source_map: list[dict[str, object]] = []

    def rel(path: Path) -> str:
        return path.resolve().relative_to(root).as_posix()

    def add_map(table: str, target_file: Path, row_key: str, column: str,
                target_value: object, source_file: Path, selector: dict[str, object],
                source_columns: list[str], transform: str) -> None:
        source_map.append({
            "table": table,
            "target_csv": rel(target_file),
            "target_row_key": row_key,
            "target_column": column,
            "target_value": target_value,
            "source_csv": rel(source_file),
            "source_selector_json": json.dumps(selector, sort_keys=True, ensure_ascii=False),
            "source_columns": ";".join(source_columns),
            "transformation": transform,
            "source_sha256": sha256(source_file),
        })

    # Freeze a normalized per-seed CSV for the 25% validation ablation.
    normalized_25 = src_dir / "fractaldb25_validation_per_seed.csv"
    normalized_rows: list[dict[str, object]] = []
    for summary in sorted((root / "fractaldb/step16_acdc25_3x3").glob("*_seed*/training_summary.json")):
        data = json.loads(summary.read_text(encoding="utf-8"))
        normalized_rows.append({
            "label_fraction_percent": 25,
            "condition": data["condition"],
            "seed": data["seed"],
            "best_validation_dice": data["best_validation_dice"],
            "best_validation_hd95_mm": data["best_validation_hd95_mm"],
            "source_json": rel(summary),
            "source_json_sha256": sha256(summary),
        })
    write_csv(normalized_25, normalized_rows, [
        "label_fraction_percent", "condition", "seed", "best_validation_dice",
        "best_validation_hd95_mm", "source_json", "source_json_sha256",
    ])

    # Table 1a: reproduced Synapse results under the frozen evaluator.
    syn_overall_path = root / "synapse/final_v2/method_mean_std.csv"
    syn_organ_path = root / "synapse/final_v2/per_organ_mean_std.csv"
    nn_overall_path = root / "nnunet/isolated_test/three_seed_mean_std.csv"
    nn_organ_path = root / "nnunet/isolated_test/per_organ_three_seed_mean_std.csv"
    syn_overall, syn_organ = read_csv(syn_overall_path), read_csv(syn_organ_path)
    nn_overall, nn_organ = read_csv(nn_overall_path), read_csv(nn_organ_path)
    organs = ["Aorta", "Gallbladder", "Left Kidney", "Right Kidney", "Liver", "Pancreas", "Spleen", "Stomach"]
    table1a_path = csv_dir / "Table1a_Synapse_reproduced.csv"
    t1: list[dict[str, object]] = []
    for method, label in [("E1", "E1 (VM-UNet)"), ("E2_modify_2", "E2_modify_2 (BiUMamba)")]:
        ov = one(syn_overall, method=method)
        row: dict[str, object] = {
            "Method": label,
            "Status": "Reproduced; same frozen 14/4/12 patient split and isolated test",
            "Mean Dice (%) ↑": fmt_pct(float(ov["test_mean_dice_mean"]), float(ov["test_mean_dice_sample_std"])),
            "HD95 (mm) ↓": fmt_num(float(ov["test_mean_hd95_mm_mean"]), float(ov["test_mean_hd95_mm_sample_std"])),
            "NSD@1mm (%) ↑": fmt_pct(float(ov["test_mean_nsd_1mm_mean"]), float(ov["test_mean_nsd_1mm_sample_std"])),
        }
        add_map("Table 1a", table1a_path, label, "Mean Dice (%) ↑", row["Mean Dice (%) ↑"], syn_overall_path, {"method": method}, ["test_mean_dice_mean", "test_mean_dice_sample_std"], "mean_std_percent:2")
        add_map("Table 1a", table1a_path, label, "HD95 (mm) ↓", row["HD95 (mm) ↓"], syn_overall_path, {"method": method}, ["test_mean_hd95_mm_mean", "test_mean_hd95_mm_sample_std"], "mean_std_number:2")
        add_map("Table 1a", table1a_path, label, "NSD@1mm (%) ↑", row["NSD@1mm (%) ↑"], syn_overall_path, {"method": method}, ["test_mean_nsd_1mm_mean", "test_mean_nsd_1mm_sample_std"], "mean_std_percent:2")
        for organ in organs:
            rr = one(syn_organ, method=method, organ=organ)
            row[f"{organ} Dice (%)"] = fmt_pct(float(rr["mean_dice_mean"]), float(rr["mean_dice_sample_std"]))
            add_map("Table 1a", table1a_path, label, f"{organ} Dice (%)", row[f"{organ} Dice (%)"], syn_organ_path, {"method": method, "organ": organ}, ["mean_dice_mean", "mean_dice_sample_std"], "mean_std_percent:2")
        t1.append(row)

    nn_metrics = {r["metric"]: r for r in nn_overall}
    nn_label = "nnU-Net v2"
    nn_row: dict[str, object] = {
        "Method": nn_label,
        "Status": "Reproduced on same patient split/test set; model-specific training protocol",
        "Mean Dice (%) ↑": fmt_pct(float(nn_metrics["dice"]["mean"]), float(nn_metrics["dice"]["std_sample"])),
        "HD95 (mm) ↓": fmt_num(float(nn_metrics["hd95_mm"]["mean"]), float(nn_metrics["hd95_mm"]["std_sample"])),
        "NSD@1mm (%) ↑": fmt_pct(float(nn_metrics["nsd_1mm"]["mean"]), float(nn_metrics["nsd_1mm"]["std_sample"])),
    }
    add_map("Table 1a", table1a_path, nn_label, "Mean Dice (%) ↑", nn_row["Mean Dice (%) ↑"], nn_overall_path, {"metric": "dice"}, ["mean", "std_sample"], "mean_std_percent:2")
    add_map("Table 1a", table1a_path, nn_label, "HD95 (mm) ↓", nn_row["HD95 (mm) ↓"], nn_overall_path, {"metric": "hd95_mm"}, ["mean", "std_sample"], "mean_std_number:2")
    add_map("Table 1a", table1a_path, nn_label, "NSD@1mm (%) ↑", nn_row["NSD@1mm (%) ↑"], nn_overall_path, {"metric": "nsd_1mm"}, ["mean", "std_sample"], "mean_std_percent:2")
    for organ in organs:
        rr = one(nn_organ, organ=organ)
        nn_row[f"{organ} Dice (%)"] = fmt_pct(float(rr["mean_dice_mean"]), float(rr["mean_dice_std"]))
        add_map("Table 1a", table1a_path, nn_label, f"{organ} Dice (%)", nn_row[f"{organ} Dice (%)"], nn_organ_path, {"organ": organ}, ["mean_dice_mean", "mean_dice_std"], "mean_std_percent:2")
    t1.append(nn_row)
    t1_cols = ["Method", "Status", "Mean Dice (%) ↑", "HD95 (mm) ↓", "NSD@1mm (%) ↑"] + [f"{o} Dice (%)" for o in organs]
    write_csv(table1a_path, t1, t1_cols)

    # Table 1b: original-paper values are kept in a separate panel.
    reported_path = root / "reported_baselines/reported_transformer_results.csv"
    reported = read_csv(reported_path)
    table1b_path = csv_dir / "Table1b_Synapse_reported_baselines.csv"
    t1b = []
    for r in reported:
        label = r["method"]
        row = {
            "Method": label,
            "Original paper split": r["training_test_split"],
            "Input size": r["input_size"],
            "Mean Dice (%) ↑": r["reported_dice_percent"],
            "HD95 (mm) ↓": r["reported_hd_mm"],
            "Status": "Reported by the original paper; not reproduced under our setting",
            "Source": r["source_url"],
        }
        add_map("Table 1b", table1b_path, label, "Mean Dice (%) ↑", row["Mean Dice (%) ↑"], reported_path, {"method": label}, ["reported_dice_percent"], "identity_number:2")
        add_map("Table 1b", table1b_path, label, "HD95 (mm) ↓", row["HD95 (mm) ↓"], reported_path, {"method": label}, ["reported_hd_mm"], "identity_number:2")
        t1b.append(row)
    write_csv(table1b_path, t1b, ["Method", "Original paper split", "Input size", "Mean Dice (%) ↑", "HD95 (mm) ↓", "Status", "Source"])

    # Table 2: scan design ablation.  Screen50 and Full300 are explicitly separated.
    scan_full_path = root / "ablations/scan_design/E1_E2_E2_modify_2_full300_seed42.csv"
    scan_screen_path = root / "ablations/scan_design/E2_modify_1_vs_E2_modify_2_screen50_seed42.csv"
    scan_full, scan_screen = read_csv(scan_full_path), read_csv(scan_screen_path)
    design = {
        "E1": ("Four-direction SS2D on all channels", "Original baseline"),
        "E2": ("Horizontal forward/backward scans only", "Lower memory but loses vertical coverage"),
        "E2_modify_2": ("C/2 horizontal + C/2 vertical channels in every block", "Final BiUMamba design"),
    }
    full_col = {"E1": "e1_original_four_direction", "E2": "e2_row_bidirectional", "E2_modify_2": "e2_modify_2_grouped_2d"}
    metric_rows = {r["metric"]: r for r in scan_full}
    table2_path = csv_dir / "Table2_scan_design_ablation.csv"
    t2: list[dict[str, object]] = []
    for variant in ("E1", "E2", "E2_modify_2"):
        col = full_col[variant]
        row = {
            "Variant": variant,
            "Design": design[variant][0],
            "Protocol": "Full300; exploratory single-seed ablation",
            "Epochs": 300,
            "Seed": 42,
            "Dice (%) ↑": fmt_num(float(metric_rows["mean_dice_percentage_points"][col]), decimals=2),
            "HD95 ↓": fmt_num(float(metric_rows["mean_hd95"][col]), decimals=2),
            "Peak memory (MiB) ↓": fmt_num(float(metric_rows["peak_device_memory_mib"][col]), decimals=0),
            "Interpretation": design[variant][1],
        }
        for target_col, src_metric, transform in [
            ("Dice (%) ↑", "mean_dice_percentage_points", "identity_number:2"),
            ("HD95 ↓", "mean_hd95", "identity_number:2"),
            ("Peak memory (MiB) ↓", "peak_device_memory_mib", "identity_number:0"),
        ]:
            add_map("Table 2", table2_path, f"{variant}|Full300", target_col, row[target_col], scan_full_path, {"metric": src_metric}, [col], transform)
        t2.append(row)
    screen_metrics = {r["metric"]: r for r in scan_screen}
    for variant, col, desc in [
        ("E2_modify_1", "e2_modify_1", "Alternate horizontal/vertical scans between blocks"),
        ("E2_modify_2", "e2_modify_2", "C/2 horizontal + C/2 vertical channels in every block"),
    ]:
        row = {
            "Variant": variant,
            "Design": desc,
            "Protocol": "Screen50; exploratory single-seed ablation; not directly comparable with Full300",
            "Epochs": 50,
            "Seed": 42,
            "Dice (%) ↑": fmt_pct(float(screen_metrics["mean_dice"][col]), decimals=2),
            "HD95 ↓": fmt_num(float(screen_metrics["mean_hd95"][col]), decimals=2),
            "Peak memory (MiB) ↓": fmt_num(float(screen_metrics["peak_gpu_memory_mib"][col]), decimals=0),
            "Interpretation": "Alternate-axis screen" if variant == "E2_modify_1" else "Same-protocol screen comparator",
        }
        for target_col, src_metric, transform in [
            ("Dice (%) ↑", "mean_dice", "identity_percent:2"),
            ("HD95 ↓", "mean_hd95", "identity_number:2"),
            ("Peak memory (MiB) ↓", "peak_gpu_memory_mib", "identity_number:0"),
        ]:
            add_map("Table 2", table2_path, f"{variant}|Screen50", target_col, row[target_col], scan_screen_path, {"metric": src_metric}, [col], transform)
        t2.append(row)
    write_csv(table2_path, t2, ["Variant", "Design", "Protocol", "Epochs", "Seed", "Dice (%) ↑", "HD95 ↓", "Peak memory (MiB) ↓", "Interpretation"])

    # Table 3: fusion ablation.
    fusion_full_path = root / "ablations/fusion/E1_E2_E2_modify_2_E3_full300_seed42.csv"
    gate1_path = root / "ablations/fusion/E4_version_1_full300_seed42.csv"
    gate2_path = root / "ablations/fusion/E4_v2_stabilized_b_screen50_seed42.csv"
    fusion_full, gate1, gate2 = read_csv(fusion_full_path), read_csv(gate1_path), read_csv(gate2_path)
    fusion_specs = [
        ("Fixed sum", fusion_full_path, one(fusion_full, experiment="E2_modify_2"), "experiment", "E2_modify_2", "mean_dice", "mean_hd95", "peak_sampled_gpu_memory_mib", "Full300", "Final selected fusion"),
        ("Static learnable fusion", fusion_full_path, one(fusion_full, experiment="E3_full300"), "experiment", "E3_full300", "mean_dice", "mean_hd95", "peak_sampled_gpu_memory_mib", "Full300", "No clear gain over fixed sum"),
        ("Adaptive Gate v1", gate1_path, one(gate1, Experiment="E4_version_1_full300"), "Experiment", "E4_version_1_full300", "Mean_Dice", "Mean_HD95", "Peak_Memory_MiB", "Full300", "Unstable negative result"),
        ("Stabilized Adaptive Gate v2-B", gate2_path, one(gate2, Experiment="E4_v2_stabilized_b_epoch50"), "Experiment", "E4_v2_stabilized_b_epoch50", "Mean_Dice", "Mean_HD95", "Peak_Memory_MiB", "Screen50 + held-out; not directly comparable", "Diagnostic only"),
    ]
    table3_path = csv_dir / "Table3_fusion_ablation.csv"
    t3: list[dict[str, object]] = []
    for name, spath, r, keycol, keyval, dcol, hcol, mcol, protocol, note in fusion_specs:
        epochs_col = "epochs" if "epochs" in r else "Epochs"
        seed_col = "Seed" if "Seed" in r else None
        row = {
            "Fusion": name,
            "Protocol": protocol,
            "Epochs": r[epochs_col],
            "Seed": r[seed_col] if seed_col else 42,
            "Dice (%) ↑": fmt_pct(float(r[dcol]), decimals=2),
            "HD95 ↓": fmt_num(float(r[hcol]), decimals=2),
            "Peak memory (MiB) ↓": fmt_num(float(r[mcol]), decimals=0),
            "Conclusion": note,
        }
        for target_col, src_col, transform in [
            ("Dice (%) ↑", dcol, "identity_percent:2"),
            ("HD95 ↓", hcol, "identity_number:2"),
            ("Peak memory (MiB) ↓", mcol, "identity_number:0"),
        ]:
            add_map("Table 3", table3_path, name, target_col, row[target_col], spath, {keycol: keyval}, [src_col], transform)
        t3.append(row)
    write_csv(table3_path, t3, ["Fusion", "Protocol", "Epochs", "Seed", "Dice (%) ↑", "HD95 ↓", "Peak memory (MiB) ↓", "Conclusion"])

    # Table 4: cross-dataset patient-level means and same-GPU training memory.
    stats_path = root / "statistics/seed_level_mean_std.csv"
    paired_path = root / "statistics/paired_patient_statistics.csv"
    train_agg_path = root / "efficiency/unified_benchmark_20260906/step19_training_efficiency_aggregate.csv"
    stats, paired, train_agg = read_csv(stats_path), read_csv(paired_path), read_csv(train_agg_path)
    table4_path = csv_dir / "Table4_cross_dataset_results.csv"
    t4: list[dict[str, object]] = []
    modalities = {"Synapse": "CT", "ACDC": "MRI", "BUSI": "Ultrasound"}
    for dataset in ("Synapse", "ACDC", "BUSI"):
        dice_test = one(paired, dataset=dataset, metric="dice")
        sig = "No significant patient-level Dice difference" if float(dice_test["p_holm_across_three_metrics"]) >= 0.05 else "Significant patient-level Dice decrease for BiUMamba"
        for method in ("E1", "E2_modify_2"):
            s = one(stats, dataset=dataset, method=method)
            tr = one(train_agg, dataset=dataset, method=method)
            label = f"{dataset}|{method}"
            row = {
                "Dataset": dataset,
                "Modality": modalities[dataset],
                "Method": "E1 (VM-UNet)" if method == "E1" else "E2_modify_2 (BiUMamba)",
                "Seeds": 3,
                "Dice (%) ↑": fmt_pct(float(s["dice_mean"]), float(s["dice_std"])),
                "HD95 ↓": fmt_num(float(s["hd95_mean"]), float(s["hd95_std"])),
                "NSD (%) ↑": fmt_pct(float(s["nsd_mean"]), float(s["nsd_std"])),
                "Peak training allocated (GiB) ↓": fmt_num(float(tr["peak_training_allocated_gib_mean"]), float(tr["peak_training_allocated_gib_sample_std"] or "nan"), 2),
                "Patient-level Dice result": sig,
            }
            for target_col, cols, transform in [
                ("Dice (%) ↑", ["dice_mean", "dice_std"], "mean_std_percent:2"),
                ("HD95 ↓", ["hd95_mean", "hd95_std"], "mean_std_number:2"),
                ("NSD (%) ↑", ["nsd_mean", "nsd_std"], "mean_std_percent:2"),
            ]:
                add_map("Table 4", table4_path, label, target_col, row[target_col], stats_path, {"dataset": dataset, "method": method}, cols, transform)
            add_map("Table 4", table4_path, label, "Peak training allocated (GiB) ↓", row["Peak training allocated (GiB) ↓"], train_agg_path, {"dataset": dataset, "method": method}, ["peak_training_allocated_gib_mean", "peak_training_allocated_gib_sample_std"], "mean_std_number:2")
            t4.append(row)
    write_csv(table4_path, t4, ["Dataset", "Modality", "Method", "Seeds", "Dice (%) ↑", "HD95 ↓", "NSD (%) ↑", "Peak training allocated (GiB) ↓", "Patient-level Dice result"])

    # Table 5: three-seed 25% validation and seed42 isolated-test label fractions.
    val25 = read_csv(normalized_25)
    frac_test_path = root / "fractaldb/label_fraction_seed42_isolated_test/ACDC_FRACTALDB_LABEL_FRACTIONS_OVERALL.csv"
    frac_test = read_csv(frac_test_path)
    table5_path = csv_dir / "Table5_pretraining_ablation.csv"
    t5: list[dict[str, object]] = []
    name_map = {"scratch": "Scratch", "imagenet": "ImageNet", "fractaldb60": "FractalDB-60"}
    for cond in ("scratch", "imagenet", "fractaldb60"):
        selected = [r for r in val25 if r["condition"] == cond]
        dm = statistics.mean(float(r["best_validation_dice"]) for r in selected)
        ds = statistics.stdev(float(r["best_validation_dice"]) for r in selected)
        hm = statistics.mean(float(r["best_validation_hd95_mm"]) for r in selected)
        hs = statistics.stdev(float(r["best_validation_hd95_mm"]) for r in selected)
        key = f"validation25|{cond}"
        row = {
            "Evaluation": "Validation; formal three-seed training ablation",
            "Labels": "25%",
            "Initialization": name_map[cond],
            "Seeds": "42, 3407, 2026",
            "Dice (%) ↑": fmt_pct(dm, ds),
            "HD95 (mm) ↓": fmt_num(hm, hs),
            "NSD@1mm (%) ↑": "Not computed in validation history",
            "Interpretation": "Red: below Scratch" if cond == "fractaldb60" else "Reference initialization",
        }
        add_map("Table 5", table5_path, key, "Dice (%) ↑", row["Dice (%) ↑"], normalized_25, {"condition": cond, "label_fraction_percent": 25}, ["best_validation_dice"], "aggregate_mean_std_percent:2")
        add_map("Table 5", table5_path, key, "HD95 (mm) ↓", row["HD95 (mm) ↓"], normalized_25, {"condition": cond, "label_fraction_percent": 25}, ["best_validation_hd95_mm"], "aggregate_mean_std_number:2")
        t5.append(row)
    for pct in (25, 50, 100):
        for cond in ("scratch", "imagenet", "fractaldb60"):
            r = one(frac_test, label_fraction_percent=pct, condition=cond, seed=42)
            key = f"test{pct}|{cond}"
            if cond == "fractaldb60":
                if pct == 25:
                    interpretation = "Red; below Scratch"
                elif pct == 50:
                    interpretation = "Yellow; above Scratch but below ImageNet"
                else:
                    interpretation = "Yellow; above Scratch and close to ImageNet"
            else:
                interpretation = "Exploratory seed42 reference"
            row = {
                "Evaluation": "Isolated test; exploratory single seed",
                "Labels": f"{pct}%",
                "Initialization": name_map[cond],
                "Seeds": "42 only",
                "Dice (%) ↑": fmt_pct(float(r["test_mean_dice"])),
                "HD95 (mm) ↓": fmt_num(float(r["test_mean_hd95_mm"])),
                "NSD@1mm (%) ↑": fmt_pct(float(r["test_mean_nsd_at_1mm"])),
                "Interpretation": interpretation,
            }
            for target_col, src_col, transform in [
                ("Dice (%) ↑", "test_mean_dice", "identity_percent:2"),
                ("HD95 (mm) ↓", "test_mean_hd95_mm", "identity_number:2"),
                ("NSD@1mm (%) ↑", "test_mean_nsd_at_1mm", "identity_percent:2"),
            ]:
                add_map("Table 5", table5_path, key, target_col, row[target_col], frac_test_path, {"label_fraction_percent": pct, "condition": cond, "seed": 42}, [src_col], transform)
            t5.append(row)
    write_csv(table5_path, t5, ["Evaluation", "Labels", "Initialization", "Seeds", "Dice (%) ↑", "HD95 (mm) ↓", "NSD@1mm (%) ↑", "Interpretation"])

    # Table 6: final strict RTX 4090 inference benchmark and audited training efficiency.
    inf_path = root / "efficiency/unified_benchmark_20260906/step19_unified_inference_and_theory.csv"
    train_run_path = root / "efficiency/unified_benchmark_20260906/step19_training_efficiency_per_run.csv"
    inf, train_runs = read_csv(inf_path), read_csv(train_run_path)
    table6_path = csv_dir / "Table6_efficiency.csv"
    t6: list[dict[str, object]] = []
    for dataset in ("Synapse", "ACDC", "BUSI"):
        for method in ("E1", "E2_modify_2"):
            r = one(inf, dataset=dataset, method=method, seed=42)
            if dataset == "Synapse":
                tr = one(train_runs, dataset=dataset, method=method, seed=42)
                tr_path = train_run_path
                tr_selector = {"dataset": dataset, "method": method, "seed": 42}
                train_seeds = "42 (same-GPU comparison)"
                epoch_val, epoch_std = float(tr["mean_epoch_total_s_stable"]), None
                wall_val, wall_std = float(tr["wall_clock_training_and_validation_h"]), None
                ta_val, ta_std = float(tr["peak_training_allocated_gib"]), None
                tr_val, tr_std = float(tr["peak_training_reserved_gib"]), None
                epoch_cols, wall_cols = ["mean_epoch_total_s_stable"], ["wall_clock_training_and_validation_h"]
                ta_cols, tr_cols = ["peak_training_allocated_gib"], ["peak_training_reserved_gib"]
                tr_transform = "identity_number:2"
            else:
                tr = one(train_agg, dataset=dataset, method=method)
                tr_path = train_agg_path
                tr_selector = {"dataset": dataset, "method": method}
                train_seeds = tr["seeds"]
                epoch_val, epoch_std = float(tr["mean_epoch_total_s_stable_mean"]), float(tr["mean_epoch_total_s_stable_sample_std"])
                wall_val, wall_std = float(tr["wall_clock_training_and_validation_h_mean"]), float(tr["wall_clock_training_and_validation_h_sample_std"])
                ta_val, ta_std = float(tr["peak_training_allocated_gib_mean"]), float(tr["peak_training_allocated_gib_sample_std"])
                tr_val, tr_std = float(tr["peak_training_reserved_gib_mean"]), float(tr["peak_training_reserved_gib_sample_std"])
                epoch_cols = ["mean_epoch_total_s_stable_mean", "mean_epoch_total_s_stable_sample_std"]
                wall_cols = ["wall_clock_training_and_validation_h_mean", "wall_clock_training_and_validation_h_sample_std"]
                ta_cols = ["peak_training_allocated_gib_mean", "peak_training_allocated_gib_sample_std"]
                tr_cols = ["peak_training_reserved_gib_mean", "peak_training_reserved_gib_sample_std"]
                tr_transform = "mean_std_number:2"
            key = f"{dataset}|{method}"
            row = {
                "Dataset": dataset,
                "Method": "E1 (VM-UNet)" if method == "E1" else "E2_modify_2 (BiUMamba)",
                "Hardware": r["hardware"],
                "Input": r["input_shape"],
                "Parameters (M)": fmt_num(float(r["parameter_count"]) / 1e6, decimals=2),
                "Estimated whole-model FLOPs (G)": fmt_num(float(r["estimated_whole_model_flops_g"]), decimals=2),
                "Analytical SS2D-core FLOPs (G)": fmt_num(float(r["analytical_ss2d_scan_core_flops_g"]), decimals=2),
                "Deployable state_dict (MiB)": fmt_num(float(r["deployable_state_dict_mib"]), decimals=2),
                "Latency mean ± SD (ms)": fmt_num(float(r["mean_latency_ms"]), float(r["sample_std_latency_ms"]), 3),
                "Median latency (ms)": fmt_num(float(r["median_latency_ms"]), decimals=3),
                "P95 latency (ms)": fmt_num(float(r["p95_latency_ms"]), decimals=3),
                "Throughput (images/s)": fmt_num(float(r["throughput_images_per_second"]), decimals=2),
                "Peak inference allocated (MiB)": fmt_num(float(r["peak_inference_allocated_mib"]), decimals=2),
                "Peak inference reserved (MiB)": fmt_num(float(r["peak_inference_reserved_mib"]), decimals=2),
                "Stable epoch time (s)": fmt_num(epoch_val, epoch_std, 2),
                "Training+validation wall time (h)": fmt_num(wall_val, wall_std, 2),
                "Peak training allocated (GiB)": fmt_num(ta_val, ta_std, 2),
                "Peak training reserved (GiB)": fmt_num(tr_val, tr_std, 2),
                "Training seeds": train_seeds,
                "Protocol note": "AMP off; 20 warm-ups; 200 timed iterations; no data I/O, saving, metrics, or post-processing",
            }
            inf_maps = [
                ("Parameters (M)", ["parameter_count"], "divide_1e6_number:2"),
                ("Estimated whole-model FLOPs (G)", ["estimated_whole_model_flops_g"], "identity_number:2"),
                ("Analytical SS2D-core FLOPs (G)", ["analytical_ss2d_scan_core_flops_g"], "identity_number:2"),
                ("Deployable state_dict (MiB)", ["deployable_state_dict_mib"], "identity_number:2"),
                ("Latency mean ± SD (ms)", ["mean_latency_ms", "sample_std_latency_ms"], "mean_std_number:3"),
                ("Median latency (ms)", ["median_latency_ms"], "identity_number:3"),
                ("P95 latency (ms)", ["p95_latency_ms"], "identity_number:3"),
                ("Throughput (images/s)", ["throughput_images_per_second"], "identity_number:2"),
                ("Peak inference allocated (MiB)", ["peak_inference_allocated_mib"], "identity_number:2"),
                ("Peak inference reserved (MiB)", ["peak_inference_reserved_mib"], "identity_number:2"),
            ]
            for target_col, cols, transform in inf_maps:
                add_map("Table 6", table6_path, key, target_col, row[target_col], inf_path, {"dataset": dataset, "method": method, "seed": 42}, cols, transform)
            for target_col, cols in [
                ("Stable epoch time (s)", epoch_cols),
                ("Training+validation wall time (h)", wall_cols),
                ("Peak training allocated (GiB)", ta_cols),
                ("Peak training reserved (GiB)", tr_cols),
            ]:
                add_map("Table 6", table6_path, key, target_col, row[target_col], tr_path, tr_selector, cols, tr_transform)
            t6.append(row)
    table6_cols = [
        "Dataset", "Method", "Hardware", "Input", "Parameters (M)",
        "Estimated whole-model FLOPs (G)", "Analytical SS2D-core FLOPs (G)",
        "Deployable state_dict (MiB)", "Latency mean ± SD (ms)", "Median latency (ms)",
        "P95 latency (ms)", "Throughput (images/s)", "Peak inference allocated (MiB)",
        "Peak inference reserved (MiB)", "Stable epoch time (s)",
        "Training+validation wall time (h)", "Peak training allocated (GiB)",
        "Peak training reserved (GiB)", "Training seeds", "Protocol note",
    ]
    write_csv(table6_path, t6, table6_cols)

    source_map_path = out / "source_map" / "table_cell_source_map.csv"
    write_csv(source_map_path, source_map, [
        "table", "target_csv", "target_row_key", "target_column", "target_value",
        "source_csv", "source_selector_json", "source_columns", "transformation", "source_sha256",
    ])

    readme = f"""# BiUMamba final paper tables (v2)

Generated automatically from the verified result tree by `repro_scripts/generate_final_tables.py`.

## Contents

- `csv/`: manuscript Tables 1–6. Table 1 is split into reproduced and original-paper panels.
- `source_map/table_cell_source_map.csv`: cell-level provenance for every reported numeric result.
- `audits/`: independent cross-check report.
- `workbook/`: formatted Excel workbook for manuscript preparation.
- `source_inputs/`: normalized source CSV needed for the 25% three-seed validation aggregation.

## Important interpretation rules

1. Table 1a uses the frozen Synapse evaluator's macro-organ aggregate. Table 4 uses patient-level means, because the paired statistical unit is the patient. These values answer different questions and must not be mixed.
2. TransUNet and Swin-Unet are reported in Table 1b only: original-paper values, not reproduced under this study's 14/4/12 split.
3. Table 2 separates Full300 and Screen50. Screen50 rows are exploratory and are not directly comparable with Full300.
4. Table 3 marks both adaptive-gate results as exploratory/negative. Fixed sum remains the final design.
5. Table 5 distinguishes formal three-seed 25% validation results from exploratory seed42 isolated-test results at 25%, 50%, and 100% labels.
6. Table 6 reports estimated whole-model FLOPs, not exact FLOPs. Strict inference used one RTX 4090, AMP off, 20 warm-ups, and 200 timed iterations. Final measurements show lower memory but higher latency for E2_modify_2 in all three tested settings.

Generated table count: 7 CSV panels (Table 1 has two panels). Provenance entries: {len(source_map)}.
"""
    (out / "README.md").write_text(readme, encoding="utf-8")

    generation_manifest = {
        "schema_version": 1,
        "table_panels": [p.name for p in sorted(csv_dir.glob("*.csv"))],
        "source_map": rel(source_map_path),
        "numeric_cell_provenance_entries": len(source_map),
        "step20_merged": (root / "statistics/step20_paper_table.csv").exists(),
        "step20_5_merged": (root / "qualitative_figures/error_analysis/analysis_manifest_v2_complete.json").exists(),
        "notes": [
            "No value was copied from the PPT.",
            "Table 1 and Table 4 use different pre-declared aggregation levels.",
            "External baselines are isolated in Table 1b.",
        ],
    }
    (out / "GENERATION_MANIFEST.json").write_text(json.dumps(generation_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    script_copy = script_dir / Path(__file__).name
    if Path(__file__).resolve() != script_copy.resolve():
        shutil.copy2(Path(__file__), script_copy)


if __name__ == "__main__":
    main()
