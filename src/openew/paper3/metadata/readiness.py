"""Performance-independent metadata readiness scorecards."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from .enums import ReadinessLevel, TemporalVerdict


@dataclass(frozen=True)
class RelationReadiness:
    field: str
    coverage: float
    repeated_group_fraction: float
    target_proxy_rejected: bool
    independently_verified: bool
    true_multi_node_relation: bool = False


@dataclass(frozen=True)
class ReadinessScorecard:
    highest_level: ReadinessLevel
    eligible_levels: tuple[ReadinessLevel, ...]
    relation_count: int
    temporal_verdict: TemporalVerdict
    reasons: tuple[str, ...]

    def to_mapping(self) -> dict[str, object]:
        result = asdict(self)
        result["highest_level"] = self.highest_level.value
        result["eligible_levels"] = [level.value for level in self.eligible_levels]
        result["temporal_verdict"] = self.temporal_verdict.value
        return result


def build_readiness_scorecard(
    relations: Iterable[RelationReadiness],
    *,
    temporal_verdict: TemporalVerdict,
    mixed_target_episode_fraction: float,
    minimum_coverage: float = 0.8,
    minimum_repeated_group_fraction: float = 0.5,
) -> ReadinessScorecard:
    safe = [
        relation
        for relation in relations
        if relation.independently_verified
        and relation.target_proxy_rejected
        and relation.coverage >= minimum_coverage
        and relation.repeated_group_fraction >= minimum_repeated_group_fraction
    ]
    levels = [ReadinessLevel.INDEPENDENT_SAMPLE_ONLY]
    reasons = ["independent-sample analysis does not require relational metadata"]
    if safe:
        levels.append(ReadinessLevel.STATIC_RELATIONAL)
        reasons.append(f"{len(safe)} relation type(s) satisfy structural safety thresholds")
    if len(safe) >= 2 or any(relation.true_multi_node_relation for relation in safe):
        levels.append(ReadinessLevel.STATIC_HYPERGRAPH)
        reasons.append("at least two safe relation types or one verified multi-node relation exists")
    temporal_ok = (
        temporal_verdict is TemporalVerdict.VALID_TEMPORAL_CONTEXT
        and mixed_target_episode_fraction > 0
    )
    if temporal_ok:
        levels.append(ReadinessLevel.TEMPORAL_RELATIONAL)
        reasons.append("temporal context and mixed-target episodes are structurally validated")
    if temporal_ok and len(safe) >= 2:
        levels.append(ReadinessLevel.DYNAMIC_HYPERGRAPH)
        reasons.append("temporal criteria and at least two safe relation types are satisfied")
    return ReadinessScorecard(levels[-1], tuple(levels), len(safe), temporal_verdict, tuple(reasons))
