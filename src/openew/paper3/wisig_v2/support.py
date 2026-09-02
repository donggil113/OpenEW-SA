"""Disjoint, bounded, label-free receiver support/query construction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

from .contracts import PRIMARY_CONTEXT_K, PRIMARY_SUPPORT_BUDGET, validate_support_fields
from .hashing import stable_digest


@dataclass(frozen=True)
class SupportQuerySplit:
    receiver_id: str
    support_indices: tuple[int, ...]
    query_indices: tuple[int, ...]
    requested_budget: int

    @property
    def support_count(self) -> int:
        return len(self.support_indices)

    @property
    def query_count(self) -> int:
        return len(self.query_indices)

    @property
    def full_budget_met(self) -> bool:
        return self.support_count == self.requested_budget

    def validate(self) -> "SupportQuerySplit":
        if set(self.support_indices) & set(self.query_indices):
            raise ValueError("support and query must be disjoint")
        if len(set(self.support_indices)) != len(self.support_indices):
            raise ValueError("support contains duplicate indices")
        if len(set(self.query_indices)) != len(self.query_indices):
            raise ValueError("query contains duplicate indices")
        return self


def freeze_support_query(
    indices: Sequence[int] | np.ndarray,
    sample_ids: Sequence[str] | np.ndarray,
    receiver_ids: Sequence[str] | np.ndarray,
    *,
    receiver_id: str,
    support_budget: int = PRIMARY_SUPPORT_BUDGET,
    seed: int = 829,
) -> SupportQuerySplit:
    """Select fixed support before prediction; annotation values are not accepted."""

    validate_support_fields(("sample_id", "receiver_id"))
    if support_budget <= 0:
        raise ValueError("support_budget must be positive")
    candidates = [int(index) for index in indices if str(receiver_ids[int(index)]) == str(receiver_id)]
    if not candidates:
        raise ValueError(f"no samples for receiver {receiver_id}")
    ordered = sorted(
        candidates,
        key=lambda index: stable_digest(seed, receiver_id, str(sample_ids[index]), namespace="wisig-v2-support"),
    )
    count = min(support_budget, max(0, len(ordered) - 1))
    split = SupportQuerySplit(
        receiver_id=str(receiver_id),
        support_indices=tuple(ordered[:count]),
        query_indices=tuple(ordered[count:]),
        requested_budget=support_budget,
    )
    return split.validate()


def build_query_context_indices(
    query_indices: Sequence[int] | np.ndarray,
    support_indices: Sequence[int] | np.ndarray,
    sample_ids: Sequence[str] | np.ndarray,
    receiver_id: str,
    *,
    k: int = PRIMARY_CONTEXT_K,
    seed: int = 829,
    retention: float = 1.0,
) -> np.ndarray:
    """Return [query, k] peer indices selected only from the frozen support pool."""

    if k <= 0:
        raise ValueError("context k must be positive")
    if retention not in (0.0, 0.25, 0.5, 0.75, 1.0):
        raise ValueError("retention is not prespecified")
    support = tuple(int(value) for value in support_indices)
    if not support and retention > 0:
        raise ValueError("nonzero retention requires support")
    retained_count = min(k, int(round(k * retention)), len(support))
    result = np.full((len(query_indices), k), -1, dtype=np.int64)
    for row, query_index in enumerate(query_indices):
        query_id = str(sample_ids[int(query_index)])
        ordered = sorted(
            support,
            key=lambda support_index: stable_digest(
                seed,
                receiver_id,
                query_id,
                str(sample_ids[support_index]),
                namespace="wisig-v2-query-context",
            ),
        )
        result[row, :retained_count] = ordered[:retained_count]
    return result


def support_query_statistics(split: SupportQuerySplit) -> dict[str, int | float | bool | str]:
    total = split.support_count + split.query_count
    return {
        "receiver_id": split.receiver_id,
        "support_count": split.support_count,
        "query_count": split.query_count,
        "requested_budget": split.requested_budget,
        "full_budget_met": split.full_budget_met,
        "support_fraction": split.support_count / total if total else 0.0,
        "support_query_overlap": 0,
    }


def freeze_all_test_receivers(
    indices: Sequence[int] | np.ndarray,
    sample_ids: Sequence[str] | np.ndarray,
    receiver_ids: Sequence[str] | np.ndarray,
    *,
    budget: int,
    seed: int,
) -> Mapping[str, SupportQuerySplit]:
    receivers = sorted({str(receiver_ids[int(index)]) for index in indices})
    return {
        receiver: freeze_support_query(indices, sample_ids, receiver_ids, receiver_id=receiver, support_budget=budget, seed=seed)
        for receiver in receivers
    }
