#!/usr/bin/env python3
"""Safely summarize official WiSig metadata pickles without loading RF payloads."""

from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import pickle
from typing import Any

import numpy as np
from numpy._core.multiarray import _reconstruct


class RestrictedUnpickler(pickle.Unpickler):
    """Allow primitives and the small NumPy objects used by official summaries."""

    _ALLOWED = {
        ("numpy.core.multiarray", "_reconstruct"): _reconstruct,
        ("numpy._core.multiarray", "_reconstruct"): _reconstruct,
        ("numpy", "ndarray"): np.ndarray,
        ("numpy", "dtype"): np.dtype,
    }

    def find_class(self, module: str, name: str) -> Any:
        try:
            return self._ALLOWED[(module, name)]
        except KeyError as error:
            raise pickle.UnpicklingError(f"forbidden pickle global: {module}.{name}") from error


def restricted_load(path: Path) -> Any:
    return RestrictedUnpickler(io.BytesIO(path.read_bytes())).load()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    summaries: dict[str, object] = {}
    for path in sorted(root.rglob("*.pkl")):
        if ".git" in path.parts:
            continue
        value = restricted_load(path)
        relative = path.relative_to(root).as_posix()
        summaries[relative] = summarize(relative, value)
    result = {
        "schema_version": 1,
        "root": str(root),
        "payload_loaded": False,
        "public_download_identifiers_emitted": False,
        "files": summaries,
    }
    write_json_atomic(Path(args.output), result)
    print(json.dumps(result, indent=2, sort_keys=True))


def summarize(relative: str, value: Any) -> dict[str, object]:
    if relative.endswith("raw_info_dct.pkl"):
        days = sorted(str(day) for day in value)
        receivers_by_day = {str(day): len(value[day]) for day in value}
        groups_by_day = {
            str(day): sum(len(groups) for groups in value[day].values()) for day in value
        }
        total_bytes = sum(
            int(entry[2])
            for day in value.values()
            for groups in day.values()
            for entry in groups.values()
        )
        return {
            "kind": "raw_download_index",
            "days": days,
            "receivers_by_day": receivers_by_day,
            "archive_groups_by_day": groups_by_day,
            "indexed_total_bytes": total_bytes,
            "download_identifiers_redacted": True,
        }
    if relative.endswith("IdSig_info.pkl"):
        equalization_keys = sorted(str(key) for key in value)
        dates: set[str] = set()
        receiver_counts: dict[str, int] = {}
        for by_date in value.values():
            for date, by_receiver in by_date.items():
                dates.add(str(date))
                receiver_counts[str(date)] = max(receiver_counts.get(str(date), 0), len(by_receiver))
        return {
            "kind": "full_dataset_file_index",
            "equalization_keys": equalization_keys,
            "capture_dates": sorted(dates),
            "receiver_counts_by_date": receiver_counts,
            "download_identifiers_redacted": True,
        }
    if relative.endswith("orbit_hardware.pkl"):
        if isinstance(value, dict):
            structure: dict[str, object] = {
                "python_type": "dict",
                "top_level_keys": sorted(str(key) for key in value),
                "entry_counts": {
                    str(key): len(item) if hasattr(item, "__len__") else None
                    for key, item in value.items()
                },
            }
        elif isinstance(value, (list, tuple)):
            nested_value_keys = sorted(
                {
                    str(nested_key)
                    for item in value
                    if isinstance(item, dict)
                    for nested in item.values()
                    if isinstance(nested, dict)
                    for nested_key in nested
                }
            )
            structure = {
                "python_type": type(value).__name__,
                "length": len(value),
                "element_types": sorted({type(item).__name__ for item in value}),
                "mapping_lengths": [len(item) for item in value if isinstance(item, dict)],
                "nested_value_field_names": nested_value_keys,
            }
        else:
            structure = {"python_type": type(value).__name__}
        return {
            "kind": "orbit_hardware_mapping",
            "structure": structure,
            "target_identity_values_emitted": False,
        }
    if relative.endswith("data_summary.pkl"):
        return {
            "kind": "aggregate_signal_count_summary",
            "top_level_keys": sorted(str(key) for key in value),
            "arrays": _array_shapes(value),
        }
    return {"kind": "unknown_pickle", "python_type": type(value).__name__}


def _array_shapes(value: dict[Any, Any]) -> list[dict[str, object]]:
    arrays: list[dict[str, object]] = []
    for key, item in value.items():
        if isinstance(item, np.ndarray):
            arrays.append({"key": str(key), "shape": list(item.shape), "dtype": str(item.dtype)})
        elif isinstance(item, (list, tuple)):
            arrays.append(
                {
                    "key": str(key),
                    "length": len(item),
                    "python_type": type(item).__name__,
                    "element_shapes": [
                        list(element.shape) if isinstance(element, np.ndarray) else None
                        for element in item
                    ],
                    "element_types": sorted({type(element).__name__ for element in item}),
                }
            )
    return arrays


def write_json_atomic(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


if __name__ == "__main__":
    main()
