"""Content-tree integrity checks for frozen artifacts and pilot source."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable


class IntegrityViolation(RuntimeError):
    """Suite-stopping source or frozen-artifact mismatch."""


def tree_digest(root: str | Path) -> dict[str, object]:
    path_root = Path(root)
    if not path_root.is_dir():
        raise FileNotFoundError(path_root)
    digest = hashlib.sha256()
    file_count = 0
    total_bytes = 0
    for path in sorted(item for item in path_root.rglob("*") if item.is_file()):
        relative = path.relative_to(path_root).as_posix().encode("utf-8")
        size = path.stat().st_size
        digest.update(relative)
        digest.update(b"\0")
        digest.update(str(size).encode("ascii"))
        digest.update(b"\0")
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
                digest.update(chunk)
        file_count += 1
        total_bytes += size
    return {
        "path": str(path_root),
        "sha256": digest.hexdigest(),
        "file_count": file_count,
        "total_bytes": total_bytes,
    }


def verify_pre_run_snapshot(path: str | Path) -> dict[str, object]:
    snapshot = json.loads(Path(path).read_text(encoding="utf-8"))
    for name, expected in snapshot["roots"].items():
        actual = tree_digest(expected["path"])
        if actual != expected:
            raise IntegrityViolation(
                f"Frozen tree mismatch for {name}: expected {expected}, observed {actual}"
            )
    return snapshot


def source_tree_hash(paths: Iterable[str | Path], root: str | Path) -> str:
    root_path = Path(root)
    digest = hashlib.sha256()
    files: list[Path] = []
    for item in paths:
        path = Path(item)
        if path.is_dir():
            files.extend(child for child in path.rglob("*") if child.is_file())
        elif path.is_file():
            files.append(path)
    for path in sorted(set(files)):
        try:
            relative = path.relative_to(root_path).as_posix()
        except ValueError:
            relative = str(path)
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()
