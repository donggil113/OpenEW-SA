"""High-level prospective collection quality checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .provenance import ProvenanceSidecar
from .schema import AcquisitionRecord
from .validation import ValidationReport, validate_records


@dataclass(frozen=True)
class QualityThresholds:
    max_session_size: int = 100_000
    minimum_receiver_coverage: float = 0.8
    maximum_missing_timestamp_fraction: float = 0.2


def validate_collection_quality(
    records: Sequence[AcquisitionRecord],
    *,
    provenance: ProvenanceSidecar | None = None,
    thresholds: QualityThresholds = QualityThresholds(),
) -> ValidationReport:
    return validate_records(
        records, provenance=provenance, max_session_size=thresholds.max_session_size
    )
