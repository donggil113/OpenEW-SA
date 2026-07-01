#!/usr/bin/env python
"""Compute calibration metrics for Paper 2 RF recognition predictions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SYMBOLIC_STRING_COLUMNS = ["sample_id", "true_label", "predicted_label", "ood_label"]
PROBABILITY_PREFIXES = ("prob_", "probability_", "p_")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Compute ECE, MCE, NLL, and Brier score from a prediction CSV.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--predictions", required=True, type=Path, help="Prediction CSV path.")
    parser.add_argument("--true-label-column", default="true_label", help="Ground-truth label column.")
    parser.add_argument("--predicted-label-column", default="predicted_label", help="Predicted label column.")
    parser.add_argument("--confidence-column", default="confidence", help="Prediction confidence column.")
    parser.add_argument(
        "--probability-columns",
        action="append",
        help="Class probability columns. Comma-separated values may be repeated.",
    )
    parser.add_argument(
        "--class-labels",
        action="append",
        help="Class labels matching probability columns. Defaults to probability column names.",
    )
    parser.add_argument(
        "--probability-prefix",
        default="prob_",
        help="Preferred prefix stripped from probability columns; auto-detection also supports probability_ and p_.",
    )
    parser.add_argument("--n-bins", type=int, default=15, help="Number of confidence bins.")
    parser.add_argument("--output", type=Path, help="Optional JSON or CSV output path.")
    return parser.parse_args()


def main() -> None:
    """Run calibration metric computation."""

    args = parse_args()
    predictions = _read_predictions(args.predictions)
    metrics = compute_calibration_metrics(
        predictions=predictions,
        true_label_column=args.true_label_column,
        predicted_label_column=args.predicted_label_column,
        confidence_column=args.confidence_column,
        probability_columns=_list_option(args.probability_columns),
        class_labels=_list_option(args.class_labels),
        probability_prefix=args.probability_prefix,
        n_bins=args.n_bins,
    )
    _write_metrics(metrics, args.output)
    print(json.dumps(metrics, indent=2, sort_keys=True))


def compute_calibration_metrics(
    predictions: pd.DataFrame,
    true_label_column: str = "true_label",
    predicted_label_column: str = "predicted_label",
    confidence_column: str = "confidence",
    probability_columns: list[str] | None = None,
    class_labels: list[str] | None = None,
    probability_prefix: str = "prob_",
    n_bins: int = 15,
) -> dict[str, Any]:
    """Return calibration metrics from prediction labels, confidence, and optional probabilities."""

    predictions = _preserve_string_columns(predictions, [true_label_column, predicted_label_column])
    probability_columns = probability_columns or _detect_probability_columns(predictions)
    class_labels = class_labels or []
    _require_columns(predictions, [true_label_column])

    probabilities: np.ndarray | None = None
    if probability_columns:
        _require_columns(predictions, probability_columns)
        probabilities = _normalized_probabilities(predictions, probability_columns)
        if not class_labels:
            class_labels = [_probability_label(column, probability_prefix) for column in probability_columns]
        if len(class_labels) != len(probability_columns):
            raise ValueError("--class-labels must match the number of probability columns.")

    if confidence_column in predictions.columns:
        confidence = predictions[confidence_column].astype(float).to_numpy()
    elif probabilities is not None:
        confidence = probabilities.max(axis=1)
    else:
        raise ValueError(
            f"Missing confidence column '{confidence_column}'. Provide it or pass --probability-columns."
        )
    confidence = np.clip(confidence, 0.0, 1.0)

    true_labels = predictions[true_label_column].fillna("").astype(str).to_numpy()
    if predicted_label_column in predictions.columns:
        predicted_labels = predictions[predicted_label_column].fillna("").astype(str).to_numpy()
    elif probabilities is not None and class_labels:
        predicted_labels = np.asarray([class_labels[index] for index in probabilities.argmax(axis=1)])
    else:
        raise ValueError(
            f"Missing predicted label column '{predicted_label_column}'. Provide it or probabilities."
        )

    correct = (true_labels == predicted_labels).astype(float)
    ece, mce, bins = _expected_calibration_error(confidence, correct, n_bins)
    metrics: dict[str, Any] = {
        "n_samples": int(len(predictions)),
        "accuracy": float(correct.mean()) if len(correct) else 0.0,
        "average_confidence": float(confidence.mean()) if len(confidence) else 0.0,
        "confidence_accuracy_gap": float(confidence.mean() - correct.mean()) if len(correct) else 0.0,
        "ece": ece,
        "mce": mce,
        "n_bins": int(n_bins),
        "bins": bins,
    }

    if probabilities is not None:
        nll, brier, valid_probability_rows = _probability_metrics(probabilities, true_labels, class_labels)
        metrics.update(
            {
                "nll": nll,
                "brier": brier,
                "valid_probability_rows": int(valid_probability_rows),
            }
        )
    else:
        metrics.update({"nll": None, "brier": None, "valid_probability_rows": 0})
    return metrics


def _expected_calibration_error(
    confidence: np.ndarray,
    correct: np.ndarray,
    n_bins: int,
) -> tuple[float, float, list[dict[str, float]]]:
    if n_bins <= 0:
        raise ValueError("n_bins must be positive")
    if len(confidence) != len(correct):
        raise ValueError("confidence and correctness arrays must have the same length")

    edges = np.linspace(0.0, 1.0, n_bins + 1)
    total = len(confidence)
    ece = 0.0
    mce = 0.0
    rows: list[dict[str, float]] = []
    for index in range(n_bins):
        lower = edges[index]
        upper = edges[index + 1]
        if index == n_bins - 1:
            mask = (confidence >= lower) & (confidence <= upper)
        else:
            mask = (confidence >= lower) & (confidence < upper)
        count = int(mask.sum())
        if count == 0:
            accuracy = 0.0
            avg_confidence = 0.0
            gap = 0.0
        else:
            accuracy = float(correct[mask].mean())
            avg_confidence = float(confidence[mask].mean())
            gap = abs(accuracy - avg_confidence)
        weight = count / total if total else 0.0
        ece += weight * gap
        mce = max(mce, gap)
        rows.append(
            {
                "bin_lower": float(lower),
                "bin_upper": float(upper),
                "count": float(count),
                "accuracy": accuracy,
                "average_confidence": avg_confidence,
                "gap": float(gap),
            }
        )
    return float(ece), float(mce), rows


def _probability_metrics(
    probabilities: np.ndarray,
    true_labels: np.ndarray,
    class_labels: list[str],
) -> tuple[float | None, float | None, int]:
    label_to_index = {str(label): index for index, label in enumerate(class_labels)}
    true_indices = np.asarray(
        [_label_index(str(label), label_to_index, class_labels) for label in true_labels],
        dtype=int,
    )
    valid = true_indices >= 0
    if not valid.any():
        return None, None, 0

    clipped = np.clip(probabilities[valid], 1e-12, 1.0)
    valid_indices = true_indices[valid]
    nll = -np.log(clipped[np.arange(len(valid_indices)), valid_indices]).mean()
    one_hot = np.zeros_like(clipped)
    one_hot[np.arange(len(valid_indices)), valid_indices] = 1.0
    brier = np.square(clipped - one_hot).sum(axis=1).mean()
    return float(nll), float(brier), int(valid.sum())


def _normalized_probabilities(predictions: pd.DataFrame, probability_columns: list[str]) -> np.ndarray:
    probabilities = predictions[probability_columns].astype(float).to_numpy()
    probabilities = np.clip(probabilities, 0.0, None)
    row_sums = probabilities.sum(axis=1, keepdims=True)
    if np.any(row_sums <= 0):
        raise ValueError("Probability rows must have positive total mass.")
    return probabilities / row_sums


def _label_index(label: str, label_to_index: dict[str, int], class_labels: list[str]) -> int:
    """Return the probability-column index for a true label, recovering unique zero-padded labels."""

    if label in label_to_index:
        return label_to_index[label]
    recovered = _zero_padded_label(label, class_labels)
    if recovered in label_to_index:
        return label_to_index[recovered]
    return -1


def _zero_padded_label(label: str, class_labels: list[str]) -> str:
    """Safely map numeric-looking labels such as ``100`` to class labels like ``0100``."""

    if not label.isdigit():
        return label
    matches = [
        candidate
        for candidate in class_labels
        if candidate.isdigit() and len(candidate) > len(label) and int(candidate) == int(label)
    ]
    return matches[0] if len(matches) == 1 else label


def _detect_probability_columns(predictions: pd.DataFrame) -> list[str]:
    """Return probability columns using supported Paper 2 prefixes."""

    return [
        column
        for column in predictions.columns
        if any(column.startswith(prefix) and len(column) > len(prefix) for prefix in PROBABILITY_PREFIXES)
    ]


def _probability_label(column: str, prefix: str) -> str:
    prefixes = [prefix] if prefix else []
    prefixes.extend(item for item in PROBABILITY_PREFIXES if item not in prefixes)
    for candidate in prefixes:
        if candidate and column.startswith(candidate):
            return column[len(candidate) :]
    return column


def _read_predictions(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Prediction CSV not found: {path}")
    predictions = pd.read_csv(path, dtype=str, keep_default_na=False)
    if predictions.empty:
        raise ValueError(f"Prediction CSV is empty: {path}")
    return _preserve_string_columns(predictions)


def _preserve_string_columns(frame: pd.DataFrame, extra_columns: list[str] | None = None) -> pd.DataFrame:
    preserved = frame.copy()
    for column in [*SYMBOLIC_STRING_COLUMNS, *(extra_columns or [])]:
        if column in preserved.columns:
            preserved[column] = preserved[column].fillna("").astype(str)
    return preserved


def _require_columns(frame: pd.DataFrame, columns: list[str]) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")


def _list_option(values: list[str] | None) -> list[str]:
    if values is None:
        return []
    parsed: list[str] = []
    for value in values:
        parsed.extend(part.strip() for part in str(value).split(",") if part.strip())
    return parsed


def _write_metrics(metrics: dict[str, Any], output: Path | None) -> None:
    if output is None:
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() == ".csv":
        flattened = {key: value for key, value in metrics.items() if key != "bins"}
        pd.DataFrame([flattened]).to_csv(output, index=False)
    else:
        with output.open("w", encoding="utf-8") as handle:
            json.dump(metrics, handle, indent=2, sort_keys=True)
            handle.write("\n")


if __name__ == "__main__":
    main()
