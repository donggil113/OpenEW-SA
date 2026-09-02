"""Versioned acquisition and annotation records with strict separation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "1.0.0"

IDENTIFIER_FIELDS = frozenset(
    {
        "sample_id",
        "acquisition_session_id",
        "capture_id",
        "clock_domain",
        "clock_reset_id",
        "receiver_id",
        "station_id",
        "site_id",
        "sensor_id",
        "hardware_model",
        "hardware_serial_hash",
        "firmware_version",
        "antenna_id",
        "antenna_configuration",
        "channel_id",
        "location_id",
        "location_precision_class",
        "campaign_id",
        "environment_context_id",
        "operational_context_id",
        "source_file_id",
    }
)

ANNOTATION_FIELD_TOKENS = frozenset(
    {
        "label",
        "target",
        "attack",
        "ood",
        "prediction",
        "correctness",
        "occupancy",
        "jammer_type",
        "technology_class",
    }
)


@dataclass(frozen=True)
class AcquisitionRecord:
    """One target-free acquisition row.

    Identifiers must arrive as strings. Numeric identifiers are rejected instead of
    being coerced because coercion can irreversibly remove leading zeros.
    """

    schema_version: str
    sample_id: str
    acquisition_session_id: str
    capture_id: str
    within_capture_index: int
    timestamp_utc: str | None = None
    timestamp_source: str | None = None
    timestamp_resolution_ns: int | None = None
    timestamp_uncertainty_ns: int | None = None
    clock_domain: str | None = None
    clock_reset_id: str | None = None
    receiver_id: str | None = None
    station_id: str | None = None
    site_id: str | None = None
    sensor_id: str | None = None
    hardware_model: str | None = None
    hardware_serial_hash: str | None = None
    firmware_version: str | None = None
    antenna_id: str | None = None
    antenna_configuration: str | None = None
    center_frequency_hz: float | None = None
    lower_frequency_hz: float | None = None
    upper_frequency_hz: float | None = None
    bandwidth_hz: float | None = None
    sample_rate_hz: float | None = None
    channel_id: str | None = None
    location_id: str | None = None
    location_precision_class: str | None = None
    campaign_id: str | None = None
    environment_context_id: str | None = None
    operational_context_id: str | None = None
    source_file_id: str | None = None
    source_record_index: int | None = None
    metadata_missing_mask: tuple[str, ...] = ()
    metadata_quality_flags: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "AcquisitionRecord":
        allowed = {field.name for field in fields(cls)}
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ValueError(f"Unknown acquisition fields fail closed: {unknown}")
        _reject_annotation_like_fields(value)
        required = {
            "schema_version",
            "sample_id",
            "acquisition_session_id",
            "capture_id",
            "within_capture_index",
        }
        missing = sorted(field for field in required if field not in value)
        if missing:
            raise ValueError(f"Missing required acquisition fields: {missing}")
        data = dict(value)
        for name in IDENTIFIER_FIELDS:
            if name in data:
                data[name] = _optional_identifier(data[name], name)
        data["schema_version"] = _required_string(data["schema_version"], "schema_version")
        data["within_capture_index"] = _integer(data["within_capture_index"], "within_capture_index")
        if data["within_capture_index"] < 0:
            raise ValueError("within_capture_index must be non-negative")
        for name in ("timestamp_resolution_ns", "timestamp_uncertainty_ns", "source_record_index"):
            if name in data and data[name] not in (None, ""):
                data[name] = _integer(data[name], name)
                if data[name] < 0:
                    raise ValueError(f"{name} must be non-negative")
            elif name in data:
                data[name] = None
        for name in (
            "center_frequency_hz",
            "lower_frequency_hz",
            "upper_frequency_hz",
            "bandwidth_hz",
            "sample_rate_hz",
        ):
            if name in data and data[name] not in (None, ""):
                data[name] = _number(data[name], name)
            elif name in data:
                data[name] = None
        for name in ("metadata_missing_mask", "metadata_quality_flags"):
            data[name] = _string_tuple(data.get(name, ()), name)
        record = cls(**data)
        record.validate()
        return record

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported schema_version {self.schema_version!r}; expected {SCHEMA_VERSION!r}"
            )
        for name in ("sample_id", "acquisition_session_id", "capture_id"):
            if not getattr(self, name):
                raise ValueError(f"{name} must not be empty")
        if self.timestamp_utc is not None:
            _parse_utc_timestamp(self.timestamp_utc)
        if self.timestamp_resolution_ns is not None and not self.timestamp_source:
            raise ValueError("timestamp_resolution_ns requires timestamp_source")
        if self.timestamp_uncertainty_ns is not None and not self.timestamp_source:
            raise ValueError("timestamp_uncertainty_ns requires timestamp_source")
        if self.bandwidth_hz is not None and self.bandwidth_hz <= 0:
            raise ValueError("bandwidth_hz must be positive")
        if self.sample_rate_hz is not None and self.sample_rate_hz <= 0:
            raise ValueError("sample_rate_hz must be positive")
        frequencies = (
            self.lower_frequency_hz,
            self.center_frequency_hz,
            self.upper_frequency_hz,
        )
        if any(value is not None and value < 0 for value in frequencies):
            raise ValueError("frequency values must be non-negative")
        if self.lower_frequency_hz is not None and self.upper_frequency_hz is not None:
            if self.lower_frequency_hz > self.upper_frequency_hz:
                raise ValueError("lower_frequency_hz exceeds upper_frequency_hz")
            if self.center_frequency_hz is not None and not (
                self.lower_frequency_hz <= self.center_frequency_hz <= self.upper_frequency_hz
            ):
                raise ValueError("center_frequency_hz is outside lower/upper bounds")
        valid_names = {field.name for field in fields(self)}
        invalid_missing = sorted(set(self.metadata_missing_mask) - valid_names)
        if invalid_missing:
            raise ValueError(f"metadata_missing_mask names unknown fields: {invalid_missing}")

    def to_mapping(self) -> dict[str, Any]:
        result = asdict(self)
        result["metadata_missing_mask"] = list(self.metadata_missing_mask)
        result["metadata_quality_flags"] = list(self.metadata_quality_flags)
        return result


@dataclass(frozen=True)
class AnnotationRecord:
    """Task annotation stored separately from acquisition metadata."""

    sample_id: str
    task_name: str
    target_label: str
    annotation_source: str
    annotation_time: str | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "AnnotationRecord":
        allowed = {field.name for field in fields(cls)}
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ValueError(f"Unknown annotation fields: {unknown}")
        missing = sorted(name for name in allowed - {"annotation_time"} if name not in value)
        if missing:
            raise ValueError(f"Missing annotation fields: {missing}")
        data = dict(value)
        for name in ("sample_id", "task_name", "target_label", "annotation_source"):
            data[name] = _required_string(data[name], name)
        if data.get("annotation_time") not in (None, ""):
            _parse_utc_timestamp(str(data["annotation_time"]))
            data["annotation_time"] = str(data["annotation_time"])
        else:
            data["annotation_time"] = None
        return cls(**data)

    def to_mapping(self) -> dict[str, Any]:
        return asdict(self)


def acquisition_field_names() -> tuple[str, ...]:
    return tuple(field.name for field in fields(AcquisitionRecord))


def annotation_field_names() -> tuple[str, ...]:
    return tuple(field.name for field in fields(AnnotationRecord))


def _reject_annotation_like_fields(value: Mapping[str, Any]) -> None:
    rejected = []
    for field_name in value:
        lowered = field_name.lower()
        if any(token in lowered for token in ANNOTATION_FIELD_TOKENS):
            rejected.append(field_name)
    if rejected:
        raise ValueError(f"Annotation/target fields are forbidden in acquisition metadata: {sorted(rejected)}")


def _required_string(value: Any, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be supplied as a string")
    if value == "":
        raise ValueError(f"{name} must not be empty")
    return value


def _optional_identifier(value: Any, name: str) -> str | None:
    if value in (None, ""):
        return None
    return _required_string(value, name)


def _integer(value: Any, name: str) -> int:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be an integer, not bool")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{name} must be an integer") from error
    if isinstance(value, float) and value != parsed:
        raise TypeError(f"{name} must be an integer")
    return parsed


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be numeric, not bool")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{name} must be numeric") from error
    if parsed != parsed or parsed in (float("inf"), float("-inf")):
        raise ValueError(f"{name} must be finite")
    return parsed


def _string_tuple(value: Any, name: str) -> tuple[str, ...]:
    if value in (None, ""):
        return ()
    if isinstance(value, str):
        return tuple(part for part in value.split(";") if part)
    if not isinstance(value, Sequence):
        raise TypeError(f"{name} must be a string sequence")
    if any(not isinstance(item, str) for item in value):
        raise TypeError(f"{name} entries must be strings")
    return tuple(value)


def _parse_utc_timestamp(value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise TypeError("timestamp_utc must be a non-empty ISO-8601 string")
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as error:
        raise ValueError(f"Invalid timestamp_utc: {value!r}") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError("timestamp_utc must include an explicit UTC offset")
    return parsed
