"""Configuration loading helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML configuration file."""

    with Path(path).expanduser().open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping at top level of YAML config: {path}")
    return data


def ensure_dir(path: str | Path) -> Path:
    """Create and return a directory path."""

    directory = Path(path).expanduser()
    directory.mkdir(parents=True, exist_ok=True)
    return directory
