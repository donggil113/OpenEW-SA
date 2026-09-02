"""Controlled vocabularies for metadata validation and readiness decisions."""

from __future__ import annotations

from enum import Enum


class StringEnum(str, Enum):
    """String-valued enum with stable JSON serialization."""

    def __str__(self) -> str:
        return self.value


class Eligibility(StringEnum):
    RELATION_ALLOWED = "RELATION_ALLOWED"
    MODEL_FEATURE_ALLOWED = "MODEL_FEATURE_ALLOWED"
    SPLIT_ONLY = "SPLIT_ONLY"
    AUDIT_ONLY = "AUDIT_ONLY"
    FORBIDDEN_LABEL = "FORBIDDEN_LABEL"
    FORBIDDEN_TARGET_PROXY = "FORBIDDEN_TARGET_PROXY"
    UNRESOLVED = "UNRESOLVED"


class Confidence(StringEnum):
    VERIFIED = "VERIFIED"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNRESOLVED = "UNRESOLVED"


class TemporalVerdict(StringEnum):
    VALID_TEMPORAL_CONTEXT = "VALID_TEMPORAL_CONTEXT"
    COARSE_DATE_ONLY = "COARSE_DATE_ONLY"
    ORDER_ONLY_NO_TIME = "ORDER_ONLY_NO_TIME"
    TARGET_NESTED_ORDER = "TARGET_NESTED_ORDER"
    SYSTEM_TIMESTAMP_ONLY = "SYSTEM_TIMESTAMP_ONLY"
    UNRESOLVED = "UNRESOLVED"
    NO_TEMPORAL_METADATA = "NO_TEMPORAL_METADATA"


class ReadinessLevel(StringEnum):
    INDEPENDENT_SAMPLE_ONLY = "INDEPENDENT_SAMPLE_ONLY"
    STATIC_RELATIONAL = "STATIC_RELATIONAL"
    STATIC_HYPERGRAPH = "STATIC_HYPERGRAPH"
    TEMPORAL_RELATIONAL = "TEMPORAL_RELATIONAL"
    DYNAMIC_HYPERGRAPH = "DYNAMIC_HYPERGRAPH"


class Severity(StringEnum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
