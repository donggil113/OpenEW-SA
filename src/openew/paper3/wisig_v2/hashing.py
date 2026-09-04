"""Canonical hashes used for deterministic V2 assignment and audit trails."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def stable_digest(*parts: object, namespace: str) -> str:
    payload = "\x1f".join([namespace, *(str(part) for part in parts)])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def sha256_file(path: str | Path, block_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while block := stream.read(block_size):
            digest.update(block)
    return digest.hexdigest()
