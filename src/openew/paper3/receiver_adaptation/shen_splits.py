"""Payload-independent Shen LOSO and support/query planning."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Mapping, Sequence

from .shen_adapter import SHEN_RECEIVERS, ShenSample

SHEN_SEEDS = (829, 1829, 2829, 3829, 4829)


def _digest(*values: object, namespace: str) -> str:
    return hashlib.sha256("\0".join([namespace, *(str(value) for value in values)]).encode()).hexdigest()


@dataclass(frozen=True)
class ShenLosoSplit:
    test_receiver: str
    validation_receivers: tuple[str, ...]
    train_receivers: tuple[str, ...]

    def validate(self) -> "ShenLosoSplit":
        roles = [set(self.train_receivers), set(self.validation_receivers), {self.test_receiver}]
        if any(roles[left] & roles[right] for left in range(3) for right in range(left + 1, 3)):
            raise ValueError("receiver crosses LOSO roles")
        if set.union(*roles) != set(SHEN_RECEIVERS):
            raise ValueError("LOSO split does not cover exactly the documented receivers")
        return self


@dataclass(frozen=True)
class ShenSupportQuery:
    receiver_id: str
    support_sample_ids: tuple[str, ...]
    query_sample_ids: tuple[str, ...]
    requested_budget: int

    def validate(self) -> "ShenSupportQuery":
        if set(self.support_sample_ids) & set(self.query_sample_ids):
            raise ValueError("support/query overlap")
        if len(set(self.support_sample_ids)) != len(self.support_sample_ids):
            raise ValueError("duplicate support sample")
        if not self.query_sample_ids:
            raise ValueError("query pool must be nonempty")
        return self


def build_loso_splits(validation_count: int = 3) -> tuple[ShenLosoSplit, ...]:
    if validation_count <= 0 or validation_count >= len(SHEN_RECEIVERS) - 1:
        raise ValueError("invalid validation receiver count")
    rows: list[ShenLosoSplit] = []
    for test_receiver in SHEN_RECEIVERS:
        candidates = [value for value in SHEN_RECEIVERS if value != test_receiver]
        ordered = sorted(candidates, key=lambda value: _digest(test_receiver, value, namespace="shen-source-validation-v1"))
        validation = tuple(sorted(ordered[:validation_count]))
        train = tuple(sorted(set(candidates) - set(validation)))
        rows.append(ShenLosoSplit(test_receiver, validation, train).validate())
    return tuple(rows)


def freeze_support_query(samples: Sequence[ShenSample], receiver_id: str, *, budget: int = 128, seed: int = 829) -> ShenSupportQuery:
    if budget <= 0:
        raise ValueError("support budget must be positive")
    candidates = [row.sample_id for row in samples if row.receiver_id == receiver_id]
    if len(candidates) <= 1:
        raise ValueError("receiver lacks query-supportable data")
    ordered = sorted(candidates, key=lambda value: _digest(seed, receiver_id, value, namespace="shen-support-v1"))
    count = min(budget, len(ordered) - 1)
    return ShenSupportQuery(receiver_id, tuple(ordered[:count]), tuple(ordered[count:]), budget).validate()


def support_ids_from_acquisition_rows(rows: Sequence[Mapping[str, object]], receiver_id: str, *, budget: int = 128, seed: int = 829) -> tuple[str, ...]:
    allowed = {"sample_id", "receiver_id", "hardware_family", "source_record_index", "sample_rate_hz", "center_frequency_hz"}
    for row in rows:
        forbidden = set(row) - allowed
        if forbidden:
            raise ValueError(f"unknown/annotation acquisition fields fail closed: {sorted(forbidden)}")
    candidates = [str(row["sample_id"]) for row in rows if str(row["receiver_id"]) == receiver_id]
    if len(candidates) <= budget:
        raise ValueError("insufficient receiver rows for requested support and query")
    return tuple(sorted(candidates, key=lambda value: _digest(seed, receiver_id, value, namespace="shen-support-v1"))[:budget])
