"""ElectroSense PSD Spectrum Dataset conversion utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from openew.data.common import discover_files, save_conversion
from openew.data.schema import MetadataRecord, records_to_frame

DATASET_SOURCE = "electrosense_psd_spectrum"


def convert(config: dict[str, Any]) -> None:
    """Convert ElectroSense PSD exports into OpenEW-SA artifacts."""

    input_dir = Path(config["input_dir"]).expanduser()
    files = discover_files(input_dir, config.get("patterns", ["**/*.csv", "**/*.npy", "**/*.npz"]))
    if not files:
        raise FileNotFoundError(f"No ElectroSense files found in {input_dir}; download manually first.")

    arrays: list[np.ndarray] = []
    records: list[MetadataRecord] = []
    for index, path in enumerate(files):
        psd = _load_psd(path, config.get("value_columns"))
        arrays.append(psd)
        records.append(
            MetadataRecord(
                sample_id=f"electrosense_{index:08d}",
                dataset_source=DATASET_SOURCE,
                input_type="psd",
                time_index=_infer_time(path, index),
                frequency_band=config.get("frequency_band"),
                rx_id=config.get("sensor_id") or path.parent.name,
                occupancy_label=config.get("default_occupancy_label"),
                domain_id=config.get("domain_id") or path.parent.name,
                synthetic_mission_context=config.get("synthetic_mission_context", "wideband_monitoring"),
                situation_label=config.get("situation_label"),
                threat_level=config.get("threat_level", 0),
                human_review_required=config.get("human_review_required", False),
            )
        )

    labels = {"task": "psd_occupancy_or_anomaly", "dataset_source": DATASET_SOURCE, "num_samples": len(records)}
    save_conversion(config["output_dir"], records_to_frame(records), np.stack(arrays), labels, config.get("feature_format", "npy"))


def _load_psd(path: Path, value_columns: list[str] | None) -> np.ndarray:
    if path.suffix == ".csv":
        frame = pd.read_csv(path)
        values = frame[value_columns] if value_columns else frame.select_dtypes(include="number")
        return values.to_numpy(dtype=np.float32).reshape(-1)
    if path.suffix == ".npz":
        archive = np.load(path)
        key = "psd" if "psd" in archive else archive.files[0]
        return np.asarray(archive[key], dtype=np.float32).reshape(-1)
    return np.asarray(np.load(path), dtype=np.float32).reshape(-1)


def _infer_time(path: Path, fallback: int) -> str | int:
    stem = path.stem
    return stem if any(char.isdigit() for char in stem) else fallback
