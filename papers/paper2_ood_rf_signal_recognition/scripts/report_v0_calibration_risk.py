#!/usr/bin/env python
"""Build Paper 2 v0 calibration and risk-coverage report tables."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

DEFAULT_CALIBRATION_DIR = Path(r"D:\openew_sa_data\paper2\calibration")
DEFAULT_RISK_COVERAGE_DIR = Path(r"D:\openew_sa_data\paper2\risk_coverage")
DEFAULT_CALIBRATION_CSV = Path(r"D:\openew_sa_data\paper2\tables\paper2_v0_calibration_results.csv")
DEFAULT_CALIBRATION_MD = Path(r"D:\openew_sa_data\paper2\tables\paper2_v0_calibration_results.md")
DEFAULT_RISK_CSV = Path(r"D:\openew_sa_data\paper2\tables\paper2_v0_risk_coverage_summary.csv")
DEFAULT_RISK_MD = Path(r"D:\openew_sa_data\paper2\tables\paper2_v0_risk_coverage_summary.md")

CALIBRATION_COLUMNS = [
    "dataset",
    "protocol",
    "model",
    "accuracy",
    "average_confidence",
    "confidence_accuracy_gap",
    "ece",
    "mce",
    "nll",
    "brier",
    "n_bins",
    "valid_probability_rows",
    "n_samples",
]

RISK_COLUMNS = [
    "dataset",
    "protocol",
    "model",
    "aurc",
    "base_accuracy",
    "base_risk",
    "risk_at_50_coverage",
    "risk_at_80_coverage",
    "risk_at_95_coverage",
    "n_samples",
]

CALIBRATION_METRICS = [
    "accuracy",
    "average_confidence",
    "confidence_accuracy_gap",
    "ece",
    "mce",
    "nll",
    "brier",
    "n_bins",
    "valid_probability_rows",
    "n_samples",
]

RISK_METRICS = [
    "aurc",
    "base_accuracy",
    "base_risk",
    "risk_at_50_coverage",
    "risk_at_80_coverage",
    "risk_at_95_coverage",
    "n_samples",
]

MODEL_ALIASES = {
    "nc": "nearest_centroid",
    "nearest_centroid": "nearest_centroid",
    "lr": "logistic_regression",
    "logreg": "logistic_regression",
    "logistic_regression": "logistic_regression",
    "mlp": "mlp",
}

PROTOCOL_ALIASES = {
    "class_ood": "class_ood",
    "domain_ood": "domain_ood",
    "hybrid_ood": "hybrid_ood",
    "day2_ood": "day2_ood",
    "scenario_ood": "scenario_ood",
}


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Summarize Paper 2 v0 calibration and risk-coverage JSON files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--calibration-dir",
        type=Path,
        default=DEFAULT_CALIBRATION_DIR,
        help="Directory of calibration metric JSON files.",
    )
    parser.add_argument(
        "--risk-coverage-dir",
        type=Path,
        default=DEFAULT_RISK_COVERAGE_DIR,
        help="Directory of risk-coverage summary JSON files.",
    )
    parser.add_argument("--calibration-pattern", default="*.json", help="Glob pattern for calibration JSON files.")
    parser.add_argument("--risk-pattern", default="*.json", help="Glob pattern for risk-coverage JSON files.")
    parser.add_argument(
        "--calibration-output-csv",
        type=Path,
        default=DEFAULT_CALIBRATION_CSV,
        help="Output CSV path for calibration results.",
    )
    parser.add_argument(
        "--calibration-output-md",
        type=Path,
        default=DEFAULT_CALIBRATION_MD,
        help="Output Markdown path for calibration results.",
    )
    parser.add_argument(
        "--risk-output-csv",
        type=Path,
        default=DEFAULT_RISK_CSV,
        help="Output CSV path for risk-coverage summaries.",
    )
    parser.add_argument(
        "--risk-output-md",
        type=Path,
        default=DEFAULT_RISK_MD,
        help="Output Markdown path for risk-coverage summaries.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on JSON files that do not contain the expected aggregate fields.",
    )
    parser.add_argument("--float-format", default=".4f", help="Format specifier for Markdown float values.")
    return parser.parse_args()


def main() -> None:
    """Run v0 calibration and risk-coverage report generation."""

    args = parse_args()
    calibration_rows = collect_rows(
        directory=args.calibration_dir,
        pattern=args.calibration_pattern,
        table_kind="calibration",
        metric_columns=CALIBRATION_METRICS,
        strict=args.strict,
    )
    risk_rows = collect_rows(
        directory=args.risk_coverage_dir,
        pattern=args.risk_pattern,
        table_kind="risk_coverage",
        metric_columns=RISK_METRICS,
        strict=args.strict,
    )
    if not calibration_rows:
        raise ValueError(f"No calibration JSON files found in {args.calibration_dir}.")
    if not risk_rows:
        raise ValueError(f"No risk-coverage JSON files found in {args.risk_coverage_dir}.")

    calibration_rows = _sort_rows(calibration_rows)
    risk_rows = _sort_rows(risk_rows)
    _write_csv(args.calibration_output_csv, calibration_rows, CALIBRATION_COLUMNS)
    _write_markdown(args.calibration_output_md, calibration_rows, CALIBRATION_COLUMNS, args.float_format)
    _write_csv(args.risk_output_csv, risk_rows, RISK_COLUMNS)
    _write_markdown(args.risk_output_md, risk_rows, RISK_COLUMNS, args.float_format)
    print(f"Wrote {args.calibration_output_csv} ({len(calibration_rows)} rows)")
    print(f"Wrote {args.calibration_output_md} ({len(calibration_rows)} rows)")
    print(f"Wrote {args.risk_output_csv} ({len(risk_rows)} rows)")
    print(f"Wrote {args.risk_output_md} ({len(risk_rows)} rows)")


def collect_rows(
    directory: Path,
    pattern: str,
    table_kind: str,
    metric_columns: list[str],
    strict: bool = False,
) -> list[dict[str, Any]]:
    """Collect report rows from metric JSON files."""

    if not directory.exists():
        raise FileNotFoundError(f"JSON directory not found: {directory}")
    rows: list[dict[str, Any]] = []
    for path in sorted(directory.glob(pattern)):
        if not path.is_file():
            continue
        try:
            payload = _read_json(path)
            rows.append(_row_from_payload(path, payload, table_kind, metric_columns))
        except ValueError as exc:
            if strict:
                raise
            print(f"Skipping {path}: {exc}", file=sys.stderr)
    return rows


def _row_from_payload(
    path: Path,
    payload: dict[str, Any],
    table_kind: str,
    metric_columns: list[str],
) -> dict[str, Any]:
    """Build one report row from a JSON payload and metric filename."""

    missing = [column for column in metric_columns if column not in payload]
    if missing:
        raise ValueError(f"missing required {table_kind} fields: {missing}")
    inferred = infer_metadata(path, table_kind)
    row: dict[str, Any] = {
        "dataset": inferred["dataset"],
        "protocol": inferred["protocol"],
        "model": inferred["model"],
    }
    for column in metric_columns:
        row[column] = _coerce_metric(payload[column], column)
    return row


def infer_metadata(path: Path, table_kind: str) -> dict[str, str]:
    """Infer dataset, protocol, and model from a v0 metric filename."""

    stem = _strip_metric_suffix(path.stem, table_kind)
    tokens = stem.split("_")
    if len(tokens) < 3:
        raise ValueError(f"Could not infer dataset/protocol/model from filename: {path.name}")

    model_token = tokens[-1]
    model = MODEL_ALIASES.get(model_token, model_token)
    dataset = tokens[0]
    protocol = _normalize_protocol_name("_".join(tokens[1:-1]))
    return {
        "dataset": dataset or "unknown",
        "protocol": PROTOCOL_ALIASES.get(protocol, protocol or "unknown"),
        "model": model or "unknown",
    }


def _strip_metric_suffix(stem: str, table_kind: str) -> str:
    """Remove known report suffixes from a metric filename stem."""

    if table_kind == "calibration":
        suffixes = ("_calibration_test_id", "_calibration")
    elif table_kind == "risk_coverage":
        suffixes = ("_risk_coverage_summary", "_risk_coverage")
    else:
        suffixes = ()
    for suffix in suffixes:
        if stem.endswith(suffix):
            return stem[: -len(suffix)]
    return stem


def _normalize_protocol_name(protocol: str) -> str:
    """Return display protocol names with split-file suffixes removed."""

    return protocol[: -len("_eval")] if protocol.endswith("_eval") else protocol


def _read_json(path: Path) -> dict[str, Any]:
    """Read a JSON object from disk."""

    with path.open("r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("expected a JSON object")
    return payload


def _coerce_metric(value: Any, column: str) -> float | int | str:
    """Coerce aggregate metrics into table-friendly values."""

    if value is None:
        return ""
    if column in {"n_bins", "valid_probability_rows", "n_samples"}:
        return int(value)
    return float(value)


def _sort_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return rows in a stable dataset/protocol/model order."""

    return sorted(rows, key=lambda row: (row["dataset"], row["protocol"], row["model"]))


def _write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    """Write result rows as CSV."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown(path: Path, rows: list[dict[str, Any]], columns: list[str], float_format: str) -> None:
    """Write result rows as a GitHub-flavored Markdown table."""

    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        values = [_format_markdown_value(row[column], float_format) for column in columns]
        lines.append("| " + " | ".join(values) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _format_markdown_value(value: Any, float_format: str) -> str:
    """Return a Markdown-safe table cell value."""

    if isinstance(value, float):
        if not math.isfinite(value):
            return str(value)
        return format(value, float_format)
    return str(value).replace("|", "\\|")


if __name__ == "__main__":
    main()
