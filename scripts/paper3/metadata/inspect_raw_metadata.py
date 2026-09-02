#!/usr/bin/env python3
"""Read-only structural forensics for the three locally available RF sources."""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", default="/mnt/d/openew_sa_data")
    parser.add_argument(
        "--output",
        default="/mnt/d/openew_sa_data/paper3/source_forensics/raw_metadata_forensics.json",
    )
    args = parser.parse_args()
    root = Path(args.data_root) / "raw"
    result = {
        "schema_version": 1,
        "read_only": True,
        "filesystem_mtime_policy": "SYSTEM_METADATA_ONLY",
        "jamshield": inspect_jamshield(root / "jamshield"),
        "deepsense": inspect_deepsense(root / "deepsense"),
        "electrosense": inspect_electrosense(root / "electrosense"),
    }
    write_json_atomic(Path(args.output), result)
    print(json.dumps(summary(result), indent=2, sort_keys=True))


def inspect_jamshield(root: Path) -> dict[str, Any]:
    files = sorted(root.rglob("*.csv"))
    rows: list[dict[str, Any]] = []
    for path in files:
        frame = pd.read_csv(path)
        samples = pd.to_numeric(frame.get("sample"), errors="coerce")
        attacks = sorted(str(value) for value in frame.get("attack", pd.Series(dtype=str)).dropna().unique())
        rows.append(
            {
                "relative_path": path.relative_to(root).as_posix(),
                "row_count": len(frame),
                "columns": list(frame.columns),
                "station_count": int(frame["station"].nunique()) if "station" in frame else 0,
                "attack_values": attacks,
                "target_pure_file": len(attacks) <= 1,
                "sample_unique": bool(samples.notna().all() and samples.is_unique),
                "sample_consecutive_from_one": bool(
                    len(samples)
                    and samples.notna().all()
                    and np.array_equal(samples.to_numpy(dtype=np.int64), np.arange(1, len(samples) + 1))
                ),
            }
        )
    return {
        "source_root": str(root),
        "csv_file_count": len(rows),
        "row_count": sum(row["row_count"] for row in rows),
        "all_files_target_pure": all(row["target_pure_file"] for row in rows),
        "all_sample_counters_consecutive": all(row["sample_consecutive_from_one"] for row in rows),
        "recovery_verdict": "NO_NEW_LABEL_INDEPENDENT_ACQUISITION_CONTEXT",
        "temporal_verdict": "TARGET_NESTED_ORDER",
        "files": rows,
        "notes": [
            "station is source-table metadata but was already evaluated in PR #81",
            "sample is a per-file identifier/counter, not a documented acquisition timestamp",
            "source filenames encode jammer/benign scenario state",
        ],
    }


def inspect_deepsense(root: Path) -> dict[str, Any]:
    binary_files = sorted(root.rglob("*.bin"))
    rows = []
    for path in binary_files:
        match = re.fullmatch(r"([01]{4})_(day[12])\.bin", path.name)
        sample_count = path.stat().st_size // np.dtype(np.complex64).itemsize
        rows.append(
            {
                "relative_path": path.relative_to(root).as_posix(),
                "size_bytes": path.stat().st_size,
                "complex64_sample_count": sample_count,
                "duration_seconds_at_documented_20_msps": sample_count / 20_000_000,
                "filename_semantics": "TARGET_BEARING_FILENAME" if match else "UNKNOWN_FILENAME_TOKEN",
                "occupancy_token": match.group(1) if match else None,
                "day_token": match.group(2) if match else None,
                "target_pure_file": bool(match),
            }
        )
    h5_files = sorted(root.rglob("*.h5"))
    return {
        "source_root": str(root),
        "sdr_binary_file_count": len(rows),
        "simulated_lte_h5_file_count": len(h5_files),
        "all_sdr_files_target_pure": all(row["target_pure_file"] for row in rows),
        "recovery_verdict": "NO_NEW_LABEL_INDEPENDENT_ACQUISITION_CONTEXT",
        "temporal_verdict": "TARGET_NESTED_ORDER",
        "files": rows,
        "simulated_lte_files": [path.relative_to(root).as_posix() for path in h5_files],
        "notes": [
            "day1/day2 is a coarse campaign/split token, not within-session time",
            "binary payload is a headerless complex64 stream per official documentation",
            "window order remains nested inside occupancy-pure captures",
            "local LTE H5 files are simulated train/test artifacts, not new acquisition context",
        ],
    }


def inspect_electrosense(root: Path) -> dict[str, Any]:
    files = sorted(root.rglob("*.npy"))
    technologies: Counter[str] = Counter()
    sensors: set[str] = set()
    dates: set[str] = set()
    shape_counts: Counter[str] = Counter()
    mismatched_frequency_tokens = 0
    rows = []
    technology_pattern = re.compile(r"_(dab|dvbt|fm|gsm|lte|tetra|unkn)_", re.IGNORECASE)
    frequency_pattern = re.compile(r"SpectrumBands_([0-9.]+)_([0-9.]+)", re.IGNORECASE)
    for path in files:
        relative = path.relative_to(root).as_posix()
        array = np.load(path, mmap_mode="r", allow_pickle=False)
        match = technology_pattern.search(path.name)
        technology = match.group(1).lower() if match else "unresolved"
        technologies[technology] += 1
        parts = relative.split("/")
        sensor = parts[-3] if len(parts) >= 3 else "unresolved"
        date = parts[-2] if len(parts) >= 2 else "unresolved"
        sensors.add(sensor); dates.add(date)
        shape_counts[str(tuple(int(value) for value in array.shape))] += 1
        frequency_tokens = frequency_pattern.findall(path.name)
        if len(frequency_tokens) >= 2 and frequency_tokens[0] != frequency_tokens[-1]:
            mismatched_frequency_tokens += 1
        rows.append(
            {
                "relative_path": relative,
                "shape": [int(value) for value in array.shape],
                "dtype": str(array.dtype),
                "sensor_token": sensor,
                "date_token": date,
                "technology_token": technology,
                "filename_semantics": "TARGET_BEARING_FILENAME" if match else "UNKNOWN_FILENAME_TOKEN",
                "target_pure_file": bool(match),
            }
        )
    return {
        "source_root": str(root),
        "npy_file_count": len(rows),
        "sensor_count": len(sensors),
        "date_token_count": len(dates),
        "technology_file_counts": dict(sorted(technologies.items())),
        "shape_counts": dict(sorted(shape_counts.items())),
        "frequency_filename_pair_mismatch_count": mismatched_frequency_tokens,
        "container_format": "plain NumPy ndarray; no per-row header/attribute channel",
        "recovery_verdict": "NO_NEW_LABEL_INDEPENDENT_ACQUISITION_CONTEXT",
        "temporal_verdict": "COARSE_DATE_ONLY_AND_TARGET_NESTED_ORDER",
        "files": rows,
        "notes": [
            "sensor and coarse date tokens were already used in PR #81",
            "technology is encoded in each filename and each array is target-pure",
            "array row order has no verified timestamp, gap, or clock-reset semantics",
            "frequency tokens are target-associated and remain forbidden for this frozen protocol",
        ],
    }


def summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "jamshield_files": result["jamshield"]["csv_file_count"],
        "deepsense_sdr_files": result["deepsense"]["sdr_binary_file_count"],
        "deepsense_lte_files": result["deepsense"]["simulated_lte_h5_file_count"],
        "electrosense_files": result["electrosense"]["npy_file_count"],
        "new_valid_metadata_recovered": False,
        "valid_temporal_context_recovered": False,
    }


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


if __name__ == "__main__":
    main()
