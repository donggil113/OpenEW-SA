"""Machine-checkable, performance-independent Shen qualification gate."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Mapping


class GateStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    NOT_RUN = "NOT_RUN"


@dataclass(frozen=True)
class ShenQualification:
    official_provenance: GateStatus
    licence: GateStatus
    access: GateStatus
    storage: GateStatus
    task_compatibility: GateStatus
    raw_iq_conversion: GateStatus
    target_proxy: GateStatus
    split_integrity: GateStatus
    acquired_calibration_episode: GateStatus

    def validate(self) -> "ShenQualification":
        for field, value in asdict(self).items():
            try:
                GateStatus(value)
            except ValueError as exc:
                raise ValueError(f"invalid gate status for {field}: {value}") from exc
        return self

    @property
    def payload_authorized(self) -> bool:
        required = (self.official_provenance, self.licence, self.access, self.storage, self.task_compatibility, self.raw_iq_conversion)
        return all(value is GateStatus.PASS for value in required)

    @property
    def bounded_benchmark_authorized(self) -> bool:
        return self.payload_authorized and self.target_proxy is GateStatus.PASS and self.split_integrity is GateStatus.PASS

    @property
    def exact_replication_authorized(self) -> bool:
        return self.bounded_benchmark_authorized and self.acquired_calibration_episode is GateStatus.PASS

    def to_dict(self) -> dict[str, object]:
        return {
            "gates": {key: value.value for key, value in self.__dict__.items()},
            "payload_authorized": self.payload_authorized,
            "bounded_benchmark_authorized": self.bounded_benchmark_authorized,
            "exact_replication_authorized": self.exact_replication_authorized,
        }


REQUIRED_KEYS = frozenset(ShenQualification.__dataclass_fields__)


def evaluate_qualification(values: Mapping[str, str]) -> ShenQualification:
    """Parse exact gate names and fail closed on missing or unknown input."""

    extra = set(values) - REQUIRED_KEYS
    if extra:
        raise ValueError(f"unknown qualification gates: {sorted(extra)}")
    parsed: dict[str, GateStatus] = {}
    for key in REQUIRED_KEYS:
        raw = values.get(key, GateStatus.UNKNOWN.value)
        try:
            parsed[key] = GateStatus(str(raw).upper())
        except ValueError as exc:
            raise ValueError(f"invalid gate status for {key}: {raw}") from exc
    return ShenQualification(**parsed).validate()


def current_official_evidence_qualification() -> ShenQualification:
    """Frozen 2026-09-05 qualification; no payload/model result is consulted."""

    return ShenQualification(
        official_provenance=GateStatus.PASS,
        licence=GateStatus.FAIL,
        access=GateStatus.FAIL,
        storage=GateStatus.PASS,
        task_compatibility=GateStatus.PASS,
        raw_iq_conversion=GateStatus.UNKNOWN,
        target_proxy=GateStatus.NOT_RUN,
        split_integrity=GateStatus.NOT_RUN,
        acquired_calibration_episode=GateStatus.FAIL,
    )
