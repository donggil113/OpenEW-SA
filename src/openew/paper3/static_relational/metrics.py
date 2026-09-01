"""Classification and calibration metrics for the frozen pilot."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, recall_score


def expected_calibration_error(
    probabilities: np.ndarray, targets: np.ndarray, bins: int = 15
) -> float:
    probabilities = np.asarray(probabilities, dtype=np.float64)
    targets = np.asarray(targets, dtype=np.int64)
    require_finite_probabilities(probabilities)
    if len(probabilities) != len(targets):
        raise ValueError("Probability/target length mismatch")
    if not len(targets):
        return 0.0
    confidence = probabilities.max(axis=1)
    predictions = probabilities.argmax(axis=1)
    correctness = predictions == targets
    boundaries = np.linspace(0.0, 1.0, bins + 1)
    result = 0.0
    for index in range(bins):
        lower, upper = boundaries[index], boundaries[index + 1]
        selected = (confidence > lower) & (confidence <= upper)
        if index == 0:
            selected |= confidence == 0.0
        if selected.any():
            result += float(selected.mean()) * abs(
                float(correctness[selected].mean()) - float(confidence[selected].mean())
            )
    return float(result)


def classification_metrics(
    targets: np.ndarray,
    probabilities: np.ndarray,
    domains: np.ndarray,
    class_names: tuple[str, ...],
    ece_bins: int,
) -> dict[str, Any]:
    targets = np.asarray(targets, dtype=np.int64)
    probabilities = np.asarray(probabilities, dtype=np.float64)
    domains = np.asarray(domains).astype(str)
    require_finite_probabilities(probabilities)
    if probabilities.shape != (len(targets), len(class_names)):
        raise ValueError(
            f"Probability shape {probabilities.shape} != {(len(targets), len(class_names))}"
        )
    predictions = probabilities.argmax(axis=1)
    labels = list(range(len(class_names)))
    per_domain: dict[str, dict[str, float | int]] = {}
    for domain in sorted(set(domains.tolist())):
        mask = domains == domain
        per_domain[domain] = {
            "n_samples": int(mask.sum()),
            "macro_f1": float(
                f1_score(targets[mask], predictions[mask], labels=labels, average="macro", zero_division=0)
            ),
            "balanced_accuracy": _balanced_accuracy(targets[mask], predictions[mask]),
            "accuracy": float(accuracy_score(targets[mask], predictions[mask])),
        }
    return {
        "n_samples": int(len(targets)),
        "macro_f1": float(
            f1_score(targets, predictions, labels=labels, average="macro", zero_division=0)
        ),
        "balanced_accuracy": _balanced_accuracy(targets, predictions),
        "accuracy": float(accuracy_score(targets, predictions)),
        "ece": expected_calibration_error(probabilities, targets, bins=ece_bins),
        "per_domain": per_domain,
    }


def require_finite_probabilities(probabilities: np.ndarray) -> None:
    if not np.isfinite(probabilities).all():
        raise ValueError("Non-finite model probabilities are forbidden")
    if probabilities.ndim != 2:
        raise ValueError(f"Expected two-dimensional probabilities, got {probabilities.shape}")
    row_sums = probabilities.sum(axis=1)
    if not np.allclose(row_sums, 1.0, rtol=1e-4, atol=1e-5):
        raise ValueError("Probability rows do not sum to one")


def _balanced_accuracy(targets: np.ndarray, predictions: np.ndarray) -> float:
    present = sorted(set(np.asarray(targets, dtype=np.int64).tolist()))
    return float(
        recall_score(targets, predictions, labels=present, average="macro", zero_division=0)
    ) if present else 0.0
