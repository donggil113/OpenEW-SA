"""Deterministic, label-independent, partition-local receiver episodes."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np


def _hash_key(*values: object) -> bytes:
    return hashlib.sha256("\x1f".join(str(value) for value in values).encode("utf-8")).digest()


@dataclass(frozen=True)
class ContextEpisodes:
    episodes: tuple[tuple[int, ...], ...]
    context_size: int
    shuffled: bool
    partition: str

    @property
    def sample_count(self) -> int:
        return sum(len(episode) for episode in self.episodes)

    @property
    def isolated_count(self) -> int:
        return sum(len(episode) == 1 for episode in self.episodes)


def build_context_episodes(
    indices: Sequence[int] | np.ndarray,
    receiver_ids: Sequence[str] | np.ndarray,
    sample_ids: Sequence[str] | np.ndarray,
    *,
    context_size: int,
    seed: int,
    partition: str,
    shuffled: bool = False,
) -> ContextEpisodes:
    """Chunk a partition into unordered episodes without labels or model outputs."""

    if context_size <= 0:
        raise ValueError("context_size must be positive")
    indices = [int(value) for value in indices]
    if len(indices) != len(set(indices)):
        raise ValueError("partition indices must be unique")
    groups: dict[str, list[int]] = {}
    for index in indices:
        receiver = str(receiver_ids[index])
        groups.setdefault(receiver, []).append(index)
    for receiver, group in groups.items():
        group.sort(key=lambda index: _hash_key("actual", seed, partition, receiver, str(sample_ids[index])))
    if shuffled:
        sizes = [len(groups[key]) for key in sorted(groups)]
        pooled = sorted(
            indices,
            key=lambda index: _hash_key("shuffled", seed, partition, str(sample_ids[index])),
        )
        shuffled_groups: list[list[int]] = []
        offset = 0
        for size in sizes:
            shuffled_groups.append(pooled[offset : offset + size])
            offset += size
        grouped_values = shuffled_groups
    else:
        grouped_values = [groups[key] for key in sorted(groups)]
    episodes: list[tuple[int, ...]] = []
    for group in grouped_values:
        for offset in range(0, len(group), context_size):
            episodes.append(tuple(group[offset : offset + context_size]))
    flattened = [index for episode in episodes for index in episode]
    if len(flattened) != len(indices) or set(flattened) != set(indices):
        raise RuntimeError("context construction did not preserve every partition sample exactly once")
    return ContextEpisodes(tuple(episodes), context_size, shuffled, partition)


def retained_nodes(
    episode: Sequence[int],
    sample_ids: Sequence[str] | np.ndarray,
    *,
    retention: float,
    seed: int,
) -> tuple[int, ...]:
    """Select context contributors independently of labels while preserving anchors."""

    if retention < 0.0 or retention > 1.0:
        raise ValueError("retention must be in [0, 1]")
    if retention == 0.0 or not episode:
        return ()
    count = int(np.ceil(len(episode) * retention))
    ranked = sorted(
        (int(index) for index in episode),
        key=lambda index: _hash_key("retention", seed, str(sample_ids[index])),
    )
    return tuple(ranked[:count])


def pad_episode_batch(
    episodes: Sequence[Sequence[int]],
    *,
    sample_ids: Sequence[str] | np.ndarray,
    retention: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if not episodes:
        raise ValueError("cannot pad an empty episode batch")
    width = max(len(episode) for episode in episodes)
    indices = np.zeros((len(episodes), width), dtype=np.int64)
    valid = np.zeros((len(episodes), width), dtype=bool)
    retained = np.zeros((len(episodes), width), dtype=bool)
    for row, episode in enumerate(episodes):
        indices[row, : len(episode)] = episode
        valid[row, : len(episode)] = True
        keep = set(retained_nodes(episode, sample_ids, retention=retention, seed=seed))
        retained[row, : len(episode)] = [index in keep for index in episode]
    return indices, valid, retained


def episode_statistics(episodes: ContextEpisodes) -> dict[str, float | int | bool | str]:
    sizes = np.asarray([len(episode) for episode in episodes.episodes], dtype=np.int64)
    covered = int(sizes[sizes > 1].sum())
    return {
        "partition": episodes.partition,
        "shuffled": episodes.shuffled,
        "context_size": episodes.context_size,
        "episode_count": len(episodes.episodes),
        "sample_count": int(sizes.sum()),
        "isolated_anchor_count": int((sizes == 1).sum()),
        "isolated_anchor_fraction": float((sizes == 1).sum() / sizes.sum()) if sizes.sum() else 0.0,
        "relation_coverage": float(covered / sizes.sum()) if sizes.sum() else 0.0,
        "episode_size_min": int(sizes.min()) if len(sizes) else 0,
        "episode_size_median": float(np.median(sizes)) if len(sizes) else 0.0,
        "episode_size_mean": float(sizes.mean()) if len(sizes) else 0.0,
        "episode_size_max": int(sizes.max()) if len(sizes) else 0,
    }
