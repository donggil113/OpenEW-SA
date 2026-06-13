#!/usr/bin/env python
"""Create Paper 1-ready OpenEW-SA tables and matplotlib figures."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd

DEFAULT_TABLES_DIR = Path(r"D:\openew_sa_data\tables")
DEFAULT_OUTPUT_TABLE_DIR = Path(r"D:\openew_sa_data\paper1\tables")
DEFAULT_OUTPUT_FIGURE_DIR = Path(r"D:\openew_sa_data\paper1\figures")

DEFAULT_DATASET_TABLE = DEFAULT_TABLES_DIR / "openew_sa_dataset_table.csv"
DEFAULT_BASELINE_TABLE = DEFAULT_TABLES_DIR / "openew_sa_baseline_table.csv"
DEFAULT_ELECTROSENSE_DOMAIN_TABLE = DEFAULT_TABLES_DIR / "electrosense_sensor_holdout_by_domain.csv"
DEFAULT_JAMSHIELD_DOMAIN_TABLE = (
    DEFAULT_TABLES_DIR / "jamshield_domain_holdout_by_domain_balanced.csv"
)
DEFAULT_JAMSHIELD_REACTIVE_TABLE = (
    DEFAULT_TABLES_DIR / "jamshield_reactive_holdout_by_domain_balanced.csv"
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create Paper 1 CSV tables and compact matplotlib figures.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--dataset-table", default=DEFAULT_DATASET_TABLE, type=Path)
    parser.add_argument("--baseline-table", default=DEFAULT_BASELINE_TABLE, type=Path)
    parser.add_argument(
        "--electrosense-domain-table",
        default=DEFAULT_ELECTROSENSE_DOMAIN_TABLE,
        type=Path,
    )
    parser.add_argument(
        "--jamshield-domain-table",
        default=DEFAULT_JAMSHIELD_DOMAIN_TABLE,
        type=Path,
    )
    parser.add_argument(
        "--jamshield-reactive-table",
        default=DEFAULT_JAMSHIELD_REACTIVE_TABLE,
        type=Path,
    )
    parser.add_argument("--output-table-dir", default=DEFAULT_OUTPUT_TABLE_DIR, type=Path)
    parser.add_argument("--output-figure-dir", default=DEFAULT_OUTPUT_FIGURE_DIR, type=Path)
    args = parser.parse_args()

    dataset_table = _paper_dataset_table(_read_csv(args.dataset_table, "dataset table"))
    baseline_table = _paper_baseline_table(_read_csv(args.baseline_table, "baseline table"))
    domain_holdout_table = _paper_domain_holdout_table(args)

    args.output_table_dir.mkdir(parents=True, exist_ok=True)
    args.output_figure_dir.mkdir(parents=True, exist_ok=True)

    dataset_output = args.output_table_dir / "table1_dataset_summary.csv"
    baseline_output = args.output_table_dir / "table2_baseline_results.csv"
    domain_output = args.output_table_dir / "table3_domain_holdout_summary.csv"

    _write_csv(dataset_table, dataset_output)
    _write_csv(baseline_table, baseline_output)
    _write_csv(domain_holdout_table, domain_output)

    _plot_baseline_macro_f1(
        baseline_table,
        args.output_figure_dir / "figure_baseline_macro_f1.png",
    )
    _plot_domain_holdout_macro_f1(
        domain_holdout_table,
        args.output_figure_dir / "figure_domain_holdout_macro_f1.png",
    )

    print(f"Wrote {dataset_output}")
    print(f"Wrote {baseline_output}")
    print(f"Wrote {domain_output}")
    print(f"Wrote {args.output_figure_dir / 'figure_baseline_macro_f1.png'}")
    print(f"Wrote {args.output_figure_dir / 'figure_domain_holdout_macro_f1.png'}")


def _read_csv(path: Path, description: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"{description} not found: {path}")
    return pd.read_csv(path)


def _paper_dataset_table(frame: pd.DataFrame) -> pd.DataFrame:
    required = {
        "dataset",
        "task",
        "sample_count",
        "input_type",
        "feature_shape",
        "feature_dimension",
        "num_classes",
        "num_domains",
        "split_protocols",
    }
    _require_columns(frame, required, "dataset table")
    table = frame.loc[
        :,
        [
            "dataset",
            "task",
            "sample_count",
            "input_type",
            "feature_shape",
            "feature_dimension",
            "num_classes",
            "num_domains",
            "split_protocols",
        ],
    ].copy()
    return table.rename(
        columns={
            "sample_count": "samples",
            "num_classes": "classes",
            "num_domains": "domains",
        }
    )


def _paper_baseline_table(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"dataset", "task", "model", "split_protocol", "accuracy", "macro_f1"}
    _require_columns(frame, required, "baseline table")
    table = frame.copy()
    for optional in ("AUROC", "AUPRC"):
        if optional not in table.columns:
            table[optional] = pd.NA
    table = table.loc[
        :,
        [
            "dataset",
            "task",
            "model",
            "split_protocol",
            "accuracy",
            "macro_f1",
            "AUROC",
            "AUPRC",
        ],
    ].copy()
    return table.rename(columns={"AUROC": "auroc", "AUPRC": "auprc"})


def _paper_domain_holdout_table(args: argparse.Namespace) -> pd.DataFrame:
    pieces = [
        _domain_rows(
            _read_csv(args.jamshield_domain_table, "JamShield scenario holdout domain table"),
            dataset="JamShield",
            split_protocol="Scenario holdout with benign control",
        ),
        _domain_rows(
            _read_csv(args.jamshield_reactive_table, "JamShield reactive holdout domain table"),
            dataset="JamShield",
            split_protocol="Reactive jammer-type holdout with benign control",
        ),
        _domain_rows(
            _read_csv(args.electrosense_domain_table, "ElectroSense sensor holdout domain table"),
            dataset="ElectroSense PSD",
            split_protocol="Sensor holdout",
        ),
    ]
    table = pd.concat(pieces, ignore_index=True)
    return table.reset_index(drop=True)


def _domain_rows(frame: pd.DataFrame, *, dataset: str, split_protocol: str) -> pd.DataFrame:
    required = {
        "domain_id",
        "n_samples",
        "true_label_distribution",
        "predicted_label_distribution",
        "accuracy",
        "macro_f1",
    }
    _require_columns(frame, required, f"{dataset} {split_protocol} table")
    table = frame.loc[
        :,
        [
            "domain_id",
            "n_samples",
            "true_label_distribution",
            "predicted_label_distribution",
            "accuracy",
            "macro_f1",
        ],
    ].copy()
    table.insert(0, "split_protocol", split_protocol)
    table.insert(0, "dataset", dataset)
    return table


def _require_columns(frame: pd.DataFrame, required: set[str], description: str) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{description} is missing required columns: {missing}")


def _plot_baseline_macro_f1(table: pd.DataFrame, output: Path) -> None:
    plot_table = table.copy()
    plot_table["label"] = plot_table.apply(_baseline_label, axis=1)
    _plot_horizontal_bars(
        labels=plot_table["label"].tolist(),
        values=plot_table["macro_f1"].astype(float).tolist(),
        xlabel="Macro-F1",
        title="Baseline Macro-F1 by Split",
        output=output,
        color="#4C78A8",
        height=max(3.2, min(4.8, 1.8 + 0.32 * len(plot_table))),
    )


def _plot_domain_holdout_macro_f1(table: pd.DataFrame, output: Path) -> None:
    plot_table = table.copy()
    plot_table["label"] = plot_table.apply(_domain_label, axis=1)
    _plot_horizontal_bars(
        labels=plot_table["label"].tolist(),
        values=plot_table["macro_f1"].astype(float).tolist(),
        xlabel="Macro-F1",
        title="Domain Holdout Macro-F1",
        output=output,
        color="#5F9E6E",
        height=max(3.8, min(5.8, 1.8 + 0.28 * len(plot_table))),
    )


def _plot_horizontal_bars(
    *,
    labels: list[str],
    values: list[float],
    xlabel: str,
    title: str,
    output: Path,
    color: str,
    height: float,
) -> None:
    fig, ax = plt.subplots(figsize=(6.8, height), dpi=300)
    positions = list(range(len(values)))
    ax.barh(positions, values, color=color, edgecolor="black", linewidth=0.4)
    ax.set_yticks(positions, labels)
    ax.invert_yaxis()
    ax.set_xlim(0.0, 1.0)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Experiment")
    ax.set_title(title)
    ax.grid(axis="x", linestyle=":", linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    for position, value in zip(positions, values):
        if value >= 0.88:
            ax.text(value - 0.02, position, f"{value:.3f}", ha="right", va="center", fontsize=8)
        else:
            ax.text(value + 0.015, position, f"{value:.3f}", ha="left", va="center", fontsize=8)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)


def _baseline_label(row: pd.Series) -> str:
    dataset = str(row["dataset"])
    original_split = str(row["split_protocol"])
    split = original_split.lower()
    model = str(row["model"]).lower()
    if dataset == "JamShield":
        if "reactive" in split:
            return "JamShield reactive holdout"
        if "hold out" in split:
            return "JamShield scenario holdout"
        return "JamShield random"
    if dataset.startswith("DeepSense"):
        is_day2_holdout = "train on day1" in split or "evaluate on day2" in split
        is_iq_cnn = "iq cnn" in model or "unflattened" in split
        if is_iq_cnn and is_day2_holdout:
            return "DeepSense IQ-CNN Day2 holdout"
        if is_iq_cnn:
            return "DeepSense IQ-CNN random"
        if is_day2_holdout:
            return "DeepSense MLP Day2 holdout"
        return "DeepSense MLP random"
    if dataset.startswith("ElectroSense"):
        if "hold out" in split or "sensor" in split:
            return "ElectroSense sensor holdout"
        return "ElectroSense random"
    return f"{dataset}\n{_shorten(original_split, 28)}"


def _domain_label(row: pd.Series) -> str:
    dataset = str(row["dataset"])
    split = str(row["split_protocol"])
    domain = str(row["domain_id"])
    if dataset == "JamShield" and "Reactive" in split:
        prefix = "JS reactive"
    elif dataset == "JamShield":
        prefix = "JS scenario"
    elif dataset.startswith("ElectroSense"):
        prefix = "ES sensor"
    else:
        prefix = dataset
    return f"{prefix}: {_shorten(domain, 34)}"


def _shorten(value: Any, max_chars: int) -> str:
    text = str(value)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1] + "..."


def _write_csv(table: pd.DataFrame, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(output, index=False, float_format="%.6f")


if __name__ == "__main__":
    main()
