"""Evaluation helpers for saved baseline checkpoints."""

from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path
from typing import Any

import torch
from torch.utils.data import DataLoader, Subset

from openew.models.factory import build_model
from openew.training.dataset import ArtifactDataset
from openew.training.splits import build_holdout_split_indices
from openew.training.train import apply_saved_preprocessing, evaluate_loader, label_names_for_dataset, metadata_for_dataset
from openew.utils.config import ensure_dir, load_yaml


def load_checkpoint_safely(checkpoint_path: str | Path, map_location: str | torch.device) -> dict[str, Any]:
    """Load a checkpoint with safe tensor-only loading when supported."""

    if _torch_load_supports_weights_only():
        checkpoint = torch.load(checkpoint_path, map_location=map_location, weights_only=True)
    else:
        checkpoint = _load_checkpoint_without_weights_only_support(checkpoint_path, map_location)
    if not isinstance(checkpoint, dict) or "model_state_dict" not in checkpoint:
        raise ValueError(f"Expected checkpoint dict with model_state_dict: {checkpoint_path}")
    return checkpoint


def _torch_load_supports_weights_only() -> bool:
    try:
        return "weights_only" in inspect.signature(torch.load).parameters
    except (TypeError, ValueError):
        return False


def _load_checkpoint_without_weights_only_support(
    checkpoint_path: str | Path,
    map_location: str | torch.device,
) -> dict[str, Any]:
    try:
        return torch.load(checkpoint_path, map_location=map_location, weights_only=False)
    except TypeError as error:
        if "weights_only" not in str(error):
            raise
        return torch.load(checkpoint_path, map_location=map_location)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate an OpenEW-SA checkpoint.",
        epilog="Example: python scripts\\evaluate_baseline.py --config configs\\train\\tiny_tabular_mlp.yaml",
    )
    parser.add_argument("--config", required=True, help="YAML evaluation config.")
    args = parser.parse_args()
    config = load_yaml(args.config)
    checkpoint_path = config.get("checkpoint_path") or f"{config.get('output_dir', 'runs/default')}/checkpoint.pt"
    checkpoint = load_checkpoint_safely(checkpoint_path, map_location=config.get("device", "cpu"))
    model = build_model(config["model"])
    model.load_state_dict(checkpoint["model_state_dict"])
    device = torch.device(config.get("device", "cpu"))
    model.to(device)
    dataset = ArtifactDataset(config["artifact_dir"], config["label_column"])
    apply_saved_preprocessing(dataset, checkpoint.get("preprocessing"))
    split_indices = build_holdout_split_indices(dataset.metadata, config)
    eval_dataset = dataset if split_indices is None else Subset(dataset, split_indices[1])
    output_dir = ensure_dir(config.get("output_dir", "runs/default"))
    metrics = evaluate_loader(
        model,
        DataLoader(eval_dataset, batch_size=config.get("batch_size", 64)),
        device,
        config.get("task_head", "occupancy"),
        label_names=label_names_for_dataset(dataset),
        metadata=metadata_for_dataset(dataset, eval_dataset),
        predictions_path=output_dir / "predictions.csv",
    )
    with (output_dir / "metrics.json").open("w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2, sort_keys=True)
    print(metrics)


if __name__ == "__main__":
    main()
