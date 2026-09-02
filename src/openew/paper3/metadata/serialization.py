"""CSV, JSON, and optional Parquet serialization with string-safe identifiers."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable
import csv
import json
import os

from .schema import AcquisitionRecord, AnnotationRecord, acquisition_field_names


def write_acquisition_records(
    path: str | Path, records: Iterable[AcquisitionRecord], file_format: str | None = None
) -> None:
    rows = list(records)
    destination = Path(path)
    fmt = (file_format or destination.suffix.lstrip(".")).lower()
    if fmt == "json":
        _write_json(destination, [row.to_mapping() for row in rows])
    elif fmt == "csv":
        _write_csv(destination, [row.to_mapping() for row in rows], acquisition_field_names())
    elif fmt in {"parquet", "pq"}:
        _write_parquet(destination, [row.to_mapping() for row in rows])
    else:
        raise ValueError(f"Unsupported acquisition metadata format: {fmt}")


def read_acquisition_records(
    path: str | Path, file_format: str | None = None
) -> list[AcquisitionRecord]:
    source = Path(path)
    fmt = (file_format or source.suffix.lstrip(".")).lower()
    if fmt == "json":
        rows = json.loads(source.read_text(encoding="utf-8"))
    elif fmt == "csv":
        with source.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    elif fmt in {"parquet", "pq"}:
        rows = _read_parquet(source)
    else:
        raise ValueError(f"Unsupported acquisition metadata format: {fmt}")
    return [AcquisitionRecord.from_mapping(_decode_collections(row)) for row in rows]


def write_annotation_records(
    path: str | Path, records: Iterable[AnnotationRecord], file_format: str | None = None
) -> None:
    rows = [row.to_mapping() for row in records]
    destination = Path(path)
    fmt = (file_format or destination.suffix.lstrip(".")).lower()
    if fmt == "json":
        _write_json(destination, rows)
    elif fmt == "csv":
        _write_csv(
            destination,
            rows,
            ("sample_id", "task_name", "target_label", "annotation_source", "annotation_time"),
        )
    elif fmt in {"parquet", "pq"}:
        _write_parquet(destination, rows)
    else:
        raise ValueError(f"Unsupported annotation format: {fmt}")


def read_annotation_records(
    path: str | Path, file_format: str | None = None
) -> list[AnnotationRecord]:
    source = Path(path)
    fmt = (file_format or source.suffix.lstrip(".")).lower()
    if fmt == "json":
        rows = json.loads(source.read_text(encoding="utf-8"))
    elif fmt == "csv":
        with source.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    elif fmt in {"parquet", "pq"}:
        rows = _read_parquet(source)
    else:
        raise ValueError(f"Unsupported annotation format: {fmt}")
    return [AnnotationRecord.from_mapping(row) for row in rows]


def _write_json(destination: Path, rows: list[dict[str, object]]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, destination)


def _write_csv(
    destination: Path, rows: list[dict[str, object]], fieldnames: Iterable[str]
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            encoded = dict(row)
            for name in ("metadata_missing_mask", "metadata_quality_flags"):
                if name in encoded:
                    encoded[name] = json.dumps(encoded[name], ensure_ascii=False)
            writer.writerow(encoded)
    os.replace(temporary, destination)


def _decode_collections(row: dict[str, object]) -> dict[str, object]:
    result = dict(row)
    for name in ("metadata_missing_mask", "metadata_quality_flags"):
        value = result.get(name)
        if isinstance(value, str) and value.startswith("["):
            result[name] = json.loads(value)
    return result


def _write_parquet(destination: Path, rows: list[dict[str, object]]) -> None:
    try:
        import pandas as pd

        destination.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_parquet(destination, index=False)
    except ImportError as error:
        raise RuntimeError("Parquet support requires pandas and a Parquet engine") from error
    except (ValueError, ModuleNotFoundError) as error:
        raise RuntimeError("Parquet support requires pyarrow or fastparquet") from error


def _read_parquet(source: Path) -> list[dict[str, object]]:
    try:
        import pandas as pd

        return pd.read_parquet(source).to_dict(orient="records")
    except ImportError as error:
        raise RuntimeError("Parquet support requires pandas and a Parquet engine") from error
    except (ValueError, ModuleNotFoundError) as error:
        raise RuntimeError("Parquet support requires pyarrow or fastparquet") from error
