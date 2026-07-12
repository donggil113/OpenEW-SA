#!/usr/bin/env python
"""Generate Paper 2 feature-distance OOD scores from split manifests."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

SUPPORTED_METHODS = (
    "nearest_centroid_euclidean",
    "nearest_centroid_cosine",
    "mahalanobis",
)
SYMBOLIC_STRING_COLUMNS = [
    "sample_id",
    "dataset_source",
    "task",
    "label",
    "domain_id",
    "input_type",
    "split",
    "paper2_split",
    "split_hint",
    "true_label",
    "ood_label",
    "feature_path",
    "nearest_class",
    "method",
]


@dataclass(frozen=True)
class SplitFrame:
    """Loaded split manifest with its display name."""

    name: str
    frame: pd.DataFrame


@dataclass(frozen=True)
class FittedDistanceModel:
    """Centroid-based feature distance model."""

    method: str
    classes: np.ndarray
    centroids: np.ndarray
    inverse_covariance: np.ndarray | None
    feature_dim: int
    class_counts: dict[str, int]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Generate feature-space OOD scores from Paper 2 train/eval split manifests.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--train-csv", required=True, type=Path, help="Training split manifest CSV.")
    parser.add_argument("--eval-csv", required=True, type=Path, help="Evaluation split manifest CSV.")
    parser.add_argument("--output", required=True, type=Path, help="Output OOD score CSV path.")
    parser.add_argument("--method", required=True, choices=SUPPORTED_METHODS, help="Feature-distance scoring method.")
    parser.add_argument("--label-column", default="label", help="Ground-truth label column.")
    parser.add_argument("--feature-index-column", default="feature_index", help="Feature row index column.")
    parser.add_argument("--feature-path-column", default="feature_path", help="Feature tensor path column.")
    parser.add_argument("--sample-id-column", default="sample_id", help="Sample identifier column.")
    parser.add_argument("--regularization", type=float, default=1e-4, help="Covariance diagonal regularization.")
    parser.add_argument(
        "--max-train-samples-per-class",
        type=int,
        help="Optional per-class cap for fitting centroids/covariance.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for optional train subsampling.")
    parser.add_argument(
        "--metadata-output",
        type=Path,
        help="Optional metadata JSON path. Defaults to <output_stem>_metadata.json.",
    )
    return parser.parse_args()


def main() -> None:
    """Fit a train-only feature-distance model and write OOD scores for the eval split."""

    args = parse_args()
    train = _read_split(args.train_csv, "train")
    eval_split = _read_split(args.eval_csv, "eval")
    train = _preserve_split_strings(train, [args.sample_id_column, args.label_column])
    eval_split = _preserve_split_strings(eval_split, [args.sample_id_column, args.label_column])
    _validate_manifest_columns(
        [train, eval_split],
        label_column=args.label_column,
        feature_index_column=args.feature_index_column,
        feature_path_column=args.feature_path_column,
        sample_id_column=args.sample_id_column,
    )

    train = SplitFrame(
        name=train.name,
        frame=_sample_train_rows(
            train.frame,
            label_column=args.label_column,
            max_per_class=args.max_train_samples_per_class,
            seed=args.seed,
        ),
    )
    target_dim = _max_feature_dim([train, eval_split], feature_path_column=args.feature_path_column)
    train_features = _load_features(
        train,
        target_dim=target_dim,
        feature_path_column=args.feature_path_column,
        feature_index_column=args.feature_index_column,
    )
    train_labels = train.frame[args.label_column].astype(str).to_numpy()
    model = fit_distance_model(
        features=train_features,
        labels=train_labels,
        method=args.method,
        regularization=args.regularization,
    )

    eval_features = _load_features(
        eval_split,
        target_dim=target_dim,
        feature_path_column=args.feature_path_column,
        feature_index_column=args.feature_index_column,
    )
    scores, nearest_classes = score_features(eval_features, model)
    output = pd.DataFrame(
        {
            "sample_id": eval_split.frame[args.sample_id_column].astype(str).to_numpy(),
            "true_label": eval_split.frame[args.label_column].astype(str).to_numpy(),
            "ood_label": _ood_labels(eval_split.frame),
            "ood_score": scores,
            "nearest_class": nearest_classes,
            "method": args.method,
        }
    )
    output = _preserve_string_columns(output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)

    metadata_path = args.metadata_output or args.output.with_name(f"{args.output.stem}_metadata.json")
    _write_metadata(
        metadata_path,
        model=model,
        n_train_samples=len(train.frame),
        n_eval_samples=len(eval_split.frame),
        regularization=args.regularization,
        max_train_samples_per_class=args.max_train_samples_per_class,
        seed=args.seed,
    )
    print(f"Wrote {args.output} ({len(output)} rows, method={args.method})")
    print(f"Wrote {metadata_path}")


def fit_distance_model(
    features: np.ndarray,
    labels: np.ndarray,
    method: str,
    regularization: float,
) -> FittedDistanceModel:
    """Fit centroids and optional shared covariance from train features."""

    if method not in SUPPORTED_METHODS:
        supported = ", ".join(SUPPORTED_METHODS)
        raise ValueError(f"Unsupported method '{method}'. Expected one of: {supported}")
    if regularization < 0.0:
        raise ValueError("--regularization must be non-negative.")

    labels = labels.astype(str)
    classes = pd.Series(labels).drop_duplicates().to_numpy(dtype=str)
    if len(classes) < 1:
        raise ValueError("Training split must contain at least one class.")

    fit_features = _l2_normalize(features) if method == "nearest_centroid_cosine" else features
    centroids = []
    class_counts: dict[str, int] = {}
    residuals = np.zeros_like(features, dtype=np.float64)
    for label in classes:
        mask = labels == label
        class_features = fit_features[mask]
        if len(class_features) == 0:
            raise ValueError(f"No training rows for class: {label}")
        centroid = class_features.mean(axis=0)
        centroids.append(centroid)
        class_counts[str(label)] = int(mask.sum())
        if method == "mahalanobis":
            residuals[mask] = features[mask] - centroid

    centroid_matrix = np.vstack(centroids).astype(np.float64, copy=False)
    inverse_covariance = None
    if method == "nearest_centroid_cosine":
        centroid_matrix = _l2_normalize(centroid_matrix)
    elif method == "mahalanobis":
        inverse_covariance = _regularized_pinv_covariance(residuals, regularization)

    return FittedDistanceModel(
        method=method,
        classes=classes,
        centroids=centroid_matrix,
        inverse_covariance=inverse_covariance,
        feature_dim=int(features.shape[1]),
        class_counts=class_counts,
    )


def score_features(features: np.ndarray, model: FittedDistanceModel) -> tuple[np.ndarray, np.ndarray]:
    """Return OOD scores and nearest train class for feature rows."""

    if model.method == "nearest_centroid_euclidean":
        distances = _euclidean_distances(features.astype(np.float64, copy=False), model.centroids)
    elif model.method == "nearest_centroid_cosine":
        similarities = _l2_normalize(features.astype(np.float64, copy=False)) @ model.centroids.T
        distances = 1.0 - similarities
    elif model.method == "mahalanobis":
        if model.inverse_covariance is None:
            raise ValueError("Mahalanobis model is missing an inverse covariance matrix.")
        distances = _mahalanobis_distances(features.astype(np.float64, copy=False), model.centroids, model.inverse_covariance)
    else:
        raise ValueError(f"Unsupported fitted method: {model.method}")

    nearest_indices = distances.argmin(axis=1)
    scores = distances[np.arange(len(features)), nearest_indices]
    nearest_classes = model.classes[nearest_indices].astype(str)
    return scores.astype(float), nearest_classes


def _read_split(path: Path, name: str) -> SplitFrame:
    if not path.exists():
        raise FileNotFoundError(f"{name} split CSV not found: {path}")
    frame = _preserve_string_columns(pd.read_csv(path, dtype=str, keep_default_na=False))
    if frame.empty:
        raise ValueError(f"{name} split CSV is empty: {path}")
    return SplitFrame(name=name, frame=frame)


def _preserve_split_strings(split: SplitFrame, extra_columns: list[str] | None = None) -> SplitFrame:
    """Return a split frame with symbolic identifier columns stored as strings."""

    return SplitFrame(name=split.name, frame=_preserve_string_columns(split.frame, extra_columns))


def _preserve_string_columns(frame: pd.DataFrame, extra_columns: list[str] | None = None) -> pd.DataFrame:
    """Return a copy with symbolic identifier columns stored as strings."""

    preserved = frame.copy()
    for column in [*SYMBOLIC_STRING_COLUMNS, *(extra_columns or [])]:
        if column in preserved.columns:
            preserved[column] = preserved[column].fillna("").astype(str)
    return preserved


def _validate_manifest_columns(
    splits: list[SplitFrame],
    label_column: str,
    feature_index_column: str,
    feature_path_column: str,
    sample_id_column: str,
) -> None:
    required = [label_column, feature_index_column, feature_path_column, sample_id_column]
    for split in splits:
        missing = [column for column in required if column not in split.frame.columns]
        if missing:
            raise ValueError(f"{split.name} split is missing required columns: {missing}")
        missing_feature_paths = split.frame[feature_path_column].astype(str).eq("")
        if missing_feature_paths.any():
            raise ValueError(f"{split.name} split has {int(missing_feature_paths.sum())} empty feature paths.")


def _sample_train_rows(
    frame: pd.DataFrame,
    label_column: str,
    max_per_class: int | None,
    seed: int,
) -> pd.DataFrame:
    """Optionally cap train rows per class while preserving symbolic labels."""

    if max_per_class is None:
        return frame
    if max_per_class <= 0:
        raise ValueError("--max-train-samples-per-class must be positive when provided.")
    rng = np.random.default_rng(seed)
    selected_indices: list[int] = []
    for _, group in frame.groupby(label_column, sort=False):
        indices = group.index.to_numpy()
        if len(indices) > max_per_class:
            indices = rng.choice(indices, size=max_per_class, replace=False)
        selected_indices.extend(int(index) for index in indices)
    return frame.loc[sorted(selected_indices)].reset_index(drop=True)


def _max_feature_dim(splits: list[SplitFrame], feature_path_column: str) -> int:
    max_dim = 0
    for path_text in _unique_feature_paths(splits, feature_path_column):
        features = np.load(path_text, mmap_mode="r")
        feature_dim = int(np.prod(features.shape[1:])) if len(features.shape) > 1 else 1
        max_dim = max(max_dim, feature_dim)
    if max_dim <= 0:
        raise ValueError("Could not infer a positive feature dimension.")
    return max_dim


def _unique_feature_paths(splits: list[SplitFrame], feature_path_column: str) -> list[Path]:
    paths: list[Path] = []
    seen: set[str] = set()
    for split in splits:
        for value in split.frame[feature_path_column].astype(str):
            if value not in seen:
                path = Path(value)
                if not path.exists():
                    raise FileNotFoundError(f"Feature tensor not found: {path}")
                paths.append(path)
                seen.add(value)
    return paths


def _load_features(
    split: SplitFrame,
    target_dim: int,
    feature_path_column: str,
    feature_index_column: str,
) -> np.ndarray:
    matrix = np.zeros((len(split.frame), target_dim), dtype=np.float32)
    for feature_path_text, group in split.frame.groupby(feature_path_column, sort=False):
        feature_path = Path(str(feature_path_text))
        features = np.load(feature_path, mmap_mode="r")
        row_indices = group[feature_index_column].astype(int).to_numpy()
        if row_indices.min(initial=0) < 0 or row_indices.max(initial=0) >= features.shape[0]:
            raise IndexError(f"{split.name} split has feature indices outside {feature_path}")
        values = np.asarray(features[row_indices]).reshape(len(row_indices), -1).astype(np.float32, copy=False)
        if values.shape[1] > target_dim:
            raise ValueError(f"Feature dimension {values.shape[1]} exceeds target dimension {target_dim}.")
        matrix[group.index.to_numpy(), : values.shape[1]] = values
    return matrix


def _ood_labels(frame: pd.DataFrame) -> np.ndarray:
    if "ood_label" in frame.columns:
        return frame["ood_label"].astype(str).to_numpy()
    return np.asarray([""] * len(frame), dtype=str)


def _euclidean_distances(features: np.ndarray, centroids: np.ndarray) -> np.ndarray:
    feature_norms = np.sum(features * features, axis=1, keepdims=True)
    centroid_norms = np.sum(centroids * centroids, axis=1, keepdims=True).T
    squared = feature_norms + centroid_norms - 2.0 * features @ centroids.T
    return np.sqrt(np.maximum(squared, 0.0))


def _mahalanobis_distances(
    features: np.ndarray,
    centroids: np.ndarray,
    inverse_covariance: np.ndarray,
) -> np.ndarray:
    columns = []
    for centroid in centroids:
        diff = features - centroid
        squared = np.einsum("ij,jk,ik->i", diff, inverse_covariance, diff, optimize=True)
        columns.append(np.sqrt(np.maximum(squared, 0.0)))
    return np.vstack(columns).T


def _regularized_pinv_covariance(residuals: np.ndarray, regularization: float) -> np.ndarray:
    if len(residuals) <= 1:
        covariance = np.zeros((residuals.shape[1], residuals.shape[1]), dtype=np.float64)
    else:
        covariance = np.cov(residuals, rowvar=False, bias=False)
        covariance = np.atleast_2d(covariance).astype(np.float64, copy=False)
    covariance = covariance + regularization * np.eye(covariance.shape[0], dtype=np.float64)
    try:
        return np.linalg.pinv(covariance, hermitian=True)
    except TypeError:
        return np.linalg.pinv(covariance)


def _l2_normalize(values: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    norms = np.where(norms > 0.0, norms, 1.0)
    return values / norms


def _write_metadata(
    path: Path,
    model: FittedDistanceModel,
    n_train_samples: int,
    n_eval_samples: int,
    regularization: float,
    max_train_samples_per_class: int | None,
    seed: int,
) -> None:
    metadata = {
        "method": model.method,
        "n_train_samples": int(n_train_samples),
        "n_eval_samples": int(n_eval_samples),
        "feature_dim": int(model.feature_dim),
        "regularization": float(regularization),
        "max_train_samples_per_class": max_train_samples_per_class,
        "seed": int(seed),
        "classes": [str(label) for label in model.classes.tolist()],
        "class_counts": model.class_counts,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, sort_keys=True)
        handle.write("\n")


if __name__ == "__main__":
    main()
