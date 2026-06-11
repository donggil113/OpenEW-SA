"""Minimal supervised training entry point for baseline experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
import torch
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    roc_auc_score,
)
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

    model = build_model(config["model"]).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(config.get("lr", 1e-3)))
    criterion = nn.CrossEntropyLoss()

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
    torch.save({"model_state_dict": model.state_dict(), "config": config, "metrics": metrics}, output_dir / "checkpoint.pt")
    with (output_dir / "metrics.json").open("w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2, sort_keys=True)
    return metrics


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
    probability_scores: list[float] = []
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
                probability_scores.extend(probabilities[:, 1].cpu().tolist())

    resolved_label_names = label_names or _labels_from_indices(targets, predictions)
    metrics = _classification_metrics(targets, predictions, resolved_label_names, probability_scores)
    if predictions_path is not None:
        _write_predictions(predictions_path, metadata, targets, predictions, resolved_label_names)
    return metrics


def _classification_metrics(
    targets: list[int],
    predictions: list[int],
    label_names: list[str],
    probability_scores: list[float],
) -> dict[str, Any]:
    labels = list(range(len(label_names)))
    precision, recall, f1, support = precision_recall_fscore_support(
        targets,
        predictions,
        labels=labels,
        zero_division=0,
    )
    prediction_counts = [predictions.count(label) for label in labels]
    metrics: dict[str, Any] = {
        "accuracy": float(accuracy_score(targets, predictions)),
        "macro_f1": float(f1_score(targets, predictions, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(targets, predictions, average="weighted", zero_division=0)),
        "per_class_precision": _named_metric(precision, label_names),
        "per_class_recall": _named_metric(recall, label_names),
        "per_class_f1": _named_metric(f1, label_names),
        "confusion_matrix": confusion_matrix(targets, predictions, labels=labels).astype(int).tolist(),
        "support_per_class": _named_count(support, label_names),
        "prediction_count_per_class": _named_count(prediction_counts, label_names),
    }
    if len(label_names) == 2 and len(probability_scores) == len(targets):
        metrics.update(_binary_probability_metrics(targets, probability_scores))
    return metrics


def _binary_probability_metrics(targets: list[int], probability_scores: list[float]) -> dict[str, float | None]:
    metrics: dict[str, float | None] = {}
    try:
        metrics["AUROC"] = float(roc_auc_score(targets, probability_scores))
    except ValueError:
        metrics["AUROC"] = None
    try:
        metrics["AUPRC"] = float(average_precision_score(targets, probability_scores))
    except ValueError:
        metrics["AUPRC"] = None
    return metrics


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
