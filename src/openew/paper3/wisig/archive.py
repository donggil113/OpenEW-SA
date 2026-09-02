"""Safe inspection, extraction, and immutable-manifest utilities for ManyRx."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import stat
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


class ArchiveSafetyError(RuntimeError):
    """Raised when an archive violates the extraction contract."""


def sha256_file(path: str | Path, chunk_bytes: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while block := stream.read(chunk_bytes):
            digest.update(block)
    return digest.hexdigest()


def inspect_zip(path: str | Path) -> dict[str, Any]:
    archive = Path(path)
    records: list[dict[str, Any]] = []
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            member = PurePosixPath(info.filename)
            mode = info.external_attr >> 16
            reasons: list[str] = []
            if member.is_absolute() or info.filename.startswith(("/", "\\")):
                reasons.append("absolute_path")
            if ".." in member.parts:
                reasons.append("parent_traversal")
            if stat.S_ISLNK(mode):
                reasons.append("symlink")
            if mode and (mode & 0o111):
                reasons.append("executable")
            if reasons:
                raise ArchiveSafetyError(f"unsafe archive member {info.filename!r}: {reasons}")
            records.append(
                {
                    "relative_path": info.filename,
                    "compressed_bytes": info.compress_size,
                    "uncompressed_bytes": info.file_size,
                    "crc32": f"{info.CRC:08x}",
                    "unix_mode": f"{mode:o}" if mode else "",
                    "is_directory": info.is_dir(),
                }
            )
    return {
        "archive": archive.name,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": sha256_file(archive),
        "member_count": len(records),
        "compressed_member_bytes": sum(r["compressed_bytes"] for r in records),
        "uncompressed_bytes": sum(r["uncompressed_bytes"] for r in records),
        "largest_member_bytes": max((r["uncompressed_bytes"] for r in records), default=0),
        "suffix_counts": dict(sorted(Counter(Path(r["relative_path"]).suffix.lower() or "[none]" for r in records).items())),
        "members": records,
        "safety_status": "PASS",
    }


def extract_zip_once(path: str | Path, destination: str | Path) -> list[Path]:
    """Extract after validation; refuse an existing destination."""

    report = inspect_zip(path)
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(f"immutable extraction destination already exists: {destination}")
    destination.mkdir(parents=True)
    try:
        with zipfile.ZipFile(path) as zf:
            for record in report["members"]:
                if record["is_directory"]:
                    continue
                target = destination / record["relative_path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(record["relative_path"], "r") as source, target.open("xb") as sink:
                    shutil.copyfileobj(source, sink, length=8 * 1024 * 1024)
        return sorted(p for p in destination.rglob("*") if p.is_file())
    except Exception:
        # The destination is new and owned by this operation; leave it in place
        # for forensic diagnosis instead of hiding a partial extraction.
        raise


def write_raw_manifest(root: str | Path, output_csv: str | Path, sums_path: str | Path) -> dict[str, Any]:
    root = Path(root).resolve()
    files = sorted(p for p in root.rglob("*") if p.is_file())
    rows: list[dict[str, Any]] = []
    for path in files:
        rows.append(
            {
                "relative_path": path.relative_to(root).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    output_csv = Path(output_csv)
    sums_path = Path(sums_path)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["relative_path", "size_bytes", "sha256"])
        writer.writeheader()
        writer.writerows(rows)
    with sums_path.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(f"{row['sha256']}  {row['relative_path']}\n")
    return {
        "root": str(root),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "file_count": len(rows),
        "total_bytes": sum(r["size_bytes"] for r in rows),
        "files": rows,
    }


def mark_tree_read_only(root: str | Path) -> None:
    root = Path(root)
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_file():
            path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        elif path.is_dir():
            path.chmod(stat.S_IRUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
    root.chmod(stat.S_IRUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)


def write_json_atomic(path: str | Path, value: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)
