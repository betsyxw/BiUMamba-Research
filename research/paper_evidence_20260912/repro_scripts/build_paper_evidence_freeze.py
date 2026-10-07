#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs" / "BiUMamba_Paper_Evidence_Freeze_20260912_v1"
V2 = ROOT / "outputs" / "paper_final_results_v2_verified" / "paper_final_results_v2"
E1N = ROOT / "outputs" / "BiUMamba_E1_Narrow_Update_20260911"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def copy_file(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def parse_mean_std(value: str):
    parts = value.replace("±", "+/-").split("+/-")
    return float(parts[0].strip()), float(parts[1].strip()) if len(parts) > 1 else 0.0


def source_cell_map(target_name: str, target_path: Path, source_path: Path):
    rows = read_csv(target_path)
    source_rows = read_csv(source_path)
    source_fields = list(source_rows[0].keys()) if source_rows else []
    source_hash = sha256(source_path)
    mapped = []
    for r_idx, row in enumerate(rows, start=2):
        for c_idx, (col, value) in enumerate(row.items(), start=1):
            mapped.append({
                "table": target_name,
                "target_csv": str(target_path.relative_to(OUT)),
                "target_cell": f"R{r_idx}C{c_idx}",
                "target_column": col,
                "target_value": value,
                "source_csv": str(source_path),
                "source_row": r_idx,
                "source_column": source_fields[c_idx - 1] if c_idx <= len(source_fields) else col,
                "source_sha256": source_hash,
                "transformation": "identity copy from audited frozen table CSV",
            })
    return mapped


def build_tables():
    csv_dir = OUT / "paper_tables" / "csv"
    source_map = []
    unchanged = [
        "Table1a_Synapse_reproduced.csv",
        "Table1b_Synapse_reported_baselines.csv",
        "Table3_fusion_ablation.csv",
        "Table5_pretraining_ablation.csv",
        "Table7_paired_statistical_tests.csv",
    ]
    for name in unchanged:
        src = V2 / "paper_tables" / "csv" / name
        dst = csv_dir / name
        copy_file(src, dst)
        source_map.extend(source_cell_map(name, dst, src))

    # Table 2 is reorganized around explicit research questions, while preserving values.
    src2 = E1N / "paper_tables" / "csv" / "Table2_scan_design_ablation_updated.csv"
    source2 = read_csv(src2)
    questions = {
        "E1": "What is the cost of full four-direction SS2D?",
        "E2": "Can one spatial axis be removed safely?",
        "E2_modify_1": "Is alternating one axis between blocks sufficient?",
        "E2_modify_2": "Can both axes remain in every block at lower scan cost?",
        "E1 (VM-UNet)": "What is the full-capacity reference under the formal protocol?",
        "E1-Narrow": "Is uniform width reduction an adequate memory-matched substitute?",
        "E2_modify_2 (BiUMamba)": "Does structured directional allocation provide a better memory trade-off?",
    }
    rows2 = []
    for r in source2:
        rows2.append({
            "Panel": r["Panel"],
            "Variant": r["Variant"],
            "Research question": questions[r["Variant"]],
            "Directional design": r["Scan directions / design"],
            "Per-path capacity": r["Capacity"],
            "Axis coverage": r["Axis coverage"],
            "Protocol and evidence": r["Protocol"],
            "Seeds": r["Seeds"],
            "Dice (%) ↑": r["Dice (%) ↑"],
            "HD95 ↓": r["HD95 ↓"],
            "NSD (%) ↑": r["NSD (%) ↑"],
            "Parameters (M)": r["Parameters (M)"],
            "Peak training memory (GiB) ↓": r["Peak training memory (GiB) ↓"],
            "Evidence-based interpretation": r["Conclusion"],
        })
    dst2 = csv_dir / "Table2_scan_design_and_memory_control.csv"
    write_csv(dst2, rows2)
    # Field-level mapping back to the audited updated Table 2.
    src2_hash = sha256(src2)
    for ridx, r in enumerate(rows2, start=2):
        original = source2[ridx - 2]
        for cidx, (col, value) in enumerate(r.items(), start=1):
            source_col = {
                "Directional design": "Scan directions / design",
                "Per-path capacity": "Capacity",
                "Protocol and evidence": "Protocol",
                "Evidence-based interpretation": "Conclusion",
            }.get(col, col)
            source_map.append({
                "table": "Table 2",
                "target_csv": str(dst2.relative_to(OUT)),
                "target_cell": f"R{ridx}C{cidx}",
                "target_column": col,
                "target_value": value,
                "source_csv": str(src2) if col != "Research question" else "author-defined research-question mapping",
                "source_row": ridx,
                "source_column": source_col if col != "Research question" else r["Variant"],
                "source_sha256": src2_hash if col != "Research question" else "not_applicable",
                "transformation": "renamed/reordered field" if col != "Research question" else "interpretive label; no numeric transformation",
            })

    # Table 4 adds target/scope fields but keeps all reported numbers from the audited E1-Narrow update.
    src4 = E1N / "paper_tables" / "csv" / "Table4_cross_dataset_results_updated.csv"
    source4 = read_csv(src4)
    target = {"Synapse": "Eight abdominal organs", "ACDC": "RV, myocardium, and LV", "BUSI": "Breast lesions"}
    scope = {
        "Synapse": "Favorable observed accuracy-memory trade-off; E1 remains faster in strict inference.",
        "ACDC": "Small observed mean differences and lower training memory; E1 remains faster in strict inference.",
        "BUSI": "Memory reduction did not preserve segmentation performance; ultrasound limitation.",
    }
    rows4 = []
    for r in source4:
        rows4.append({
            "Dataset": r["Dataset"], "Modality": r["Modality"], "Target": target[r["Dataset"]],
            "Method": r["Method"], "Seeds": r["Seeds"], "Dice (%) ↑": r["Dice (%) ↑"],
            "HD95 ↓": r["HD95 ↓"], "NSD (%) ↑": r["NSD (%) ↑"],
            "Peak training allocated (GiB) ↓": r["Peak training allocated (GiB) ↓"],
            "Strict inference latency (ms) ↓": r["Strict inference latency (ms) ↓"],
            "Statistical/experimental conclusion": r["Evidence-based conclusion"],
            "Applicability statement": scope[r["Dataset"]],
        })
    dst4 = csv_dir / "Table4_cross_dataset_scope.csv"
    write_csv(dst4, rows4)
    src4_hash = sha256(src4)
    for ridx, r in enumerate(rows4, start=2):
        for cidx, (col, value) in enumerate(r.items(), start=1):
            derived = col in {"Target", "Applicability statement"}
            source_map.append({
                "table": "Table 4", "target_csv": str(dst4.relative_to(OUT)),
                "target_cell": f"R{ridx}C{cidx}", "target_column": col, "target_value": value,
                "source_csv": "frozen protocol and evidence synthesis" if derived else str(src4),
                "source_row": ridx, "source_column": col if col != "Statistical/experimental conclusion" else "Evidence-based conclusion",
                "source_sha256": "not_applicable" if derived else src4_hash,
                "transformation": "scope label; no numeric transformation" if derived else "identity copy from audited frozen table CSV",
            })

    src6 = E1N / "paper_tables" / "csv" / "Table6_efficiency_updated.csv"
    dst6 = csv_dir / "Table6_efficiency.csv"
    copy_file(src6, dst6)
    source_map.extend(source_cell_map("Table 6", dst6, src6))

    # Separate matched-memory statistical evidence; this avoids mixing it into cross-dataset Table 7.
    src7b = E1N / "statistics" / "paired_statistics.csv"
    dst7b = csv_dir / "Table7b_Synapse_matched_memory_statistics.csv"
    copy_file(src7b, dst7b)
    source_map.extend(source_cell_map("Table 7b", dst7b, src7b))

    write_csv(OUT / "paper_tables" / "source_map" / "table_cell_source_map.csv", source_map)


def build_related_work():
    rows = [
        {"Method": "VM-UNet", "Channel grouping": "No", "Directional allocation": "Four directions process all channels", "Bidirectional on each axis": "Yes", "Cross-group mechanism": "Not applicable", "Primary setting": "Medical image segmentation", "Difference from BiUMamba": "Full directional capacity and higher scan-core workload", "Source": "https://arxiv.org/abs/2402.02491"},
        {"Method": "GroupMamba", "Channel grouping": "Four groups", "Directional allocation": "One unidirectional scan per group", "Bidirectional on each axis": "No within a group", "Cross-group mechanism": "Channel Affinity Modulation", "Primary setting": "Generic vision", "Difference from BiUMamba": "Four unidirectional groups rather than two axis-specific bidirectional groups", "Source": "https://openaccess.thecvf.com/content/CVPR2025/html/Shaker_GroupMamba_Efficient_Group-Based_Visual_State_Space_Model_CVPR_2025_paper.html"},
        {"Method": "LocalMamba", "Channel grouping": "No directional channel grouping", "Directional allocation": "Windowed scans and layer-wise scan-choice search", "Bidirectional on each axis": "Pattern dependent", "Cross-group mechanism": "Not the central design", "Primary setting": "Generic vision", "Difference from BiUMamba": "Optimizes local windows and per-layer scan patterns rather than axis-specific channel allocation", "Source": "https://doi.org/10.1007/978-3-031-91979-4_2"},
        {"Method": "EfficientVMamba", "Channel grouping": "Spatial skip-sampling rather than axis groups", "Directional allocation": "Atrous selective scan", "Bidirectional on each axis": "Different formulation", "Cross-group mechanism": "Dual-path convolution and channel attention", "Primary setting": "Generic vision", "Difference from BiUMamba": "Reduces spatial samples instead of assigning channel halves to bidirectional axes", "Source": "https://doi.org/10.1609/aaai.v39i6.32690"},
        {"Method": "BiUMamba", "Channel grouping": "Two axis-specific groups", "Directional allocation": "Horizontal F/B on C/2; vertical F/B on C/2", "Bidirectional on each axis": "Yes", "Cross-group mechanism": "Concatenation and linear projection", "Primary setting": "U-shaped medical image segmentation", "Difference from BiUMamba": "Proposed method", "Source": "This study"},
    ]
    write_csv(OUT / "related_work" / "method_difference_table.csv", rows)


def draw_core_figure():
    out = OUT / "figures" / "method"
    out.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(13, 6), constrained_layout=True)
    colors = {"h": "#D95F59", "v": "#4C78A8", "neutral": "#F4F6F8", "accent": "#2A9D8F"}
    titles = ["E1: full four-direction SS2D", "BiUMamba: axis-specific channel grouping"]
    for ax, title in zip(axes, titles):
        ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off"); ax.set_title(title, fontsize=15, fontweight="bold", pad=12)
        ax.add_patch(FancyBboxPatch((0.5, 4.0), 2.0, 2.0, boxstyle="round,pad=0.08", fc=colors["neutral"], ec="#666"))
        ax.text(1.5, 5.0, "Input feature\nH × W × C", ha="center", va="center", fontsize=12)
    # E1 paths
    labels = [("Horizontal forward\nC channels", 4.0, 8.0, colors["h"]), ("Horizontal backward\nC channels", 4.0, 5.7, colors["h"]),
              ("Vertical forward\nC channels", 4.0, 3.3, colors["v"]), ("Vertical backward\nC channels", 4.0, 1.0, colors["v"])]
    for text, x, y, color in labels:
        axes[0].add_patch(FancyBboxPatch((x, y), 3.0, 1.2, boxstyle="round,pad=0.06", fc=color+"22", ec=color, lw=1.6))
        axes[0].text(x+1.5, y+0.6, text, ha="center", va="center", fontsize=11)
        axes[0].add_patch(FancyArrowPatch((2.5,5.0),(x,y+0.6),arrowstyle="->",mutation_scale=12,color="#666"))
    axes[0].text(8.0, 5.0, "Fixed sum", ha="center", va="center", fontsize=12, bbox=dict(boxstyle="round", fc="#FFF3CD", ec="#A67C00"))
    for _, x, y, _ in labels:
        axes[0].add_patch(FancyArrowPatch((x+3.0,y+0.6),(7.4,5.0),arrowstyle="->",mutation_scale=10,color="#888"))
    axes[0].text(5.5, 0.15, "Directional scan-core workload ∝ 4HWC", ha="center", fontsize=13, fontweight="bold")
    # BiUMamba groups
    axes[1].add_patch(FancyBboxPatch((3.2, 5.7), 3.3, 3.0, boxstyle="round,pad=0.08", fc=colors["h"]+"18", ec=colors["h"], lw=1.8))
    axes[1].text(4.85, 8.35, "Horizontal group (C/2)", ha="center", fontsize=12, fontweight="bold", color=colors["h"])
    axes[1].text(4.85, 7.45, "Forward: C/2", ha="center", fontsize=11)
    axes[1].text(4.85, 6.55, "Backward: C/2", ha="center", fontsize=11)
    axes[1].add_patch(FancyBboxPatch((3.2, 1.3), 3.3, 3.0, boxstyle="round,pad=0.08", fc=colors["v"]+"18", ec=colors["v"], lw=1.8))
    axes[1].text(4.85, 3.95, "Vertical group (C/2)", ha="center", fontsize=12, fontweight="bold", color=colors["v"])
    axes[1].text(4.85, 3.05, "Forward: C/2", ha="center", fontsize=11)
    axes[1].text(4.85, 2.15, "Backward: C/2", ha="center", fontsize=11)
    for y in (7.2, 2.8):
        axes[1].add_patch(FancyArrowPatch((2.5,5.0),(3.2,y),arrowstyle="->",mutation_scale=12,color="#666"))
    axes[1].text(8.1, 5.0, "Concatenate\n+ linear projection", ha="center", va="center", fontsize=12, bbox=dict(boxstyle="round", fc="#DFF2EF", ec=colors["accent"]))
    for y in (7.2, 2.8):
        axes[1].add_patch(FancyArrowPatch((6.5,y),(7.3,5.0),arrowstyle="->",mutation_scale=10,color="#888"))
    axes[1].text(5.5, 0.15, "Directional scan-core workload ∝ 2HWC", ha="center", fontsize=13, fontweight="bold")
    fig.suptitle("E1 and BiUMamba directional allocation", fontsize=18, fontweight="bold")
    fig.savefig(out / "Figure_method_E1_vs_BiUMamba.png", dpi=300, bbox_inches="tight")
    fig.savefig(out / "Figure_method_E1_vs_BiUMamba.pdf", bbox_inches="tight")
    plt.close(fig)


def draw_pareto_figures():
    rows = read_csv(OUT / "paper_tables" / "csv" / "Table2_scan_design_and_memory_control.csv")
    formal = {r["Variant"]: r for r in rows if r["Panel"].startswith("B:")}
    order = ["E1 (VM-UNet)", "E1-Narrow", "E2_modify_2 (BiUMamba)"]
    labels = {"E1 (VM-UNet)": "E1", "E1-Narrow": "E1-Narrow", "E2_modify_2 (BiUMamba)": "BiUMamba"}
    colors = {"E1 (VM-UNet)": "#6B7280", "E1-Narrow": "#E69F00", "E2_modify_2 (BiUMamba)": "#0072B2"}
    out = OUT / "figures" / "pareto"; out.mkdir(parents=True, exist_ok=True)
    for metric, ylabel, fname in [("Dice (%) ↑", "Mean Dice (%)", "Figure_pareto_Dice_vs_memory"), ("NSD (%) ↑", "Mean NSD (%)", "Figure_pareto_NSD_vs_memory")]:
        fig, ax = plt.subplots(figsize=(7.2, 5.4), constrained_layout=True)
        for key in order:
            r = formal[key]
            mean, sd = parse_mean_std(r[metric])
            x = (float(r["Peak training memory (GB) ↓"])
                 if "Peak training memory (GB) ↓" in r
                 else float(r["Peak training memory (GiB) ↓"]) * 2**30 / 1e9)
            ax.errorbar(x, mean, yerr=sd, fmt="o", ms=9, capsize=4, color=colors[key], label=labels[key])
            ax.annotate(labels[key], (x, mean), xytext=(7, 7), textcoords="offset points", fontsize=10)
        ax.set_xlabel("Peak training allocated memory (GB; RTX 4090)")
        ax.set_ylabel(ylabel)
        ax.set_title(f"Synapse {ylabel}–memory comparison")
        ax.grid(True, alpha=0.22)
        ax.text(0.01, -0.18, "Error bars show the sample SD across seeds 42, 2026, and 3407. Left and upward are favorable.", transform=ax.transAxes, fontsize=9)
        fig.savefig(out / f"{fname}.png", dpi=300, bbox_inches="tight")
        fig.savefig(out / f"{fname}.pdf", bbox_inches="tight")
        plt.close(fig)


def parse_ci(s):
    a, b = s.split(" to ")
    return float(a), float(b)


def draw_forest():
    rows = read_csv(OUT / "paper_tables" / "csv" / "Table7_paired_statistical_tests.csv")
    metrics = ["Dice (primary)", "HD95 (secondary)", "NSD (secondary)"]
    datasets = ["Synapse", "ACDC", "BUSI"]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.7), constrained_layout=True)
    for ax, metric in zip(axes, metrics):
        subset = {r["Dataset"]: r for r in rows if r["Metric"] == metric}
        for y, ds in enumerate(datasets[::-1]):
            r = subset[ds]
            val = float(r["Paired difference (BiUMamba − E1)"])
            lo, hi = parse_ci(r["Bootstrap 95% CI"])
            sig = float(r["Holm-adjusted p"]) < 0.05
            ax.errorbar(val, y, xerr=[[val-lo], [hi-val]], fmt="o", capsize=4, color="#B22222" if sig else "#2C5282", ms=7)
        ax.axvline(0, color="#666", lw=1, ls="--")
        ax.set_yticks(range(3), datasets[::-1])
        ax.set_title(metric.replace(" (primary)", "").replace(" (secondary)", ""))
        ax.set_xlabel("BiUMamba − E1 (pp)" if "HD95" not in metric else "BiUMamba − E1 (mm)")
        ax.grid(axis="x", alpha=0.2)
    fig.suptitle("Patient-level paired differences with bootstrap 95% confidence intervals", fontsize=15, fontweight="bold")
    fig.text(0.5, -0.02, "Red marks indicate Holm-adjusted p < 0.05. Patient/case means were formed across three seeds before pairing.", ha="center", fontsize=9)
    out = OUT / "figures" / "statistics"; out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / "Figure_patient_level_forest_plot.png", dpi=300, bbox_inches="tight")
    fig.savefig(out / "Figure_patient_level_forest_plot.pdf", bbox_inches="tight")
    plt.close(fig)


def copy_qualitative():
    src = V2 / "qualitative_figures" / "step23_publication_figures"
    dst = OUT / "qualitative_figures" / "fixed_rule_selection"
    for name in ["STEP23_REPORT.md", "STEP23_SELECTION_AND_METRIC_MANIFEST.csv", "STEP23_SELECTION_AND_METRIC_MANIFEST.json", "STEP23_SHA256_MANIFEST.csv"]:
        copy_file(src / name, dst / name)
    for dataset in ["synapse", "acdc", "busi"]:
        sdir = src / dataset / "medical_images_DO_NOT_UPLOAD_GITHUB"
        ddir = dst / dataset / "medical_images_DO_NOT_UPLOAD_GITHUB"
        for p in sdir.glob("*"):
            if p.is_file(): copy_file(p, ddir / p.name)
    # Preserve full seven-category selection records, even though the main composite shows four panels.
    for dataset in ["synapse", "acdc", "busi"]:
        s = V2 / "qualitative_figures" / "fixed_selection_v2" / dataset / "selection_manifest_rendered.csv"
        copy_file(s, dst / dataset / "full_fixed_selection_manifest.csv")


def crosscheck_tables():
    mappath = OUT / "paper_tables" / "source_map" / "table_cell_source_map.csv"
    maps = read_csv(mappath)
    failures = []
    checked = 0
    for m in maps:
        if m["source_sha256"] in {"not_applicable", ""}:
            continue
        src = Path(m["source_csv"])
        if not src.exists() or sha256(src) != m["source_sha256"]:
            failures.append({"target": m["target_cell"], "reason": "source missing or hash mismatch"})
            continue
        checked += 1
    report = {
        "status": "PASS" if not failures else "FAIL",
        "mapped_cells": len(maps), "hash_checked_cells": checked,
        "failures": failures,
        "notes": [
            "Table 1/4 seed-level mean±SD and Table 7 patient-level aggregated means are distinct reporting levels.",
            "Table 2 Screen50 and Full300 rows are explicitly separated.",
            "E1-Narrow is a Synapse-only near-memory-matched control selected before full training.",
        ],
    }
    p = OUT / "audit" / "TABLE_CROSSCHECK_REPORT.json"; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(report, indent=2), encoding="utf-8")
    (p.parent / "TABLE_CROSSCHECK_REPORT.md").write_text(
        "# Final table cross-check\n\n"
        f"Status: **{report['status']}**\n\n"
        f"Mapped cells: {report['mapped_cells']}  \nHash-checked source cells: {report['hash_checked_cells']}  \nFailures: {len(failures)}\n\n"
        "The audit verifies every declared source file against its recorded SHA-256. Numeric content is copied from previously audited frozen table CSVs; newly added research-question and applicability columns are interpretive labels and are marked as such in the source map.\n\n"
        "Table 1/4 report seed-level mean ± SD. Table 7 reports patient/case-level means after averaging within each unit across three seeds; these levels must not be substituted for each other.\n",
        encoding="utf-8")
    if failures:
        raise RuntimeError(f"Cross-check failed: {failures[:3]}")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    build_tables()
    # Convert presentation outputs while retaining frozen source measurements.
    from standardize_memory_units import csv_text
    for table in (OUT / "paper_tables").rglob("*.csv"):
        original = table.read_text(encoding="utf-8-sig")
        table.write_text(csv_text(original, str(table)), encoding="utf-8")
    build_related_work()
    draw_core_figure()
    draw_pareto_figures()
    draw_forest()
    copy_qualitative()
    crosscheck_tables()


if __name__ == "__main__":
    main()
