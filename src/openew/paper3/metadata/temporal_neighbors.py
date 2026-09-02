"""Linear-size temporal neighbor structures with optional causal semantics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Sequence

import numpy as np

from .schema import AcquisitionRecord


@dataclass(frozen=True)
class TemporalNeighborPlan:
    source_indices: np.ndarray
    destination_indices: np.ndarray
    isolated_nodes: np.ndarray
    causal: bool


def build_temporal_neighbors(
    records: Sequence[AcquisitionRecord],
    *,
    neighbor_count: int = 1,
    causal: bool = True,
    partition_by_sample: Mapping[str, str] | None = None,
) -> TemporalNeighborPlan:
    if neighbor_count <= 0:
        raise ValueError("neighbor_count must be positive")
    if any(record.timestamp_utc is None for record in records):
        raise ValueError("All temporal-neighbor records require timestamp_utc")
    if len({record.sample_id for record in records}) != len(records):
        raise ValueError("Duplicate sample IDs are forbidden")
    groups: dict[tuple[str, str, str | None], list[int]] = {}
    for index, record in enumerate(records):
        partition = "all" if partition_by_sample is None else partition_by_sample[record.sample_id]
        groups.setdefault(
            (str(partition), record.acquisition_session_id, record.clock_reset_id), []
        ).append(index)
    sources: list[int] = []
    destinations: list[int] = []
    connected: set[int] = set()
    for indices in groups.values():
        ordered = sorted(
            indices,
            key=lambda index: (
                _timestamp(records[index].timestamp_utc),
                records[index].within_capture_index,
                records[index].sample_id,
            ),
        )
        for position, destination in enumerate(ordered):
            left = max(0, position - neighbor_count)
            right = position if causal else min(len(ordered), position + neighbor_count + 1)
            candidates = ordered[left:right]
            if not causal:
                candidates = [index for index in candidates if index != destination]
            for source in candidates:
                if source == destination:
                    continue
                sources.append(source)
                destinations.append(destination)
                connected.update((source, destination))
    isolated = sorted(set(range(len(records))) - connected)
    return TemporalNeighborPlan(
        np.asarray(sources, dtype=np.int64),
        np.asarray(destinations, dtype=np.int64),
        np.asarray(isolated, dtype=np.int64),
        causal,
    )


def _timestamp(value: str | None) -> datetime:
    if value is None:
        raise ValueError("timestamp is required")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
