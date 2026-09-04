"""Publication-oriented V2 tables and figures from external analysis files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .contracts import method_registry


def _save(figure: plt.Figure, root: Path, name: str) -> None:
    figure.tight_layout()
    figure.savefig(root / f"{name}.png", dpi=300, bbox_inches="tight")
    figure.savefig(root / f"{name}.pdf", bbox_inches="tight")
    plt.close(figure)


def _mean_sem(frame: pd.DataFrame, x: str, y: str) -> pd.DataFrame:
    result = frame.groupby(x)[y].agg(["mean", "std", "count"]).reset_index()
    result["sem"] = result["std"] / np.sqrt(result["count"])
    return result


def _receiver_mean_sem(frame: pd.DataFrame, x: str, y: str) -> pd.DataFrame:
    """Average algorithmic seeds inside receiver before uncertainty display."""

    if "receiver_id" not in frame:
        raise ValueError("receiver_id is required for receiver-level uncertainty")
    receiver_values = frame.groupby(["receiver_id", x], as_index=False)[y].mean()
    return _mean_sem(receiver_values, x, y)


def generate_figures(analysis_root: str | Path) -> list[str]:
    root = Path(analysis_root); root.mkdir(parents=True, exist_ok=True)
    primary = pd.read_csv(root / "primary_receiver_seed_results.csv")
    paired = pd.read_csv(root / "paired_receiver_seed_differences.csv")
    composition = pd.read_csv(root / "support_composition_audit.csv")
    outputs: list[str] = []

    delta = paired[paired["comparison"] == "P2_MINUS_P0"].groupby("receiver_id")["difference"].mean().sort_values()
    fig, ax = plt.subplots(figsize=(10, 4.8)); colors = np.where(delta >= 0, "#2f78b7", "#777777")
    ax.bar(np.arange(len(delta)), delta.values, color=colors); ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(np.arange(len(delta))); ax.set_xticklabels(delta.index, rotation=70, ha="right", fontsize=7)
    ax.set_ylabel("P2 - P0 macro-F1"); ax.set_xlabel("Held-out receiver (equal-weight units)")
    ax.set_title("Per-receiver attentive-context difference from P0")
    _save(fig, root, "per_receiver_p2_minus_p0"); outputs.append("per_receiver_p2_minus_p0")

    comparators = [value for value in ["P2_SHUFFLED", "P2_MISMATCHED_RX", "P2_NULL", "RX_NORM", "T3A"] if value in set(primary["model"])]
    receiver_means = primary[primary["model"].isin(["P2", *comparators])].groupby(["receiver_id", "model"])["macro_f1"].mean().unstack()
    differences = [receiver_means["P2"] - receiver_means[model] for model in comparators]
    fig, ax = plt.subplots(figsize=(8, 4.8)); ax.boxplot(differences, tick_labels=[f"vs {model}" for model in comparators], showmeans=True)
    ax.axhline(0, color="black", linewidth=0.8); ax.set_ylabel("Paired receiver-level P2 difference in macro-F1"); ax.tick_params(axis="x", rotation=35)
    ax.set_title("Attentive receiver context versus controls and TTA")
    _save(fig, root, "p2_vs_controls_and_tta"); outputs.append("p2_vs_controls_and_tta")

    composition_mean = composition.groupby("receiver_id").agg({"class_entropy_nats": "mean", "p2_minus_p0_macro_f1": "mean"}).reset_index()
    fig, ax = plt.subplots(figsize=(6, 4.8)); ax.scatter(composition_mean["class_entropy_nats"], composition_mean["p2_minus_p0_macro_f1"], alpha=0.8)
    ax.axhline(0, color="black", linewidth=0.8); ax.set_xlabel("Support class entropy (audit only, nats)"); ax.set_ylabel("P2 - P0 macro-F1")
    ax.set_title("Support composition and attentive-context difference")
    _save(fig, root, "context_composition_vs_gain"); outputs.append("context_composition_vs_gain")

    if (root / "support_budget_results.csv").exists():
        budget = pd.read_csv(root / "support_budget_results.csv"); summary = _receiver_mean_sem(budget, "support_budget", "macro_f1")
        fig, ax = plt.subplots(figsize=(6, 4.8)); ax.errorbar(summary["support_budget"], summary["mean"], yerr=1.96 * summary["sem"], marker="o")
        ax.axvline(128, color="#777777", linestyle="--", linewidth=0.9, label="Primary budget")
        ax.set_ylim(0, 1); ax.set_xlabel("Unlabeled receiver support budget"); ax.set_ylabel("Mean macro-F1 +/- 1.96 receiver-level SE")
        ax.set_title("Attentive context by fixed support-bank budget"); ax.legend(frameon=False)
        _save(fig, root, "support_budget_curve"); outputs.append("support_budget_curve")

    if (root / "context_k_results.csv").exists():
        context = pd.read_csv(root / "context_k_results.csv"); summary = _receiver_mean_sem(context, "context_k", "macro_f1")
        fig, ax = plt.subplots(figsize=(6, 4.8)); ax.errorbar(summary["context_k"], summary["mean"], yerr=1.96 * summary["sem"], marker="o")
        ax.axvline(32, color="#777777", linestyle="--", linewidth=0.9, label="Primary k")
        ax.set_ylim(0, 1); ax.set_xlabel("Support peers per query, k"); ax.set_ylabel("Mean macro-F1 +/- 1.96 receiver-level SE")
        ax.set_title("Attentive context by peers per query"); ax.legend(frameon=False)
        _save(fig, root, "context_k_curve"); outputs.append("context_k_curve")

    hardware = primary[primary["model"].isin(["P0", "P2"])].groupby(["receiver_id", "hardware_family", "model"])["macro_f1"].mean().unstack().reset_index()
    hardware["difference"] = hardware["P2"] - hardware["P0"]
    families = sorted(hardware["hardware_family"].astype(str).unique())
    fig, ax = plt.subplots(figsize=(7, 4.8))
    for position, family in enumerate(families):
        values = hardware.loc[hardware["hardware_family"].astype(str) == family, "difference"].sort_values().to_numpy()
        offsets = np.linspace(-0.18, 0.18, len(values)) if len(values) > 1 else np.asarray([0.0])
        ax.scatter(position + offsets, values, color="#2f78b7", alpha=0.8, s=28)
        ax.hlines(values.mean(), position - 0.27, position + 0.27, color="black", linewidth=1.8)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(range(len(families))); ax.set_xticklabels(families)
    ax.set_ylabel("P2 - P0 receiver-level macro-F1"); ax.set_xlabel("Receiver hardware family (diagnostic only)")
    ax.set_title("Attentive-context difference by receiver hardware family")
    _save(fig, root, "hardware_stratified_receiver_results"); outputs.append("hardware_stratified_receiver_results")

    if (root / "day_receiver_seed_results.csv").exists():
        day = pd.read_csv(root / "day_receiver_seed_results.csv"); subset = day[day["model"].isin(["P0", "P2"])]
        day_means = subset.groupby(["test_day", "model"])["equal_weight_receiver_macro_f1"].mean().unstack().reindex(columns=["P0", "P2"])
        fig, ax = plt.subplots(figsize=(6, 4.8))
        for _, row in day_means.iterrows():
            ax.plot([0, 1], row.values, color="#aaaaaa", linewidth=1, alpha=0.8)
            ax.scatter([0, 1], row.values, color=["#777777", "#2f78b7"], s=32, zorder=3)
        ax.set_xticks([0, 1]); ax.set_xticklabels(["P0", "P2"]); ax.set_ylim(0, 1)
        ax.set_ylabel("Equal-receiver macro-F1 (mean over seeds)")
        ax.set_title("Four coarse-day holdouts (secondary)")
        _save(fig, root, "day_holdout_secondary"); outputs.append("day_holdout_secondary")

    info = primary.groupby("model").agg(parameter_count=("parameter_count", "median"), wall_seconds=("wall_seconds", "mean"), peak_gpu_memory_bytes=("peak_gpu_memory_bytes", "median")).reset_index()
    inference_path = root / "standardized_inference_benchmark_summary.csv"
    if not inference_path.exists():
        raise FileNotFoundError("standardized inference benchmark is required for the compute/latency figure")
    inference = pd.read_csv(inference_path).set_index("model").reindex(info["model"])
    if inference["latency_seconds_median"].isna().any():
        raise RuntimeError("standardized inference benchmark is incomplete")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8)); axes[0].bar(info["model"], inference["latency_seconds_median"]); axes[1].bar(info["model"], info["peak_gpu_memory_bytes"] / 2**20)
    axes[0].set_ylabel("Median test-time latency (s)"); axes[1].set_ylabel("Median peak allocated GPU memory (MiB)")
    axes[0].set_title("Support/adaptation-inclusive latency"); axes[1].set_title("Peak GPU allocation")
    for ax in axes: ax.tick_params(axis="x", rotation=70)
    _save(fig, root, "compute_latency_comparison"); outputs.append("compute_latency_comparison")

    figure, ax = plt.subplots(figsize=(11, 5)); ax.axis("off")
    access = _information_access_rows(sorted(primary["model"].unique()))
    rows = [
        [
            item["model"],
            item["target_receiver_support"],
            item["source_validation_donor_support"],
            "No",
            item["test_update"],
        ]
        for item in access
    ]
    table = ax.table(
        cellText=rows,
        colLabels=["Method", "Target-RX support", "Source-val donor", "Target labels", "Test update"],
        loc="center",
    )
    ax.set_title("Test-time information and update budget", pad=12)
    table.auto_set_font_size(False); table.set_fontsize(8); table.scale(1, 1.25)
    _save(figure, root, "information_budget_diagram"); outputs.append("information_budget_diagram")
    return outputs


def generate_tables(analysis_root: str | Path, split_root: str | Path) -> dict[str, str]:
    root, split_root = Path(analysis_root), Path(split_root)
    primary = pd.read_csv(root / "primary_receiver_seed_results.csv")
    summary = pd.read_csv(root / "primary_receiver_level_summary.csv")
    paired = pd.read_csv(root / "paired_receiver_seed_differences.csv")
    table1_rows: list[dict[str, Any]] = []
    for path in sorted(split_root.glob("receiver_loso_*/split_summary.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        table1_rows.append({"protocol_id": value["protocol_id"], "test_receiver": value["assignment_metadata"]["test_receiver"], "hardware": value["assignment_metadata"]["test_receiver_hardware"], **value["split_counts"], "eligible_transmitters": value["eligible_transmitter_count"]})
    paths = {
        "table1": root / "table1_wisig_v2_split_summary.csv",
        "table2": root / "table2_information_regimes.csv",
        "table3": root / "table3_receiver_level_primary.csv",
        "table4": root / "table4_receiver_context_controls.csv",
        "table5": root / "table5_tta_dg_baselines.csv",
        "supplement": root / "supplement_all_receiver_seed_results.csv",
    }
    pd.DataFrame(table1_rows).to_csv(paths["table1"], index=False, lineterminator="\n")
    all_models = sorted(primary["model"].astype(str).unique())
    pd.DataFrame(_information_access_rows(all_models)).to_csv(paths["table2"], index=False, lineterminator="\n")
    summary[summary["model"].isin(["P0", "P0_WIDE", "P1", "P2"])].to_csv(paths["table3"], index=False, lineterminator="\n")
    summary[summary["model"].isin(["P2", "P2_SHUFFLED", "P2_NULL", "P2_MISMATCHED_RX", "RX_NORM"])].to_csv(paths["table4"], index=False, lineterminator="\n")
    summary[summary["model"].isin(["SOURCE_NORM", "DG_CORAL", "DG_GROUPDRO", "DG_DANN", "T3A", "RX_NORM"])].to_csv(paths["table5"], index=False, lineterminator="\n")
    primary.to_csv(paths["supplement"], index=False, lineterminator="\n")
    paired.groupby(["comparison", "receiver_id"], as_index=False)["difference"].mean().groupby("comparison")["difference"].agg(["count", "mean", "std", "median", "min", "max"]).to_csv(root / "paired_comparison_table.csv")
    return {key: str(value) for key, value in paths.items()}


def _information_access_rows(models: list[str] | dict[str, str]) -> list[dict[str, Any]]:
    """Describe test-time information without conflating target and donor support."""

    regime = {
        "P0": "R0",
        "P0_WIDE": "R0",
        "DG_CORAL": "R0",
        "DG_GROUPDRO": "R0",
        "DG_DANN": "R0",
        "SOURCE_NORM": "R0",
        "P1": "R1",
        "P2": "R1",
        "P2_SHUFFLED": "R1_CONTROL",
        "P2_NULL": "R1_CONTROL",
        "P2_MISMATCHED_RX": "R1_CONTROL",
        "RX_NORM": "R1",
        "T3A": "R2",
    }
    names = list(models)
    registry = method_registry()
    rows: list[dict[str, Any]] = []
    for model in names:
        if model not in registry:
            raise KeyError(model)
        spec = registry[model]
        rows.append(
            {
                "model": model,
                "regime": regime[model],
                "source_train": spec.source_train,
                "source_validation": spec.source_validation,
                "target_receiver_support": spec.target_support_count,
                "source_validation_donor_support": spec.source_validation_donor_support_count,
                "query_samples_used_as_support": spec.query_samples_used_as_support,
                "target_labels": spec.target_labels,
                "test_gradient_updates": spec.gradient_updates_at_test,
                "test_batch_stat_updates": spec.batch_stat_updates,
                "test_prototype_updates": spec.prototype_updates,
                "extra_parameters": spec.extra_parameters,
                "test_update": "Prototype" if model == "T3A" else ("Statistics" if model == "RX_NORM" else "None"),
            }
        )
    return rows
