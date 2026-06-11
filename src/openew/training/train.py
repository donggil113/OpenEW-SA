"""Minimal supervised training entry point for baseline experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, Subset, random_split
from tqdm import tqdm

from openew.models.factory import build_model
from openew.training.dataset import ArtifactDataset
from openew.training.splits import build_holdout_split_indices
from openew.utils.config import ensure_dir, load_yaml


def train(config: dict[str, Any]) -> dict[str, Any]:
    """Train a single-task classifier from converted artifacts."""

    device = torch.device(config.get("device", "cuda" if torch.cuda.is_available() else "cpu"))
    dataset = ArtifactDataset(config["artifact_dir"], config["label_column"])
    split_indices = build_holdout_split_indices(dataset.metadata, config)
    if split_indices is None:
        validation_fraction = float(config.get("validation_fraction", 0.2))
        val_size = max(1, int(len(dataset) * validation_fraction))
        train_size = len(dataset) - val_size
        train_ds, val_ds = random_split(dataset, [train_size, val_size])
    else:
        train_indices, val_indices = split_indices
        train_ds, val_ds = Subset(dataset, train_indices), Subset(dataset, val_indices)
    train_loader = DataLoader(train_ds, batch_size=config.get("batch_size", 64), shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=config.get("batch_size", 64))
    output_dir = ensure_dir(config.get("output_dir", "runs/default"))
    preprocessing_state = apply_training_preprocessing(dataset, train_ds, config, output_dir)

    model = build_model(config["model"]).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(config.get("lr", 1e-3)))
    class_weights = build_class_weights(dataset, train_ds, config, output_dir)
    criterion = nn.CrossEntropyLoss(weight=class_weights.to(device) if class_weights is not None else None)

    for _epoch in tqdm(range(int(config.get("epochs", 10))), desc="epochs"):
        model.train()
        for features, labels in train_loader:
            features, labels = features.to(device), labels.to(device)
            logits = model(features)
            if isinstance(logits, dict):
                logits = logits[config.get("task_head", "occupancy")]
            loss = criterion(logits, labels)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    metrics = evaluate_loader(
        model,
        val_loader,
        device,
        config.get("task_head", "occupancy"),
        label_names=label_names_for_dataset(dataset),
        metadata=metadata_for_dataset(dataset, val_ds),
        predictions_path=output_dir / "predictions.csv",
    )
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "config": config,
            "metrics": metrics,
            "preprocessing": preprocessing_state,
        },
        output_dir / "checkpoint.pt",
    )
    with (output_dir / "metrics.json").open("w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2, sort_keys=True)
    return metrics


def apply_training_preprocessing(
    dataset: ArtifactDataset,
    train_ds: Any,
    config: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    """Fit configured preprocessing on train features only and apply it to all dataset features."""

    preprocessing = config.get("preprocessing", {})
    if not preprocessing.get("standardize", False):
        return {"standardize": False}

    train_indices = _dataset_indices(train_ds)
    features = _features_to_numpy(dataset.features)
    flat_features, sample_shape = _flatten_features(features)
    train_features = flat_features[train_indices]
    mean = train_features.mean(axis=0)
    var = train_features.var(axis=0)
    scale = np.sqrt(var)
    scale[scale == 0.0] = 1.0
    transformed = ((flat_features - mean) / scale).reshape(features.shape).astype(np.float32)
    dataset.features = transformed

    state = {
        "standardize": True,
        "mean": mean.astype(float).tolist(),
        "scale": scale.astype(float).tolist(),
        "var": var.astype(float).tolist(),
        "n_features_in": int(flat_features.shape[1]),
        "n_samples_seen": int(len(train_indices)),
        "sample_shape": list(sample_shape),
    }
    with (output_dir / "scaler.json").open("w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
    return state


def apply_saved_preprocessing(dataset: ArtifactDataset, preprocessing_state: dict[str, Any] | None) -> None:
    """Apply checkpoint preprocessing state to a dataset before evaluation."""

    if not preprocessing_state or not preprocessing_state.get("standardize", False):
        return
    features = _features_to_numpy(dataset.features)
    flat_features, sample_shape = _flatten_features(features)
    expected_shape = tuple(preprocessing_state.get("sample_shape", sample_shape))
    if sample_shape != expected_shape:
        raise ValueError(f"Feature sample shape {sample_shape} does not match scaler sample shape {expected_shape}")
    mean = np.asarray(preprocessing_state["mean"], dtype=np.float32)
    scale = np.asarray(preprocessing_state["scale"], dtype=np.float32)
    transformed = ((flat_features - mean) / scale).reshape(features.shape).astype(np.float32)
    dataset.features = transformed


def build_class_weights(
    dataset: ArtifactDataset,
    train_ds: Any,
    config: dict[str, Any],
    output_dir: Path,
) -> torch.Tensor | None:
    """Build class weights for cross entropy from training labels only."""

    loss_config = config.get("loss", {})
    if loss_config.get("class_weight") != "balanced":
        return None
    train_labels = labels_for_dataset(dataset, train_ds)
    num_classes = len(dataset.label_to_index)
    counts = np.bincount(train_labels, minlength=num_classes).astype(np.float32)
    weights = np.zeros(num_classes, dtype=np.float32)
    nonzero = counts > 0
    weights[nonzero] = len(train_labels) / (num_classes * counts[nonzero])
    state = {
        "class_weight": "balanced",
        "class_names": label_names_for_dataset(dataset),
        "counts": counts.astype(int).tolist(),
        "weights": weights.astype(float).tolist(),
    }
    with (output_dir / "class_weights.json").open("w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
    return torch.as_tensor(weights, dtype=torch.float32)


def evaluate_loader(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    task_head: str,
    label_names: list[str] | None = None,
    metadata: pd.DataFrame | None = None,
    predictions_path: str | Path | None = None,
) -> dict[str, Any]:
    """Evaluate a model on a dataloader."""

    model.eval()
    predictions: list[int] = []
    targets: list[int] = []
    probability_rows: list[list[float]] = []
    with torch.no_grad():
        for features, labels in loader:
            features = features.to(device)
            logits = model(features)
            if isinstance(logits, dict):
                logits = logits[task_head]
            predictions.extend(logits.argmax(dim=1).cpu().tolist())
            targets.extend(labels.tolist())
            probabilities = torch.softmax(logits, dim=1)
            if probabilities.shape[1] == 2:
                probability_rows.extend(probabilities.cpu().tolist())

    resolved_label_names = label_names or _labels_from_indices(targets, predictions)
    metrics = _classification_metrics(targets, predictions, resolved_label_names, probability_rows)
    if predictions_path is not None:
        _write_predictions(predictions_path, metadata, targets, predictions, resolved_label_names)
    return metrics


def _classification_metrics(
    targets: list[int],
    predictions: list[int],
    label_names: list[str],
    probability_rows: list[list[float]],
) -> dict[str, Any]:
    labels = list(range(len(label_names)))
    confusion = _confusion_matrix(targets, predictions, labels)
    precision, recall, f1, support = _precision_recall_f1_support(confusion)
    prediction_counts = [predictions.count(label) for label in labels]
    metrics: dict[str, Any] = {
        "accuracy": _accuracy(targets, predictions),
        "macro_f1": _macro_average(f1),
        "weighted_f1": _weighted_average(f1, support),
        "per_class_precision": _named_metric(precision, label_names),
        "per_class_recall": _named_metric(recall, label_names),
        "per_class_f1": _named_metric(f1, label_names),
        "confusion_matrix": confusion.astype(int).tolist(),
        "support_per_class": _named_count(support, label_names),
        "prediction_count_per_class": _named_count(prediction_counts, label_names),
    }
    if len(label_names) == 2 and len(probability_rows) == len(targets):
        positive_index = _binary_positive_index(label_names)
        probability_scores = [row[positive_index] for row in probability_rows]
        binary_targets = [1 if target == positive_index else 0 for target in targets]
        metrics["binary_positive_class"] = label_names[positive_index]
        metrics.update(_binary_probability_metrics(binary_targets, probability_scores))
    return metrics


def _binary_probability_metrics(targets: list[int], probability_scores: list[float]) -> dict[str, float | None]:
    return {
        "AUROC": _binary_auroc(targets, probability_scores),
        "AUPRC": _binary_auprc(targets, probability_scores),
    }


def _binary_positive_index(label_names: list[str]) -> int:
    for index, label_name in enumerate(label_names):
        text = label_name.lower()
        if any(token in text for token in ["abnormal", "interference", "jammer", "attack", "high"]):
            return index
    return 1


def _write_predictions(
    predictions_path: str | Path,
    metadata: pd.DataFrame | None,
    targets: list[int],
    predictions: list[int],
    label_names: list[str],
) -> None:
    if metadata is None:
        metadata = pd.DataFrame(index=range(len(targets)))
    if len(metadata) != len(targets):
        raise ValueError(f"Prediction metadata length {len(metadata)} does not match predictions length {len(targets)}")
    output = Path(predictions_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = pd.DataFrame(
        {
            "sample_id": metadata.get("sample_id", pd.Series([""] * len(targets))).fillna("").astype(str).tolist(),
            "domain_id": metadata.get("domain_id", pd.Series([""] * len(targets))).fillna("").astype(str).tolist(),
            "true_label": [_label_name(index, label_names) for index in targets],
            "predicted_label": [_label_name(index, label_names) for index in predictions],
            "true_label_index": targets,
            "predicted_label_index": predictions,
        }
    )
    rows.to_csv(output, index=False)


def metadata_for_dataset(base_dataset: ArtifactDataset, dataset: Any) -> pd.DataFrame:
    indices = _dataset_indices(dataset)
    return base_dataset.metadata.iloc[indices].reset_index(drop=True)


def labels_for_dataset(base_dataset: ArtifactDataset, dataset: Any) -> list[int]:
    indices = _dataset_indices(dataset)
    labels = []
    for index in indices:
        label_value = base_dataset.metadata.iloc[index][base_dataset.label_column]
        if pd.isna(label_value):
            label_value = "unknown"
        labels.append(base_dataset.label_to_index[str(label_value)])
    return labels


def _dataset_indices(dataset: Any) -> list[int]:
    if isinstance(dataset, Subset):
        parent_indices = _dataset_indices(dataset.dataset)
        return [parent_indices[index] for index in dataset.indices]
    return list(range(len(dataset)))


def label_names_for_dataset(dataset: ArtifactDataset) -> list[str]:
    return [label for label, _index in sorted(dataset.label_to_index.items(), key=lambda item: item[1])]


def _labels_from_indices(targets: list[int], predictions: list[int]) -> list[str]:
    max_index = max(targets + predictions, default=-1)
    return [str(index) for index in range(max_index + 1)]


def _label_name(index: int, label_names: list[str]) -> str:
    if 0 <= index < len(label_names):
        return label_names[index]
    return str(index)


def _named_metric(values: Any, label_names: list[str]) -> dict[str, float]:
    return {label: float(value) for label, value in zip(label_names, values)}


def _named_count(values: Any, label_names: list[str]) -> dict[str, int]:
    return {label: int(value) for label, value in zip(label_names, values)}


def _accuracy(targets: list[int], predictions: list[int]) -> float:
    if not targets:
        return 0.0
    return float(sum(target == prediction for target, prediction in zip(targets, predictions)) / len(targets))


def _confusion_matrix(targets: list[int], predictions: list[int], labels: list[int]) -> np.ndarray:
    label_to_position = {label: position for position, label in enumerate(labels)}
    matrix = np.zeros((len(labels), len(labels)), dtype=np.int64)
    for target, prediction in zip(targets, predictions):
        if target in label_to_position and prediction in label_to_position:
            matrix[label_to_position[target], label_to_position[prediction]] += 1
    return matrix


def _precision_recall_f1_support(confusion: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    true_positive = np.diag(confusion).astype(np.float64)
    predicted_positive = confusion.sum(axis=0).astype(np.float64)
    actual_positive = confusion.sum(axis=1).astype(np.float64)
    precision = np.divide(true_positive, predicted_positive, out=np.zeros_like(true_positive), where=predicted_positive != 0)
    recall = np.divide(true_positive, actual_positive, out=np.zeros_like(true_positive), where=actual_positive != 0)
    denominator = precision + recall
    f1 = np.divide(2 * precision * recall, denominator, out=np.zeros_like(denominator), where=denominator != 0)
    return precision, recall, f1, actual_positive


def _macro_average(values: np.ndarray) -> float:
    if values.size == 0:
        return 0.0
    return float(values.mean())


def _weighted_average(values: np.ndarray, support: np.ndarray) -> float:
    total = support.sum()
    if total == 0:
        return 0.0
    return float((values * support).sum() / total)


def _binary_auroc(targets: list[int], probability_scores: list[float]) -> float | None:
    positives = sum(targets)
    negatives = len(targets) - positives
    if positives == 0 or negatives == 0:
        return None
    ranks = _average_ranks(probability_scores)
    positive_rank_sum = sum(rank for rank, target in zip(ranks, targets) if target == 1)
    return float((positive_rank_sum - positives * (positives + 1) / 2) / (positives * negatives))


def _binary_auprc(targets: list[int], probability_scores: list[float]) -> float | None:
    positives = sum(targets)
    if positives == 0:
        return None
    ordered = sorted(zip(probability_scores, targets), key=lambda item: item[0], reverse=True)
    true_positives = 0
    precision_sum = 0.0
    for rank, (_score, target) in enumerate(ordered, start=1):
        if target == 1:
            true_positives += 1
            precision_sum += true_positives / rank
    return float(precision_sum / positives)


def _average_ranks(values: list[float]) -> list[float]:
    ordered = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    index = 0
    while index < len(ordered):
        end = index
        while end + 1 < len(ordered) and ordered[end + 1][1] == ordered[index][1]:
            end += 1
        average_rank = (index + 1 + end + 1) / 2
        for ordered_index in range(index, end + 1):
            original_index = ordered[ordered_index][0]
            ranks[original_index] = average_rank
        index = end + 1
    return ranks


def _features_to_numpy(features: Any) -> np.ndarray:
    if isinstance(features, torch.Tensor):
        return features.detach().cpu().numpy()
    return np.asarray(features)


def _flatten_features(features: np.ndarray) -> tuple[np.ndarray, tuple[int, ...]]:
    sample_shape = tuple(features.shape[1:])
    return features.reshape(features.shape[0], -1), sample_shape


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train OpenEW-SA baseline models.",
        epilog="Example: python scripts\\train_baseline.py --config configs\\train\\tiny_tabular_mlp.yaml",
    )
    parser.add_argument("--config", required=True, help="YAML training config.")
    args = parser.parse_args()
    metrics = train(load_yaml(args.config))
    print(metrics)


if __name__ == "__main__":
    main()
