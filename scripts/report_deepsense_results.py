#!/usr/bin/env python
"""Generate a DeepSense experiment report from saved OpenEW-SA artifacts."""

from __future__ import annotations

import argparse
import json
from functools import reduce
from operator import mul
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DEFAULT_DATASET_SUMMARY = Path(r"D:\openew_sa_data\tables\deepsense_dataset_summary.csv")
DEFAULT_MARKDOWN_OUTPUT = Path(r"D:\openew_sa_data\tables\deepsense_results_summary.md")
DEFAULT_CSV_OUTPUT = Path(r"D:\openew_sa_data\tables\deepsense_results_summary.csv")

EXPERIMENTS = (
    {
        "name": "deepsense_occupancy_mlp",
        "model": "Tabular MLP",
        "split_protocol": "Random row split across DeepSense day1/day2 windows.",
        "metrics_arg": "random_mlp_metrics",
    },
    {
        "name": "deepsense_day2_holdout_mlp",
        "model": "Tabular MLP",
        "split_protocol": "Train on day1 domains and validate/evaluate on day2 domains.",
        "metrics_arg": "day2_holdout_mlp_metrics",
    },
    {
        "name": "deepsense_occupancy_iqcnn",
        "model": "IQ CNN 1D",
        "split_protocol": "Random row split using unflattened [2, 1024] I/Q windows.",
        "metrics_arg": "iqcnn_metrics",
    },
    {
        "name": "deepsense_day2_holdout_iqcnn",
        "model": "IQ CNN 1D",
        "split_protocol": "Train on day1 domains and validate/evaluate on day2 domains.",
        "metrics_arg": "day2_holdout_iqcnn_metrics",
        "optional": True,
    },
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create Markdown and CSV summaries for DeepSense OpenEW-SA experiments.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--dataset-summary", default=DEFAULT_DATASET_SUMMARY, type=Path)
    parser.add_argument(
        "--random-mlp-metrics",
        default=Path("runs") / "deepsense_occupancy_mlp" / "metrics.json",
        type=Path,
    )
    parser.add_argument(
        "--day2-holdout-mlp-metrics",
        default=Path("runs") / "deepsense_day2_holdout_mlp" / "metrics.json",
        type=Path,
    )
    parser.add_argument(
        "--iqcnn-metrics",
        default=Path("runs") / "deepsense_occupancy_iqcnn" / "metrics.json",
        type=Path,
    )
    parser.add_argument(
        "--day2-holdout-iqcnn-metrics",
        default=Path("runs") / "deepsense_day2_holdout_iqcnn" / "metrics.json",
        type=Path,
    )
    parser.add_argument("--markdown-output", default=DEFAULT_MARKDOWN_OUTPUT, type=Path)
    parser.add_argument("--csv-output", default=DEFAULT_CSV_OUTPUT, type=Path)
    args = parser.parse_args()

    dataset_summary = _read_csv(args.dataset_summary, "DeepSense dataset summary")
    dataset_info = _dataset_info(dataset_summary)
    experiment_table = _build_experiment_table(args, dataset_info)

    _write_csv(experiment_table, args.csv_output)
    _write_markdown(dataset_info, experiment_table, args.markdown_output)
    print(f"Wrote {args.markdown_output}")
    print(f"Wrote {args.csv_output}")


def _read_csv(path: Path, description: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"{description} not found: {path}")
    return pd.read_csv(path)


def _read_json(path: Path, description: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"{description} not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _dataset_info(dataset_summary: pd.DataFrame) -> dict[str, Any]:
    if dataset_summary.empty:
        raise ValueError("DeepSense dataset summary is empty")
    required = {"dataset_source", "num_samples", "input_types", "domains", "frequency_bands", "artifact_dir"}
    missing = required.difference(dataset_summary.columns)
    if missing:
        raise ValueError(f"Dataset summary is missing required columns: {sorted(missing)}")

    row = dataset_summary.iloc[0]
    artifact_dir = Path(str(row["artifact_dir"]))
    labels = _read_json(artifact_dir / "labels.json", "DeepSense labels.json")
    feature_shape = _feature_shape(labels, artifact_dir)
    return {
        "dataset_source": str(row["dataset_source"]),
        "dataset_size": int(row["num_samples"]),
        "input_types": str(row["input_types"]),
        "domain_count": int(row["domains"]),
        "frequency_band_count": int(row["frequency_bands"]),
        "artifact_dir": str(artifact_dir),
        "feature_shape": feature_shape,
        "feature_dimension": _feature_dimension(feature_shape),
    }


def _feature_shape(labels: dict[str, Any], artifact_dir: Path) -> list[int]:
    if "feature_shape" in labels:
        return [int(value) for value in labels["feature_shape"]]
    features_path = artifact_dir / "features.npy"
    if not features_path.exists():
        raise FileNotFoundError(f"Cannot infer feature shape; missing labels feature_shape and {features_path}")
    features = np.load(features_path, mmap_mode="r")
    return [int(value) for value in features.shape[1:]]


def _feature_dimension(feature_shape: list[int]) -> int:
    if not feature_shape:
        return 1
    return int(reduce(mul, feature_shape, 1))


def _build_experiment_table(args: argparse.Namespace, dataset_info: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for experiment in EXPERIMENTS:
        metrics_path = getattr(args, experiment["metrics_arg"])
        if experiment.get("optional") and not metrics_path.exists():
            continue
        metrics = _read_json(metrics_path, f"{experiment['name']} metrics")
        per_class_f1 = _string_key_dict(metrics.get("per_class_f1", {}))
        support_per_class = _string_key_dict(metrics.get("support_per_class", {}))
        rows.append(
            {
                "experiment": experiment["name"],
                "model": experiment["model"],
                "split_protocol": experiment["split_protocol"],
                "dataset_size": dataset_info["dataset_size"],
                "feature_shape": json.dumps(dataset_info["feature_shape"]),
                "feature_dimension": dataset_info["feature_dimension"],
                "accuracy": _metric(metrics, "accuracy"),
                "macro_f1": _metric(metrics, "macro_f1"),
                "weighted_f1": _metric(metrics, "weighted_f1"),
                "class_count": len(support_per_class),
                "per_class_f1": json.dumps(per_class_f1, sort_keys=True),
                "support_per_class": json.dumps(support_per_class, sort_keys=True),
                "metrics_file": str(metrics_path),
            }
        )
    return pd.DataFrame(rows)


def _metric(metrics: dict[str, Any], key: str) -> float | None:
    value = metrics.get(key)
    if value is None:
        return None
    return float(value)


def _string_key_dict(values: Any) -> dict[str, Any]:
    if not isinstance(values, dict):
        return {}
    return {str(key): value for key, value in values.items()}


def _write_csv(table: pd.DataFrame, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(output, index=False)


def _write_markdown(dataset_info: dict[str, Any], experiment_table: pd.DataFrame, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# DeepSense Experiment Results",
        "",
        "## Dataset",
        "",
        _markdown_table(
            [
                {
                    "dataset_source": dataset_info["dataset_source"],
                    "dataset_size": dataset_info["dataset_size"],
                    "feature_shape": json.dumps(dataset_info["feature_shape"]),
                    "feature_dimension": dataset_info["feature_dimension"],
                    "input_types": dataset_info["input_types"],
                    "domains": dataset_info["domain_count"],
                    "frequency_bands": dataset_info["frequency_band_count"],
                    "artifact_dir": dataset_info["artifact_dir"],
                }
            ],
            [
                "dataset_source",
                "dataset_size",
                "feature_shape",
                "feature_dimension",
                "input_types",
                "domains",
                "frequency_bands",
                "artifact_dir",
            ],
        ),
        "",
        "## Split Results",
        "",
        _markdown_table(
            experiment_table.to_dict(orient="records"),
            [
                "experiment",
                "model",
                "split_protocol",
                "accuracy",
                "macro_f1",
                "weighted_f1",
                "class_count",
                "support_per_class",
            ],
        ),
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(_markdown_value(row.get(column)) for column in columns) + " |" for row in rows]
    return "\n".join([header, separator, *body])


def _markdown_value(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value).replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    main()
