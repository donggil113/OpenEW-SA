#!/usr/bin/env python
"""Train lightweight Paper 2 ID classifiers and write prediction CSVs."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np
import pandas as pd

SUPPORTED_MODELS = ("logistic_regression", "mlp", "nearest_centroid")
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
    "predicted_label",
    "feature_path",
    "modulation_label",
    "occupancy_label",
    "abnormal_event_label",
    "situation_label",
    "threat_level",
]


class ProbabilityClassifier(Protocol):
    """Minimal classifier interface used by this script."""

    classes_: np.ndarray

    def predict_proba(self, features: np.ndarray) -> np.ndarray:
        """Return class probabilities for feature rows."""


@dataclass(frozen=True)
class SplitFrame:
    """Loaded split manifest with its name."""

    name: str
    frame: pd.DataFrame


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Train Paper 2 baseline classifiers from split manifests and features.npy files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--train-csv", required=True, type=Path, help="Training split manifest CSV.")
    parser.add_argument("--val-csv", type=Path, help="Optional validation split manifest CSV.")
    parser.add_argument("--test-id-csv", required=True, type=Path, help="ID test split manifest CSV.")
    parser.add_argument("--test-ood-csv", required=True, type=Path, help="OOD test split manifest CSV.")
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory for prediction CSVs.")
    parser.add_argument("--model", required=True, choices=SUPPORTED_MODELS, help="Baseline classifier.")
    parser.add_argument(
        "--feature-cache",
        type=Path,
        help="Optional directory for cached flattened split feature matrices.",
    )
    parser.add_argument("--label-column", default="label", help="Ground-truth label column.")
    parser.add_argument("--feature-index-column", default="feature_index", help="Feature row index column.")
    parser.add_argument("--feature-path-column", default="feature_path", help="Feature tensor path column.")
    parser.add_argument("--sample-id-column", default="sample_id", help="Sample identifier column.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for stochastic models.")
    return parser.parse_args()


def main() -> None:
    """Train a baseline classifier and write predictions for ID and OOD test splits."""

    args = parse_args()
    train = _read_split(args.train_csv, "train")
    val = _read_split(args.val_csv, "val") if args.val_csv else None
    test_id = _read_split(args.test_id_csv, "test_id")
    test_ood = _read_split(args.test_ood_csv, "test_ood")
    split_frames = [
        _preserve_split_strings(split, [args.sample_id_column, args.label_column])
        for split in [train, val, test_id, test_ood]
        if split is not None
    ]
    train = split_frames[0]
    val = split_frames[1] if args.val_csv else None
    test_id = split_frames[2 if args.val_csv else 1]
    test_ood = split_frames[3 if args.val_csv else 2]
    _validate_manifest_columns(
        split_frames,
        label_column=args.label_column,
        feature_index_column=args.feature_index_column,
        feature_path_column=args.feature_path_column,
        sample_id_column=args.sample_id_column,
    )

    target_dim = _max_feature_dim(
        split_frames,
        feature_path_column=args.feature_path_column,
    )
    train_features = _load_features(
        train,
        target_dim=target_dim,
        feature_path_column=args.feature_path_column,
        feature_index_column=args.feature_index_column,
        feature_cache=args.feature_cache,
    )
    y_train = train.frame[args.label_column].astype(str).to_numpy()
    classifier = _fit_classifier(args.model, train_features, y_train, args.seed)

    predictions_val = None
    if val is not None:
        val_features = _load_features(
            val,
            target_dim=target_dim,
            feature_path_column=args.feature_path_column,
            feature_index_column=args.feature_index_column,
            feature_cache=args.feature_cache,
        )
        predictions_val = _predict_split(
            val,
            classifier,
            val_features,
            label_column=args.label_column,
            sample_id_column=args.sample_id_column,
        )

    test_id_features = _load_features(
        test_id,
        target_dim=target_dim,
        feature_path_column=args.feature_path_column,
        feature_index_column=args.feature_index_column,
        feature_cache=args.feature_cache,
    )
    test_ood_features = _load_features(
        test_ood,
        target_dim=target_dim,
        feature_path_column=args.feature_path_column,
        feature_index_column=args.feature_index_column,
        feature_cache=args.feature_cache,
    )
    predictions_id = _predict_split(
        test_id,
        classifier,
        test_id_features,
        label_column=args.label_column,
        sample_id_column=args.sample_id_column,
    )
    predictions_ood = _predict_split(
        test_ood,
        classifier,
        test_ood_features,
        label_column=args.label_column,
        sample_id_column=args.sample_id_column,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    if predictions_val is not None:
        predictions_val.to_csv(args.output_dir / "predictions_val.csv", index=False)
    predictions_id.to_csv(args.output_dir / "predictions_test_id.csv", index=False)
    predictions_ood.to_csv(args.output_dir / "predictions_test_ood.csv", index=False)
    predictions_all = pd.concat([predictions_id, predictions_ood], ignore_index=True)
    predictions_all.to_csv(args.output_dir / "predictions_all.csv", index=False)
    _write_summary(args.output_dir, args.model, classifier, target_dim, split_frames, predictions_all)
    print(f"Wrote predictions to {args.output_dir}")


class NearestCentroidClassifier:
    """Nearest-centroid classifier with softmax over negative squared distances."""

    def __init__(self) -> None:
        self.classes_: np.ndarray = np.asarray([], dtype=str)
        self.centroids_: np.ndarray = np.empty((0, 0), dtype=np.float32)
        self.temperature_: float = 1.0

    def fit(self, features: np.ndarray, labels: np.ndarray) -> "NearestCentroidClassifier":
        """Fit one centroid per class."""

        classes = pd.Series(labels.astype(str)).drop_duplicates().to_numpy(dtype=str)
        if len(classes) < 2:
            raise ValueError("Training labels must contain at least two classes.")
        centroids = []
        for label in classes:
            class_features = features[labels.astype(str) == label]
            if len(class_features) == 0:
                raise ValueError(f"No training rows for class: {label}")
            centroids.append(class_features.mean(axis=0))
        self.classes_ = classes
        self.centroids_ = np.vstack(centroids).astype(np.float32)
        train_distances = _squared_distances(features, self.centroids_)
        self.temperature_ = float(np.median(train_distances))
        if not np.isfinite(self.temperature_) or self.temperature_ <= 0.0:
            self.temperature_ = 1.0
        return self

    def predict_proba(self, features: np.ndarray) -> np.ndarray:
        """Return softmax probabilities over centroid similarities."""

        distances = _squared_distances(features, self.centroids_)
        return _softmax(-distances / self.temperature_)


def _fit_classifier(model_name: str, features: np.ndarray, labels: np.ndarray, seed: int) -> ProbabilityClassifier:
    if model_name == "nearest_centroid":
        return NearestCentroidClassifier().fit(features, labels)
    if model_name == "logistic_regression":
        try:
            from sklearn.linear_model import LogisticRegression
            from sklearn.pipeline import make_pipeline
            from sklearn.preprocessing import StandardScaler
        except ImportError as exc:
            raise RuntimeError("scikit-learn is required for logistic_regression; use nearest_centroid instead.") from exc
        classifier = make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=1000, random_state=seed),
        )
        classifier.fit(features, labels)
        return _SklearnPipelineWrapper(classifier)
    if model_name == "mlp":
        try:
            from sklearn.neural_network import MLPClassifier
            from sklearn.pipeline import make_pipeline
            from sklearn.preprocessing import StandardScaler
        except ImportError as exc:
            raise RuntimeError("scikit-learn is required for mlp; use nearest_centroid instead.") from exc
        classifier = make_pipeline(
            StandardScaler(),
            MLPClassifier(hidden_layer_sizes=(64,), max_iter=200, random_state=seed),
        )
        classifier.fit(features, labels)
        return _SklearnPipelineWrapper(classifier)
    supported = ", ".join(SUPPORTED_MODELS)
    raise ValueError(f"Unsupported model '{model_name}'. Expected one of: {supported}")


class _SklearnPipelineWrapper:
    """Adapter exposing pipeline classes and probabilities."""

    def __init__(self, pipeline: object) -> None:
        self.pipeline = pipeline
        classes = getattr(pipeline, "classes_", None)
        if classes is None:
            classes = pipeline[-1].classes_
        self.classes_ = np.asarray(classes, dtype=str)

    def predict_proba(self, features: np.ndarray) -> np.ndarray:
        """Return class probabilities from a scikit-learn pipeline."""

        return np.asarray(self.pipeline.predict_proba(features), dtype=float)


def _read_split(path: Path | None, name: str) -> SplitFrame:
    if path is None:
        raise ValueError(f"{name} split path is required.")
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
    feature_cache: Path | None,
) -> np.ndarray:
    cache_path = _cache_path(feature_cache, split.name, len(split.frame), target_dim)
    if cache_path is not None and cache_path.exists():
        cached = np.load(cache_path)
        if cached.shape == (len(split.frame), target_dim):
            return cached.astype(np.float32, copy=False)

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

    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(cache_path, matrix)
    return matrix


def _cache_path(feature_cache: Path | None, split_name: str, n_rows: int, target_dim: int) -> Path | None:
    if feature_cache is None:
        return None
    return feature_cache / f"{split_name}_{n_rows}_x_{target_dim}.npy"


def _predict_split(
    split: SplitFrame,
    classifier: ProbabilityClassifier,
    features: np.ndarray,
    label_column: str,
    sample_id_column: str,
) -> pd.DataFrame:
    probabilities = classifier.predict_proba(features)
    if probabilities.shape[1] != len(classifier.classes_):
        raise ValueError("Classifier probability columns do not match classifier classes.")
    predicted_indices = probabilities.argmax(axis=1)
    predicted_labels = classifier.classes_[predicted_indices]
    confidence = probabilities[np.arange(len(predicted_indices)), predicted_indices]
    output = pd.DataFrame(
        {
            "sample_id": split.frame[sample_id_column].astype(str).to_numpy(),
            "true_label": split.frame[label_column].astype(str).to_numpy(),
            "predicted_label": predicted_labels,
            "confidence": confidence,
            "ood_label": _ood_labels(split.frame),
        }
    )
    for class_index, class_name in enumerate(classifier.classes_):
        output[f"prob_{class_name}"] = probabilities[:, class_index]
    return _preserve_string_columns(output)


def _ood_labels(frame: pd.DataFrame) -> np.ndarray:
    if "ood_label" in frame.columns:
        return frame["ood_label"].astype(str).to_numpy()
    return np.asarray([""] * len(frame), dtype=str)


def _write_summary(
    output_dir: Path,
    model_name: str,
    classifier: ProbabilityClassifier,
    target_dim: int,
    splits: list[SplitFrame],
    predictions: pd.DataFrame,
) -> None:
    summary = {
        "model": model_name,
        "classes": [str(label) for label in classifier.classes_.tolist()],
        "feature_dim": int(target_dim),
        "split_rows": {split.name: int(len(split.frame)) for split in splits},
        "prediction_rows": int(len(predictions)),
    }
    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _squared_distances(features: np.ndarray, centroids: np.ndarray) -> np.ndarray:
    feature_norms = np.sum(features * features, axis=1, keepdims=True)
    centroid_norms = np.sum(centroids * centroids, axis=1, keepdims=True).T
    distances = feature_norms + centroid_norms - 2.0 * features @ centroids.T
    return np.maximum(distances, 0.0)


def _softmax(scores: np.ndarray) -> np.ndarray:
    shifted = scores - scores.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / exp.sum(axis=1, keepdims=True)


if __name__ == "__main__":
    main()
