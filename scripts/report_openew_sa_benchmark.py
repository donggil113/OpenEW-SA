#!/usr/bin/env python
"""Generate OpenEW-SA paper benchmark tables across converted datasets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

DEFAULT_JAMSHIELD_RESULTS = Path(r"D:\openew_sa_data\tables\jamshield_results_summary.csv")
DEFAULT_DEEPSENSE_RESULTS = Path(r"D:\openew_sa_data\tables\deepsense_results_summary.csv")
DEFAULT_JAMSHIELD_DATASET = Path(r"D:\openew_sa_data\tables\jamshield_dataset_summary.csv")
DEFAULT_DEEPSENSE_DATASET = Path(r"D:\openew_sa_data\tables\deepsense_dataset_summary.csv")
DEFAULT_DATASET_OUTPUT = Path(r"D:\openew_sa_data\tables\openew_sa_dataset_table.csv")
DEFAULT_BASELINE_OUTPUT = Path(r"D:\openew_sa_data\tables\openew_sa_baseline_table.csv")
DEFAULT_MARKDOWN_OUTPUT = Path(r"D:\openew_sa_data\tables\openew_sa_benchmark_summary.md")

DATASET_SPECS = {
    "jamshield": {
        "dataset": "JamShield",
        "task": "Jamming/interference detection",
        "default_model": "Tabular MLP",
    },
    "deepsense": {
        "dataset": "DeepSense SDR WiFi",
        "task": "4-channel WiFi occupancy classification",
        "default_model": "",
    },
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create OpenEW-SA paper benchmark dataset and baseline tables.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--jamshield-results", default=DEFAULT_JAMSHIELD_RESULTS, type=Path)
    parser.add_argument("--deepsense-results", default=DEFAULT_DEEPSENSE_RESULTS, type=Path)
    parser.add_argument("--jamshield-dataset", default=DEFAULT_JAMSHIELD_DATASET, type=Path)
    parser.add_argument("--deepsense-dataset", default=DEFAULT_DEEPSENSE_DATASET, type=Path)
    parser.add_argument("--dataset-output", default=DEFAULT_DATASET_OUTPUT, type=Path)
    parser.add_argument("--baseline-output", default=DEFAULT_BASELINE_OUTPUT, type=Path)
    parser.add_argument("--markdown-output", default=DEFAULT_MARKDOWN_OUTPUT, type=Path)
    args = parser.parse_args()

    inputs = {
        "jamshield": {
            "results": _read_csv(args.jamshield_results, "JamShield results summary"),
            "dataset": _read_csv(args.jamshield_dataset, "JamShield dataset summary"),
        },
        "deepsense": {
            "results": _read_csv(args.deepsense_results, "DeepSense results summary"),
            "dataset": _read_csv(args.deepsense_dataset, "DeepSense dataset summary"),
        },
    }

    dataset_table = _build_dataset_table(inputs)
    baseline_table = _build_baseline_table(inputs)
    _write_csv(dataset_table, args.dataset_output)
    _write_csv(baseline_table, args.baseline_output)
    _write_markdown(dataset_table, baseline_table, args.markdown_output)
    print(f"Wrote {args.dataset_output}")
    print(f"Wrote {args.baseline_output}")
    print(f"Wrote {args.markdown_output}")


def _read_csv(path: Path, description: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"{description} not found: {path}")
    return pd.read_csv(path)


def _build_dataset_table(inputs: dict[str, dict[str, pd.DataFrame]]) -> pd.DataFrame:
    rows = []
    for key, tables in inputs.items():
        spec = DATASET_SPECS[key]
        dataset_summary = _first_row(tables["dataset"], f"{spec['dataset']} dataset summary")
        results = tables["results"]
        rows.append(
            {
                "dataset": spec["dataset"],
                "task": spec["task"],
                "sample_count": int(dataset_summary["num_samples"]),
                "input_type": str(dataset_summary["input_types"]),
                "feature_shape": _feature_shape(results),
                "feature_dimension": _feature_dimension(results),
                "num_classes": _num_classes(results),
                "num_domains": int(dataset_summary["domains"]),
                "split_protocols": _join_unique(results["split_protocol"]),
            }
        )
    return pd.DataFrame(rows)


def _build_baseline_table(inputs: dict[str, dict[str, pd.DataFrame]]) -> pd.DataFrame:
    rows = []
    for key, tables in inputs.items():
        spec = DATASET_SPECS[key]
        results = tables["results"]
        for _, row in results.iterrows():
            rows.append(
                {
                    "dataset": spec["dataset"],
                    "task": spec["task"],
                    "model": _model_name(row, spec),
                    "split_protocol": str(row["split_protocol"]),
                    "accuracy": _optional_float(row.get("accuracy")),
                    "macro_f1": _optional_float(row.get("macro_f1")),
                    "AUROC": _optional_float(row.get("AUROC")),
                    "AUPRC": _optional_float(row.get("AUPRC")),
                }
            )
    return pd.DataFrame(rows)


def _first_row(frame: pd.DataFrame, description: str) -> pd.Series:
    if frame.empty:
        raise ValueError(f"{description} is empty")
    return frame.iloc[0]


def _feature_shape(results: pd.DataFrame) -> str:
    if "feature_shape" in results.columns:
        values = [str(value) for value in results["feature_shape"].dropna().unique() if str(value)]
        if values:
            return values[0]
    dimension = _feature_dimension(results)
    return f"[{dimension}]" if dimension is not None else ""


def _feature_dimension(results: pd.DataFrame) -> int | None:
    if "feature_dimension" not in results.columns:
        return None
    values = results["feature_dimension"].dropna()
    if values.empty:
        return None
    return int(values.iloc[0])


def _num_classes(results: pd.DataFrame) -> int:
    if "class_count" in results.columns:
        values = results["class_count"].dropna()
        if not values.empty:
            return int(values.max())
    if "support_per_class" not in results.columns:
        return 0
    counts = [_json_object_len(value) for value in results["support_per_class"].dropna()]
    return max(counts) if counts else 0


def _json_object_len(value: Any) -> int:
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return 0
    return len(parsed) if isinstance(parsed, dict) else 0


def _join_unique(values: pd.Series) -> str:
    unique = [str(value) for value in values.dropna().tolist()]
    return "; ".join(dict.fromkeys(unique))


def _model_name(row: pd.Series, spec: dict[str, str]) -> str:
    model = row.get("model")
    if model is not None and not pd.isna(model) and str(model):
        return str(model)
    return spec["default_model"]


def _optional_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)


def _write_csv(table: pd.DataFrame, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(output, index=False)


def _write_markdown(dataset_table: pd.DataFrame, baseline_table: pd.DataFrame, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# OpenEW-SA Benchmark Summary",
        "",
        "## Dataset Table",
        "",
        _markdown_table(dataset_table.to_dict(orient="records"), dataset_table.columns.tolist()),
        "",
        "## Baseline Table",
        "",
        _markdown_table(baseline_table.to_dict(orient="records"), baseline_table.columns.tolist()),
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
