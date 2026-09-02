"""Frozen WiSig classification metrics and calibration summaries."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score


def expected_calibration_error(probabilities: np.ndarray, labels: np.ndarray, bins: int = 15) -> float:
    probabilities = np.asarray(probabilities, dtype=np.float64)
    labels = np.asarray(labels, dtype=np.int64)
    confidence = probabilities.max(axis=1)
    predictions = probabilities.argmax(axis=1)
    boundaries = np.linspace(0.0, 1.0, bins + 1)
    ece = 0.0
    for index in range(bins):
        mask = (confidence > boundaries[index]) & (confidence <= boundaries[index + 1])
        if index == 0:
            mask |= confidence == 0.0
        if mask.any():
            ece += mask.mean() * abs(float((predictions[mask] == labels[mask]).mean()) - float(confidence[mask].mean()))
    return float(ece)


def classification_metrics(labels: np.ndarray, probabilities: np.ndarray) -> dict[str, float]:
    labels = np.asarray(labels, dtype=np.int64)
    probabilities = np.asarray(probabilities, dtype=np.float64)
    if not np.isfinite(probabilities).all():
        raise FloatingPointError("non-finite probabilities")
    predictions = probabilities.argmax(axis=1)
    return {
        "macro_f1": float(f1_score(labels, predictions, average="macro", zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(labels, predictions)),
        "accuracy": float(accuracy_score(labels, predictions)),
        "ece": expected_calibration_error(probabilities, labels),
    }


def per_group_macro_f1(labels: np.ndarray, probabilities: np.ndarray, groups: np.ndarray) -> dict[str, float]:
    predictions = probabilities.argmax(axis=1)
    return {
        str(group): float(f1_score(labels[groups == group], predictions[groups == group], average="macro", zero_division=0))
        for group in sorted(set(str(value) for value in groups))
    }
