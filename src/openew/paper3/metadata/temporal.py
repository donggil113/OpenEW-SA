"""Evidence-gated temporal feasibility audits."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from .enums import TemporalVerdict
from .schema import AcquisitionRecord


@dataclass(frozen=True)
class TemporalEvidence:
    field: str
    physical_order_verified: bool
    session_reset_semantics_verified: bool
    gaps_have_defined_meaning: bool
    inference_time_available: bool
    container_target_pure: bool
    filesystem_timestamp_only: bool = False
    coarse_date_only: bool = False
    mixed_target_episode_fraction: float | None = None


@dataclass(frozen=True)
class TemporalAudit:
    field: str
    verdict: TemporalVerdict
    populated_fraction: float
    monotonic_session_fraction: float | None
    duplicate_timestamp_count: int
    negative_gap_count: int
    reasons: tuple[str, ...]


def audit_temporal_field(
    records: Sequence[AcquisitionRecord], evidence: TemporalEvidence
) -> TemporalAudit:
    if not records:
        return TemporalAudit(
            evidence.field,
            TemporalVerdict.NO_TEMPORAL_METADATA,
            0.0,
            None,
            0,
            0,
            ("no records",),
        )
    values = [getattr(record, evidence.field, None) for record in records]
    populated = sum(value not in (None, "") for value in values) / len(records)
    duplicate_count = 0
    negative_count = 0
    monotonic: list[bool] = []
    if evidence.field == "timestamp_utc":
        by_session: dict[tuple[str, str | None], list[AcquisitionRecord]] = {}
        for record in records:
            if record.timestamp_utc is None:
                continue
            by_session.setdefault(
                (record.acquisition_session_id, record.clock_reset_id), []
            ).append(record)
        for group in by_session.values():
            ordered = sorted(group, key=lambda item: item.within_capture_index)
            timestamps = [_parse_timestamp(item.timestamp_utc) for item in ordered]
            duplicate_count += len(timestamps) - len(set(timestamps))
            negatives = sum(left > right for left, right in zip(timestamps, timestamps[1:]))
            negative_count += negatives
            monotonic.append(negatives == 0)
    monotonic_fraction = sum(monotonic) / len(monotonic) if monotonic else None
    reasons: list[str] = []
    if populated == 0:
        verdict = TemporalVerdict.NO_TEMPORAL_METADATA
        reasons.append("field is unpopulated")
    elif evidence.filesystem_timestamp_only:
        verdict = TemporalVerdict.SYSTEM_TIMESTAMP_ONLY
        reasons.append("filesystem metadata is not acquisition time")
    elif evidence.coarse_date_only:
        verdict = TemporalVerdict.COARSE_DATE_ONLY
        reasons.append("only a coarse campaign/date token is available")
    elif evidence.container_target_pure:
        verdict = TemporalVerdict.TARGET_NESTED_ORDER
        reasons.append("order is nested inside a target-pure container")
    elif evidence.physical_order_verified and not evidence.session_reset_semantics_verified:
        verdict = TemporalVerdict.ORDER_ONLY_NO_TIME
        reasons.append("physical order exists but reset/session semantics are unverified")
    elif not all(
        (
            evidence.physical_order_verified,
            evidence.session_reset_semantics_verified,
            evidence.gaps_have_defined_meaning,
            evidence.inference_time_available,
        )
    ):
        verdict = TemporalVerdict.UNRESOLVED
        reasons.append("one or more required temporal evidence conditions are absent")
    elif negative_count:
        verdict = TemporalVerdict.UNRESOLVED
        reasons.append("timestamps decrease within a declared clock-reset segment")
    elif evidence.mixed_target_episode_fraction is not None and (
        evidence.mixed_target_episode_fraction <= 0
    ):
        verdict = TemporalVerdict.TARGET_NESTED_ORDER
        reasons.append("candidate temporal episodes have no mixed-target variation")
    else:
        verdict = TemporalVerdict.VALID_TEMPORAL_CONTEXT
        reasons.append("all predeclared temporal evidence conditions are satisfied")
    return TemporalAudit(
        evidence.field,
        verdict,
        populated,
        monotonic_fraction,
        duplicate_count,
        negative_count,
        tuple(reasons),
    )


def _parse_timestamp(value: str | None) -> datetime:
    if value is None:
        raise ValueError("timestamp required")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
