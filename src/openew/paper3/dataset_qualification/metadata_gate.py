"""Adapter to the frozen PR #82 metadata readiness thresholds."""

from __future__ import annotations

from dataclasses import dataclass

from openew.paper3.metadata.enums import TemporalVerdict
from openew.paper3.metadata.readiness import RelationReadiness, build_readiness_scorecard

from .temporal_gate import CandidateTemporalStatus


@dataclass(frozen=True)
class CandidateRelationEvidence:
    field: str
    coverage: float
    repeated_group_fraction: float
    target_proxy_rejected: bool
    independently_verified: bool
    true_multi_node_relation: bool = False


def evaluate_metadata_readiness(
    relations: tuple[CandidateRelationEvidence, ...],
    *,
    temporal_status: CandidateTemporalStatus,
    mixed_target_episode_fraction: float,
) -> dict[str, object]:
    mapped = tuple(
        RelationReadiness(
            field=item.field,
            coverage=item.coverage,
            repeated_group_fraction=item.repeated_group_fraction,
            target_proxy_rejected=item.target_proxy_rejected,
            independently_verified=item.independently_verified,
            true_multi_node_relation=item.true_multi_node_relation,
        )
        for item in relations
    )
    temporal = (
        TemporalVerdict.VALID_TEMPORAL_CONTEXT
        if temporal_status is CandidateTemporalStatus.VALID_TEMPORAL_CONTEXT
        else TemporalVerdict.UNRESOLVED
    )
    return build_readiness_scorecard(
        mapped,
        temporal_verdict=temporal,
        mixed_target_episode_fraction=mixed_target_episode_fraction,
        minimum_coverage=0.8,
        minimum_repeated_group_fraction=0.5,
    ).to_mapping()
