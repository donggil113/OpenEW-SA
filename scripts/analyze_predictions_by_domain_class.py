#!/usr/bin/env python
"""Summarize OpenEW-SA predictions by domain and true class."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

DEFAULT_OUTPUT = Path("tables") / "predictions_by_domain_class.csv"


def summarize_by_domain_class(predictions_csv: str | Path, top_k: int = 5) -> pd.DataFrame:
    """Return per-domain, per-true-class prediction metrics."""

    predictions = pd.read_csv(predictions_csv)
    required = {"domain_id", "true_label", "predicted_label"}
    missing = required.difference(predictions.columns)
    if missing:
        raise ValueError(f"Predictions CSV is missing required columns: {sorted(missing)}")

    normalized = pd.DataFrame(
        {
            "domain_id": predictions["domain_id"].fillna("").astype(str),
            "true_label": predictions["true_label"].fillna("unknown").astype(str),
            "predicted_label": predictions["predicted_label"].fillna("unknown").astype(str),
        }
    )

    rows = []
    for domain_id, domain_group in normalized.groupby("domain_id", dropna=False):
        for true_label, class_group in domain_group.groupby("true_label", dropna=False):
            rows.append(
                {
                    "domain_id": domain_id,
                    "true_label": true_label,
                    "n_samples": int(len(class_group)),
                    "top_predicted_labels": _top_predicted_labels(class_group["predicted_label"], top_k),
                    "precision": _precision(domain_group, true_label),
                    "recall": _recall(domain_group, true_label),
                    "f1": _f1(domain_group, true_label),
                }
            )

    return pd.DataFrame(rows).sort_values(["domain_id", "true_label"]).reset_index(drop=True)


def _top_predicted_labels(predicted_labels: pd.Series, top_k: int) -> str:
    counts = predicted_labels.value_counts()
    ordered = sorted(counts.items(), key=lambda item: (-int(item[1]), str(item[0])))[:top_k]
    return json.dumps({str(label): int(count) for label, count in ordered})


def _precision(domain_group: pd.DataFrame, label: str) -> float:
    true_positive = int(((domain_group["true_label"] == label) & (domain_group["predicted_label"] == label)).sum())
    false_positive = int(((domain_group["true_label"] != label) & (domain_group["predicted_label"] == label)).sum())
    denominator = true_positive + false_positive
    return float(true_positive / denominator) if denominator else 0.0


def _recall(domain_group: pd.DataFrame, label: str) -> float:
    true_positive = int(((domain_group["true_label"] == label) & (domain_group["predicted_label"] == label)).sum())
    false_negative = int(((domain_group["true_label"] == label) & (domain_group["predicted_label"] != label)).sum())
    denominator = true_positive + false_negative
    return float(true_positive / denominator) if denominator else 0.0


def _f1(domain_group: pd.DataFrame, label: str) -> float:
    precision = _precision(domain_group, label)
    recall = _recall(domain_group, label)
    denominator = precision + recall
    return float(2 * precision * recall / denominator) if denominator else 0.0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze OpenEW-SA predictions by domain_id and true_label.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("predictions_csv", help="Path to predictions.csv from training or evaluation.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, type=Path, help="Output CSV path.")
    parser.add_argument("--top-k", default=5, type=int, help="Number of predicted labels to include per row.")
    args = parser.parse_args()

    table = summarize_by_domain_class(args.predictions_csv, top_k=args.top_k)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.output, index=False)
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
