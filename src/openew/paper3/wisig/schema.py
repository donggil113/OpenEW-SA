"""Strict separated schemas for converted WiSig acquisition and annotation rows."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

ACQUISITION_FIELDS = (
    "sample_id",
    "receiver_id",
    "day_id",
    "packet_index",
    "source_record_index",
    "center_frequency_hz",
    "bandwidth_hz",
    "sample_rate_hz",
    "data_quality_flags",
    "feature_shard",
    "feature_row",
)
ANNOTATION_FIELDS = ("sample_id", "task_name", "transmitter_id")
FORBIDDEN_MODEL_FIELDS = frozenset(
    {
        "transmitter_id",
        "target",
        "target_label",
        "label",
        "class",
        "source_path",
        "source_filename",
        "domain_id",
        "day_id",
    }
)
RELATION_WHITELIST = frozenset({"receiver_id"})
SPLIT_ONLY_FIELDS = frozenset({"day_id"})


def _nonempty_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{field} must be a non-empty exact string without outer whitespace")
    return value


@dataclass(frozen=True)
class AcquisitionRow:
    sample_id: str
    receiver_id: str
    day_id: str
    packet_index: int
    source_record_index: int
    center_frequency_hz: int
    bandwidth_hz: int
    sample_rate_hz: int
    data_quality_flags: str
    feature_shard: str
    feature_row: int

    def validate(self) -> "AcquisitionRow":
        for field in ("sample_id", "receiver_id", "day_id", "feature_shard"):
            _nonempty_string(getattr(self, field), field)
        if not isinstance(self.data_quality_flags, str):
            raise ValueError("data_quality_flags must be a string")
        for field in ("packet_index", "source_record_index", "feature_row"):
            value = getattr(self, field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{field} must be a non-negative integer")
        for field in ("center_frequency_hz", "bandwidth_hz", "sample_rate_hz"):
            value = getattr(self, field)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(f"{field} must be a positive integer")
        return self

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class AnnotationRow:
    sample_id: str
    task_name: str
    transmitter_id: str

    def validate(self) -> "AnnotationRow":
        for field in ANNOTATION_FIELDS:
            _nonempty_string(getattr(self, field), field)
        if self.task_name != "transmitter_fingerprinting":
            raise ValueError("unexpected WiSig task_name")
        return self

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


def assert_model_visible_fields(fields: set[str] | frozenset[str]) -> None:
    leaked = sorted(fields & FORBIDDEN_MODEL_FIELDS)
    if leaked:
        raise ValueError(f"forbidden model-visible WiSig fields: {leaked}")


def assert_relation_fields(fields: set[str] | frozenset[str]) -> None:
    unknown = sorted(fields - RELATION_WHITELIST)
    if unknown:
        raise ValueError(f"WiSig relation fields are not allowlisted: {unknown}")
