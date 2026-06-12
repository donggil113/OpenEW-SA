"""DeepSense SDR WiFi conversion utilities for OpenEW-SA.

The real SDR 802.11 a/g release stores complex64 I/Q streams in ``.bin`` files. File
stems begin with a four-bit occupancy label, for example ``1101_day2.bin``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from openew.data.common import save_conversion
from openew.data.schema import MetadataRecord, records_to_frame

DATASET_SOURCE = "deepsense"
INPUT_TYPE = "iq_features"
FREQUENCY_BAND = "wifi_20mhz_4ch"
RX_ID = "deepsense_receiver"
OCCUPANCY_STATES = [f"{state:04b}" for state in range(16)]


def convert(config: dict[str, Any]) -> None:
    """Convert DeepSense SDR WiFi ``.bin`` files into OpenEW-SA artifacts."""

    raw_dir = Path(config.get("raw_dir", config.get("input_dir", ""))).expanduser()
    output_dir = config["output_dir"]
    window_size = int(config.get("window_size", 1024))
    stride = int(config.get("stride", 1024))
    max_windows_per_file = _optional_positive_int(config.get("max_windows_per_file", 1000))
    flatten = bool(config.get("flatten", True))
    feature_format = config.get("feature_format", "npy")

    _validate_windowing(window_size, stride)
    files = _discover_bin_files(raw_dir)
    if not files:
        raise FileNotFoundError(f"No DeepSense .bin files found in {raw_dir}; download manually first.")

    feature_batches: list[np.ndarray] = []
    records: list[MetadataRecord] = []
    source_files: list[dict[str, Any]] = []
    sample_index = 0
    feature_shape: list[int] | None = None

    for path in files:
        occupancy_label, domain_id = _parse_labels(path)
        signal = _read_complex64(path, window_size, stride, max_windows_per_file)
        file_features = _window_features(signal, window_size, stride, max_windows_per_file, flatten)
        row_count = int(file_features.shape[0])
        source_files.append(
            {
                "path": _relative_path(path, raw_dir),
                "occupancy_label": occupancy_label,
                "domain_id": domain_id,
                "row_count": row_count,
            }
        )
        if row_count == 0:
            continue

        if feature_shape is None:
            feature_shape = list(file_features.shape[1:])
        feature_batches.append(file_features)
        for window_index in range(row_count):
            records.append(
                MetadataRecord(
                    sample_id=f"deepsense_{sample_index:08d}",
                    dataset_source=DATASET_SOURCE,
                    input_type=INPUT_TYPE,
                    time_index=window_index,
                    frequency_band=FREQUENCY_BAND,
                    tx_id="",
                    rx_id=RX_ID,
                    modulation_label="",
                    occupancy_label=occupancy_label,
                    abnormal_event_label="",
                    domain_id=domain_id,
                    synthetic_mission_context="spectrum_monitoring",
                    situation_label="occupied" if "1" in occupancy_label else "idle",
                    threat_level="low",
                    human_review_required=False,
                )
            )
            sample_index += 1

    if not feature_batches:
        raise ValueError(
            f"DeepSense conversion produced no windows. Check window_size={window_size}, stride={stride}, and raw files."
        )

    features = np.concatenate(feature_batches, axis=0).astype(np.float32, copy=False)
    labels = {
        "dataset_source": DATASET_SOURCE,
        "label_column": "occupancy_label",
        "class_names": {
            "occupancy_label": OCCUPANCY_STATES,
            "situation_label": ["idle", "occupied"],
            "threat_level": ["low"],
        },
        "feature_shape": feature_shape or list(features.shape[1:]),
        "window_size": window_size,
        "stride": stride,
        "max_windows_per_file": max_windows_per_file,
        "flatten": flatten,
        "num_samples": len(records),
        "source_files": source_files,
    }
    save_conversion(output_dir, records_to_frame(records), features, labels, feature_format)


def _discover_bin_files(raw_dir: Path) -> list[Path]:
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw DeepSense directory does not exist: {raw_dir}")
    return sorted(path for path in raw_dir.rglob("*.bin") if path.is_file())


def _parse_labels(path: Path) -> tuple[str, str]:
    stem = path.stem
    occupancy_label = stem[:4]
    if len(occupancy_label) != 4 or any(bit not in {"0", "1"} for bit in occupancy_label):
        raise ValueError(f"DeepSense filename must start with a four-bit occupancy label: {path.name}")

    parts = stem.split("_")
    domain_id = next((part.lower() for part in parts[1:] if part.lower().startswith("day")), None)
    if domain_id is None:
        domain_id = parts[1].lower() if len(parts) > 1 else "unknown_day"
    return occupancy_label, domain_id


def _read_complex64(
    path: Path,
    window_size: int,
    stride: int,
    max_windows_per_file: int | None,
) -> np.ndarray:
    count = _max_samples_to_read(window_size, stride, max_windows_per_file)
    if count is None:
        return np.fromfile(path, dtype=np.complex64)
    return np.fromfile(path, dtype=np.complex64, count=count)


def _max_samples_to_read(window_size: int, stride: int, max_windows_per_file: int | None) -> int | None:
    if max_windows_per_file is None:
        return None
    return window_size + stride * (max_windows_per_file - 1)


def _window_features(
    signal: np.ndarray,
    window_size: int,
    stride: int,
    max_windows_per_file: int | None,
    flatten: bool,
) -> np.ndarray:
    num_windows = _num_windows(len(signal), window_size, stride, max_windows_per_file)
    if flatten:
        features = np.empty((num_windows, 2 * window_size), dtype=np.float32)
    else:
        features = np.empty((num_windows, 2, window_size), dtype=np.float32)

    for window_index in range(num_windows):
        start = window_index * stride
        window = signal[start : start + window_size]
        stacked = np.stack((window.real, window.imag), axis=0).astype(np.float32, copy=False)
        features[window_index] = stacked.reshape(-1) if flatten else stacked
    return features


def _num_windows(
    num_samples: int,
    window_size: int,
    stride: int,
    max_windows_per_file: int | None,
) -> int:
    if num_samples < window_size:
        return 0
    count = 1 + (num_samples - window_size) // stride
    if max_windows_per_file is not None:
        count = min(count, max_windows_per_file)
    return int(count)


def _optional_positive_int(value: Any) -> int | None:
    if value is None:
        return None
    parsed = int(value)
    if parsed <= 0:
        raise ValueError("max_windows_per_file must be positive or null")
    return parsed


def _validate_windowing(window_size: int, stride: int) -> None:
    if window_size <= 0:
        raise ValueError("window_size must be positive")
    if stride <= 0:
        raise ValueError("stride must be positive")


def _relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
