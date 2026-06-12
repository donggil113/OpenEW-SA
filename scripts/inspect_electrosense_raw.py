#!/usr/bin/env python
"""Inspect raw ElectroSense PSD NumPy files before conversion."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DEFAULT_OUTPUT = Path(r"D:\openew_sa_data\tables\electrosense_raw_inspection.txt")
DEFAULT_CSV_OUTPUT = Path(r"D:\openew_sa_data\tables\electrosense_raw_inspection.csv")
TECHNOLOGY_LABELS = ("fm", "dab", "tetra", "dvbt", "lte", "gsm")
MIN_FILE_SIZE_BYTES = 1024


def inspect_raw_electrosense(raw_dir: str | Path) -> list[dict[str, Any]]:
    """Collect shape, dtype, filename labels, and summary stats for ElectroSense ``.npy`` files."""

    root = Path(raw_dir).expanduser()
    if not root.exists():
        raise FileNotFoundError(f"Raw ElectroSense directory does not exist: {root}")

    rows: list[dict[str, Any]] = []
    for npy_path in sorted(root.rglob("*.npy")):
        rows.append(_inspect_npy_file(npy_path, root))
    return rows


def _inspect_npy_file(path: Path, root: Path) -> dict[str, Any]:
    file_size = path.stat().st_size
    frequency_start, frequency_end = _infer_frequency_range(path.name)
    row: dict[str, Any] = {
        "relative_path": str(path.relative_to(root)),
        "file_size_bytes": int(file_size),
        "sensor_id": _infer_sensor_id(path),
        "date_id": _infer_date_id(path),
        "filename": path.name,
        "technology_label": _infer_technology(path.name),
        "frequency_range": _format_frequency_range(frequency_start, frequency_end),
        "frequency_start_mhz": frequency_start,
        "frequency_end_mhz": frequency_end,
        "shape": None,
        "dtype": None,
        "min": None,
        "max": None,
        "mean": None,
        "std": None,
        "status": "ok",
        "error": "",
    }

    if file_size < MIN_FILE_SIZE_BYTES:
        row["status"] = "too_small"
        return row

    try:
        array = np.load(path, allow_pickle=False, mmap_mode="r")
    except Exception as error:  # noqa: BLE001 - inspection should continue across corrupt files.
        row["status"] = "load_failed"
        row["error"] = str(error)
        return row

    row["shape"] = list(array.shape)
    row["dtype"] = str(array.dtype)
    row.update(_array_stats(array))
    if array.ndim not in {1, 2}:
        row["status"] = "unexpected_shape"
    return row


def _infer_sensor_id(path: Path) -> str:
    return path.parent.parent.name if len(path.parents) >= 2 else ""


def _infer_date_id(path: Path) -> str:
    return path.parent.name if path.parent != path else ""


def _infer_technology(filename: str) -> str:
    tokens = re.split(r"[_\-.]+", filename.lower())
    for label in TECHNOLOGY_LABELS:
        if label in tokens:
            return label
    return "unknown"


def _infer_frequency_range(filename: str) -> tuple[float | None, float | None]:
    match = re.search(r"SpectrumBands_(\d+(?:\.\d+)?)_(\d+(?:\.\d+)?)", filename, flags=re.IGNORECASE)
    if not match:
        return None, None
    return float(match.group(1)), float(match.group(2))


def _format_frequency_range(start: float | None, end: float | None) -> str:
    if start is None or end is None:
        return ""
    return f"{_format_number(start)}-{_format_number(end)}"


def _format_number(value: float) -> str:
    return str(int(value)) if value.is_integer() else str(value)


def _array_stats(array: np.ndarray) -> dict[str, float | None]:
    if array.size == 0 or not np.issubdtype(array.dtype, np.number):
        return {"min": None, "max": None, "mean": None, "std": None}
    values = np.abs(array) if np.issubdtype(array.dtype, np.complexfloating) else array
    values = np.asarray(values, dtype=np.float64)
    return {
        "min": float(np.nanmin(values)),
        "max": float(np.nanmax(values)),
        "mean": float(np.nanmean(values)),
        "std": float(np.nanstd(values)),
    }


def write_reports(
    rows: list[dict[str, Any]],
    output: str | Path,
    csv_output: str | Path | None = None,
) -> tuple[Path, Path]:
    """Write a readable text report and a CSV summary table."""

    text_path = Path(output).expanduser()
    csv_path = Path(csv_output).expanduser() if csv_output else text_path.with_suffix(".csv")
    text_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    text_path.write_text(format_text_report(rows), encoding="utf-8")
    pd.DataFrame([_flatten_row(row) for row in rows]).to_csv(csv_path, index=False)
    return text_path, csv_path


def format_text_report(rows: list[dict[str, Any]]) -> str:
    lines = ["ElectroSense raw NPY inspection", ""]
    if not rows:
        lines.append("No NPY files found.")
        return "\n".join(lines)

    status_counts = pd.Series([row["status"] for row in rows]).value_counts().sort_index().to_dict()
    lines.append(f"Files inspected: {len(rows)}")
    lines.append(f"Status counts: {json.dumps(status_counts, sort_keys=True)}")
    lines.append("")

    for row in rows:
        lines.extend(
            [
                f"File: {row['relative_path']}",
                f"Status: {row['status']}",
                f"Size bytes: {row['file_size_bytes']}",
                f"Sensor/date: {row['sensor_id']} / {row['date_id']}",
                f"Technology: {row['technology_label']}",
                f"Frequency range MHz: {row['frequency_range'] or '<unparsed>'}",
                f"Shape: {row['shape'] if row['shape'] is not None else '<not loaded>'}",
                f"Dtype: {row['dtype'] if row['dtype'] is not None else '<not loaded>'}",
                f"Stats: min={_display(row['min'])}, max={_display(row['max'])}, "
                f"mean={_display(row['mean'])}, std={_display(row['std'])}",
            ]
        )
        if row["error"]:
            lines.append(f"Error: {row['error']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _display(value: Any) -> str:
    if value is None or pd.isna(value):
        return "NA"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _flatten_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "relative_path": row["relative_path"],
        "file_size_bytes": row["file_size_bytes"],
        "sensor_id": row["sensor_id"],
        "date_id": row["date_id"],
        "filename": row["filename"],
        "technology_label": row["technology_label"],
        "frequency_range": row["frequency_range"],
        "frequency_start_mhz": row["frequency_start_mhz"],
        "frequency_end_mhz": row["frequency_end_mhz"],
        "shape": json.dumps(row["shape"]),
        "dtype": row["dtype"],
        "min": row["min"],
        "max": row["max"],
        "mean": row["mean"],
        "std": row["std"],
        "status": row["status"],
        "error": row["error"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect raw ElectroSense NPY files.")
    parser.add_argument("--raw-dir", required=True, help="Raw ElectroSense directory to scan recursively.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, type=Path, help="Readable text report path.")
    parser.add_argument("--csv-output", default=DEFAULT_CSV_OUTPUT, type=Path, help="CSV summary output path.")
    args = parser.parse_args()

    rows = inspect_raw_electrosense(args.raw_dir)
    text_path, csv_path = write_reports(rows, args.output, args.csv_output)
    status_counts = pd.Series([row["status"] for row in rows]).value_counts().sort_index().to_dict() if rows else {}
    print(f"Inspected {len(rows)} ElectroSense NPY files.")
    print(f"Status counts: {json.dumps(status_counts, sort_keys=True)}")
    print(f"Wrote text report: {text_path}")
    print(f"Wrote CSV summary: {csv_path}")


if __name__ == "__main__":
    main()
