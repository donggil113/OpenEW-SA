"""Strict machine-readable evidence schema for candidate RF datasets."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from enum import Enum
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "1.0.0"


class StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class TriState(StringEnum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNKNOWN = "UNKNOWN"


class AccessStatus(StringEnum):
    PUBLIC_DIRECT = "PUBLIC_DIRECT"
    PUBLIC_METADATA_ONLY = "PUBLIC_METADATA_ONLY"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    RESTRICTED = "RESTRICTED"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class AdoptionStatus(StringEnum):
    GO = "GO"
    CONDITIONAL_GO = "CONDITIONAL_GO"
    NO_GO = "NO-GO"
    UNKNOWN = "UNKNOWN"


class EvidenceConfidence(StringEnum):
    VERIFIED = "VERIFIED"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class CandidateEvidence:
    """Facts available before model evaluation.

    Missing facts remain ``None`` or ``UNKNOWN``.  Numeric counts are never
    silently treated as zero, and identifiers are never coerced to integers.
    """

    schema_version: str
    candidate_id: str
    dataset_name: str
    task: str
    official_source: str | None
    official_paper: str | None
    license: str | None
    license_verified: TriState
    download_size_bytes: int | None
    receiver_count: int | None
    site_count: int | None
    day_count: int | None
    session_count: int | None
    timestamp_available: TriState
    order_available: TriState
    frequency_available: TriState
    sample_rate_available: TriState
    annotation_separated: TriState
    target_field: str | None
    target_proxy_fields: tuple[str, ...]
    relation_allowed_fields: tuple[str, ...]
    temporal_status: str
    metadata_readiness: str
    access_status: AccessStatus
    adoption_status: AdoptionStatus
    evidence_confidence: EvidenceConfidence

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "CandidateEvidence":
        allowed = {item.name for item in fields(cls)}
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ValueError(f"Unknown candidate fields fail closed: {unknown}")
        missing = sorted(allowed - set(value))
        if missing:
            raise ValueError(f"Missing candidate fields: {missing}")
        data = dict(value)
        for name in ("schema_version", "candidate_id", "dataset_name", "task"):
            data[name] = _required_string(data[name], name)
        if data["schema_version"] != SCHEMA_VERSION:
            raise ValueError(f"Unsupported schema_version: {data['schema_version']!r}")
        for name in ("official_source", "official_paper", "license", "target_field"):
            data[name] = _optional_string(data[name], name)
        for name in (
            "download_size_bytes",
            "receiver_count",
            "site_count",
            "day_count",
            "session_count",
        ):
            data[name] = _optional_nonnegative_int(data[name], name)
        for name in (
            "license_verified",
            "timestamp_available",
            "order_available",
            "frequency_available",
            "sample_rate_available",
            "annotation_separated",
        ):
            data[name] = TriState(data[name])
        data["target_proxy_fields"] = _string_tuple(data["target_proxy_fields"], "target_proxy_fields")
        data["relation_allowed_fields"] = _string_tuple(
            data["relation_allowed_fields"], "relation_allowed_fields"
        )
        data["temporal_status"] = _required_string(data["temporal_status"], "temporal_status")
        data["metadata_readiness"] = _required_string(
            data["metadata_readiness"], "metadata_readiness"
        )
        data["access_status"] = AccessStatus(data["access_status"])
        data["adoption_status"] = AdoptionStatus(data["adoption_status"])
        data["evidence_confidence"] = EvidenceConfidence(data["evidence_confidence"])
        return cls(**data)

    def to_mapping(self) -> dict[str, Any]:
        result = asdict(self)
        for name in (
            "license_verified",
            "timestamp_available",
            "order_available",
            "frequency_available",
            "sample_rate_available",
            "annotation_separated",
            "access_status",
            "adoption_status",
            "evidence_confidence",
        ):
            result[name] = getattr(self, name).value
        result["target_proxy_fields"] = list(self.target_proxy_fields)
        result["relation_allowed_fields"] = list(self.relation_allowed_fields)
        return result


def _required_string(value: Any, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value


def _optional_string(value: Any, name: str) -> str | None:
    if value in (None, ""):
        return None
    return _required_string(value, name)


def _optional_nonnegative_int(value: Any, name: str) -> int | None:
    if value is None or value == "UNKNOWN":
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer or null")
    if value < 0:
        raise ValueError(f"{name} must be non-negative")
    return value


def _string_tuple(value: Any, name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise TypeError(f"{name} must be a sequence of strings")
    if any(not isinstance(item, str) or not item for item in value):
        raise TypeError(f"{name} must contain non-empty strings")
    return tuple(value)
