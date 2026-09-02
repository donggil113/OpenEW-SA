"""Evidence-only temporal/session qualification."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CandidateTemporalStatus(str, Enum):
    VALID_TEMPORAL_CONTEXT = "VALID_TEMPORAL_CONTEXT"
    ORDER_ONLY_NO_CLOCK = "ORDER_ONLY_NO_CLOCK"
    COARSE_DAY_ONLY = "COARSE_DAY_ONLY"
    TARGET_NESTED_SEQUENCE = "TARGET_NESTED_SEQUENCE"
    UNKNOWN = "UNKNOWN"
    NO_TEMPORAL_CONTEXT = "NO_TEMPORAL_CONTEXT"


@dataclass(frozen=True)
class CandidateTemporalEvidence:
    explicit_acquisition_timestamp: bool | None
    physical_order_preserved: bool | None
    session_boundaries_verified: bool | None
    clock_reset_semantics_verified: bool | None
    gap_meaning_verified: bool | None
    inference_time_available: bool | None
    coarse_day_only: bool
    filesystem_mtime_only: bool
    container_target_pure: bool | None
    mixed_target_episode_fraction: float | None


@dataclass(frozen=True)
class TemporalGateResult:
    status: CandidateTemporalStatus
    reasons: tuple[str, ...]


def evaluate_temporal(evidence: CandidateTemporalEvidence) -> TemporalGateResult:
    if evidence.filesystem_mtime_only:
        return TemporalGateResult(
            CandidateTemporalStatus.NO_TEMPORAL_CONTEXT,
            ("filesystem mtime is system metadata, not acquisition time",),
        )
    if evidence.coarse_day_only:
        return TemporalGateResult(
            CandidateTemporalStatus.COARSE_DAY_ONLY,
            ("only coarse day/domain context is verified",),
        )
    if evidence.container_target_pure is True:
        return TemporalGateResult(
            CandidateTemporalStatus.TARGET_NESTED_SEQUENCE,
            ("order is nested inside a target-pure container",),
        )
    if evidence.physical_order_preserved is True and evidence.explicit_acquisition_timestamp is not True:
        return TemporalGateResult(
            CandidateTemporalStatus.ORDER_ONLY_NO_CLOCK,
            ("physical order exists without an acquisition clock",),
        )
    required = (
        evidence.explicit_acquisition_timestamp,
        evidence.physical_order_preserved,
        evidence.session_boundaries_verified,
        evidence.clock_reset_semantics_verified,
        evidence.gap_meaning_verified,
        evidence.inference_time_available,
    )
    if all(value is True for value in required):
        if evidence.mixed_target_episode_fraction is not None and evidence.mixed_target_episode_fraction > 0:
            return TemporalGateResult(
                CandidateTemporalStatus.VALID_TEMPORAL_CONTEXT,
                ("clock, order, sessions, gaps, deployment access, and mixed-target episodes are verified",),
            )
        if evidence.mixed_target_episode_fraction == 0:
            return TemporalGateResult(
                CandidateTemporalStatus.TARGET_NESTED_SEQUENCE,
                ("verified sequences contain no mixed-target episodes",),
            )
    if all(value in (False, None) for value in required[:2]):
        if all(value is False for value in required[:2]):
            return TemporalGateResult(
                CandidateTemporalStatus.NO_TEMPORAL_CONTEXT,
                ("neither acquisition timestamps nor physical order are available",),
            )
    return TemporalGateResult(
        CandidateTemporalStatus.UNKNOWN,
        ("one or more temporal evidence requirements remain unknown or false",),
    )
