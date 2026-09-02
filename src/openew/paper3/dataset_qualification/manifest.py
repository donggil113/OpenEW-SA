"""Checksum manifest for bounded official metadata acquisitions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path


@dataclass(frozen=True)
class ManifestFile:
    relative_path: str
    size_bytes: int
    sha256: str


def sha256_file(path: Path, block_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(block_size), b""):
            digest.update(block)
    return digest.hexdigest()


def build_metadata_manifest(
    root: str | Path,
    *,
    source_urls: tuple[str, ...],
    license_evidence: str,
    source_versions: dict[str, str],
) -> dict[str, object]:
    base = Path(root).resolve()
    files = [
        ManifestFile(path.relative_to(base).as_posix(), path.stat().st_size, sha256_file(path))
        for path in sorted(base.rglob("*"))
        if path.is_file() and path.name != "metadata_manifest.json"
    ]
    return {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(base),
        "source_urls": list(source_urls),
        "license_evidence": license_evidence,
        "source_versions": source_versions,
        "file_count": len(files),
        "total_size_bytes": sum(item.size_bytes for item in files),
        "files": [asdict(item) for item in files],
    }


def write_manifest_atomic(path: str | Path, manifest: dict[str, object]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, destination)
