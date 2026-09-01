from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

from openew.paper3.metadata.schema import AcquisitionRecord, SCHEMA_VERSION


def record(
    index: int = 0,
    *,
    session: str = "session-01",
    capture: str = "capture-01",
    receiver: str | None = "receiver-01",
    site: str | None = "site-01",
    timestamp: str | None = None,
    reset: str | None = "reset-01",
) -> AcquisitionRecord:
    value = AcquisitionRecord(
        schema_version=SCHEMA_VERSION,
        sample_id=f"sample-{index:04d}",
        acquisition_session_id=session,
        capture_id=capture,
        within_capture_index=index,
        timestamp_utc=timestamp
        or (datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=index))
        .isoformat()
        .replace("+00:00", "Z"),
        timestamp_source="hardware_clock",
        timestamp_resolution_ns=1_000,
        timestamp_uncertainty_ns=2_000,
        clock_domain="receiver_clock",
        clock_reset_id=reset,
        receiver_id=receiver,
        site_id=site,
        center_frequency_hz=100_000_000.0,
        lower_frequency_hz=99_000_000.0,
        upper_frequency_hz=101_000_000.0,
        bandwidth_hz=2_000_000.0,
        sample_rate_hz=2_400_000.0,
        source_file_id=f"capture-{index // 4:04d}.bin",
        source_record_index=index,
    )
    value.validate()
    return value


def records(count: int = 6) -> list[AcquisitionRecord]:
    return [
        record(
            index,
            session="session-A" if index < count // 2 else "session-B",
            capture="capture-A" if index < count // 2 else "capture-B",
            receiver="receiver-01" if index % 2 == 0 else "receiver-02",
            site="site-01" if index < count // 2 else "site-02",
        )
        for index in range(count)
    ]


def changed(value: AcquisitionRecord, **updates: object) -> AcquisitionRecord:
    return replace(value, **updates)
