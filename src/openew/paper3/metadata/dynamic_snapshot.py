"""Target-free dynamic snapshot boundaries for software contract validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Mapping, Sequence
import hashlib

from .enums import TemporalVerdict
from .schema import AcquisitionRecord


@dataclass(frozen=True)
class DynamicSnapshot:
    snapshot_id: str
    session_id: str
    partition: str
    sample_indices: tuple[int, ...]
    start_time_utc: str
    end_time_utc: str


def build_dynamic_snapshots(
    records: Sequence[AcquisitionRecord],
    *,
    temporal_verdict: TemporalVerdict,
    window_seconds: float,
    partition_by_sample: Mapping[str, str] | None = None,
) -> tuple[DynamicSnapshot, ...]:
    if temporal_verdict is not TemporalVerdict.VALID_TEMPORAL_CONTEXT:
        raise ValueError("Dynamic snapshots require VALID_TEMPORAL_CONTEXT")
    if window_seconds <= 0:
        raise ValueError("window_seconds must be positive")
    groups: dict[tuple[str, str, str | None], list[int]] = {}
    for index, record in enumerate(records):
        if record.timestamp_utc is None:
            raise ValueError("Dynamic snapshots require timestamp_utc")
        partition = "all" if partition_by_sample is None else partition_by_sample[record.sample_id]
        groups.setdefault(
            (str(partition), record.acquisition_session_id, record.clock_reset_id), []
        ).append(index)
    result: list[DynamicSnapshot] = []
    width = timedelta(seconds=window_seconds)
    for (partition, session, reset), indices in sorted(groups.items()):
        ordered = sorted(indices, key=lambda index: _time(records[index].timestamp_utc))
        start = _time(records[ordered[0]].timestamp_utc)
        bins: dict[int, list[int]] = {}
        for index in ordered:
            offset = _time(records[index].timestamp_utc) - start
            bin_index = int(offset.total_seconds() // window_seconds)
            bins.setdefault(bin_index, []).append(index)
        for bin_index, sample_indices in sorted(bins.items()):
            window_start = start + bin_index * width
            window_end = window_start + width
            digest = hashlib.sha256(
                f"{partition}|{session}|{reset}|{bin_index}".encode("utf-8")
            ).hexdigest()[:16]
            result.append(
                DynamicSnapshot(
                    digest,
                    session,
                    partition,
                    tuple(sample_indices),
                    window_start.isoformat(),
                    window_end.isoformat(),
                )
            )
    return tuple(result)


def _time(value: str | None) -> datetime:
    if value is None:
        raise ValueError("timestamp is required")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
