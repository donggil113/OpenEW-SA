"""Deterministic target-free deployment episode construction."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Iterable, Mapping, Sequence

from .leakage import EligibilityEngine
from .schema import AcquisitionRecord


@dataclass(frozen=True)
class Episode:
    episode_id: str
    sample_indices: tuple[int, ...]
    relation_fields: tuple[str, ...]
    partition: str


@dataclass(frozen=True)
class EpisodePlan:
    sample_ids: tuple[str, ...]
    episodes: tuple[Episode, ...]
    isolated_indices: tuple[int, ...]
    max_episode_size: int


def build_episodes(
    records: Sequence[AcquisitionRecord],
    episode_fields: Iterable[str],
    *,
    eligibility: EligibilityEngine,
    explicit_whitelist: Iterable[str],
    max_episode_size: int,
    seed: int,
    partition_by_sample: Mapping[str, str] | None = None,
) -> EpisodePlan:
    fields = eligibility.require_relation_fields(episode_fields, explicit_whitelist)
    if not fields:
        raise ValueError("At least one episode field is required")
    if max_episode_size <= 0:
        raise ValueError("max_episode_size must be positive")
    if len({record.sample_id for record in records}) != len(records):
        raise ValueError("Duplicate sample_id values are forbidden")
    partitions = {
        record.sample_id: "all" if partition_by_sample is None else partition_by_sample[record.sample_id]
        for record in records
    }
    grouped: dict[tuple[str, tuple[str, ...]], list[int]] = {}
    isolated: list[int] = []
    for index, record in enumerate(records):
        values = tuple(getattr(record, field) for field in fields)
        if any(value in (None, "") for value in values):
            isolated.append(index)
            continue
        grouped.setdefault(
            (str(partitions[record.sample_id]), tuple(str(value) for value in values)), []
        ).append(index)
    episodes: list[Episode] = []
    for (partition, values), indices in sorted(grouped.items()):
        ordered = sorted(
            indices,
            key=lambda index: hashlib.sha256(
                f"{seed}|{partition}|{'|'.join(values)}|{records[index].sample_id}".encode(
                    "utf-8"
                )
            ).hexdigest(),
        )
        for chunk_index, start in enumerate(range(0, len(ordered), max_episode_size)):
            chunk = tuple(ordered[start : start + max_episode_size])
            digest = hashlib.sha256(
                f"{partition}|{'|'.join(values)}|{seed}|{chunk_index}".encode("utf-8")
            ).hexdigest()[:16]
            episodes.append(Episode(digest, chunk, fields, partition))
    return EpisodePlan(
        sample_ids=tuple(record.sample_id for record in records),
        episodes=tuple(episodes),
        isolated_indices=tuple(sorted(isolated)),
        max_episode_size=max_episode_size,
    )
