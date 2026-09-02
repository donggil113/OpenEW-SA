"""Atomic checkpoint and compatible-run resume helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import torch


def atomic_torch_save(value: object, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    torch.save(value, temporary)
    os.replace(temporary, path)


def atomic_json(value: dict[str, Any], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def compatible_completion(path: str | Path, expected: dict[str, str]) -> dict[str, Any] | None:
    path = Path(path)
    if not path.exists():
        return None
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("status") != "COMPLETE":
        return None
    for field, value in expected.items():
        if record.get(field) != value:
            raise RuntimeError(f"completed run incompatibility for {field}: {record.get(field)!r} != {value!r}")
    return record
