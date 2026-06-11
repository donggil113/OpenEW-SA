"""WiSig RF fingerprinting conversion utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from openew.data.common import discover_files, save_conversion
from openew.data.schema import MetadataRecord, records_to_frame

DATASET_SOURCE = "wisig_rf_fingerprinting"


def convert(config: dict[str, Any]) -> None:
    """Convert WiSig transmitter fingerprinting data into OpenEW-SA artifacts."""

    input_dir = Path(config["input_dir"]).expanduser()
    files = discover_files(input_dir, config.get("patterns", ["**/*.npy", "**/*.npz"]))
    if not files:
        raise FileNotFoundError(f"No WiSig files found in {input_dir}; download manually first.")

    arrays: list[np.ndarray] = []
    records: list[MetadataRecord] = []
    for index, path in enumerate(files):
        arrays.append(_load_array(path))
        tx_id = _infer_entity(path, config.get("tx_id_prefix", "tx"))
        rx_id = _infer_entity(path, config.get("rx_id_prefix", "rx"))
        records.append(
            MetadataRecord(
                sample_id=f"wisig_{index:08d}",
                dataset_source=DATASET_SOURCE,
                input_type=config.get("input_type", "iq"),
                time_index=index,
                frequency_band=config.get("frequency_band"),
                tx_id=tx_id,
                rx_id=rx_id,
                domain_id=rx_id or config.get("domain_id", "wisig_default"),
                synthetic_mission_context=config.get("synthetic_mission_context", "rf_fingerprinting"),
                situation_label=config.get("situation_label", "authorized_or_unknown_transmitter"),
                threat_level=config.get("threat_level", 0),
                human_review_required=config.get("human_review_required", False),
            )
        )

    labels = {"task": "tx_identification", "dataset_source": DATASET_SOURCE, "num_samples": len(records)}
    save_conversion(config["output_dir"], records_to_frame(records), np.stack(arrays), labels, config.get("feature_format", "npy"))


def _load_array(path: Path) -> np.ndarray:
    if path.suffix == ".npz":
        archive = np.load(path)
        key = "iq" if "iq" in archive else archive.files[0]
        return np.asarray(archive[key])
    return np.asarray(np.load(path))


def _infer_entity(path: Path, prefix: str) -> str | None:
    for part in path.parts:
        if part.lower().startswith(prefix.lower()):
            return part
    return None
