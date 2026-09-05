"""Hardware-neutral prospective receiver-calibration collection contract."""

from __future__ import annotations

import json
import math
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping, Sequence

TARGET_TOKENS = frozenset({"class", "label", "transmitter", "device", "jammer", "occupancy", "technology", "target"})
SAMPLE_FORMAT_BYTES = {"ci8": 2, "ci16_le": 4, "cf32_le": 8, "cf64_le": 16}


@dataclass(frozen=True)
class CollectionTier:
    name: str
    minimum_receivers: int
    minimum_hardware_families: int
    minimum_sites: int
    minimum_days: int


COLLECTION_TIERS = {
    "SMALL": CollectionTier("SMALL", 8, 3, 2, 1),
    "MEDIUM": CollectionTier("MEDIUM", 12, 3, 2, 2),
    "FULL": CollectionTier("FULL", 20, 4, 3, 2),
}


@dataclass(frozen=True)
class CaptureRecord:
    capture_uuid: str
    session_uuid: str
    session_role: str
    receiver_id: str
    hardware_id: str
    hardware_family: str
    site_id: str
    campaign_id: str
    day_id: str
    timestamp_start_utc: str
    timestamp_end_utc: str
    clock_authority: str
    clock_reset_id: str
    sample_counter_start: int
    sample_count: int
    sample_rate_hz: float
    center_frequency_hz: float
    sample_format: str
    relative_data_path: str
    relative_meta_path: str
    source_record_namespace: str

    def validate(self) -> "CaptureRecord":
        for name in ("capture_uuid", "session_uuid"):
            try:
                uuid.UUID(str(getattr(self, name)))
            except ValueError as exc:
                raise ValueError(f"{name} must be an opaque UUID") from exc
        if self.session_role not in {"CALIBRATION", "QUERY"}:
            raise ValueError("session_role must be CALIBRATION or QUERY")
        if self.sample_count <= 0 or self.sample_counter_start < 0:
            raise ValueError("invalid sample counter/count")
        if self.sample_rate_hz <= 0 or self.center_frequency_hz <= 0:
            raise ValueError("frequency and sample rate must be positive")
        if self.sample_format not in SAMPLE_FORMAT_BYTES:
            raise ValueError("unsupported sample format")
        if _utc(self.timestamp_end_utc) <= _utc(self.timestamp_start_utc):
            raise ValueError("session/capture end must follow start")
        if not self.clock_authority.strip() or not self.clock_reset_id.strip():
            raise ValueError("clock authority and reset ID are required")
        assert_target_neutral_path(self.relative_data_path)
        assert_target_neutral_path(self.relative_meta_path)
        if Path(self.relative_data_path).name.split(".")[0] != self.capture_uuid:
            raise ValueError("raw filename must use only the opaque capture UUID")
        return self

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CollectionValidation:
    status: str
    tier: str
    receiver_count: int
    hardware_family_count: int
    site_count: int
    day_count: int
    calibration_receiver_count: int
    query_receiver_count: int
    disjoint_source_records: bool
    target_neutral_paths: bool
    annotation_separated: bool
    provenance_complete: bool
    issues: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _utc(value: str) -> datetime:
    if not str(value).endswith("Z"):
        raise ValueError("timestamp must be explicit UTC ending Z")
    parsed = datetime.fromisoformat(str(value)[:-1] + "+00:00")
    if parsed.utcoffset() is None:
        raise ValueError("timestamp lacks UTC offset")
    return parsed


def assert_target_neutral_path(path: str) -> None:
    value = str(path)
    if Path(value).is_absolute() or ".." in Path(value).parts:
        raise ValueError("capture path must be safe and relative")
    tokens = {token.lower() for token in re.split(r"[^A-Za-z0-9]+", value) if token}
    hit = sorted(tokens & TARGET_TOKENS)
    if hit:
        raise ValueError(f"target-bearing path tokens: {hit}")


def validate_collection(records: Sequence[CaptureRecord], *, tier: str, annotation_sample_ids: Iterable[str] | None = None, provenance_by_capture: Mapping[str, object] | None = None) -> CollectionValidation:
    if tier not in COLLECTION_TIERS:
        raise ValueError(f"unknown collection tier: {tier}")
    required = COLLECTION_TIERS[tier]
    issues: list[str] = []
    captures: set[str] = set()
    role_records: dict[str, set[str]] = {"CALIBRATION": set(), "QUERY": set()}
    receivers: set[str] = set()
    families: set[str] = set()
    sites: set[str] = set()
    days: set[str] = set()
    source_by_role: dict[str, set[str]] = {"CALIBRATION": set(), "QUERY": set()}
    for row in records:
        try:
            row.validate()
        except (ValueError, TypeError) as exc:
            issues.append(f"capture {row.capture_uuid}: {exc}")
            continue
        if row.capture_uuid in captures:
            issues.append(f"duplicate capture UUID: {row.capture_uuid}")
        captures.add(row.capture_uuid)
        receivers.add(row.receiver_id)
        families.add(row.hardware_family)
        sites.add(row.site_id)
        days.add(row.day_id)
        role_records[row.session_role].add(row.receiver_id)
        source_by_role[row.session_role].add(row.source_record_namespace)
    if len(receivers) < required.minimum_receivers:
        issues.append("receiver count below tier requirement")
    if len(families) < required.minimum_hardware_families:
        issues.append("hardware-family diversity below tier requirement")
    if len(sites) < required.minimum_sites:
        issues.append("site diversity below tier requirement")
    if len(days) < required.minimum_days:
        issues.append("day diversity below tier requirement")
    if role_records["CALIBRATION"] != receivers:
        issues.append("every receiver requires a physical calibration session")
    if role_records["QUERY"] != receivers:
        issues.append("every receiver requires a physical query session")
    disjoint = not (source_by_role["CALIBRATION"] & source_by_role["QUERY"])
    if not disjoint:
        issues.append("calibration/query source-record namespaces overlap")
    annotation_separated = not any(key in CaptureRecord.__dataclass_fields__ for key in ("target_label", "transmitter_id", "label"))
    if not annotation_separated:
        issues.append("annotations are not logically separate")
    provenance_complete = provenance_by_capture is not None and captures <= set(provenance_by_capture)
    if not provenance_complete:
        issues.append("field/capture provenance incomplete")
    return CollectionValidation("PASS" if not issues else "FAIL", tier, len(receivers), len(families), len(sites), len(days), len(role_records["CALIBRATION"]), len(role_records["QUERY"]), disjoint, True, annotation_separated, provenance_complete, tuple(issues))


def estimate_collection_storage(*, receivers: int, transmitters: int, sample_rate_hz: float, sample_format: str, capture_duration_seconds: float, sessions_per_receiver: int, sites: int, days: int, captures_per_session: int = 1) -> dict[str, float | int | str]:
    values = (receivers, transmitters, sample_rate_hz, capture_duration_seconds, sessions_per_receiver, sites, days, captures_per_session)
    if any(float(value) <= 0 for value in values):
        raise ValueError("all estimator inputs must be positive")
    if sample_format not in SAMPLE_FORMAT_BYTES:
        raise ValueError("unknown sample format")
    captures = int(receivers * sessions_per_receiver * sites * days * captures_per_session)
    raw = int(math.ceil(captures * capture_duration_seconds * sample_rate_hz * SAMPLE_FORMAT_BYTES[sample_format]))
    converted = int(math.ceil(raw * 0.30))
    checkpoints = int(math.ceil(transmitters * receivers * 2_000_000))
    reserve = int(math.ceil((raw + converted + checkpoints) * 1.5))
    return {"capture_count": captures, "raw_bytes": raw, "compressed_low_bytes": int(raw * 0.45), "compressed_high_bytes": int(raw * 0.85), "converted_bytes": converted, "expected_training_storage_bytes": checkpoints, "minimum_disk_reserve_bytes": reserve, "capture_hours": captures * capture_duration_seconds / 3600.0, "sample_format": sample_format}


def write_synthetic_collection(root: str | Path, *, tier: str = "SMALL") -> tuple[list[CaptureRecord], dict[str, dict[str, str]]]:
    requirement = COLLECTION_TIERS[tier]
    root = Path(root)
    records: list[CaptureRecord] = []
    provenance: dict[str, dict[str, str]] = {}
    for receiver in range(requirement.minimum_receivers):
        for role_index, role in enumerate(("CALIBRATION", "QUERY")):
            capture = str(uuid.uuid5(uuid.NAMESPACE_URL, f"openew-synthetic-{tier}-{receiver}-{role}"))
            session = str(uuid.uuid5(uuid.NAMESPACE_URL, f"openew-synthetic-session-{tier}-{receiver}-{role}"))
            relative_data = f"raw/campaign-00/{session}/{capture}.sigmf-data"
            relative_meta = f"raw/campaign-00/{session}/{capture}.sigmf-meta"
            row = CaptureRecord(capture, session, role, f"rx-{receiver:02d}", f"hw-{receiver:02d}", f"family-{receiver % requirement.minimum_hardware_families:02d}", f"site-{receiver % requirement.minimum_sites:02d}", "campaign-00", f"day-{receiver % requirement.minimum_days:02d}", f"2026-01-{1 + receiver % 20:02d}T0{role_index}:00:00Z", f"2026-01-{1 + receiver % 20:02d}T0{role_index}:00:01Z", "GNSS_DISCIPLINED", f"clock-{receiver:02d}-0", 0, 256, 1_000_000.0, 868_100_000.0, "ci16_le", relative_data, relative_meta, f"source-{role.lower()}-{receiver:02d}").validate()
            data_path, meta_path = root / relative_data, root / relative_meta
            data_path.parent.mkdir(parents=True, exist_ok=True)
            data_path.write_bytes(b"\x00" * 16)
            meta_path.write_text(json.dumps(row.to_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")
            records.append(row)
            provenance[capture] = {"source": "synthetic_contract_fixture", "verified_by": "unit-test-generator"}
    return records, provenance


def training_authorization_gate(validation: CollectionValidation) -> dict[str, object]:
    return {"authorized": validation.status == "PASS", "status": "AUTHORIZED_FOR_PREREGISTERED_MODELING" if validation.status == "PASS" else "NOT_AUTHORIZED", "scientific_evidence": False, "reason": "Synthetic dry-run establishes software readiness only." if validation.status == "PASS" else "; ".join(validation.issues)}
