"""Prospective acquisition validation independent of predictive modeling."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Sequence

from .enums import Severity
from .leakage import target_bearing_path_tokens
from .provenance import ProvenanceSidecar, missing_provenance
from .schema import AcquisitionRecord


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    severity: Severity
    message: str
    sample_ids: tuple[str, ...] = ()

    def to_mapping(self) -> dict[str, object]:
        result = asdict(self)
        result["severity"] = self.severity.value
        result["sample_ids"] = list(self.sample_ids)
        return result


@dataclass(frozen=True)
class ValidationReport:
    total_records: int
    unique_sample_ids: int
    session_count: int
    capture_count: int
    issues: tuple[ValidationIssue, ...]

    @property
    def passed(self) -> bool:
        return not any(issue.severity is Severity.ERROR for issue in self.issues)

    def to_mapping(self) -> dict[str, object]:
        return {
            "total_records": self.total_records,
            "unique_sample_ids": self.unique_sample_ids,
            "session_count": self.session_count,
            "capture_count": self.capture_count,
            "passed": self.passed,
            "issue_count": len(self.issues),
            "issues": [issue.to_mapping() for issue in self.issues],
        }


def validate_records(
    records: Sequence[AcquisitionRecord],
    *,
    provenance: ProvenanceSidecar | None = None,
    max_session_size: int = 100_000,
) -> ValidationReport:
    issues: list[ValidationIssue] = []
    for record in records:
        try:
            record.validate()
        except (TypeError, ValueError) as error:
            issues.append(
                ValidationIssue("SCHEMA_INVALID", Severity.ERROR, str(error), (record.sample_id,))
            )
    ids = [record.sample_id for record in records]
    duplicate_ids = sorted(value for value, count in Counter(ids).items() if count > 1)
    if duplicate_ids:
        issues.append(
            ValidationIssue(
                "DUPLICATE_SAMPLE_ID",
                Severity.ERROR,
                f"{len(duplicate_ids)} sample IDs are duplicated",
                tuple(duplicate_ids[:20]),
            )
        )
    pair_index: dict[tuple[str, str, int], list[str]] = {}
    by_session: dict[str, list[AcquisitionRecord]] = {}
    for record in records:
        pair_index.setdefault(
            (record.acquisition_session_id, record.capture_id, record.within_capture_index), []
        ).append(record.sample_id)
        by_session.setdefault(record.acquisition_session_id, []).append(record)
    duplicate_pairs = [values for values in pair_index.values() if len(values) > 1]
    if duplicate_pairs:
        issues.append(
            ValidationIssue(
                "DUPLICATE_SESSION_CAPTURE_INDEX",
                Severity.ERROR,
                f"{len(duplicate_pairs)} session/capture/index keys are duplicated",
                tuple(value for group in duplicate_pairs[:10] for value in group),
            )
        )
    for session, group in sorted(by_session.items()):
        if len(group) == 1:
            issues.append(
                ValidationIssue(
                    "SINGLE_ROW_SESSION",
                    Severity.WARNING,
                    f"Session {session!r} contains one row",
                    (group[0].sample_id,),
                )
            )
        if len(group) > max_session_size:
            issues.append(
                ValidationIssue(
                    "OVER_LARGE_SESSION",
                    Severity.WARNING,
                    f"Session {session!r} contains {len(group)} rows",
                )
            )
    if records and not any(
        record.receiver_id or record.station_id or record.sensor_id for record in records
    ):
        issues.append(
            ValidationIssue(
                "MISSING_RECEIVER_ID",
                Severity.WARNING,
                "No receiver_id, station_id, or sensor_id is populated",
            )
        )
    issues.extend(_timestamp_issues(records))
    for record in records:
        if record.source_file_id:
            tokens = target_bearing_path_tokens(record.source_file_id)
            if tokens:
                issues.append(
                    ValidationIssue(
                        "TARGET_BEARING_SOURCE_FILE_ID",
                        Severity.ERROR,
                        f"source_file_id contains forbidden target tokens: {tokens}",
                        (record.sample_id,),
                    )
                )
    if provenance is None:
        issues.append(
            ValidationIssue(
                "PROVENANCE_SIDECAR_MISSING",
                Severity.WARNING,
                "No field-level provenance sidecar was supplied",
            )
        )
    else:
        missing = missing_provenance(records, provenance)
        if missing:
            issues.append(
                ValidationIssue(
                    "FIELD_PROVENANCE_INCOMPLETE",
                    Severity.ERROR,
                    f"Populated fields lack provenance: {list(missing)}",
                )
            )
    return ValidationReport(
        total_records=len(records),
        unique_sample_ids=len(set(ids)),
        session_count=len(by_session),
        capture_count=len({record.capture_id for record in records}),
        issues=tuple(issues),
    )


def _timestamp_issues(records: Sequence[AcquisitionRecord]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    grouped: dict[tuple[str, str | None], list[AcquisitionRecord]] = {}
    for record in records:
        if record.timestamp_utc is None:
            continue
        grouped.setdefault((record.acquisition_session_id, record.clock_reset_id), []).append(record)
    for (session, reset), group in grouped.items():
        ordered = sorted(group, key=lambda row: row.within_capture_index)
        times = [_time(row.timestamp_utc) for row in ordered]
        duplicates = [ordered[index].sample_id for index in range(1, len(times)) if times[index] == times[index - 1]]
        negatives = [ordered[index].sample_id for index in range(1, len(times)) if times[index] < times[index - 1]]
        if duplicates:
            issues.append(
                ValidationIssue(
                    "DUPLICATE_TIMESTAMP",
                    Severity.WARNING,
                    f"Duplicate timestamps in session {session!r}, reset {reset!r}",
                    tuple(duplicates[:20]),
                )
            )
        if negatives:
            issues.append(
                ValidationIssue(
                    "NEGATIVE_TIME_GAP",
                    Severity.ERROR,
                    f"Timestamp decreases within session {session!r}, reset {reset!r}",
                    tuple(negatives[:20]),
                )
            )
    return issues


def _time(value: str | None) -> datetime:
    if value is None:
        raise ValueError("timestamp required")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
