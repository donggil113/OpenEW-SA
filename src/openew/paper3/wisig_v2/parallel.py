"""Disjoint receiver-range scheduling for an optional second GPU process."""

from __future__ import annotations

from typing import Sequence

from .runner import RunConfig
from .suite import primary_loso_plan


def receiver_worker_plan(receivers: Sequence[int]) -> list[RunConfig]:
    values = [int(value) for value in receivers]
    if not values or len(values) != len(set(values)) or any(value < 0 or value >= 32 for value in values):
        raise ValueError("worker receivers must be a nonempty unique subset of 0..31")
    by_protocol: dict[str, list[RunConfig]] = {}
    for _, config in primary_loso_plan():
        by_protocol.setdefault(config.protocol_id, []).append(config)
    return [config for receiver in values for config in by_protocol[f"receiver_loso_{receiver:02d}"]]
