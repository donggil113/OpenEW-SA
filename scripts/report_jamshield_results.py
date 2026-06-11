#!/usr/bin/env python
"""Generate a JamShield experiment report from saved OpenEW-SA artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DEFAULT_DATASET_SUMMARY = Path(r"D:\openew_sa_data\tables\jamshield_dataset_summary.csv")
DEFAULT_DOMAIN_HOLDOUT_BY_DOMAIN = Path(r"D:\openew_sa_data\tables\jamshield_domain_holdout_by_domain_balanced.csv")
DEFAULT_REACTIVE_HOLDOUT_BY_DOMAIN = Path(r"D:\openew_sa_data\tables\jamshield_reactive_holdout_by_domain_balanced.csv")
DEFAULT_MARKDOWN_OUTPUT = Path(r"D:\openew_sa_data\tables\jamshield_results_summary.md")
DEFAULT_CSV_OUTPUT = Path(r"D:\openew_sa_data\tables\jamshield_results_summary.csv")

EXPERIMENTS = (
    {
        "name": "jamshield_random",
        "display_name": "Random split",
        "split_protocol": "Random row split across JamShield domains.",
        "metrics_arg": "random_metrics",
    },
    {
        "name": "jamshield_domain_holdout",
        "display_name": "Scenario holdout with benign control",
        "split_protocol": "Hold out selected jammer source domains plus data_benign_4.",
        "metrics_arg": "domain_holdout_metrics",
    },
    {
        "name": "jamshield_reactive_holdout",
        "display_name": "Reactive jammer-type holdout with benign control",
        "split_protocol": "Hold out reactive jammer domains plus data_benign_4.",
        "metrics_arg": "reactive_holdout_metrics",
    },
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create Markdown and CSV summaries for JamShield OpenEW-SA experiments.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--dataset-summary", default=DEFAULT_DATASET_SUMMARY, type=Path)
    parser.add_argument("--random-metrics", default=Path("runs") / "jamshield_random" / "metrics.json", type=Path)
    parser.add_argument(
        "--domain-holdout-metrics",
        default=Path("runs") / "jamshield_domain_holdout" / "metrics.json",
        type=Path,
    )
    parser.add_argument(
        "--reactive-holdout-metrics",
        default=Path("runs") / "jamshield_reactive_holdout" / "metrics.json",
        type=Path,
    )
    parser.add_argument("--domain-holdout-by-domain", default=DEFAULT_DOMAIN_HOLDOUT_BY_DOMAIN, type=Path)
    parser.add_argument("--reactive-holdout-by-domain", default=DEFAULT_REACTIVE_HOLDOUT_BY_DOMAIN, type=Path)
    parser.add_argument("--markdown-output", default=DEFAULT_MARKDOWN_OUTPUT, type=Path)
    parser.add_argument("--csv-output", default=DEFAULT_CSV_OUTPUT, type=Path)
    args = parser.parse_args()

    dataset_summary = _read_csv(args.dataset_summary, "JamShield dataset summary")
    dataset_info = _dataset_info(dataset_summary)
    experiment_table = _build_experiment_table(args, dataset_info)
    domain_reports = {
        "Scenario Holdout Domains": _read_csv(args.domain_holdout_by_domain, "domain holdout by-domain summary"),
        "Reactive Holdout Domains": _read_csv(args.reactive_holdout_by_domain, "reactive holdout by-domain summary"),
    }

    _write_csv(experiment_table, args.csv_output)
    _write_markdown(dataset_info, experiment_table, domain_reports, args.markdown_output)
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
        raise ValueError("JamShield dataset summary is empty")
    required = {"dataset_source", "num_samples", "input_types", "domains", "frequency_bands", "artifact_dir"}
    missing = required.difference(dataset_summary.columns)
    if missing:
        raise ValueError(f"Dataset summary is missing required columns: {sorted(missing)}")

    first_row = dataset_summary.iloc[0]
    artifact_dir = Path(str(first_row["artifact_dir"]))
    return {
        "dataset_source": str(first_row["dataset_source"]),
        "dataset_size": int(first_row["num_samples"]),
        "input_types": str(first_row["input_types"]),
        "domain_count": int(first_row["domains"]),
        "frequency_band_count": int(first_row["frequency_bands"]),
        "artifact_dir": str(artifact_dir),
        "feature_dimension": _infer_feature_dimension(dataset_summary, artifact_dir),
    }


def _infer_feature_dimension(dataset_summary: pd.DataFrame, artifact_dir: Path) -> int:
    if "feature_dimension" in dataset_summary.columns and not pd.isna(dataset_summary.iloc[0]["feature_dimension"]):
        return int(dataset_summary.iloc[0]["feature_dimension"])

    features_path = artifact_dir / "features.npy"
    if not features_path.exists():
        raise FileNotFoundError(
            "Cannot infer JamShield feature dimension. Expected a feature_dimension column in "
            f"the dataset summary or features.npy at: {features_path}"
        )
    features = np.load(features_path, mmap_mode="r")
    if features.ndim == 1:
        return 1
    return int(features.shape[1])


def _build_experiment_table(args: argparse.Namespace, dataset_info: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for experiment in EXPERIMENTS:
        metrics_path = getattr(args, experiment["metrics_arg"])
        metrics = _read_json(metrics_path, f"{experiment['display_name']} metrics")
        per_class_f1 = _string_key_dict(metrics.get("per_class_f1", {}))
        support_per_class = _string_key_dict(metrics.get("support_per_class", {}))
        rows.append(
            {
                "experiment": experiment["name"],
                "split_protocol": experiment["split_protocol"],
                "dataset_size": dataset_info["dataset_size"],
                "feature_dimension": dataset_info["feature_dimension"],
                "accuracy": _metric(metrics, "accuracy"),
                "macro_f1": _metric(metrics, "macro_f1"),
                "AUROC": _metric(metrics, "AUROC"),
                "AUPRC": _metric(metrics, "AUPRC"),
                "normal_f1": per_class_f1.get("normal"),
                "abnormal_interference_f1": per_class_f1.get("abnormal_interference"),
                "normal_support": support_per_class.get("normal"),
                "abnormal_interference_support": support_per_class.get("abnormal_interference"),
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


def _write_markdown(
    dataset_info: dict[str, Any],
    experiment_table: pd.DataFrame,
    domain_reports: dict[str, pd.DataFrame],
    output: Path,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# JamShield Experiment Results",
        "",
        "## Dataset",
        "",
        _markdown_table(
            [
                {
                    "dataset_source": dataset_info["dataset_source"],
                    "dataset_size": dataset_info["dataset_size"],
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
                "split_protocol",
                "accuracy",
                "macro_f1",
                "AUROC",
                "AUPRC",
                "normal_f1",
                "abnormal_interference_f1",
                "normal_support",
                "abnormal_interference_support",
            ],
        ),
    ]

    for title, table in domain_reports.items():
        lines.extend(
            [
                "",
                f"## {title}",
                "",
                _markdown_table(
                    table.to_dict(orient="records"),
                    [
                        "domain_id",
                        "n_samples",
                        "true_label_distribution",
                        "predicted_label_distribution",
                        "accuracy",
                        "macro_f1",
                    ],
                ),
            ]
        )

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
