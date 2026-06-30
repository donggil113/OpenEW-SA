#!/usr/bin/env python
"""Generate baseline OOD scores from Paper 2 split manifests and predictions."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

SUPPORTED_METHODS = (
    "random_baseline",
    "max_softmax_probability",
    "entropy",
    "energy_score",
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Generate baseline OOD score CSVs from Paper 2 split manifests.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--split-csv", required=True, type=Path, help="Paper 2 split manifest CSV.")
    parser.add_argument(
        "--predictions",
        type=Path,
        help="Optional prediction CSV with probabilities or logits keyed by sample ID.",
    )
    parser.add_argument("--probability-prefix", default="prob_", help="Probability column prefix.")
    parser.add_argument("--logit-prefix", default="logit_", help="Logit column prefix.")
    parser.add_argument("--true-label-column", default="true_label", help="Ground-truth label column.")
    parser.add_argument("--sample-id-column", default="sample_id", help="Sample identifier column.")
    parser.add_argument("--method", required=True, choices=SUPPORTED_METHODS, help="OOD scoring method.")
    parser.add_argument("--output", required=True, type=Path, help="Output score CSV path.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for random_baseline.")
    return parser.parse_args()


def main() -> None:
    """Run baseline OOD score generation."""

    args = parse_args()
    split = _read_csv(args.split_csv)
    frame = _merge_predictions(split, args.predictions, args.sample_id_column)
    scores = build_ood_scores(
        frame=frame,
        method=args.method,
        probability_prefix=args.probability_prefix,
        logit_prefix=args.logit_prefix,
        true_label_column=args.true_label_column,
        sample_id_column=args.sample_id_column,
        seed=args.seed,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    scores.to_csv(args.output, index=False)
    print(f"Wrote {args.output} ({len(scores)} rows, method={args.method})")


def build_ood_scores(
    frame: pd.DataFrame,
    method: str,
    probability_prefix: str = "prob_",
    logit_prefix: str = "logit_",
    true_label_column: str = "true_label",
    sample_id_column: str = "sample_id",
    seed: int = 42,
) -> pd.DataFrame:
    """Return a score frame where larger ``ood_score`` means more OOD-like."""

    if method not in SUPPORTED_METHODS:
        supported = ", ".join(SUPPORTED_METHODS)
        raise ValueError(f"Unsupported method '{method}'. Expected one of: {supported}")
    _require_columns(frame, [sample_id_column])
    frame = frame.reset_index(drop=True).copy()

    output = pd.DataFrame(
        {
            "sample_id": frame[sample_id_column].fillna("").astype(str),
            "true_label": _resolve_true_labels(frame, true_label_column),
        }
    )
    predicted_labels = _resolve_optional_column(frame, ["predicted_label", "predicted_label_prediction"])
    confidence = _resolve_optional_column(frame, ["confidence", "confidence_prediction"])

    if method == "random_baseline":
        rng = np.random.default_rng(seed)
        output["ood_score"] = rng.random(len(frame))
    elif method in {"max_softmax_probability", "entropy"}:
        probability_columns = _prefixed_columns(frame, probability_prefix)
        probabilities = _normalized_matrix(frame, probability_columns)
        max_prob = probabilities.max(axis=1)
        if predicted_labels is None:
            labels = [_strip_prefix(column, probability_prefix) for column in probability_columns]
            predicted_labels = pd.Series([labels[index] for index in probabilities.argmax(axis=1)])
        if confidence is None:
            confidence = pd.Series(max_prob)
        if method == "max_softmax_probability":
            output["ood_score"] = 1.0 - max_prob
        else:
            output["ood_score"] = _normalized_entropy(probabilities)
    elif method == "energy_score":
        logit_columns = _prefixed_columns(frame, logit_prefix)
        logits = _numeric_matrix(frame, logit_columns)
        if predicted_labels is None:
            labels = [_strip_prefix(column, logit_prefix) for column in logit_columns]
            predicted_labels = pd.Series([labels[index] for index in logits.argmax(axis=1)])
        if confidence is None:
            confidence = pd.Series(_softmax(logits).max(axis=1))
        output["ood_score"] = -_logsumexp(logits, axis=1)

    output["predicted_label"] = _optional_text(predicted_labels, len(frame))
    output["confidence"] = _optional_float(confidence, len(frame))
    ood_labels = _resolve_optional_column(frame, ["ood_label", "ood_label_prediction"])
    output["ood_label"] = _optional_text(ood_labels, len(frame))
    output["score_method"] = method
    return output.loc[
        :,
        [
            "sample_id",
            "true_label",
            "predicted_label",
            "confidence",
            "ood_score",
            "ood_label",
            "score_method",
        ],
    ]


def _merge_predictions(split: pd.DataFrame, predictions_path: Path | None, sample_id_column: str) -> pd.DataFrame:
    _require_columns(split, [sample_id_column])
    if predictions_path is None:
        return split.copy()
    predictions = _read_csv(predictions_path)
    _require_columns(predictions, [sample_id_column])
    marker_column = "__paper2_prediction_present"
    while marker_column in predictions.columns or marker_column in split.columns:
        marker_column = f"_{marker_column}"
    predictions = predictions.copy()
    predictions[marker_column] = "1"
    merged = split.merge(
        predictions,
        on=sample_id_column,
        how="left",
        suffixes=("", "_prediction"),
        validate="many_to_one",
    )
    missing = merged[marker_column].ne("1")
    if missing.any():
        raise ValueError(f"Predictions are missing for {int(missing.sum())} split rows.")
    merged = merged.drop(columns=[marker_column])
    return merged


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    if frame.empty:
        raise ValueError(f"CSV is empty: {path}")
    return frame


def _resolve_true_labels(frame: pd.DataFrame, true_label_column: str) -> pd.Series:
    candidates = [
        true_label_column,
        f"{true_label_column}_prediction",
        "label",
        "label_prediction",
    ]
    resolved = _resolve_optional_column(frame, candidates)
    if resolved is None:
        return pd.Series([""] * len(frame))
    return resolved.fillna("").astype(str)


def _resolve_optional_column(frame: pd.DataFrame, candidates: list[str]) -> pd.Series | None:
    for column in candidates:
        if column in frame.columns:
            return frame[column]
    return None


def _prefixed_columns(frame: pd.DataFrame, prefix: str) -> list[str]:
    if not prefix:
        raise ValueError("Column prefix cannot be empty.")
    columns = [column for column in frame.columns if column.startswith(prefix)]
    if not columns:
        raise ValueError(f"No columns found with prefix '{prefix}'.")
    return columns


def _normalized_matrix(frame: pd.DataFrame, columns: list[str]) -> np.ndarray:
    values = _numeric_matrix(frame, columns)
    values = np.clip(values, 0.0, None)
    totals = values.sum(axis=1, keepdims=True)
    if np.any(totals <= 0):
        raise ValueError("Probability rows must have positive total mass.")
    return values / totals


def _numeric_matrix(frame: pd.DataFrame, columns: list[str]) -> np.ndarray:
    values = frame[columns].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    if np.isnan(values).any():
        raise ValueError(f"Columns contain missing or non-numeric values: {columns}")
    return values


def _normalized_entropy(probabilities: np.ndarray) -> np.ndarray:
    clipped = np.clip(probabilities, 1e-12, 1.0)
    entropy = -(clipped * np.log(clipped)).sum(axis=1)
    if probabilities.shape[1] <= 1:
        return np.zeros(probabilities.shape[0], dtype=float)
    return entropy / np.log(probabilities.shape[1])


def _softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / exp.sum(axis=1, keepdims=True)


def _logsumexp(values: np.ndarray, axis: int) -> np.ndarray:
    maximum = values.max(axis=axis, keepdims=True)
    return np.squeeze(maximum, axis=axis) + np.log(np.exp(values - maximum).sum(axis=axis))


def _strip_prefix(column: str, prefix: str) -> str:
    return column[len(prefix) :] if column.startswith(prefix) else column


def _optional_text(series: pd.Series | None, length: int) -> pd.Series:
    if series is None:
        return pd.Series([""] * length)
    return series.fillna("").astype(str).reset_index(drop=True)


def _optional_float(series: pd.Series | None, length: int) -> pd.Series:
    if series is None:
        return pd.Series([""] * length)
    return pd.to_numeric(series, errors="coerce").reset_index(drop=True)


def _require_columns(frame: pd.DataFrame, columns: list[str]) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")


if __name__ == "__main__":
    main()
