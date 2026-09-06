#!/usr/bin/env python3
"""Create paper-ready Step 20/20.5 tables, reports, and completion manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def format_ci(row: pd.Series) -> str:
    return f'{row.bootstrap_95ci_low:.4f} to {row.bootstrap_95ci_high:.4f}'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final-root", type=Path, default=Path("/workspace/paper_final_results_v2"))
    args = parser.parse_args()
    root = args.final_root
    stats_dir = root / "statistics"
    error_dir = root / "qualitative_figures/error_analysis"
    fixed_dir = root / "qualitative_figures/fixed_selection_v2"
    manifests = root / "manifests"

    paired = pd.read_csv(stats_dir / "paired_patient_statistics.csv")
    paper = paired[
        [
            "dataset", "metric", "n_units", "e1_unit_mean", "e2_unit_mean",
            "mean_difference_e2_minus_e1", "bootstrap_95ci_low", "bootstrap_95ci_high",
            "selected_test", "p_raw_two_sided", "p_holm_across_three_metrics",
            "paired_cohens_dz", "rank_biserial",
        ]
    ].copy()
    paper["bootstrap_95ci"] = paper.apply(format_ci, axis=1)
    paper.to_csv(stats_dir / "step20_paper_table.csv", index=False)

    lines = [
        "# Step 20 Statistical Report",
        "",
        "Status: complete for the planned three-seed patient-level analysis.",
        "",
        "## Frozen protocol",
        "",
        "- Seeds: 42, 3407, and 2026.",
        "- The independent unit is the patient for Synapse and ACDC and the cleaned lesion group for BUSI.",
        "- Results are first averaged within each unit across the three seeds; slices and seeds are not pooled as independent samples.",
        "- Bootstrap confidence intervals use 10,000 unit-level resamples with seed 20260906.",
        "- A paired t-test is used when the paired differences pass the Shapiro-Wilk rule (p >= 0.05); otherwise a Wilcoxon signed-rank test is used.",
        "- Holm adjustment is reported across Dice, HD95, and NSD within each dataset. Organ/structure tests have their own Holm-adjusted table.",
        "",
        "## Main results",
        "",
        "| Dataset | Metric | E1 mean | E2_modify_2 mean | Mean difference | Bootstrap 95% CI | Test | Holm p |",
        "|---|---:|---:|---:|---:|---:|---|---:|",
    ]
    order = {"Synapse": 0, "ACDC": 1, "BUSI": 2}
    for _, row in paired.sort_values(["dataset", "metric"], key=lambda col: col.map(order) if col.name == "dataset" else col).iterrows():
        lines.append(
            f'| {row.dataset} | {row.metric.upper()} | {row.e1_unit_mean:.4f} | {row.e2_unit_mean:.4f} | '
            f'{row.mean_difference_e2_minus_e1:+.4f} | [{row.bootstrap_95ci_low:+.4f}, {row.bootstrap_95ci_high:+.4f}] | '
            f'{row.selected_test} | {row.p_holm_across_three_metrics:.4g} |'
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "E2_modify_2 achieved comparable patient-level Dice, HD95, and NSD to E1 on Synapse CT and ACDC MRI. On BUSI ultrasound, Dice and NSD decreased and HD95 increased after Holm correction. Therefore, the evidence supports an accuracy-memory trade-off on Synapse and ACDC, but not equal performance across all medical-image types.",
        "",
        "## Supporting files",
        "",
        "- `patient_level_paired_differences.csv`: paired unit-level source table.",
        "- `paired_patient_statistics.csv`: complete tests, confidence intervals, and effect sizes.",
        "- `organ_or_class_paired_statistics_holm.csv`: organ/structure/class analyses with Holm adjustment.",
        "- `anomaly_cases/`: ranked Synapse, ACDC, and BUSI cases.",
        "- `figures/paired_difference_forest_plot.*`: paper-ready forest plot.",
        "- `figures/paired_difference_distributions.*`: paired-difference distributions.",
        "",
    ]
    (stats_dir / "STEP20_STATISTICAL_REPORT.md").write_text("\n".join(lines), encoding="utf-8")

    subgroup_frames = []
    subgroup_files = {
        "size": "busi_size_group_complete_paired_statistics.csv",
        "shape": "busi_shape_group_paired_statistics.csv",
        "contrast": "busi_contrast_group_paired_statistics.csv",
    }
    for grouping, filename in subgroup_files.items():
        frame = pd.read_csv(error_dir / filename)
        group_col = f"{grouping}_group"
        frame = frame.loc[frame.metric.isin(["dice", "precision", "recall", "false_positive_to_gt_ratio", "false_negative_to_gt_ratio"])].copy()
        frame.insert(0, "grouping", grouping)
        frame.rename(columns={group_col: "group"}, inplace=True)
        subgroup_frames.append(frame)
    subgroup = pd.concat(subgroup_frames, ignore_index=True)
    subgroup.to_csv(error_dir / "step20_5_busi_subgroup_paper_table.csv", index=False)

    low_dice = subgroup[(subgroup.grouping == "contrast") & (subgroup.group == "Low") & (subgroup.metric == "dice")].iloc[0]
    large_dice = subgroup[(subgroup.grouping == "size") & (subgroup.group == "Large") & (subgroup.metric == "dice")].iloc[0]
    shape_dice = subgroup[(subgroup.grouping == "shape") & (subgroup.metric == "dice")]
    shape_min_holm = float(shape_dice.p_holm_within_grouping_metric.min())
    error_report = f"""# Step 20.5 Error Analysis and Applicability Boundary

Status: complete for the planned analyses using existing masks; no retraining was performed.

## Objective grouping rules

- Lesion/organ size uses ground-truth area or physical volume tertiles fixed within the dataset. Synapse and ACDC are grouped separately within each organ or structure.
- BUSI shape uses the ground-truth bounding-box width/height ratio: Horizontal >= 1.25, Vertical <= 0.80, and Balanced otherwise.
- BUSI local contrast is an objective lesion-versus-dilated-ring contrast-to-noise ratio, divided into ground-truth-group tertiles.
- Precision, recall, false-positive ratio, and false-negative ratio are computed from the saved prediction masks for every model and seed.

## Main BUSI observations

- Low-contrast lesions showed the clearest Dice decrease: mean E2_modify_2 - E1 = {low_dice.mean_difference_e2_minus_e1:+.4f}, bootstrap 95% CI [{low_dice.bootstrap_95ci_low:+.4f}, {low_dice.bootstrap_95ci_high:+.4f}], Holm p = {low_dice.p_holm_within_grouping_metric:.4g}.
- Large lesions also showed a Dice decrease: mean difference = {large_dice.mean_difference_e2_minus_e1:+.4f}, bootstrap 95% CI [{large_dice.bootstrap_95ci_low:+.4f}, {large_dice.bootstrap_95ci_high:+.4f}], Holm p = {large_dice.p_holm_within_grouping_metric:.4g}.
- No shape subgroup remained significant after correction; the smallest shape-group Holm p for Dice was {shape_min_holm:.4g}. The vertical group contains only four units and is exploratory.
- These are associations, not proof that contrast, size, or scan direction alone caused the errors.

## Fixed qualitative selection

Each dataset includes seven unique cases selected before viewing the seed-42 panels: largest decline, largest improvement, both poor, dataset-median typical case, and Small/Medium/Large representatives. The combined figures and individual 300-dpi PNG/PDF panels are under `fixed_selection_v2/<dataset>/medical_images_DO_NOT_UPLOAD_GITHUB/`. Case IDs and numerical values are public in each selection manifest, but medical images and masks must not be uploaded to GitHub.

## Safe conclusion

BiUMamba provides an effective accuracy-memory trade-off on Synapse CT and ACDC MRI. Its segmentation quality decreased on BUSI ultrasound, especially among objectively defined low-contrast lesions in this analysis. The subgroup findings describe an applicability boundary and require confirmation on additional ultrasound datasets.

## Supporting files

- `busi_mask_level_metrics_all_seeds.csv`
- `busi_*_group_summary.csv` and `busi_*_group_paired_statistics.csv`
- `synapse_acdc_per_organ_size_group_*.csv`
- `busi_size_shape_contrast_analysis.png` and `.pdf`
- `fixed_selection_v2/*/selection_manifest_rendered.csv`
"""
    (error_dir / "STEP20_5_ERROR_ANALYSIS_REPORT.md").write_text(error_report, encoding="utf-8")

    for dataset in ("synapse", "acdc", "busi"):
        private = fixed_dir / dataset / "medical_images_DO_NOT_UPLOAD_GITHUB"
        (private / "README_DO_NOT_UPLOAD_GITHUB.txt").write_text(
            "Contains medical dataset images, ground-truth overlays, and model prediction overlays.\n"
            "Use only in the professor/research archive according to dataset permissions.\n"
            "Do not upload this directory to public GitHub.\n",
            encoding="utf-8",
        )

    completion = {
        "generated_at": "2026-09-06",
        "status": "complete",
        "retraining_performed": False,
        "tasks": {
            "step20_forest_and_paired_difference_figures": "complete",
            "synapse_acdc_anomaly_tables": "complete",
            "busi_precision_recall_fp_fn": "complete",
            "busi_shape_and_low_contrast_analysis": "complete",
            "synapse_acdc_per_organ_size_groups": "complete",
            "fixed_rule_qualitative_cases": "complete",
            "step20_step205_reports_and_paper_tables": "complete",
            "github_sync": "pending_external_sync",
            "archive_download_hash_verification": "pending_external_sync",
            "runpod_stop": "pending_external_sync",
        },
        "statistical_caveats": [
            "Subgroup analyses are exploratory.",
            "The BUSI vertical-shape subgroup has only four lesion groups.",
            "Associations with size or contrast do not establish causality.",
            "Medical images, ground truth, and prediction masks are excluded from public GitHub.",
        ],
    }
    manifests.mkdir(parents=True, exist_ok=True)
    (manifests / "STEP20_STEP20_5_COMPLETION.json").write_text(json.dumps(completion, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(completion, indent=2))


if __name__ == "__main__":
    main()
