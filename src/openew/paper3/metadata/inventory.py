"""Deterministic read-only source inventory without payload hashing."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence
import csv
import json
import os


INVENTORY_COLUMNS = (
    "dataset",
    "path",
    "relative_path",
    "file_type",
    "size_bytes",
    "mtime",
    "scientifically_trustworthy_mtime",
    "candidate_metadata_container",
    "parser_available",
    "source_stage",
    "read_only",
    "notes",
)


def build_source_inventory(
    data_root: str | Path, *, excluded_roots: Sequence[str | Path] = ()
) -> list[dict[str, object]]:
    root = Path(data_root)
    if not root.is_dir():
        raise FileNotFoundError(root)
    excluded = tuple(Path(item).resolve() for item in excluded_roots)
    rows: list[dict[str, object]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        resolved = path.resolve()
        if any(resolved == item or item in resolved.parents for item in excluded):
            continue
        stat = path.stat()
        relative = path.relative_to(root).as_posix()
        suffix = _file_type(path)
        rows.append(
            {
                "dataset": _dataset(relative),
                "path": str(path),
                "relative_path": relative,
                "file_type": suffix,
                "size_bytes": stat.st_size,
                "mtime": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                "scientifically_trustworthy_mtime": "SYSTEM_METADATA_ONLY",
                "candidate_metadata_container": _candidate_container(suffix),
                "parser_available": _parser_available(suffix),
                "source_stage": _source_stage(relative),
                "read_only": True,
                "notes": "mtime is filesystem metadata and is not acquisition time",
            }
        )
    return rows


def summarize_inventory(rows: Iterable[dict[str, object]]) -> dict[str, object]:
    items = list(rows)
    by_dataset: dict[str, dict[str, int]] = defaultdict(lambda: {"file_count": 0, "bytes": 0})
    by_stage = Counter()
    by_type = Counter()
    for row in items:
        dataset = str(row["dataset"])
        by_dataset[dataset]["file_count"] += 1
        by_dataset[dataset]["bytes"] += int(row["size_bytes"])
        by_stage[str(row["source_stage"])] += 1
        by_type[str(row["file_type"])] += 1
    return {
        "schema_version": 1,
        "total_files": len(items),
        "total_bytes": sum(int(row["size_bytes"]) for row in items),
        "by_dataset": dict(sorted(by_dataset.items())),
        "file_count_by_source_stage": dict(sorted(by_stage.items())),
        "file_count_by_type": dict(sorted(by_type.items())),
        "mtime_policy": "All filesystem mtimes are SYSTEM_METADATA_ONLY unless separately verified.",
    }


def write_inventory(
    rows: Iterable[dict[str, object]], csv_path: str | Path, summary_path: str | Path
) -> None:
    items = list(rows)
    csv_destination = Path(csv_path)
    json_destination = Path(summary_path)
    csv_destination.parent.mkdir(parents=True, exist_ok=True)
    json_destination.parent.mkdir(parents=True, exist_ok=True)
    csv_temporary = csv_destination.with_suffix(csv_destination.suffix + ".tmp")
    with csv_temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=INVENTORY_COLUMNS)
        writer.writeheader()
        writer.writerows(items)
    os.replace(csv_temporary, csv_destination)
    json_temporary = json_destination.with_suffix(json_destination.suffix + ".tmp")
    json_temporary.write_text(
        json.dumps(summarize_inventory(items), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(json_temporary, json_destination)


def _dataset(relative_path: str) -> str:
    lowered = relative_path.lower()
    for dataset in ("jamshield", "deepsense", "electrosense", "radioml", "wisig"):
        if dataset in lowered:
            return dataset
    return "other_or_unresolved"


def _source_stage(relative_path: str) -> str:
    parts = relative_path.split("/")
    if parts[0] == "raw":
        return "raw_archive" if _file_type(Path(relative_path)) in {"zip", "gz", "tar"} else "raw_source"
    if parts[0] == "processed":
        return "converted_artifact"
    if parts[0] in {"experiments", "paper1", "paper2", "paper3"}:
        return "experiment_or_analysis_output"
    if parts[0] == "professor_share":
        return "documentation_snapshot"
    return "other"


def _file_type(path: Path) -> str:
    name = path.name.lower()
    if name.endswith(".tar.gz"):
        return "tar.gz"
    return path.suffix.lower().lstrip(".") or "none"


def _candidate_container(file_type: str) -> bool:
    return file_type in {
        "csv",
        "json",
        "yaml",
        "yml",
        "md",
        "txt",
        "npy",
        "npz",
        "parquet",
        "h5",
        "hdf5",
        "mat",
        "zip",
        "gz",
        "tar.gz",
    }


def _parser_available(file_type: str) -> bool:
    return file_type in {
        "csv",
        "json",
        "yaml",
        "yml",
        "md",
        "txt",
        "npy",
        "npz",
        "zip",
        "gz",
        "tar.gz",
    }
