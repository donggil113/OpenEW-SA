#!/usr/bin/env python
"""Fit train-only feature-distance models and score an evaluation manifest."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from train_baseline_classifier import (
    SplitFrame,
    _load_features,
    _max_feature_dim,
    _preserve_split_strings,
    _read_split,
    _validate_manifest_columns,
)

METHODS = ("nearest_centroid_euclidean", "nearest_centroid_cosine", "mahalanobis")
OUTPUT_COLUMNS = ["sample_id", "true_label", "ood_label", "ood_score", "nearest_class", "method"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute train-fitted feature-distance OOD scores.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--train-csv", required=True, type=Path)
    parser.add_argument("--eval-csv", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--method", required=True, choices=METHODS)
    parser.add_argument("--label-column", default="label")
    parser.add_argument("--feature-index-column", default="feature_index")
    parser.add_argument("--feature-path-column", default="feature_path")
    parser.add_argument("--sample-id-column", default="sample_id")
    parser.add_argument("--regularization", type=float, default=1e-4)
    parser.add_argument("--max-train-samples-per-class", type=int)
    parser.add_argument("--batch-size", type=int, default=4096)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--metadata-output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.regularization < 0 or not np.isfinite(args.regularization):
        raise ValueError("--regularization must be finite and non-negative.")
    if args.batch_size <= 0:
        raise ValueError("--batch-size must be positive.")
    if args.max_train_samples_per_class is not None and args.max_train_samples_per_class <= 0:
        raise ValueError("--max-train-samples-per-class must be positive when provided.")

    train = _preserve_split_strings(_read_split(args.train_csv, "train"), [args.label_column, args.sample_id_column])
    evaluation = _preserve_split_strings(_read_split(args.eval_csv, "eval"), [args.label_column, args.sample_id_column])
    train = _resolve_feature_paths(train, args.feature_path_column)
    evaluation = _resolve_feature_paths(evaluation, args.feature_path_column)
    splits = [train, evaluation]
    _validate_manifest_columns(
        splits, args.label_column, args.feature_index_column, args.feature_path_column, args.sample_id_column
    )
    if "ood_label" not in evaluation.frame.columns:
        raise ValueError("Evaluation CSV is missing required column: ood_label")
    feature_dim = _max_feature_dim(splits, args.feature_path_column)
    train_features = _load_features(
        train, feature_dim, args.feature_path_column, args.feature_index_column, None
    ).astype(np.float64)
    eval_features = _load_features(
        evaluation, feature_dim, args.feature_path_column, args.feature_index_column, None
    ).astype(np.float64)
    _require_finite(train_features, "training")
    _require_finite(eval_features, "evaluation")

    labels = train.frame[args.label_column].astype(str).to_numpy()
    selected = _subsample_indices(labels, args.max_train_samples_per_class, args.seed)
    fit_features, fit_labels = train_features[selected], labels[selected]
    classes = pd.Series(fit_labels).drop_duplicates().to_numpy(dtype=str)
    if len(classes) == 0:
        raise ValueError("Training data contains no classes.")
    centroids = np.vstack([fit_features[fit_labels == label].mean(axis=0) for label in classes])
    inverse_covariance = None
    if args.method == "mahalanobis":
        residuals = np.vstack([fit_features[fit_labels == label] - centroids[i] for i, label in enumerate(classes)])
        denominator = max(len(residuals) - len(classes), 1)
        covariance = residuals.T @ residuals / denominator
        covariance.flat[:: feature_dim + 1] += args.regularization
        inverse_covariance = np.linalg.pinv(covariance, hermitian=True)
        _require_finite(inverse_covariance, "inverse covariance")

    scores, nearest = _score_batches(
        eval_features, centroids, classes, args.method, args.batch_size, inverse_covariance
    )
    _require_finite(scores, "output scores")
    ood_labels = evaluation.frame["ood_label"].astype(str).to_numpy()
    output = pd.DataFrame({
        "sample_id": evaluation.frame[args.sample_id_column].astype(str),
        "true_label": evaluation.frame[args.label_column].astype(str),
        "ood_label": ood_labels,
        "ood_score": scores,
        "nearest_class": nearest,
        "method": args.method,
    })[OUTPUT_COLUMNS]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)

    original_counts = pd.Series(labels).value_counts(sort=False)
    fitted_counts = pd.Series(fit_labels).value_counts(sort=False)
    metadata = {
        "method": args.method,
        "feature_dim": feature_dim,
        "classes": [str(value) for value in classes],
        "class_counts": {str(key): int(value) for key, value in original_counts.items()},
        "fitted_class_counts": {str(key): int(value) for key, value in fitted_counts.items()},
        "train_count": int(len(train.frame)),
        "fitted_train_count": int(len(fit_features)),
        "eval_count": int(len(evaluation.frame)),
        "regularization": float(args.regularization),
        "batch_size": int(args.batch_size),
        "max_train_samples_per_class": args.max_train_samples_per_class,
        "seed": int(args.seed),
        "fit_data": "train_only",
        "train_csv": str(args.train_csv.resolve()),
        "eval_csv": str(args.eval_csv.resolve()),
        "score_output": str(args.output.resolve()),
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    metadata_path = args.metadata_output or args.output.with_suffix(".metadata.json")
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with metadata_path.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"Wrote {len(output)} scores to {args.output}")
    print(f"Wrote metadata to {metadata_path}")


def _subsample_indices(labels: np.ndarray, maximum: int | None, seed: int) -> np.ndarray:
    if maximum is None:
        return np.arange(len(labels))
    rng = np.random.default_rng(seed)
    selected: list[np.ndarray] = []
    for label in pd.Series(labels).drop_duplicates():
        indices = np.flatnonzero(labels == label)
        if len(indices) > maximum:
            indices = np.sort(rng.choice(indices, size=maximum, replace=False))
        selected.append(indices)
    return np.concatenate(selected)


def _resolve_feature_paths(split: SplitFrame, column: str) -> SplitFrame:
    """Resolve existing paths and conventional Windows drive paths under WSL."""

    if column not in split.frame.columns:
        return split
    frame = split.frame.copy()
    resolved: dict[str, str] = {}
    for value in frame[column].astype(str).drop_duplicates():
        candidate = Path(value)
        if not candidate.exists():
            match = re.match(r"^([A-Za-z]):[\\\\/](.*)$", value)
            if match:
                candidate = Path("/mnt") / match.group(1).lower() / Path(match.group(2).replace("\\", "/"))
        resolved[value] = str(candidate)
    frame[column] = frame[column].astype(str).map(resolved)
    return SplitFrame(name=split.name, frame=frame)


def _score_batches(features, centroids, classes, method, batch_size, inverse_covariance):
    all_scores: list[np.ndarray] = []
    all_nearest: list[np.ndarray] = []
    centroid_norms = np.linalg.norm(centroids, axis=1, keepdims=True)
    normalized_centroids = centroids / np.maximum(centroid_norms, np.finfo(float).eps)
    for start in range(0, len(features), batch_size):
        batch = features[start : start + batch_size]
        if method == "nearest_centroid_euclidean":
            distances = np.sqrt(np.maximum(_squared_euclidean(batch, centroids), 0.0))
        elif method == "nearest_centroid_cosine":
            normalized = batch / np.maximum(np.linalg.norm(batch, axis=1, keepdims=True), np.finfo(float).eps)
            distances = 1.0 - normalized @ normalized_centroids.T
        else:
            differences = batch[:, None, :] - centroids[None, :, :]
            squared = np.einsum("bcd,de,bce->bc", differences, inverse_covariance, differences, optimize=True)
            distances = np.sqrt(np.maximum(squared, 0.0))
        nearest_indices = np.argmin(distances, axis=1)
        all_scores.append(distances[np.arange(len(batch)), nearest_indices])
        all_nearest.append(classes[nearest_indices])
    return np.concatenate(all_scores), np.concatenate(all_nearest)


def _squared_euclidean(features: np.ndarray, centroids: np.ndarray) -> np.ndarray:
    values = np.sum(features * features, axis=1, keepdims=True) + np.sum(centroids * centroids, axis=1)[None, :]
    return values - 2.0 * features @ centroids.T


def _require_finite(values: np.ndarray, description: str) -> None:
    if not np.isfinite(values).all():
        raise ValueError(f"Non-finite values found in {description} features or calculations.")


if __name__ == "__main__":
    main()
