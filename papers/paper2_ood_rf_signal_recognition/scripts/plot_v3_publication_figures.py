#!/usr/bin/env python
"""Create publication figures for the Paper 2 v3 analysis."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from bootstrap_ood_statistics import DATASETS, METHOD_FILES, compute_metrics, load_dataset

DATASET_NAMES = {"electrosense": "ElectroSense", "deepsense": "DeepSense", "jamshield": "JamShield"}
METHOD_NAMES = {
    "temperature_scaled_entropy": "Temperature-scaled entropy",
    "nearest_centroid_cosine": "Nearest-centroid cosine",
    "nearest_centroid_euclidean": "Nearest-centroid Euclidean",
    "v3_primary": "Primary fusion (prespecified)",
    "four_component_exploratory": "Four-component fusion (exploratory)",
}
COLORS = {"temperature_scaled_entropy": "#777777", "nearest_centroid_cosine": "#56B4E9",
          "nearest_centroid_euclidean": "#009E73", "v3_primary": "#0072B2",
          "four_component_exploratory": "#D55E00"}


def _style() -> None:
    plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
                         "legend.fontsize": 8, "figure.dpi": 120, "savefig.dpi": 300,
                         "pdf.fonttype": 42, "ps.fonttype": 42, "axes.spines.top": False,
                         "axes.spines.right": False})


def _save(fig, root: Path, name: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    fig.savefig(root / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(root / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def metric_figure(ci: pd.DataFrame, metric: str, ylabel: str, name: str, figures: Path) -> None:
    methods = list(METHOD_FILES)
    datasets = list(DATASETS)
    x = np.arange(len(datasets)); width = 0.16
    fig, ax = plt.subplots(figsize=(7.1, 3.8))
    for i, method in enumerate(methods):
        rows = ci[(ci.metric == metric) & (ci.method == method)].set_index("dataset").loc[datasets]
        values = rows.point_estimate.to_numpy(); low = values - rows.ci_lower.to_numpy(); high = rows.ci_upper.to_numpy() - values
        ax.bar(x + (i - 2) * width, values, width, color=COLORS[method], edgecolor="#222222", linewidth=.45,
               hatch="//" if method == "four_component_exploratory" else None, label=METHOD_NAMES[method])
        ax.errorbar(x + (i - 2) * width, values, yerr=np.vstack([low, high]), fmt="none", color="#222222", capsize=2, lw=.7)
    ax.set_xticks(x, [DATASET_NAMES[d] for d in datasets]); ax.set_ylabel(ylabel); ax.set_ylim(0, 1)
    ax.set_title(f"{ylabel} with 95% paired-bootstrap confidence intervals")
    ax.grid(axis="y", color="#dddddd", linewidth=.5); ax.legend(ncol=2, frameon=False, loc="upper center", bbox_to_anchor=(.5, -0.14))
    _save(fig, figures, name)


def primary_comparison(differences: pd.DataFrame, figures: Path) -> None:
    rows = differences[(differences.metric == "auroc") & differences.comparison.str.startswith("v3_primary_vs")].copy()
    comparator_order = ["temperature_scaled_entropy", "nearest_centroid_cosine", "nearest_centroid_euclidean"]
    fig, axes = plt.subplots(1, 3, figsize=(7.1, 3.25), sharex=True)
    for panel, (ax, dataset) in enumerate(zip(axes, DATASETS)):
        subset = rows[rows.dataset == dataset].set_index("right_method").loc[comparator_order]
        y = np.arange(3); values = subset.point_difference_left_minus_right.to_numpy()
        ax.errorbar(values, y, xerr=np.vstack([values - subset.ci_lower, subset.ci_upper - values]),
                    fmt="o", color=COLORS["v3_primary"], ecolor="#333333", capsize=3)
        ax.axvline(0, color="#222222", lw=.8); ax.set_title(DATASET_NAMES[dataset]); ax.grid(axis="x", color="#dddddd", linewidth=.5)
        labels = [METHOD_NAMES[m].replace("Nearest-centroid ", "NC ") for m in comparator_order]
        ax.set_yticks(y, labels if panel == 0 else ["", "", ""]); ax.invert_yaxis()
    axes[0].set_ylabel("Prespecified comparator")
    fig.supxlabel("AUROC difference: primary fusion minus comparator (focused difference scale)")
    fig.suptitle("Prespecified primary fusion comparisons with 95% paired-bootstrap intervals", y=1.02)
    _save(fig, figures, "figure_primary_fusion_comparison")


def score_distributions(v3_root: Path, figures: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(7.1, 3.2))
    for ax, (dataset, (prefix, expected)) in zip(axes, DATASETS.items()):
        labels, scores, _ = load_dataset(v3_root, prefix, expected)
        values = scores["v3_primary"]
        lo, hi = np.percentile(values, [.5, 99.5]); bins = np.linspace(lo, hi, 45)
        ax.hist(values[labels == 0], bins=bins, density=True, histtype="step", color="#222222", lw=1.2, label="ID")
        ax.hist(values[labels == 1], bins=bins, density=True, histtype="step", color=COLORS["v3_primary"], lw=1.2, label="OOD")
        ax.set_title(DATASET_NAMES[dataset]); ax.set_xlabel("Primary fusion OOD score"); ax.set_ylabel("Density")
        ax.text(.02, .98, "Higher = more OOD-like", transform=ax.transAxes, va="top", fontsize=7)
    axes[-1].legend(frameon=False); fig.suptitle("Prespecified primary-fusion score distributions by dataset", y=1.02)
    _save(fig, figures, "figure_score_distributions_by_dataset")


def deepsense_diagnostic(v3_root: Path, figures: Path) -> None:
    prefix, expected = DATASETS["deepsense"]
    labels, scores, _ = load_dataset(v3_root, prefix, expected)
    methods = list(METHOD_FILES); fixed = [compute_metrics(labels, scores[m])["auroc"] for m in methods]
    inverted = [compute_metrics(labels, -scores[m])["auroc"] for m in methods]
    x = np.arange(len(methods)); width = .36
    fig, ax = plt.subplots(figsize=(7.1, 3.8))
    ax.bar(x - width/2, fixed, width, color="#777777", edgecolor="#222222", label="Fixed orientation (primary reporting)")
    ax.bar(x + width/2, inverted, width, facecolor="white", edgecolor="#D55E00", hatch="//", label="Negated score (post-hoc diagnostic only)")
    ax.axhline(.5, color="#222222", ls="--", lw=.8, label="Chance AUROC")
    ax.set_ylim(0, 1); ax.set_ylabel("AUROC"); ax.set_xticks(x, [METHOD_NAMES[m].replace("Nearest-centroid ", "NC ") for m in methods], rotation=20, ha="right")
    ax.set_title("DeepSense score inversion — POST-HOC DIAGNOSTIC SENSITIVITY ANALYSIS")
    ax.grid(axis="y", color="#dddddd", linewidth=.5); ax.legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(.5, -0.28))
    _save(fig, figures, "figure_deepsense_inversion_diagnostic")


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--v3-root", type=Path, required=True); parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(); _style()
    ci = pd.read_csv(args.output_root / "tables/paper2_v3_bootstrap_confidence_intervals.csv")
    differences = pd.read_csv(args.output_root / "tables/paper2_v3_paired_differences.csv")
    figures = args.output_root / "figures"
    metric_figure(ci, "auroc", "AUROC", "figure_ood_auroc_with_ci", figures)
    metric_figure(ci, "fpr95", "FPR at 95% TPR", "figure_fpr95_with_ci", figures)
    primary_comparison(differences, figures); score_distributions(args.v3_root, figures); deepsense_diagnostic(args.v3_root, figures)


if __name__ == "__main__":
    main()
