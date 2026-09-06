#!/usr/bin/env python3
"""Complete the remaining Step 20 and Step 20.5 analyses.

This script uses only frozen test outputs. It does not train or select a model.
Medical images and prediction masks stay below directories marked
``DO_NOT_UPLOAD_GITHUB``; only aggregate CSV/JSON/PDF/PNG outputs are public.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
import pandas as pd
from PIL import Image
from scipy import stats
from scipy.ndimage import binary_dilation


SEEDS = (42, 3407, 2026)
METRICS = ("dice", "hd95", "nsd")
BOOTSTRAP_SEED = 20260906
BOOTSTRAP_RESAMPLES = 10_000
SYNAPSE_LABELS = {
    1: "Aorta",
    2: "Gallbladder",
    3: "Left Kidney",
    4: "Right Kidney",
    5: "Liver",
    6: "Pancreas",
    7: "Spleen",
    8: "Stomach",
}
ACDC_LABELS = {1: "right_ventricle", 2: "myocardium", 3: "left_ventricle"}


def holm_adjust(values: pd.Series) -> pd.Series:
    raw = values.to_numpy(dtype=float)
    adjusted = np.full(raw.shape, np.nan)
    finite = np.flatnonzero(np.isfinite(raw))
    ordered = finite[np.argsort(raw[finite], kind="mergesort")]
    running = 0.0
    for rank, original in enumerate(ordered):
        running = max(running, min(1.0, (len(ordered) - rank) * raw[original]))
        adjusted[original] = running
    return pd.Series(adjusted, index=values.index)


def rank_biserial(diff: np.ndarray) -> float:
    diff = diff[np.isfinite(diff) & (diff != 0)]
    if not len(diff):
        return 0.0
    ranks = stats.rankdata(np.abs(diff), method="average")
    pos = float(ranks[diff > 0].sum())
    neg = float(ranks[diff < 0].sum())
    return (pos - neg) / (pos + neg)


def paired_stats(diff: np.ndarray, rng: np.random.Generator) -> dict[str, object]:
    diff = np.asarray(diff, dtype=float)
    diff = diff[np.isfinite(diff)]
    n = len(diff)
    if n < 2:
        return {"n_units": n}
    bootstrap = rng.choice(diff, size=(BOOTSTRAP_RESAMPLES, n), replace=True).mean(axis=1)
    low, high = np.quantile(bootstrap, [0.025, 0.975])
    sd = float(np.std(diff, ddof=1))
    dz = float(np.mean(diff) / sd) if sd > 0 else math.nan
    if n >= 3 and not np.allclose(diff, diff[0]):
        normality = stats.shapiro(diff)
        shapiro_w, shapiro_p = float(normality.statistic), float(normality.pvalue)
    else:
        shapiro_w = shapiro_p = math.nan
    if np.isfinite(shapiro_p) and shapiro_p >= 0.05:
        test = stats.ttest_1samp(diff, 0.0)
        test_name = "paired t-test"
    elif np.allclose(diff, 0):
        test_name = "Wilcoxon signed-rank"
        test = type("Result", (), {"statistic": 0.0, "pvalue": 1.0})()
    else:
        test_name = "Wilcoxon signed-rank"
        test = stats.wilcoxon(diff, zero_method="wilcox", alternative="two-sided")
    return {
        "n_units": n,
        "mean_difference_e2_minus_e1": float(np.mean(diff)),
        "median_difference_e2_minus_e1": float(np.median(diff)),
        "bootstrap_95ci_low": float(low),
        "bootstrap_95ci_high": float(high),
        "shapiro_w": shapiro_w,
        "shapiro_p": shapiro_p,
        "selected_test": test_name,
        "test_statistic": float(test.statistic),
        "p_raw_two_sided": float(test.pvalue),
        "paired_cohens_dz": dz,
        "rank_biserial": float(rank_biserial(diff)),
    }


def qcut_three(values: pd.Series) -> pd.Series:
    ranked = values.rank(method="first")
    return pd.qcut(ranked, 3, labels=["Small", "Medium", "Large"])


def complete_step20(final_root: Path) -> None:
    stats_dir = final_root / "statistics"
    figures = stats_dir / "figures"
    anomalies = stats_dir / "anomaly_cases"
    figures.mkdir(parents=True, exist_ok=True)
    anomalies.mkdir(parents=True, exist_ok=True)

    unit = pd.read_csv(stats_dir / "patient_level_seed_averages.csv")
    paired = pd.read_csv(stats_dir / "paired_patient_statistics.csv")
    datasets = ["Synapse", "ACDC", "BUSI"]
    colors = {"Synapse": "#3b82f6", "ACDC": "#10b981", "BUSI": "#ef4444"}

    difference_rows = []
    for dataset in datasets:
        group = unit.loc[unit.dataset == dataset]
        wide = group.pivot(index="unit_id", columns="method", values=list(METRICS))
        frame = pd.DataFrame({"unit_id": wide.index})
        for metric in METRICS:
            frame[f"e1_{metric}"] = wide[(metric, "E1")].to_numpy()
            frame[f"e2_{metric}"] = wide[(metric, "E2_modify_2")].to_numpy()
            frame[f"delta_{metric}_e2_minus_e1"] = frame[f"e2_{metric}"] - frame[f"e1_{metric}"]
        d = frame["delta_dice_e2_minus_e1"]
        q1, q3 = d.quantile([0.25, 0.75])
        iqr = q3 - q1
        frame["dice_iqr_outlier"] = (d < q1 - 1.5 * iqr) | (d > q3 + 1.5 * iqr)
        combined = 0.5 * (frame.e1_dice + frame.e2_dice)
        med = combined.median()
        frame["selection_largest_decline"] = frame.index == d.idxmin()
        frame["selection_largest_improvement"] = frame.index == d.idxmax()
        frame["selection_both_poor"] = frame.index == combined.idxmin()
        frame["selection_typical_median"] = frame.index == (combined - med).abs().idxmin()
        frame.sort_values("delta_dice_e2_minus_e1").to_csv(
            anomalies / f"{dataset.lower()}_paired_anomaly_cases.csv", index=False
        )
        copy = frame.copy()
        copy.insert(0, "dataset", dataset)
        difference_rows.append(copy)
    differences = pd.concat(difference_rows, ignore_index=True)
    differences.to_csv(stats_dir / "patient_level_paired_differences.csv", index=False)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), constrained_layout=True)
    labels = {"dice": "Dice difference", "hd95": "HD95 difference", "nsd": "NSD difference"}
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    for ax, metric in zip(axes, METRICS):
        arrays = [
            differences.loc[differences.dataset == d, f"delta_{metric}_e2_minus_e1"].to_numpy()
            for d in datasets
        ]
        ax.boxplot(arrays, labels=datasets, showfliers=False, widths=0.55)
        for position, (dataset, values) in enumerate(zip(datasets, arrays), start=1):
            jitter = rng.uniform(-0.09, 0.09, len(values))
            ax.scatter(position + jitter, values, s=23, alpha=0.72, color=colors[dataset], edgecolor="none")
        ax.axhline(0, color="#222222", linewidth=1, linestyle="--")
        ax.set_title(labels[metric])
        ax.set_ylabel("E2_modify_2 − E1")
        ax.grid(axis="y", alpha=0.2)
    fig.suptitle("Patient-level paired differences after averaging three seeds", fontsize=14)
    fig.savefig(figures / "paired_difference_distributions.png", dpi=300, bbox_inches="tight")
    fig.savefig(figures / "paired_difference_distributions.pdf", bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5.0), constrained_layout=True)
    for ax, metric in zip(axes, METRICS):
        rows = paired.loc[paired.metric == metric].set_index("dataset").loc[datasets].reset_index()
        y = np.arange(len(rows))[::-1]
        means = rows.mean_difference_e2_minus_e1.to_numpy()
        lows = rows.bootstrap_95ci_low.to_numpy()
        highs = rows.bootstrap_95ci_high.to_numpy()
        ax.errorbar(means, y, xerr=[means - lows, highs - means], fmt="o", capsize=4, color="#34495e")
        ax.axvline(0, color="#222222", linewidth=1, linestyle="--")
        ax.set_yticks(y, rows.dataset)
        ax.set_xlabel("E2_modify_2 − E1")
        ax.set_title(metric.upper())
        ax.grid(axis="x", alpha=0.2)
    fig.suptitle("Mean paired difference with patient-level bootstrap 95% CI", fontsize=14)
    fig.savefig(figures / "paired_difference_forest_plot.png", dpi=300, bbox_inches="tight")
    fig.savefig(figures / "paired_difference_forest_plot.pdf", bbox_inches="tight")
    plt.close(fig)


def load_busi_gt_image(data_root: Path, row: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    image = Image.open(data_root / row.image_relpath).convert("L")
    union = np.zeros((image.height, image.width), dtype=bool)
    for relpath in str(row.mask_relpaths).split("|"):
        union |= np.asarray(Image.open(data_root / relpath).convert("L")) > 0
    return np.asarray(image, dtype=np.float32), union


def resize_pad_mask(mask: np.ndarray, size: int = 224) -> np.ndarray:
    height, width = mask.shape
    scale = min(size / width, size / height)
    new_width, new_height = max(1, round(width * scale)), max(1, round(height * scale))
    resized = Image.fromarray(mask.astype(np.uint8) * 255).resize((new_width, new_height), Image.Resampling.NEAREST)
    canvas = Image.new("L", (size, size), 0)
    canvas.paste(resized, ((size - new_width) // 2, (size - new_height) // 2))
    return np.asarray(canvas) > 0


def busi_morphology(image: np.ndarray, mask: np.ndarray) -> dict[str, float | str]:
    ys, xs = np.nonzero(mask)
    height = int(ys.max() - ys.min() + 1)
    width = int(xs.max() - xs.min() + 1)
    ratio = width / max(height, 1)
    shape_group = "Horizontal" if ratio >= 1.25 else "Vertical" if ratio <= 0.80 else "Balanced"
    ring = binary_dilation(mask, iterations=max(3, round(min(image.shape) * 0.03))) & ~mask
    lesion = image[mask]
    surrounding = image[ring]
    pooled = math.sqrt(0.5 * (float(np.var(lesion)) + float(np.var(surrounding))))
    absolute_difference = abs(float(np.mean(lesion)) - float(np.mean(surrounding)))
    return {
        "bbox_width_px": width,
        "bbox_height_px": height,
        "bbox_width_height_ratio": ratio,
        "shape_group": shape_group,
        "lesion_mean_intensity": float(np.mean(lesion)),
        "surrounding_ring_mean_intensity": float(np.mean(surrounding)),
        "local_absolute_contrast_0_1": absolute_difference / 255.0,
        "local_contrast_to_noise_ratio": absolute_difference / max(pooled, 1e-8),
    }


def grouped_paired_tables(unit: pd.DataFrame, group_column: str, metrics: list[str], output: Path) -> None:
    summaries = []
    paired_rows = []
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    for group_name, group in unit.groupby(group_column, observed=True):
        for method, method_group in group.groupby("method"):
            record = {group_column: group_name, "method": method, "n_units": method_group.group_id.nunique()}
            for metric in metrics:
                record[f"{metric}_mean"] = float(method_group[metric].mean())
                record[f"{metric}_std"] = float(method_group[metric].std(ddof=1))
            summaries.append(record)
        for metric in metrics:
            wide = group.pivot(index="group_id", columns="method", values=metric).dropna()
            record = paired_stats((wide.E2_modify_2 - wide.E1).to_numpy(), rng)
            record.update({group_column: group_name, "metric": metric})
            paired_rows.append(record)
    summary = pd.DataFrame(summaries)
    paired = pd.DataFrame(paired_rows)
    paired["p_holm_within_grouping_metric"] = paired.groupby("metric")["p_raw_two_sided"].transform(holm_adjust)
    summary.to_csv(output.with_name(output.stem + "_summary.csv"), index=False)
    paired.to_csv(output.with_name(output.stem + "_paired_statistics.csv"), index=False)


def complete_busi(workspace: Path, final_root: Path) -> pd.DataFrame:
    output = final_root / "qualitative_figures" / "error_analysis"
    output.mkdir(parents=True, exist_ok=True)
    formal = workspace / "outputs/busi_v1_clean_formal_three_seed_runpod"
    manifest = pd.read_csv(formal / "github_safe_stage/protocol/clean_manifest.csv")
    manifest = manifest.loc[manifest.split == "test"].set_index("group_id")
    data_root = workspace / "datasets/Dataset_BUSI_with_GT"
    morphology = []
    for group_id, row in manifest.iterrows():
        if row.class_name == "normal":
            continue
        image, gt = load_busi_gt_image(data_root, row)
        morphology.append({"group_id": group_id, "class_name": row.class_name, **busi_morphology(image, gt)})
    morphology = pd.DataFrame(morphology)
    morphology["contrast_group"] = pd.qcut(
        morphology.local_contrast_to_noise_ratio.rank(method="first"),
        3,
        labels=["Low", "Medium", "High"],
    )

    rows = []
    for method in ("E1", "E2_modify_2"):
        for seed in SEEDS:
            metrics_path = formal / f"runs/{method}_seed{seed}/per_sample_metrics.csv"
            metrics = pd.read_csv(metrics_path)
            predictions = formal / f"runs/{method}_seed{seed}/private_do_not_upload/predictions"
            for item in metrics.itertuples(index=False):
                if float(item.gt_area_fraction) <= 0:
                    continue
                gt_image, gt_original = load_busi_gt_image(data_root, manifest.loc[item.group_id])
                del gt_image
                gt = resize_pad_mask(gt_original)
                pred = np.asarray(Image.open(predictions / f"{item.group_id}.png").convert("L")) > 0
                tp = int(np.logical_and(pred, gt).sum())
                fp = int(np.logical_and(pred, ~gt).sum())
                fn = int(np.logical_and(~pred, gt).sum())
                precision = tp / (tp + fp) if tp + fp else 0.0
                recall = tp / (tp + fn) if tp + fn else 0.0
                rows.append(
                    {
                        "method": method,
                        "seed": seed,
                        "group_id": item.group_id,
                        "class_name": item.class_name,
                        "dice": float(item.dice),
                        "hd95": float(item.hd95_px),
                        "nsd": float(item.nsd_at_2px),
                        "precision": precision,
                        "recall": recall,
                        "false_positive_area_fraction": fp / gt.size,
                        "false_negative_area_fraction": fn / gt.size,
                        "false_positive_to_gt_ratio": fp / max(int(gt.sum()), 1),
                        "false_negative_to_gt_ratio": fn / max(int(gt.sum()), 1),
                    }
                )
    raw = pd.DataFrame(rows).merge(morphology, on=["group_id", "class_name"], how="left")
    gt_fraction = raw.groupby("group_id").false_negative_area_fraction.first() * 0
    original_metrics = pd.read_csv(formal / "runs/E1_seed42/per_sample_metrics.csv").set_index("group_id")
    gt_fraction = original_metrics.loc[morphology.group_id, "gt_area_fraction"]
    size_map = qcut_three(gt_fraction).astype(str).to_dict()
    raw["size_group"] = raw.group_id.map(size_map)
    raw.to_csv(output / "busi_mask_level_metrics_all_seeds.csv", index=False)
    average_columns = [
        "dice", "hd95", "nsd", "precision", "recall",
        "false_positive_area_fraction", "false_negative_area_fraction",
        "false_positive_to_gt_ratio", "false_negative_to_gt_ratio",
    ]
    unit = raw.groupby(
        ["method", "group_id", "class_name", "size_group", "shape_group", "contrast_group"],
        as_index=False,
        observed=True,
    )[average_columns].mean()
    unit.to_csv(output / "busi_group_level_three_seed_averages_complete.csv", index=False)
    grouped_paired_tables(unit, "size_group", average_columns, output / "busi_size_group_complete.csv")
    grouped_paired_tables(unit, "shape_group", average_columns, output / "busi_shape_group.csv")
    grouped_paired_tables(unit, "contrast_group", average_columns, output / "busi_contrast_group.csv")

    wide = unit.pivot(index="group_id", columns="method", values="dice").dropna()
    meta = morphology.set_index("group_id").join(pd.Series(size_map, name="size_group"))
    candidates = meta.join(wide).reset_index()
    candidates["delta_dice_e2_minus_e1"] = candidates.E2_modify_2 - candidates.E1
    candidates["both_poor"] = (candidates.E1 < 0.60) & (candidates.E2_modify_2 < 0.60)
    candidates["e1_good_e2_poor"] = (candidates.E1 >= 0.70) & (candidates.E2_modify_2 < 0.60)
    candidates.sort_values("delta_dice_e2_minus_e1").to_csv(output / "busi_error_case_candidates_complete.csv", index=False)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), constrained_layout=True)
    plot = candidates
    axes[0].scatter(plot.local_contrast_to_noise_ratio, plot.delta_dice_e2_minus_e1, alpha=0.75)
    axes[0].set_xlabel("Local contrast-to-noise ratio")
    axes[0].set_ylabel("Dice: E2_modify_2 − E1")
    axes[1].scatter(plot.bbox_width_height_ratio, plot.delta_dice_e2_minus_e1, alpha=0.75)
    axes[1].set_xlabel("GT bounding-box width / height")
    for i, group_name in enumerate(["Small", "Medium", "Large"]):
        values = plot.loc[plot.size_group == group_name, "delta_dice_e2_minus_e1"]
        axes[2].scatter(np.full(len(values), i) + np.linspace(-0.06, 0.06, len(values)), values, alpha=0.65)
    axes[2].set_xticks(range(3), ["Small", "Medium", "Large"])
    axes[2].set_xlabel("GT lesion-size tertile")
    for ax in axes:
        ax.axhline(0, color="black", linestyle="--", linewidth=1)
        ax.grid(alpha=0.2)
    fig.suptitle("BUSI error analysis using three-seed patient-group averages")
    fig.savefig(output / "busi_size_shape_contrast_analysis.png", dpi=300, bbox_inches="tight")
    fig.savefig(output / "busi_size_shape_contrast_analysis.pdf", bbox_inches="tight")
    plt.close(fig)
    return unit


def synapse_gt_sizes(workspace: Path) -> pd.DataFrame:
    gt_root = workspace / "runs/formal_test_synapse_v2/E2_modify_2_seed42/ground_truth_do_not_upload"
    records = []
    for path in sorted(gt_root.glob("*_gt.nii.gz")):
        case = path.name.replace("_gt.nii.gz", "")
        nii = nib.load(str(path))
        data = np.asarray(nii.dataobj)
        voxel_ml = float(np.prod(nii.header.get_zooms()[:3])) / 1000.0
        for label, organ in SYNAPSE_LABELS.items():
            count = int(np.count_nonzero(data == label))
            if count:
                records.append({"dataset": "Synapse", "unit_id": case, "subgroup": organ,
                                "gt_voxels": count, "gt_volume_ml": count * voxel_ml})
    return pd.DataFrame(records)


def acdc_gt_sizes(workspace: Path, final_root: Path) -> pd.DataFrame:
    test = [x.strip() for x in (final_root / "acdc/frozen_protocol/splits/test_patients.txt").read_text().splitlines() if x.strip()]
    data_root = workspace / "datasets/ACDC_hf_preprocessed_train100/train"
    records = []
    for patient in test:
        phase_records = []
        for phase in ("ed", "es"):
            path = data_root / patient / f"{patient}_sax_{phase}_gt.nii.gz"
            nii = nib.load(str(path))
            data = np.asarray(nii.dataobj)
            voxel_ml = float(np.prod(nii.header.get_zooms()[:3])) / 1000.0
            for label, organ in ACDC_LABELS.items():
                count = int(np.count_nonzero(data == label))
                phase_records.append({"subgroup": organ, "gt_voxels": count, "gt_volume_ml": count * voxel_ml})
        frame = pd.DataFrame(phase_records).groupby("subgroup", as_index=False).mean(numeric_only=True)
        frame["dataset"], frame["unit_id"] = "ACDC", patient
        records.extend(frame.to_dict("records"))
    return pd.DataFrame(records)


def complete_size_analysis(workspace: Path, final_root: Path) -> pd.DataFrame:
    output = final_root / "qualitative_figures/error_analysis"
    metrics = pd.read_csv(final_root / "statistics/organ_or_class_seed_averages.csv")
    metrics = metrics.loc[metrics.dataset.isin(["Synapse", "ACDC"])].copy()
    sizes = pd.concat([synapse_gt_sizes(workspace), acdc_gt_sizes(workspace, final_root)], ignore_index=True)
    sizes["size_group"] = sizes.groupby(["dataset", "subgroup"], group_keys=False)["gt_volume_ml"].apply(qcut_three).astype(str)
    table = metrics.merge(sizes, on=["dataset", "unit_id", "subgroup"], how="inner")
    table.to_csv(output / "synapse_acdc_per_organ_size_group_unit_metrics.csv", index=False)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    summaries, tests = [], []
    for (dataset, organ, size_group), group in table.groupby(["dataset", "subgroup", "size_group"]):
        for method, method_group in group.groupby("method"):
            record = {"dataset": dataset, "organ": organ, "size_group": size_group,
                      "method": method, "n_units": method_group.unit_id.nunique(),
                      "gt_volume_ml_mean": float(method_group.gt_volume_ml.mean())}
            for metric in METRICS:
                record[f"{metric}_mean"] = float(method_group[metric].mean())
                record[f"{metric}_std"] = float(method_group[metric].std(ddof=1))
            summaries.append(record)
        for metric in METRICS:
            wide = group.pivot(index="unit_id", columns="method", values=metric).dropna()
            record = paired_stats((wide.E2_modify_2 - wide.E1).to_numpy(), rng)
            record.update({"dataset": dataset, "organ": organ, "size_group": size_group, "metric": metric})
            tests.append(record)
    summary = pd.DataFrame(summaries)
    tests = pd.DataFrame(tests)
    tests["p_holm_within_dataset_metric"] = tests.groupby(["dataset", "metric"])["p_raw_two_sided"].transform(holm_adjust)
    summary.to_csv(output / "synapse_acdc_per_organ_size_group_summary.csv", index=False)
    tests.to_csv(output / "synapse_acdc_per_organ_size_group_paired_statistics.csv", index=False)
    return sizes


def choose_unique_cases(frame: pd.DataFrame, id_column: str, size_column: str) -> pd.DataFrame:
    frame = frame.copy()
    frame["combined_dice"] = 0.5 * (frame.e1_dice + frame.e2_dice)
    frame["delta_dice_e2_minus_e1"] = frame.e2_dice - frame.e1_dice
    chosen: list[dict[str, object]] = []
    used: set[str] = set()

    def add(category: str, candidates: pd.DataFrame, sort_column: str, ascending: bool, rule: str) -> None:
        available = candidates.loc[~candidates[id_column].astype(str).isin(used)].sort_values(sort_column, ascending=ascending)
        if available.empty:
            available = candidates.sort_values(sort_column, ascending=ascending)
        row = available.iloc[0].to_dict()
        row.update({"category": category, "selection_rule": rule})
        chosen.append(row)
        used.add(str(row[id_column]))

    add("largest_decline", frame, "delta_dice_e2_minus_e1", True,
        "Most negative three-seed mean Dice difference (E2_modify_2 minus E1).")
    add("largest_improvement", frame, "delta_dice_e2_minus_e1", False,
        "Most positive three-seed mean Dice difference (E2_modify_2 minus E1).")
    poor = frame.loc[(frame.e1_dice < 0.60) & (frame.e2_dice < 0.60)]
    if poor.empty:
        poor = frame
    add("both_poor", poor, "combined_dice", True, "Lowest combined Dice among cases where both models are below 0.60; fallback is overall lowest.")
    median = frame.combined_dice.median()
    frame["distance_to_median"] = (frame.combined_dice - median).abs()
    add("typical_median", frame, "distance_to_median", True, "Combined Dice closest to the dataset median.")
    for group in ("Small", "Medium", "Large"):
        candidates = frame.loc[frame[size_column] == group].copy()
        candidates["distance_to_group_median"] = (candidates.combined_dice - candidates.combined_dice.median()).abs()
        add(f"{group.lower()}_representative", candidates, "distance_to_group_median", True,
            f"Combined Dice closest to the {group} group median; size group defined from ground truth only.")
    return pd.DataFrame(chosen)


def build_selection_manifests(final_root: Path, busi_unit: pd.DataFrame, sizes: pd.DataFrame) -> None:
    output_root = final_root / "qualitative_figures/fixed_selection_v2"
    output_root.mkdir(parents=True, exist_ok=True)
    patient = pd.read_csv(final_root / "statistics/patient_level_seed_averages.csv")
    for dataset in ("Synapse", "ACDC"):
        group = patient.loc[patient.dataset == dataset]
        wide = group.pivot(index="unit_id", columns="method", values="dice")
        frame = pd.DataFrame({"unit_id": wide.index, "e1_dice": wide.E1.values,
                              "e2_dice": wide.E2_modify_2.values})
        overall_size = sizes.loc[sizes.dataset == dataset].groupby("unit_id", as_index=False).gt_volume_ml.sum()
        overall_size["size_group"] = qcut_three(overall_size.gt_volume_ml).astype(str)
        frame = frame.merge(overall_size, on="unit_id", how="left")
        selected = choose_unique_cases(frame, "unit_id", "size_group")
        out = output_root / dataset.lower()
        out.mkdir(parents=True, exist_ok=True)
        selected.to_csv(out / "selection_manifest.csv", index=False)
        (out / "selection_manifest.json").write_text(json.dumps({
            "dataset": dataset,
            "metric_source": "patient-level values averaged across seeds 42, 3407, and 2026",
            "display_seed": 42,
            "size_rule": "dataset-level tertiles of total ground-truth target volume; quantitative organ analysis uses per-organ tertiles",
            "cases": selected.to_dict("records"),
        }, indent=2) + "\n")

    busi_wide = busi_unit.pivot(index="group_id", columns="method", values="dice").dropna()
    busi_meta = busi_unit.drop_duplicates("group_id").set_index("group_id")[["class_name", "size_group", "shape_group", "contrast_group"]]
    frame = busi_meta.join(busi_wide).reset_index().rename(columns={"E1": "e1_dice", "E2_modify_2": "e2_dice"})
    selected = choose_unique_cases(frame, "group_id", "size_group")
    out = output_root / "busi"
    out.mkdir(parents=True, exist_ok=True)
    selected.to_csv(out / "selection_manifest.csv", index=False)
    (out / "selection_manifest.json").write_text(json.dumps({
        "dataset": "BUSI",
        "metric_source": "lesion-group values averaged across seeds 42, 3407, and 2026",
        "display_seed": 42,
        "size_rule": "tertiles of ground-truth lesion area fraction",
        "cases": selected.to_dict("records"),
    }, indent=2) + "\n")


def write_manifest(final_root: Path) -> None:
    path = final_root / "qualitative_figures/error_analysis/analysis_manifest_v2_complete.json"
    payload = {
        "generated_by": "complete_step20_step205.py",
        "generated_date": "2026-09-06",
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "completed": [
            "patient-level paired-difference distributions and forest plot",
            "Synapse and ACDC anomaly tables",
            "BUSI precision, recall, false-positive and false-negative ratios",
            "BUSI ground-truth bounding-box shape analysis",
            "BUSI objective local contrast-to-noise analysis",
            "Synapse per-organ and ACDC per-structure ground-truth size-tertile analysis",
            "fixed seven-category qualitative selection manifests",
        ],
        "definitions": {
            "shape_horizontal": "GT bounding-box width/height >= 1.25",
            "shape_vertical": "GT bounding-box width/height <= 0.80",
            "shape_balanced": "0.80 < GT bounding-box width/height < 1.25",
            "contrast": "absolute lesion-vs-dilated-ring mean difference divided by pooled local standard deviation",
            "false_positive_to_gt_ratio": "FP pixels divided by GT-positive pixels",
            "false_negative_to_gt_ratio": "FN pixels divided by GT-positive pixels",
            "size": "GT-only tertiles; independently formed within every Synapse organ and ACDC structure",
        },
        "causal_limit": "Shape and contrast subgroup associations do not prove that scan direction or reduced channel capacity caused an error.",
    }
    path.write_text(json.dumps(payload, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=Path("/workspace"))
    parser.add_argument("--final-root", type=Path, default=Path("/workspace/paper_final_results_v2"))
    args = parser.parse_args()
    complete_step20(args.final_root)
    busi_unit = complete_busi(args.workspace, args.final_root)
    sizes = complete_size_analysis(args.workspace, args.final_root)
    build_selection_manifests(args.final_root, busi_unit, sizes)
    write_manifest(args.final_root)
    print(json.dumps({"status": "complete", "final_root": str(args.final_root)}, indent=2))


if __name__ == "__main__":
    main()
