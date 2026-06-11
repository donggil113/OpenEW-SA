"""DeepSense Spectrum Sensing conversion utilities.

The converter expects manually downloaded DeepSense spectrum sensing files. It supports NumPy
arrays directly and can be extended for lab-specific raw captures without changing downstream
OpenEW-SA training code.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from openew.data.common import discover_files, save_conversion
from openew.data.schema import MetadataRecord, records_to_frame

DATASET_SOURCE = "deepsense_spectrum_sensing"


def convert(config: dict[str, Any]) -> None:
    """Convert DeepSense samples into OpenEW-SA artifacts."""

    input_dir = Path(config["input_dir"]).expanduser()
    output_dir = config["output_dir"]
    feature_format = config.get("feature_format", "npy")
    files = discover_files(input_dir, config.get("patterns", ["**/*.npy", "**/*.npz"]))
    if not files:
        raise FileNotFoundError(f"No DeepSense files found in {input_dir}; download manually first.")

    arrays: list[np.ndarray] = []
    records: list[MetadataRecord] = []
    for index, path in enumerate(files):
        data = _load_array(path)
        arrays.append(data)
        records.append(
            MetadataRecord(
                sample_id=f"deepsense_{index:08d}",
                dataset_source=DATASET_SOURCE,
                input_type=config.get("input_type", "iq_or_spectrogram"),
                time_index=index,
                frequency_band=config.get("frequency_band"),
                rx_id=config.get("rx_id"),
                occupancy_label=_infer_label(path.name, config.get("label_map", {})),
                domain_id=config.get("domain_id", "deepsense_default"),
                synthetic_mission_context=config.get("synthetic_mission_context", "spectrum_sensing"),
                situation_label=config.get("situation_label"),
                threat_level=config.get("threat_level", 0),
                human_review_required=config.get("human_review_required", False),
            )
        )

    features = np.stack(arrays)
    labels = {
        "task": "spectrum_occupancy",
        "dataset_source": DATASET_SOURCE,
        "label_map": config.get("label_map", {}),
        "num_samples": len(records),
    }
    save_conversion(output_dir, records_to_frame(records), features, labels, feature_format)


def _load_array(path: Path) -> np.ndarray:
    if path.suffix == ".npz":
        archive = np.load(path)
        key = "features" if "features" in archive else archive.files[0]
        return np.asarray(archive[key])
    return np.asarray(np.load(path))


def _infer_label(filename: str, label_map: dict[str, Any]) -> Any:
    lowered = filename.lower()
    for token, label in label_map.items():
        if token.lower() in lowered:
            return label
    return None
