"""Generic artifact dataset loaders."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset


class ArtifactDataset(Dataset):
    """Load OpenEW-SA conversion artifacts from one directory."""

    def __init__(self, artifact_dir: str | Path, label_column: str) -> None:
        self.artifact_dir = Path(artifact_dir).expanduser()
        self.metadata = pd.read_csv(self.artifact_dir / "metadata.csv", dtype={"occupancy_label": "string"})
        self.features = self._load_features()
        self.label_column = label_column
        self.label_to_index = self._build_label_index()
        with (self.artifact_dir / "labels.json").open("r", encoding="utf-8") as handle:
            self.labels_json: dict[str, Any] = json.load(handle)

    def __len__(self) -> int:
        return len(self.metadata)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        feature = torch.as_tensor(self.features[index], dtype=torch.float32)
        label_value = self.metadata.iloc[index][self.label_column]
        if pd.isna(label_value):
            label_value = "unknown"
        label = torch.tensor(self.label_to_index[str(label_value)], dtype=torch.long)
        return feature, label

    def _load_features(self) -> np.ndarray | torch.Tensor:
        npy_path = self.artifact_dir / "features.npy"
        pt_path = self.artifact_dir / "features.pt"
        if npy_path.exists():
            return np.load(npy_path, allow_pickle=False)
        if pt_path.exists():
            return torch.load(pt_path, map_location="cpu")
        raise FileNotFoundError(f"No features.npy or features.pt found in {self.artifact_dir}")

    def _build_label_index(self) -> dict[str, int]:
        if self.label_column not in self.metadata.columns:
            raise ValueError(f"Label column not found in metadata: {self.label_column}")
        values = sorted(str(value) for value in self.metadata[self.label_column].fillna("unknown").unique())
        return {value: index for index, value in enumerate(values)}
