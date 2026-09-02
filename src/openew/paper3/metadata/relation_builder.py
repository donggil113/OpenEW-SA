"""Efficient target-free equality and interval relation construction."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Iterable, Mapping, Sequence

import numpy as np

from .enums import Eligibility
from .leakage import EligibilityEngine
from .schema import AcquisitionRecord


@dataclass(frozen=True)
class RelationTypeIncidence:
    relation_type: str
    group_offsets: np.ndarray
    node_indices: np.ndarray
    group_value_hashes: tuple[str, ...]
    isolated_nodes: np.ndarray

    @property
    def group_count(self) -> int:
        return max(0, len(self.group_offsets) - 1)

    @property
    def incidence_count(self) -> int:
        return len(self.node_indices)

    def groups(self) -> tuple[np.ndarray, ...]:
        return tuple(
            self.node_indices[self.group_offsets[index] : self.group_offsets[index + 1]]
            for index in range(self.group_count)
        )


@dataclass(frozen=True)
class RelationPlan:
    sample_ids: tuple[str, ...]
    relation_types: tuple[RelationTypeIncidence, ...]

    @property
    def storage_entries(self) -> int:
        return sum(
            len(item.node_indices) + len(item.group_offsets) + len(item.isolated_nodes)
            for item in self.relation_types
        )


def build_equality_relations(
    records: Sequence[AcquisitionRecord],
    relation_fields: Iterable[str],
    *,
    eligibility: EligibilityEngine,
    explicit_whitelist: Iterable[str],
    partition_by_sample: Mapping[str, str] | None = None,
) -> RelationPlan:
    """Build typed incidence groups without labels or pairwise cliques."""

    fields = eligibility.require_relation_fields(relation_fields, explicit_whitelist)
    _ensure_unique_samples(records)
    partitions = _partitions(records, partition_by_sample)
    relation_types: list[RelationTypeIncidence] = []
    for field in fields:
        grouped: dict[tuple[str, str], list[int]] = {}
        isolated: list[int] = []
        for index, record in enumerate(records):
            value = getattr(record, field)
            if value in (None, ""):
                isolated.append(index)
                continue
            grouped.setdefault((partitions[index], str(value)), []).append(index)
        relation_types.append(_incidence(field, grouped, isolated))
    return RelationPlan(tuple(record.sample_id for record in records), tuple(relation_types))


def build_frequency_overlap_relations(
    records: Sequence[AcquisitionRecord],
    *,
    eligibility: EligibilityEngine,
    explicit_whitelist: Iterable[str],
    partition_by_sample: Mapping[str, str] | None = None,
) -> RelationPlan:
    """Build connected interval-overlap groups in O(N log N).

    Both lower and upper frequency fields must be explicitly classified and whitelisted as
    RELATION_ALLOWED. The default policy does not allow them as relations.
    """

    fields = ("lower_frequency_hz", "upper_frequency_hz")
    eligibility.require_relation_fields(fields, explicit_whitelist)
    _ensure_unique_samples(records)
    partitions = _partitions(records, partition_by_sample)
    groups: dict[tuple[str, str], list[int]] = {}
    isolated: list[int] = []
    by_partition: dict[str, list[tuple[float, float, int]]] = {}
    for index, record in enumerate(records):
        lower, upper = record.lower_frequency_hz, record.upper_frequency_hz
        if lower is None or upper is None:
            isolated.append(index)
            continue
        by_partition.setdefault(partitions[index], []).append((lower, upper, index))
    for partition, intervals in sorted(by_partition.items()):
        ordered = sorted(intervals, key=lambda item: (item[0], item[1], item[2]))
        component: list[int] = []
        component_upper: float | None = None
        component_index = 0
        for lower, upper, index in ordered:
            if component_upper is None or lower <= component_upper:
                component.append(index)
                component_upper = upper if component_upper is None else max(component_upper, upper)
            else:
                groups[(partition, f"component_{component_index}")] = component
                component_index += 1
                component = [index]
                component_upper = upper
        if component:
            groups[(partition, f"component_{component_index}")] = component
    return RelationPlan(
        tuple(record.sample_id for record in records),
        (_incidence("frequency_overlap", groups, isolated),),
    )


def _incidence(
    relation_type: str,
    grouped: Mapping[tuple[str, str], Sequence[int]],
    isolated: Sequence[int],
) -> RelationTypeIncidence:
    offsets = [0]
    nodes: list[int] = []
    hashes: list[str] = []
    extra_isolated = list(isolated)
    for (partition, value), indices in sorted(grouped.items()):
        ordered = sorted(int(index) for index in indices)
        if len(ordered) < 2:
            extra_isolated.extend(ordered)
            continue
        nodes.extend(ordered)
        offsets.append(len(nodes))
        hashes.append(
            hashlib.sha256(f"{relation_type}|{partition}|{value}".encode("utf-8")).hexdigest()
        )
    return RelationTypeIncidence(
        relation_type=relation_type,
        group_offsets=np.asarray(offsets, dtype=np.int64),
        node_indices=np.asarray(nodes, dtype=np.int64),
        group_value_hashes=tuple(hashes),
        isolated_nodes=np.asarray(sorted(set(extra_isolated)), dtype=np.int64),
    )


def _partitions(
    records: Sequence[AcquisitionRecord], mapping: Mapping[str, str] | None
) -> tuple[str, ...]:
    if mapping is None:
        return tuple("all" for _ in records)
    missing = sorted(record.sample_id for record in records if record.sample_id not in mapping)
    if missing:
        raise ValueError(f"Missing partition assignments for samples: {missing[:5]}")
    return tuple(str(mapping[record.sample_id]) for record in records)


def _ensure_unique_samples(records: Sequence[AcquisitionRecord]) -> None:
    identifiers = [record.sample_id for record in records]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Duplicate sample_id values are forbidden")
