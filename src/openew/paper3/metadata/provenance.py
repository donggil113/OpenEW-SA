"""Field-level provenance sidecars for acquisition metadata."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping
import json
import os

from .enums import Confidence
from .schema import AcquisitionRecord, acquisition_field_names


@dataclass(frozen=True)
class FieldProvenance:
    field: str
    source_type: str
    source_path_or_record: str
    parser_version: str
    extraction_method: str
    verified_against: tuple[str, ...]
    confidence: Confidence
    transformation_history: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "FieldProvenance":
        required = {
            "field",
            "source_type",
            "source_path_or_record",
            "parser_version",
            "extraction_method",
            "verified_against",
            "confidence",
        }
        missing = sorted(required - set(value))
        if missing:
            raise ValueError(f"Missing provenance fields: {missing}")
        unknown = sorted(set(value) - required - {"transformation_history"})
        if unknown:
            raise ValueError(f"Unknown provenance fields: {unknown}")
        field = str(value["field"])
        if field not in acquisition_field_names():
            raise ValueError(f"Provenance references unknown acquisition field: {field}")
        return cls(
            field=field,
            source_type=_nonempty(value["source_type"], "source_type"),
            source_path_or_record=_nonempty(
                value["source_path_or_record"], "source_path_or_record"
            ),
            parser_version=_nonempty(value["parser_version"], "parser_version"),
            extraction_method=_nonempty(value["extraction_method"], "extraction_method"),
            verified_against=_tuple(value["verified_against"], "verified_against"),
            confidence=Confidence(str(value["confidence"])),
            transformation_history=_tuple(
                value.get("transformation_history", ()), "transformation_history"
            ),
        )

    def to_mapping(self) -> dict[str, Any]:
        result = asdict(self)
        result["confidence"] = self.confidence.value
        result["verified_against"] = list(self.verified_against)
        result["transformation_history"] = list(self.transformation_history)
        return result


@dataclass(frozen=True)
class ProvenanceSidecar:
    schema_version: str
    parser_name: str
    parser_version: str
    source_sha256: Mapping[str, str]
    fields: tuple[FieldProvenance, ...]
    warnings: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ProvenanceSidecar":
        return cls(
            schema_version=_nonempty(value.get("schema_version"), "schema_version"),
            parser_name=_nonempty(value.get("parser_name"), "parser_name"),
            parser_version=_nonempty(value.get("parser_version"), "parser_version"),
            source_sha256={str(k): str(v) for k, v in dict(value.get("source_sha256", {})).items()},
            fields=tuple(FieldProvenance.from_mapping(item) for item in value.get("fields", [])),
            warnings=_tuple(value.get("warnings", ()), "warnings"),
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "parser_name": self.parser_name,
            "parser_version": self.parser_version,
            "source_sha256": dict(self.source_sha256),
            "fields": [item.to_mapping() for item in self.fields],
            "warnings": list(self.warnings),
        }

    def field_index(self) -> dict[str, FieldProvenance]:
        result: dict[str, FieldProvenance] = {}
        for item in self.fields:
            if item.field in result:
                raise ValueError(f"Duplicate provenance for field {item.field}")
            result[item.field] = item
        return result


def missing_provenance(
    records: Iterable[AcquisitionRecord], sidecar: ProvenanceSidecar
) -> tuple[str, ...]:
    populated: set[str] = set()
    for record in records:
        for name, value in record.to_mapping().items():
            if value not in (None, "", [], ()):
                populated.add(name)
    return tuple(sorted(populated - set(sidecar.field_index())))


def write_sidecar(path: str | Path, sidecar: ProvenanceSidecar) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(
        json.dumps(sidecar.to_mapping(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, destination)


def read_sidecar(path: str | Path) -> ProvenanceSidecar:
    return ProvenanceSidecar.from_mapping(json.loads(Path(path).read_text(encoding="utf-8")))


def _nonempty(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _tuple(value: Any, name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    try:
        result = tuple(value)
    except TypeError as error:
        raise TypeError(f"{name} must be a string sequence") from error
    if any(not isinstance(item, str) for item in result):
        raise TypeError(f"{name} must contain strings")
    return result
