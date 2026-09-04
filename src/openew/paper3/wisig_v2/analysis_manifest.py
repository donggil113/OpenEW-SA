"""Deterministic hashes for external V2 analysis deliverables."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .hashing import canonical_json_bytes, sha256_file


def write_analysis_manifest(root: str | Path, destination: str | Path) -> dict[str, Any]:
    root, destination = Path(root).resolve(), Path(destination).resolve()
    if not root.is_dir():
        raise FileNotFoundError(root)
    rows = []
    for path in sorted(value for value in root.rglob("*") if value.is_file()):
        if path.resolve() == destination:
            continue
        rows.append({"relative_path": path.relative_to(root).as_posix(), "size_bytes": path.stat().st_size, "sha256": sha256_file(path)})
    if not rows:
        raise ValueError("analysis root contains no files")
    payload = {
        "schema_version": 1,
        "file_count": len(rows),
        "total_bytes": sum(row["size_bytes"] for row in rows),
        "files": rows,
    }
    destination.parent.mkdir(parents=True, exist_ok=True); destination.write_bytes(canonical_json_bytes(payload))
    return payload
