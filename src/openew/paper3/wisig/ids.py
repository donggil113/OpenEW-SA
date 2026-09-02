"""Opaque, target-neutral public identifiers for converted WiSig samples."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping

ID_NAMESPACE = "openew-sa:paper3:wisig-manyrx:v1"


def opaque_sample_id(source_identity: Mapping[str, str | int], *, namespace: str = ID_NAMESPACE) -> str:
    """Hash a canonical internal identity without exposing target-bearing tokens."""

    canonical = json.dumps(
        {"namespace": namespace, "source_identity": dict(source_identity)},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()[:32]
