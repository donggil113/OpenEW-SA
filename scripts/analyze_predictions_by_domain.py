#!/usr/bin/env python
"""Summarize prediction performance by metadata domain."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def summarize_by_domain(predictions_csv: str | Path) -> pd.DataFrame:
    predictions = pd.read_csv(predictions_csv)
    required = {"domain_id", "true_label", "predicted_label"}
    missing = required.difference(predictions.columns)
    if missing:
        raise ValueError(f"Predictions CSV is missing required columns: {sorted(missing)}")

    rows = []
    for domain_id, group in predictions.groupby("domain_id", dropna=False):
        true_labels = group["true_label"].fillna("unknown").astype(str)
        predicted_labels = group["predicted_label"].fillna("unknown").astype(str)
        rows.append(
            {
                "domain_id": "" if pd.isna(domain_id) else str(domain_id),
                "n_samples": len(group),
                "true_label_distribution": json.dumps(_distribution(true_labels), sort_keys=True),
                "predicted_label_distribution": json.dumps(_distribution(predicted_labels), sort_keys=True),
                "accuracy": _accuracy(true_labels, predicted_labels),
                "macro_f1": _macro_f1(true_labels, predicted_labels),
            }
        )
    return pd.DataFrame(rows).sort_values("domain_id").reset_index(drop=True)


def _distribution(labels: pd.Series) -> dict[str, int]:
    return {str(label): int(count) for label, count in labels.value_counts().sort_index().items()}


def _accuracy(true_labels: pd.Series, predicted_labels: pd.Series) -> float:
    if len(true_labels) == 0:
        return 0.0
    return float((true_labels.reset_index(drop=True) == predicted_labels.reset_index(drop=True)).mean())


def _macro_f1(true_labels: pd.Series, predicted_labels: pd.Series) -> float:
    labels = sorted(set(true_labels.tolist()) | set(predicted_labels.tolist()))
    if not labels:
        return 0.0
    scores = []
    for label in labels:
        true_positive = int(((true_labels == label) & (predicted_labels == label)).sum())
        false_positive = int(((true_labels != label) & (predicted_labels == label)).sum())
        false_negative = int(((true_labels == label) & (predicted_labels != label)).sum())
        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
        recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
        scores.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return float(sum(scores) / len(scores))


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze OpenEW-SA predictions by domain_id.")
    parser.add_argument("predictions_csv", help="Path to predictions.csv from training or evaluation.")
    parser.add_argument("--output", default="tables/predictions_by_domain.csv", help="Output CSV path.")
    args = parser.parse_args()

    table = summarize_by_domain(args.predictions_csv)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(output, index=False)
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
