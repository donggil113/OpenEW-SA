#!/usr/bin/env python
"""Build Paper 2 v0 OOD result tables from metric JSON files."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

DEFAULT_METRICS_DIR = Path(r"D:\openew_sa_data\paper2\metrics")
DEFAULT_OUTPUT_CSV = Path(r"D:\openew_sa_data\paper2\tables\paper2_v0_ood_results.csv")
DEFAULT_OUTPUT_MD = Path(r"D:\openew_sa_data\paper2\tables\paper2_v0_ood_results.md")

RESULT_COLUMNS = [
    "dataset",
    "protocol",
    "model",
    "score_method",
    "auroc",
    "aupr_ood",
    "fpr95",
    "detection_accuracy",
    "n_id",
    "n_ood",
    "n_samples",
]

METRIC_COLUMNS = [
    "auroc",
    "aupr_ood",
    "fpr95",
    "detection_accuracy",
    "n_id",
    "n_ood",
    "n_samples",
]
SYMBOLIC_STRING_COLUMNS = ["dataset", "protocol", "model", "score_method"]

SCORE_PATTERNS = {
    ("nearest", "centroid", "euclidean"): "nearest_centroid_euclidean",
    ("nearest_centroid_euclidean",): "nearest_centroid_euclidean",
    ("nearest", "centroid", "cosine"): "nearest_centroid_cosine",
    ("nearest_centroid_cosine",): "nearest_centroid_cosine",
    ("mahalanobis",): "mahalanobis",
    ("max", "softmax", "probability"): "max_softmax_probability",
    ("msp",): "max_softmax_probability",
    ("entropy",): "entropy",
    ("energy", "score"): "energy_score",
    ("energy",): "energy_score",
    ("random", "baseline"): "random_baseline",
    ("random",): "random_baseline",
}

MODEL_PATTERNS = {
    ("logistic", "regression", "ts"): "logistic_regression_ts",
    ("logistic_regression", "ts"): "logistic_regression_ts",
    ("logistic_regression_ts",): "logistic_regression_ts",
    ("lr", "ts"): "logistic_regression_ts",
    ("mlp", "ts"): "mlp_ts",
    ("mlp_ts",): "mlp_ts",
    ("nearest", "centroid"): "nearest_centroid",
    ("nearest_centroid",): "nearest_centroid",
    ("nc",): "nearest_centroid",
    ("logistic", "regression"): "logistic_regression",
    ("logistic_regression",): "logistic_regression",
    ("logreg",): "logistic_regression",
    ("lr",): "logistic_regression",
    ("mlp",): "mlp",
    ("random", "baseline"): "none",
    ("random_baseline",): "none",
    ("random",): "none",
}

PROTOCOL_PATTERNS = {
    ("class", "ood"): "class_ood",
    ("domain", "ood"): "domain_ood",
    ("hybrid", "ood"): "hybrid_ood",
    ("day2", "ood"): "day2_ood",
    ("scenario", "ood"): "scenario_ood",
}


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Summarize Paper 2 v0 OOD metric JSON files into CSV and Markdown tables.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--metrics-dir", type=Path, default=DEFAULT_METRICS_DIR, help="Directory of metric JSON files.")
    parser.add_argument("--pattern", default="*.json", help="Glob pattern for metric JSON files.")
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV, help="Output CSV table path.")
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD, help="Output Markdown table path.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on JSON files that do not contain all required OOD metric fields.",
    )
    parser.add_argument("--float-format", default=".4f", help="Format specifier for Markdown float values.")
    return parser.parse_args()


def main() -> None:
    """Run Paper 2 v0 result table generation."""

    args = parse_args()
    rows = collect_result_rows(args.metrics_dir, pattern=args.pattern, strict=args.strict)
    if not rows:
        raise ValueError(f"No OOD metric JSON files found in {args.metrics_dir} with pattern {args.pattern!r}.")
    rows = sorted(rows, key=lambda row: (row["dataset"], row["protocol"], row["model"], row["score_method"]))
    _write_csv(args.output_csv, rows)
    _write_markdown(args.output_md, rows, args.float_format)
    print(f"Wrote {args.output_csv} ({len(rows)} rows)")
    print(f"Wrote {args.output_md} ({len(rows)} rows)")


def collect_result_rows(metrics_dir: Path, pattern: str = "*.json", strict: bool = False) -> list[dict[str, Any]]:
    """Return table rows collected from OOD metric JSON files."""

    if not metrics_dir.exists():
        raise FileNotFoundError(f"Metrics directory not found: {metrics_dir}")
    rows: list[dict[str, Any]] = []
    for path in sorted(metrics_dir.glob(pattern)):
        if not path.is_file():
            continue
        try:
            metrics = _load_metric_payload(path)
            row = _row_from_metrics(path, metrics)
        except ValueError as exc:
            if strict:
                raise
            print(f"Skipping {path}: {exc}", file=sys.stderr)
            continue
        rows.append(row)
    return rows


def _load_metric_payload(path: Path) -> dict[str, Any]:
    """Read a metric JSON file and return the dictionary containing metric values."""

    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("expected a JSON object")
    metrics = payload.get("metrics", payload)
    if not isinstance(metrics, dict):
        raise ValueError("expected metric values in a JSON object")
    merged = dict(payload)
    merged.update(metrics)
    return merged


def _row_from_metrics(path: Path, metrics: dict[str, Any]) -> dict[str, Any]:
    """Build one result table row from a metric payload and its filename."""

    missing = [column for column in METRIC_COLUMNS if column not in metrics]
    if missing:
        raise ValueError(f"missing required OOD metric fields: {missing}")
    inferred = _infer_metadata(path, metrics)
    row: dict[str, Any] = {
        "dataset": inferred["dataset"],
        "protocol": inferred["protocol"],
        "model": inferred["model"],
        "score_method": inferred["score_method"],
    }
    _preserve_string_fields(row)
    for column in METRIC_COLUMNS:
        row[column] = _coerce_metric(metrics[column], column)
    return row


def _infer_metadata(path: Path, metrics: dict[str, Any]) -> dict[str, str]:
    """Infer dataset, protocol, model, and score method from JSON fields or filename tokens."""

    dataset = _first_text(metrics, "dataset", "dataset_source", "source_dataset")
    protocol = _first_text(metrics, "protocol", "ood_protocol")
    model = _first_text(metrics, "model", "classifier", "baseline_model")
    score_method = _first_text(metrics, "score_method", "method", "ood_score_method")

    tokens = _metric_stem(path).split("_")
    if not score_method:
        score_method, tokens = _consume_suffix(tokens, SCORE_PATTERNS)
    else:
        _, tokens = _consume_suffix(tokens, SCORE_PATTERNS)
    if not model:
        model, tokens = _consume_suffix(tokens, MODEL_PATTERNS)
    else:
        _, tokens = _consume_suffix(tokens, MODEL_PATTERNS)
        model = _normalize_model_name(model)

    if not dataset and not protocol:
        protocol, tokens = _consume_prefix(tokens, PROTOCOL_PATTERNS)
    if not dataset and tokens:
        dataset = tokens.pop(0)
    if not protocol and tokens:
        protocol = "_".join(tokens)
    protocol = _normalize_protocol_name(protocol)
    if not model:
        if score_method in {"nearest_centroid_euclidean", "nearest_centroid_cosine", "mahalanobis"}:
            model = "feature_distance"
        else:
            model = "none" if score_method == "random_baseline" else "unknown"
    return {
        "dataset": dataset or "unknown",
        "protocol": protocol or "unknown",
        "model": model,
        "score_method": score_method or "unknown",
    }


def _normalize_model_name(model: str) -> str:
    """Normalize direct model metadata values to report display names."""

    normalized = str(model).strip()
    aliases = {
        "nc": "nearest_centroid",
        "nearest_centroid": "nearest_centroid",
        "lr": "logistic_regression",
        "logreg": "logistic_regression",
        "logistic_regression": "logistic_regression",
        "lr_ts": "logistic_regression_ts",
        "logistic_regression_ts": "logistic_regression_ts",
        "mlp": "mlp",
        "mlp_ts": "mlp_ts",
        "random": "none",
        "random_baseline": "none",
        "none": "none",
    }
    return aliases.get(normalized, normalized)


def _metric_stem(path: Path) -> str:
    """Return a metric filename stem without conventional metric suffixes."""

    stem = path.stem
    for suffix in ("_ood_metrics", "_metrics"):
        if stem.endswith(suffix):
            return stem[: -len(suffix)]
    return stem


def _normalize_protocol_name(protocol: str) -> str:
    """Return display protocol names with split-file suffixes removed."""

    return protocol[: -len("_eval")] if protocol.endswith("_eval") else protocol


def _consume_suffix(tokens: list[str], patterns: dict[tuple[str, ...], str]) -> tuple[str, list[str]]:
    """Return a mapped suffix value and the remaining tokens."""

    for pattern, value in sorted(patterns.items(), key=lambda item: len(item[0]), reverse=True):
        if len(tokens) >= len(pattern) and tuple(tokens[-len(pattern) :]) == pattern:
            return value, tokens[: -len(pattern)]
    return "", tokens


def _consume_prefix(tokens: list[str], patterns: dict[tuple[str, ...], str]) -> tuple[str, list[str]]:
    """Return a mapped prefix value and the remaining tokens."""

    for pattern, value in sorted(patterns.items(), key=lambda item: len(item[0]), reverse=True):
        if len(tokens) >= len(pattern) and tuple(tokens[: len(pattern)]) == pattern:
            return value, tokens[len(pattern) :]
    return "", tokens


def _first_text(values: dict[str, Any], *keys: str) -> str:
    """Return the first non-empty string-like value from a dictionary."""

    for key in keys:
        value = values.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def _coerce_metric(value: Any, column: str) -> float | int:
    """Coerce JSON metric values into table-safe numeric values."""

    if column.startswith("n_"):
        return int(value)
    return float(value)


def _preserve_string_fields(row: dict[str, Any]) -> None:
    """Store symbolic report metadata fields as strings in-place."""

    for column in SYMBOLIC_STRING_COLUMNS:
        if column in row:
            row[column] = "" if row[column] is None else str(row[column])


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write result rows as CSV."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown(path: Path, rows: list[dict[str, Any]], float_format: str) -> None:
    """Write result rows as a GitHub-flavored Markdown table."""

    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "| " + " | ".join(RESULT_COLUMNS) + " |",
        "| " + " | ".join(["---"] * len(RESULT_COLUMNS)) + " |",
    ]
    for row in rows:
        values = [_format_markdown_value(row[column], float_format) for column in RESULT_COLUMNS]
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
