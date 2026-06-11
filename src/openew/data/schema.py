"""Unified metadata schema for heterogeneous RF datasets."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

METADATA_COLUMNS = [
    "sample_id",
    "dataset_source",
    "input_type",
    "time_index",
    "frequency_band",
    "tx_id",
    "rx_id",
    "modulation_label",
    "occupancy_label",
    "abnormal_event_label",
    "domain_id",
    "synthetic_mission_context",
    "situation_label",
    "threat_level",
    "human_review_required",
]


@dataclass(slots=True)
class MetadataRecord:
    """One row in the OpenEW-SA unified metadata table."""

    sample_id: str
    dataset_source: str
    input_type: str
    time_index: str | int | float | None = None
    frequency_band: str | None = None
    tx_id: str | None = None
    rx_id: str | None = None
    modulation_label: str | None = None
    occupancy_label: str | int | None = None
    abnormal_event_label: str | None = None
    domain_id: str | None = None
    synthetic_mission_context: str | None = None
    situation_label: str | None = None
    threat_level: int | str | None = None
    human_review_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Return the record as a dictionary ordered by the metadata schema."""

        data = asdict(self)
        return {column: data.get(column) for column in METADATA_COLUMNS}


def records_to_frame(records: list[MetadataRecord]) -> pd.DataFrame:
    """Create a schema-ordered metadata frame from records."""

    return pd.DataFrame([record.to_dict() for record in records], columns=METADATA_COLUMNS)


def validate_metadata_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate required columns and return a schema-ordered copy."""

    missing = [column for column in METADATA_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Metadata is missing required columns: {missing}")
    return frame.loc[:, METADATA_COLUMNS].copy()
