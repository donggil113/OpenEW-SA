"""Shared conversion utilities for RF datasets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from openew.data.schema import METADATA_COLUMNS, validate_metadata_frame
from openew.utils.config import ensure_dir


def discover_files(root: str | Path, patterns: list[str]) -> list[Path]:
    """Discover files under a dataset root using glob patterns."""

    root_path = Path(root).expanduser()
    files: list[Path] = []
    for pattern in patterns:
        files.extend(root_path.glob(pattern))
    return sorted(path for path in files if path.is_file())


def save_conversion(
    output_dir: str | Path,
    metadata: pd.DataFrame,
    features: np.ndarray | torch.Tensor,
    labels: dict[str, Any],
    feature_format: str = "npy",
) -> None:
    """Save metadata.csv, features.npy/features.pt, and labels.json."""

    out = ensure_dir(output_dir)
    validate_metadata_frame(metadata).to_csv(out / "metadata.csv", index=False)
    if feature_format == "pt":
        torch.save(torch.as_tensor(features), out / "features.pt")
    elif feature_format == "npy":
        np.save(out / "features.npy", np.asarray(features))
    else:
        raise ValueError("feature_format must be 'npy' or 'pt'")
    with (out / "labels.json").open("w", encoding="utf-8") as handle:
        json.dump(labels, handle, indent=2, sort_keys=True)


def load_sidecar_metadata(path: str | Path | None) -> pd.DataFrame | None:
    """Load optional CSV sidecar metadata."""

    if path is None:
        return None
    sidecar = Path(path).expanduser()
    if not sidecar.exists():
        return None
    return pd.read_csv(sidecar)


def empty_metadata_template() -> pd.DataFrame:
    """Return an empty schema-compatible metadata table."""

    return pd.DataFrame(columns=METADATA_COLUMNS)
