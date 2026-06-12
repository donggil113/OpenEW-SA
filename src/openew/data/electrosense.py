"""ElectroSense PSD Spectrum Dataset conversion utilities."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import numpy as np

from openew.data.common import save_conversion
from openew.data.schema import MetadataRecord, records_to_frame

DATASET_SOURCE = "electrosense"
INPUT_TYPE = "psd_features"
TECHNOLOGY_LABELS = ("fm", "dab", "tetra", "dvbt", "lte", "gsm")
CLASS_NAMES = ["dab", "dvbt", "fm", "gsm", "lte", "tetra"]
MIN_FILE_SIZE_BYTES = 1024


def convert(config: dict[str, Any]) -> None:
    """Convert ElectroSense PSD ``.npy`` files into OpenEW-SA artifacts."""

    raw_dir = Path(config.get("raw_dir", config.get("input_dir", ""))).expanduser()
    output_dir = config["output_dir"]
    target_length = int(config.get("target_length", 512))
    max_rows_per_file = _optional_positive_int(config.get("max_rows_per_file", 200))
    max_files = _optional_positive_int(config.get("max_files"))
    normalize_per_sample = bool(config.get("normalize_per_sample", True))
    feature_format = config.get("feature_format", "npy")

    if target_length <= 0:
        raise ValueError("target_length must be positive")
    files = _discover_npy_files(raw_dir)
    if max_files is not None:
        files = files[:max_files]
    if not files:
        raise FileNotFoundError(f"No ElectroSense .npy files found in {raw_dir}; download manually first.")

    features: list[np.ndarray] = []
    records: list[MetadataRecord] = []
    source_files: list[dict[str, Any]] = []
    skipped_files: list[dict[str, Any]] = []
    sample_index = 0

    for path in files:
        file_size = path.stat().st_size
        sensor_id = _infer_sensor_id(path)
        date_id = _infer_date_id(path)
        technology_label = _infer_technology(path.name)
        frequency_band = _infer_frequency_range(path.name)

        if file_size < MIN_FILE_SIZE_BYTES:
            skipped_files.append(_skipped_file(path, raw_dir, "too_small", file_size))
            continue
        if technology_label not in CLASS_NAMES:
            skipped_files.append(_skipped_file(path, raw_dir, "unknown_technology", file_size))
            continue

        try:
            psd = np.load(path, allow_pickle=False, mmap_mode="r")
        except Exception as error:  # noqa: BLE001 - conversion should report all skipped files.
            skipped_files.append(_skipped_file(path, raw_dir, "load_failed", file_size, str(error)))
            continue
        if psd.ndim != 2:
            skipped_files.append(_skipped_file(path, raw_dir, "unexpected_shape", file_size, f"shape={psd.shape}"))
            continue

        row_count = _row_count(psd.shape[0], max_rows_per_file)
        if row_count == 0:
            skipped_files.append(_skipped_file(path, raw_dir, "no_rows", file_size, f"shape={psd.shape}"))
            continue

        source_files.append(
            {
                "path": _relative_path(path, raw_dir),
                "sensor_id": sensor_id,
                "date_id": date_id,
                "technology_label": technology_label,
                "frequency_band": frequency_band,
                "row_count": row_count,
                "original_shape": [int(value) for value in psd.shape],
            }
        )
        for row_index in range(row_count):
            feature = _prepare_psd_row(psd[row_index], target_length, normalize_per_sample)
            features.append(feature)
            records.append(
                MetadataRecord(
                    sample_id=f"electrosense_{sample_index:08d}",
                    dataset_source=DATASET_SOURCE,
                    input_type=INPUT_TYPE,
                    time_index=row_index,
                    frequency_band=frequency_band,
                    tx_id="",
                    rx_id=sensor_id,
                    modulation_label="",
                    occupancy_label="",
                    abnormal_event_label="",
                    domain_id=sensor_id,
                    synthetic_mission_context="spectrum_monitoring",
                    situation_label=technology_label,
                    threat_level="low",
                    human_review_required=False,
                )
            )
            sample_index += 1

    if not features:
        raise ValueError(f"ElectroSense conversion produced no PSD rows from {raw_dir}")

    labels = {
        "dataset_source": DATASET_SOURCE,
        "label_column": "situation_label",
        "class_names": CLASS_NAMES,
        "feature_shape": [target_length],
        "target_length": target_length,
        "max_rows_per_file": max_rows_per_file,
        "max_files": max_files,
        "normalize_per_sample": normalize_per_sample,
        "num_samples": len(records),
        "source_files": source_files,
        "skipped_files": skipped_files,
    }
    feature_array = np.stack(features).astype(np.float32, copy=False)
    save_conversion(output_dir, records_to_frame(records), feature_array, labels, feature_format)


def _discover_npy_files(raw_dir: Path) -> list[Path]:
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw ElectroSense directory does not exist: {raw_dir}")
    return sorted(path for path in raw_dir.rglob("*.npy") if path.is_file())


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


def _infer_frequency_range(filename: str) -> str:
    match = re.search(r"SpectrumBands_(\d+(?:\.\d+)?)_(\d+(?:\.\d+)?)", filename, flags=re.IGNORECASE)
    if not match:
        return ""
    return f"{_format_number(float(match.group(1)))}-{_format_number(float(match.group(2)))}"


def _format_number(value: float) -> str:
    return str(int(value)) if value.is_integer() else str(value)


def _row_count(num_rows: int, max_rows_per_file: int | None) -> int:
    if max_rows_per_file is None:
        return int(num_rows)
    return int(min(num_rows, max_rows_per_file))


def _prepare_psd_row(row: np.ndarray, target_length: int, normalize_per_sample: bool) -> np.ndarray:
    values = np.asarray(row, dtype=np.float32).reshape(-1)
    values = _resample(values, target_length)
    values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
    if normalize_per_sample:
        mean = float(values.mean())
        std = float(values.std())
        if std > 0.0:
            values = (values - mean) / std
        else:
            values = values - mean
    return values.astype(np.float32, copy=False)


def _resample(values: np.ndarray, target_length: int) -> np.ndarray:
    if len(values) == target_length:
        return values.astype(np.float32, copy=False)
    if len(values) == 0:
        return np.zeros(target_length, dtype=np.float32)
    if len(values) == 1:
        return np.full(target_length, float(values[0]), dtype=np.float32)
    source_positions = np.linspace(0.0, 1.0, num=len(values), dtype=np.float32)
    target_positions = np.linspace(0.0, 1.0, num=target_length, dtype=np.float32)
    return np.interp(target_positions, source_positions, values).astype(np.float32)


def _optional_positive_int(value: Any) -> int | None:
    if value is None:
        return None
    parsed = int(value)
    if parsed <= 0:
        raise ValueError("Expected positive integer or null")
    return parsed


def _skipped_file(path: Path, raw_dir: Path, reason: str, file_size: int, error: str = "") -> dict[str, Any]:
    return {
        "path": _relative_path(path, raw_dir),
        "reason": reason,
        "file_size_bytes": int(file_size),
        "error": error,
    }


def _relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
