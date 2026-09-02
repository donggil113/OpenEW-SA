"""Leakage-safe prospective acquisition metadata infrastructure for Paper 3."""

from .enums import (
    Confidence,
    Eligibility,
    ReadinessLevel,
    Severity,
    TemporalVerdict,
)
from .leakage import EligibilityEngine, default_eligibility_engine
from .schema import AcquisitionRecord, AnnotationRecord, SCHEMA_VERSION

__all__ = [
    "AcquisitionRecord",
    "AnnotationRecord",
    "Confidence",
    "Eligibility",
    "EligibilityEngine",
    "ReadinessLevel",
    "SCHEMA_VERSION",
    "Severity",
    "TemporalVerdict",
    "default_eligibility_engine",
]
