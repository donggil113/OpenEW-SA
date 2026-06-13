#!/usr/bin/env python
"""Analyze binary classification F1 across probability thresholds."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

DEFAULT_THRESHOLDS = [round(value / 100, 2) for value in range(5, 100, 5)]
PROBABILITY_COLUMN_CANDIDATES = (
    "positive_label_probability",
    "positive_class_probability",
    "positive_probability",
    "probability_positive",
    "probability_abnormal_interference",
    "probability_attack",
    "score",
    "probability",
)


def analyze_thresholds(
    predictions_csv: str | Path,
    positive_label: str | None = None,
    probability_column: str | None = None,
    thresholds: list[float] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Build a threshold curve and summary for a binary predictions file."""

    predictions = pd.read_csv(predictions_csv)
    required = {"true_label", "predicted_label"}
    missing = required.difference(predictions.columns)
    if missing:
        raise ValueError(f"Predictions CSV is missing required columns: {sorted(missing)}")

    resolved_positive_label = positive_label or _infer_positive_label(predictions)
    resolved_probability_column = probability_column or _infer_probability_column(predictions, resolved_positive_label)
    thresholds = thresholds or DEFAULT_THRESHOLDS

    true_labels = predictions["true_label"].fillna("").astype(str)
    scores = pd.to_numeric(predictions[resolved_probability_column], errors="coerce")
    if scores.isna().any():
        bad_count = int(scores.isna().sum())
        raise ValueError(f"Probability column '{resolved_probability_column}' contains {bad_count} non-numeric values")
    positive_targets = true_labels == resolved_positive_label

    rows = []
    for threshold in thresholds:
        predicted_positive = scores >= threshold
        metrics = _binary_metrics(positive_targets, predicted_positive)
        rows.append(
            {
                "threshold": float(threshold),
                "positive_label": resolved_positive_label,
                "probability_column": resolved_probability_column,
                **metrics,
            }
        )

    curve = pd.DataFrame(rows)
    best_row = curve.sort_values(["f1", "threshold"], ascending=[False, True]).iloc[0]
    default_row = curve.loc[(curve["threshold"] - 0.5).abs().idxmin()]
    summary = {
        "positive_label": resolved_positive_label,
        "probability_column": resolved_probability_column,
        "default_threshold": float(default_row["threshold"]),
        "default_threshold_f1": float(default_row["f1"]),
        "best_threshold": float(best_row["threshold"]),
        "best_threshold_f1": float(best_row["f1"]),
        "best_threshold_precision": float(best_row["precision"]),
        "best_threshold_recall": float(best_row["recall"]),
        "brier_score": _brier_score(positive_targets, scores),
        "positive_prevalence": float(positive_targets.mean()),
        "mean_positive_probability": float(scores.mean()),
    }
    for key, value in summary.items():
        curve[key] = value
    curve["is_default_threshold"] = curve["threshold"] == summary["default_threshold"]
    curve["is_best_threshold"] = curve["threshold"] == summary["best_threshold"]
    return curve, summary


def _infer_positive_label(predictions: pd.DataFrame) -> str:
    if "positive_label" in predictions.columns:
        labels = predictions["positive_label"].dropna().astype(str).unique().tolist()
        if len(labels) == 1:
            return labels[0]
    labels = sorted(
        set(predictions["true_label"].fillna("").astype(str).tolist())
        | set(predictions["predicted_label"].fillna("").astype(str).tolist())
    )
    for label in labels:
        text = label.lower()
        if any(token in text for token in ["abnormal", "interference", "jammer", "attack", "high"]):
            return label
    if len(labels) != 2:
        raise ValueError(f"Expected binary labels or --positive-label, found labels: {labels}")
    return labels[1]


def _infer_probability_column(predictions: pd.DataFrame, positive_label: str) -> str:
    positive_suffix = _probability_column_suffix(positive_label)
    candidates = [f"probability_{positive_suffix}", *PROBABILITY_COLUMN_CANDIDATES]
    for candidate in candidates:
        if candidate in predictions.columns:
            return candidate
    raise ValueError(
        "No positive-class probability column found in predictions.csv. "
        "Regenerate predictions with the updated train/evaluate code so the file includes "
        "'positive_label_probability' or pass --probability-column."
    )


def _probability_column_suffix(label_name: str) -> str:
    suffix = "".join(character.lower() if character.isalnum() else "_" for character in label_name)
    return "_".join(part for part in suffix.split("_") if part)


def _binary_metrics(true_positive_mask: pd.Series, predicted_positive_mask: pd.Series) -> dict[str, float | int]:
    true_positive = int((true_positive_mask & predicted_positive_mask).sum())
    false_positive = int((~true_positive_mask & predicted_positive_mask).sum())
    true_negative = int((~true_positive_mask & ~predicted_positive_mask).sum())
    false_negative = int((true_positive_mask & ~predicted_positive_mask).sum())
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "n_samples": int(len(true_positive_mask)),
        "true_positive": true_positive,
        "false_positive": false_positive,
        "true_negative": true_negative,
        "false_negative": false_negative,
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
    }


def _brier_score(true_positive_mask: pd.Series, scores: pd.Series) -> float:
    targets = true_positive_mask.astype(float)
    return float(((scores - targets) ** 2).mean())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute binary F1 threshold curves from predictions.csv probability scores.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("predictions_csv", help="Path to predictions.csv with positive-class probabilities.")
    parser.add_argument("--output", required=True, type=Path, help="Output threshold-curve CSV path.")
    parser.add_argument("--positive-label", help="Positive class label. Inferred when omitted.")
    parser.add_argument("--probability-column", help="Column containing positive-class probability scores.")
    args = parser.parse_args()

    curve, summary = analyze_thresholds(
        args.predictions_csv,
        positive_label=args.positive_label,
        probability_column=args.probability_column,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    curve.to_csv(args.output, index=False)
    print(f"Wrote {args.output}")
    print(
        "Default threshold "
        f"{summary['default_threshold']:.2f} F1={summary['default_threshold_f1']:.6f}; "
        f"best threshold {summary['best_threshold']:.2f} F1={summary['best_threshold_f1']:.6f}"
    )


if __name__ == "__main__":
    main()
