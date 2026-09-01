"""Deterministic bounded equality contexts without clique materialization."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from openew.paper3.static_relational.relation_contract import relation_fields, validate_relation_types


@dataclass(frozen=True)
class ContextBatch:
    support_positions: np.ndarray
    anchor_positions_in_support: np.ndarray
    member_positions_by_type: dict[str, np.ndarray]


@dataclass
class RelationPlan:
    dataset: str
    partition: str
    relation_types: tuple[str, ...]
    sample_ids: np.ndarray
    group_ids_by_type: dict[str, np.ndarray]
    members_by_type: dict[str, dict[int, np.ndarray]]
    statistics: dict[str, Any]
    max_context_size: int

    @property
    def n_nodes(self) -> int:
        return len(self.sample_ids)

    @property
    def storage_items(self) -> int:
        group_items = sum(len(values) for values in self.group_ids_by_type.values())
        member_items = sum(
            sum(len(members) for members in groups.values())
            for groups in self.members_by_type.values()
        )
        return group_items + member_items


def build_relation_plan(
    metadata: pd.DataFrame,
    dataset: str,
    partition: str,
    relation_types: tuple[str, ...] | list[str],
    seed: int,
    max_context_size: int,
    retention: float = 1.0,
    shuffled: bool = False,
) -> RelationPlan:
    relation_types = validate_relation_types(dataset, relation_types)
    if not 0.0 <= float(retention) <= 1.0:
        raise ValueError(f"Relation retention must be in [0, 1], got {retention}")
    if max_context_size < 2:
        raise ValueError("max_context_size must be at least 2")
    if "sample_id" not in metadata:
        raise ValueError("Relation construction requires sample_id")
    sample_ids = metadata["sample_id"].astype(str).to_numpy()
    group_ids_by_type: dict[str, np.ndarray] = {}
    members_by_type: dict[str, dict[int, np.ndarray]] = {}
    type_stats: dict[str, dict[str, Any]] = {}

    for relation_type in relation_types:
        fields = relation_fields(dataset, relation_type)
        missing = [field for field in fields if field not in metadata]
        if missing:
            raise ValueError(f"Missing relation fields for {relation_type}: {missing}")
        columns = [metadata[field].astype(str).to_numpy() for field in fields]
        values = np.asarray(["\x1f".join(items) for items in zip(*columns)], dtype=object)
        if any(not str(value).strip() for value in values):
            raise ValueError(f"Empty relation value in {dataset}/{partition}/{relation_type}")
        if shuffled:
            generator = np.random.default_rng(_hash_int(dataset, partition, relation_type, seed, "shuffle"))
            values = values[generator.permutation(len(values))]
        raw_groups: dict[str, list[int]] = {}
        for position, value in enumerate(values.tolist()):
            raw_groups.setdefault(str(value), []).append(position)
        retained = np.asarray(
            [
                retention >= 1.0
                or (
                    retention > 0.0
                    and _hash_fraction(dataset, partition, relation_type, sample_id, seed, "retain") < retention
                )
                for sample_id in sample_ids
            ],
            dtype=bool,
        )
        group_ids = np.full(len(metadata), -1, dtype=np.int64)
        members: dict[int, np.ndarray] = {}
        next_group = 0
        raw_sizes: list[int] = []
        truncated_nodes = 0
        for value in sorted(raw_groups):
            raw = np.asarray(raw_groups[value], dtype=np.int64)
            raw_sizes.append(len(raw))
            if len(raw) > max_context_size:
                truncated_nodes += len(raw)
            kept = raw[retained[raw]]
            ordered = sorted(
                kept.tolist(),
                key=lambda position: _stable_hex(
                    dataset, partition, relation_type, value, sample_ids[position], seed, "chunk"
                ),
            )
            for start in range(0, len(ordered), max_context_size):
                chunk = np.asarray(ordered[start : start + max_context_size], dtype=np.int64)
                if not len(chunk):
                    continue
                group_ids[chunk] = next_group
                members[next_group] = chunk
                next_group += 1
        active_sizes = [len(item) for item in members.values() if len(item) >= 2]
        active_nodes = sum(active_sizes)
        group_ids_by_type[relation_type] = group_ids
        members_by_type[relation_type] = members
        type_stats[relation_type] = {
            "raw_group_count": len(raw_groups),
            "raw_group_size_min": int(min(raw_sizes, default=0)),
            "raw_group_size_mean": float(np.mean(raw_sizes)) if raw_sizes else 0.0,
            "raw_group_size_median": float(np.median(raw_sizes)) if raw_sizes else 0.0,
            "raw_group_size_max": int(max(raw_sizes, default=0)),
            "context_group_count": len(members),
            "active_context_group_count": len(active_sizes),
            "relation_incidence_count": int(retained.sum()),
            "relation_coverage": float(active_nodes / len(metadata)) if len(metadata) else 0.0,
            "context_group_size_min": int(min(active_sizes, default=0)),
            "context_group_size_mean": float(np.mean(active_sizes)) if active_sizes else 0.0,
            "context_group_size_median": float(np.median(active_sizes)) if active_sizes else 0.0,
            "context_group_size_max": int(max(active_sizes, default=0)),
            "context_truncation_rate": float(truncated_nodes / len(metadata)) if len(metadata) else 0.0,
            "retention": float(retention),
            "shuffled": bool(shuffled),
        }

    if relation_types:
        active = np.zeros(len(metadata), dtype=bool)
        for relation_type in relation_types:
            group_ids = group_ids_by_type[relation_type]
            sizes = {group_id: len(nodes) for group_id, nodes in members_by_type[relation_type].items()}
            active |= np.asarray([value >= 0 and sizes.get(int(value), 0) >= 2 for value in group_ids])
    else:
        active = np.zeros(len(metadata), dtype=bool)
    statistics = {
        "dataset": dataset,
        "partition": partition,
        "node_count": len(metadata),
        "relation_types": list(relation_types),
        "relation_coverage": float(active.mean()) if len(active) else 0.0,
        "isolated_node_count": int((~active).sum()),
        "isolated_node_fraction": float((~active).mean()) if len(active) else 0.0,
        "max_context_size": int(max_context_size),
        "per_relation_type": type_stats,
    }
    plan = RelationPlan(
        dataset=dataset,
        partition=partition,
        relation_types=relation_types,
        sample_ids=sample_ids,
        group_ids_by_type=group_ids_by_type,
        members_by_type=members_by_type,
        statistics=statistics,
        max_context_size=max_context_size,
    )
    if plan.storage_items > 2 * max(1, len(relation_types)) * len(metadata):
        raise RuntimeError("Relation plan exceeded the declared O(types x nodes) storage contract")
    return plan


def build_context_batch(plan: RelationPlan, anchor_positions: np.ndarray) -> ContextBatch:
    anchors = np.asarray(anchor_positions, dtype=np.int64)
    if np.any(anchors < 0) or np.any(anchors >= plan.n_nodes):
        raise IndexError("Anchor position outside relation plan")
    support: set[int] = set(anchors.tolist())
    for relation_type in plan.relation_types:
        group_ids = plan.group_ids_by_type[relation_type]
        members = plan.members_by_type[relation_type]
        for group_id in np.unique(group_ids[anchors]):
            if group_id >= 0:
                support.update(members[int(group_id)].tolist())
    support_positions = np.asarray(sorted(support), dtype=np.int64)
    local = {int(position): index for index, position in enumerate(support_positions.tolist())}
    anchor_local = np.asarray([local[int(position)] for position in anchors], dtype=np.int64)
    matrices: dict[str, np.ndarray] = {}
    for relation_type in plan.relation_types:
        matrix = np.full((len(anchors), plan.max_context_size), -1, dtype=np.int64)
        group_ids = plan.group_ids_by_type[relation_type]
        members = plan.members_by_type[relation_type]
        for row, anchor in enumerate(anchors):
            group_id = int(group_ids[anchor])
            if group_id < 0:
                continue
            nodes = members[group_id]
            matrix[row, : len(nodes)] = [local[int(position)] for position in nodes]
        matrices[relation_type] = matrix
    return ContextBatch(support_positions, anchor_local, matrices)


def anchor_batches(
    plan: RelationPlan | None,
    node_count: int,
    batch_size: int,
    seed: int,
    epoch: int,
    shuffle: bool,
) -> list[np.ndarray]:
    generator = np.random.default_rng(_hash_int("anchor_batches", seed, epoch))
    if plan is None or not plan.relation_types:
        order = np.arange(node_count, dtype=np.int64)
        if shuffle:
            generator.shuffle(order)
        return [order[start : start + batch_size] for start in range(0, len(order), batch_size)]
    primary = plan.relation_types[-1]
    groups = [values.copy() for values in plan.members_by_type[primary].values()]
    assigned = np.zeros(node_count, dtype=bool)
    for values in groups:
        assigned[values] = True
        if shuffle:
            generator.shuffle(values)
    isolated = np.flatnonzero(~assigned).astype(np.int64)
    if shuffle:
        generator.shuffle(groups)
        generator.shuffle(isolated)
    batches: list[np.ndarray] = []
    pending: list[int] = []
    for group in groups:
        if pending and len(pending) + len(group) > batch_size:
            batches.append(np.asarray(pending, dtype=np.int64))
            pending = []
        pending.extend(group.tolist())
    if pending:
        batches.append(np.asarray(pending, dtype=np.int64))
    batches.extend(
        isolated[start : start + batch_size] for start in range(0, len(isolated), batch_size)
    )
    if shuffle:
        generator.shuffle(batches)
    flattened = np.concatenate(batches) if batches else np.asarray([], dtype=np.int64)
    if len(flattened) != node_count or len(np.unique(flattened)) != node_count:
        raise RuntimeError("Anchor batching failed to preserve each node exactly once")
    return batches


def _stable_hex(*parts: Any) -> str:
    return hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()


def _hash_int(*parts: Any) -> int:
    return int(_stable_hex(*parts)[:16], 16) % (2**32)


def _hash_fraction(*parts: Any) -> float:
    return int(_stable_hex(*parts)[:16], 16) / float(16**16)
