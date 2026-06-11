"""JamShield Dataset conversion utilities for jamming/interference metrics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from openew.data.common import discover_files, save_conversion
from openew.data.schema import MetadataRecord, records_to_frame

DATASET_SOURCE = "jamshield"


def convert(config: dict[str, Any]) -> None:
    """Convert JamShield tabular metrics into OpenEW-SA artifacts."""

    input_dir = Path(config["input_dir"]).expanduser()
    files = discover_files(input_dir, config.get("patterns", ["**/*.csv"]))
    if not files:
        raise FileNotFoundError(f"No JamShield files found in {input_dir}; download manually first.")

    feature_columns = config.get("feature_columns")
    label_column = config.get("label_column", "attack_type")
    frames = [pd.read_csv(path) for path in files]
    frame = pd.concat(frames, ignore_index=True)
    numeric = frame[feature_columns] if feature_columns else frame.select_dtypes(include="number")
    if numeric.empty:
        raise ValueError("JamShield conversion needs numeric feature columns.")

    records: list[MetadataRecord] = []
    for index, row in frame.iterrows():
        event_label = row.get(label_column) if label_column in frame.columns else None
        records.append(
            MetadataRecord(
                sample_id=f"jamshield_{index:08d}",
                dataset_source=DATASET_SOURCE,
                input_type="tabular_metrics",
                time_index=row.get(config.get("time_column", "time"), index),
                frequency_band=config.get("frequency_band"),
                tx_id=row.get(config.get("tx_column", "tx_id")),
                rx_id=row.get(config.get("rx_column", "rx_id")),
                abnormal_event_label=event_label,
                domain_id=config.get("domain_id", "jamshield_default"),
                synthetic_mission_context=config.get("synthetic_mission_context", "jamming_detection"),
                situation_label=_situation_from_event(event_label),
                threat_level=_threat_from_event(event_label),
                human_review_required=bool(event_label) and str(event_label).lower() not in {"normal", "none", "benign"},
            )
        )

    labels = {
        "task": "jamming_or_interference_detection",
        "dataset_source": DATASET_SOURCE,
        "label_column": label_column,
        "num_samples": len(records),
    }
    save_conversion(config["output_dir"], records_to_frame(records), numeric.to_numpy(dtype=np.float32), labels, config.get("feature_format", "npy"))


def _situation_from_event(event: Any) -> str | None:
    if event is None or (isinstance(event, float) and np.isnan(event)):
        return None
    text = str(event).lower()
    return "nominal" if text in {"normal", "none", "benign"} else "suspected_interference"


def _threat_from_event(event: Any) -> int:
    situation = _situation_from_event(event)
    return 0 if situation in {None, "nominal"} else 3
