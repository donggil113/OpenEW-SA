"""Typed hypergraph incidence views without clique expansion."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .relation_builder import RelationPlan


@dataclass(frozen=True)
class TypedHypergraphIncidence:
    node_count: int
    relation_type_names: tuple[str, ...]
    type_offsets: np.ndarray
    group_offsets: np.ndarray
    node_indices: np.ndarray
    isolated_nodes_by_type: tuple[np.ndarray, ...]

    @property
    def group_count(self) -> int:
        return max(0, len(self.group_offsets) - 1)


def to_typed_hypergraph(plan: RelationPlan) -> TypedHypergraphIncidence:
    type_offsets = [0]
    group_offsets = [0]
    node_indices: list[int] = []
    group_count = 0
    isolated: list[np.ndarray] = []
    for relation in plan.relation_types:
        for group in relation.groups():
            node_indices.extend(int(value) for value in group)
            group_offsets.append(len(node_indices))
            group_count += 1
        type_offsets.append(group_count)
        isolated.append(relation.isolated_nodes.copy())
    return TypedHypergraphIncidence(
        node_count=len(plan.sample_ids),
        relation_type_names=tuple(item.relation_type for item in plan.relation_types),
        type_offsets=np.asarray(type_offsets, dtype=np.int64),
        group_offsets=np.asarray(group_offsets, dtype=np.int64),
        node_indices=np.asarray(node_indices, dtype=np.int64),
        isolated_nodes_by_type=tuple(isolated),
    )
