"""Minimal supervised training entry point for baseline experiments."""

from __future__ import annotations

import argparse
import json
from typing import Any

import torch
from sklearn.metrics import accuracy_score, f1_score
from torch import nn
from torch.utils.data import DataLoader, random_split
from tqdm import tqdm

from openew.models.factory import build_model
from openew.training.dataset import ArtifactDataset
from openew.utils.config import ensure_dir, load_yaml


def train(config: dict[str, Any]) -> dict[str, float]:
    """Train a single-task classifier from converted artifacts."""

    device = torch.device(config.get("device", "cuda" if torch.cuda.is_available() else "cpu"))
    dataset = ArtifactDataset(config["artifact_dir"], config["label_column"])
    validation_fraction = float(config.get("validation_fraction", 0.2))
    val_size = max(1, int(len(dataset) * validation_fraction))
    train_size = len(dataset) - val_size
    train_ds, val_ds = random_split(dataset, [train_size, val_size])
    train_loader = DataLoader(train_ds, batch_size=config.get("batch_size", 64), shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=config.get("batch_size", 64))

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

    metrics = evaluate_loader(model, val_loader, device, config.get("task_head", "occupancy"))
    output_dir = ensure_dir(config.get("output_dir", "runs/default"))
    torch.save({"model_state_dict": model.state_dict(), "config": config, "metrics": metrics}, output_dir / "checkpoint.pt")
    with (output_dir / "metrics.json").open("w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2, sort_keys=True)
    return metrics


def evaluate_loader(model: nn.Module, loader: DataLoader, device: torch.device, task_head: str) -> dict[str, float]:
    """Evaluate a model on a dataloader."""

    model.eval()
    predictions: list[int] = []
    targets: list[int] = []
    with torch.no_grad():
        for features, labels in loader:
            features = features.to(device)
            logits = model(features)
            if isinstance(logits, dict):
                logits = logits[task_head]
            predictions.extend(logits.argmax(dim=1).cpu().tolist())
            targets.extend(labels.tolist())
    return {
        "accuracy": float(accuracy_score(targets, predictions)),
        "macro_f1": float(f1_score(targets, predictions, average="macro", zero_division=0)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train OpenEW-SA baseline models.")
    parser.add_argument("--config", required=True, help="YAML training config.")
    args = parser.parse_args()
    metrics = train(load_yaml(args.config))
    print(metrics)


if __name__ == "__main__":
    main()
