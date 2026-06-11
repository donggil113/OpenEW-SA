"""Evaluation helpers for saved baseline checkpoints."""

from __future__ import annotations

import argparse

import torch
from torch.utils.data import DataLoader

from openew.models.factory import build_model
from openew.training.dataset import ArtifactDataset
from openew.training.train import evaluate_loader
from openew.utils.config import load_yaml


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate an OpenEW-SA checkpoint.")
    parser.add_argument("--config", required=True, help="YAML evaluation config.")
    args = parser.parse_args()
    config = load_yaml(args.config)
    checkpoint_path = config.get("checkpoint_path") or f"{config.get('output_dir', 'runs/default')}/checkpoint.pt"
    checkpoint = torch.load(checkpoint_path, map_location=config.get("device", "cpu"))
    model = build_model(config["model"])
    model.load_state_dict(checkpoint["model_state_dict"])
    device = torch.device(config.get("device", "cpu"))
    model.to(device)
    dataset = ArtifactDataset(config["artifact_dir"], config["label_column"])
    metrics = evaluate_loader(model, DataLoader(dataset, batch_size=config.get("batch_size", 64)), device, config.get("task_head", "occupancy"))
    print(metrics)


if __name__ == "__main__":
    main()
