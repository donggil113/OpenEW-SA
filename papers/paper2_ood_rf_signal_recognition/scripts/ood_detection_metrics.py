#!/usr/bin/env python
"""Compute OOD detection metrics from ID/OOD score CSV files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Compute AUROC, AUPR-OOD, FPR95, and detection accuracy for OOD scores.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--scores", type=Path, help="Single CSV with labels and OOD scores.")
    input_group.add_argument("--id-scores", type=Path, help="CSV containing ID sample scores.")
    parser.add_argument("--ood-scores", type=Path, help="CSV containing OOD sample scores.")
    parser.add_argument("--score-column", default="ood_score", help="OOD score column.")
    parser.add_argument("--label-column", default="ood_label", help="Label column for --scores.")
    parser.add_argument("--ood-label", default="1", help="OOD label value for --scores.")
    parser.add_argument("--id-label", default="0", help="ID label value for --scores.")
    direction = parser.add_mutually_exclusive_group()
    direction.add_argument("--higher-is-ood", action="store_true", default=True, help="Higher scores mean OOD.")
    direction.add_argument("--lower-is-ood", action="store_true", help="Lower scores mean OOD.")
    parser.add_argument("--output", type=Path, help="Optional JSON or CSV output path.")
    return parser.parse_args()


def main() -> None:
    """Run OOD metric computation."""

    args = parse_args()
    labels, scores = _load_scores(args)
    if args.lower_is_ood:
        scores = -scores
    metrics = compute_ood_metrics(labels, scores)
    _write_metrics(metrics, args.output)
    print(json.dumps(metrics, indent=2, sort_keys=True))


def compute_ood_metrics(labels: np.ndarray, scores: np.ndarray) -> dict[str, Any]:
    """Return OOD metrics where label 1 is OOD and higher score means more OOD-like."""

    if labels.shape != scores.shape:
        raise ValueError("labels and scores must have the same shape")
    labels = labels.astype(int)
    scores = scores.astype(float)
    if sorted(np.unique(labels).tolist()) != [0, 1]:
        raise ValueError("OOD metrics require both ID label 0 and OOD label 1.")

    auroc = _binary_auroc(labels, scores)
    aupr_ood = _average_precision(labels, scores)
    fpr95 = _fpr_at_tpr(labels, scores, target_tpr=0.95)
    detection_accuracy, threshold = _best_detection_accuracy(labels, scores)
    return {
        "n_samples": int(len(labels)),
        "n_id": int((labels == 0).sum()),
        "n_ood": int((labels == 1).sum()),
        "auroc": auroc,
        "aupr_ood": aupr_ood,
        "fpr95": fpr95,
        "detection_accuracy": detection_accuracy,
        "best_threshold": threshold,
        "score_direction": "higher_is_ood",
    }


def _load_scores(args: argparse.Namespace) -> tuple[np.ndarray, np.ndarray]:
    if args.scores is not None:
        frame = pd.read_csv(args.scores)
        _require_columns(frame, [args.label_column, args.score_column])
        labels = _labels_from_column(frame[args.label_column], args.id_label, args.ood_label)
        scores = frame[args.score_column].astype(float).to_numpy()
        return labels, scores

    if args.ood_scores is None:
        raise ValueError("--ood-scores is required when --id-scores is used.")
    id_frame = pd.read_csv(args.id_scores)
    ood_frame = pd.read_csv(args.ood_scores)
    _require_columns(id_frame, [args.score_column])
    _require_columns(ood_frame, [args.score_column])
    id_scores = id_frame[args.score_column].astype(float).to_numpy()
    ood_scores = ood_frame[args.score_column].astype(float).to_numpy()
    labels = np.concatenate([np.zeros(len(id_scores), dtype=int), np.ones(len(ood_scores), dtype=int)])
    scores = np.concatenate([id_scores, ood_scores])
    return labels, scores


def _labels_from_column(series: pd.Series, id_label: str, ood_label: str) -> np.ndarray:
    labels: list[int] = []
    for value in series.fillna("").astype(str):
        if value == str(id_label):
            labels.append(0)
        elif value == str(ood_label):
            labels.append(1)
        else:
            raise ValueError(f"Unexpected OOD label value '{value}'. Expected {id_label} or {ood_label}.")
    return np.asarray(labels, dtype=int)


def _fpr_at_tpr(labels: np.ndarray, scores: np.ndarray, target_tpr: float) -> float:
    positives = labels == 1
    negatives = labels == 0
    n_pos = int(positives.sum())
    n_neg = int(negatives.sum())
    candidates = []
    for threshold in np.unique(scores):
        predicted = scores >= threshold
        tpr = ((predicted & positives).sum() / n_pos) if n_pos else 0.0
        fpr = ((predicted & negatives).sum() / n_neg) if n_neg else 0.0
        if tpr >= target_tpr:
            candidates.append(float(fpr))
    candidates.append(1.0)
    if len(candidates) == 0:
        return 1.0
    return float(min(candidates))


def _binary_auroc(labels: np.ndarray, scores: np.ndarray) -> float:
    positives = labels == 1
    negatives = labels == 0
    n_pos = int(positives.sum())
    n_neg = int(negatives.sum())
    if n_pos == 0 or n_neg == 0:
        raise ValueError("AUROC requires at least one ID and one OOD sample.")
    ranks = _average_ranks(scores)
    positive_rank_sum = float(ranks[positives].sum())
    auc = (positive_rank_sum - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return float(auc)


def _average_precision(labels: np.ndarray, scores: np.ndarray) -> float:
    order = np.argsort(-scores, kind="mergesort")
    sorted_labels = labels[order]
    positives = sorted_labels == 1
    n_pos = int(positives.sum())
    if n_pos == 0:
        raise ValueError("AUPR-OOD requires at least one OOD sample.")
    true_positives = np.cumsum(positives)
    ranks = np.arange(1, len(sorted_labels) + 1)
    precision = true_positives / ranks
    return float(precision[positives].sum() / n_pos)


def _average_ranks(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=float)
    sorted_values = values[order]
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and sorted_values[end] == sorted_values[start]:
            end += 1
        average_rank = (start + 1 + end) / 2.0
        ranks[order[start:end]] = average_rank
        start = end
    return ranks


def _best_detection_accuracy(labels: np.ndarray, scores: np.ndarray) -> tuple[float, float]:
    thresholds = np.unique(scores)
    candidates = np.concatenate(
        [
            np.asarray([-np.inf]),
            thresholds,
            np.asarray([np.inf]),
        ]
    )
    best_accuracy = -1.0
    best_threshold = 0.0
    for threshold in candidates:
        predicted_ood = scores >= threshold
        accuracy = float((predicted_ood.astype(int) == labels).mean())
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_threshold = float(threshold)
    return best_accuracy, best_threshold


def _require_columns(frame: pd.DataFrame, columns: list[str]) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")


def _write_metrics(metrics: dict[str, Any], output: Path | None) -> None:
    if output is None:
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() == ".csv":
        pd.DataFrame([metrics]).to_csv(output, index=False)
    else:
        with output.open("w", encoding="utf-8") as handle:
            json.dump(metrics, handle, indent=2, sort_keys=True)
            handle.write("\n")


if __name__ == "__main__":
    main()
