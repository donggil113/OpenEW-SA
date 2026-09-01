"""Atomic checkpoint/metadata helpers and compatibility checks."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import torch


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def atomic_write_json(path: str | Path, payload: dict[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, destination)


def atomic_torch_save(path: str | Path, payload: dict[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    torch.save(payload, temporary)
    os.replace(temporary, destination)


def compatible_completed_run(metadata_path: str | Path, signature: dict[str, Any]) -> dict[str, Any] | None:
    path = Path(metadata_path)
    if not path.exists():
        return None
    metadata = json.loads(path.read_text(encoding="utf-8"))
    if metadata.get("status") != "COMPLETED":
        return None
    required = ("config_hash", "source_hash", "artifact_hashes", "split_hashes")
    if all(metadata.get(key) == signature.get(key) for key in required):
        return metadata
    return None
