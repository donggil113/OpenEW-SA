from __future__ import annotations

from dataclasses import replace
import pytest

from openew.paper3.receiver_adaptation.collection import COLLECTION_TIERS, assert_target_neutral_path, estimate_collection_storage, training_authorization_gate, validate_collection, write_synthetic_collection


@pytest.mark.parametrize("tier,count,families,sites,days", [("SMALL", 8, 3, 2, 1), ("MEDIUM", 12, 3, 2, 2), ("FULL", 20, 4, 3, 2)])
def test_tier_contract(tier, count, families, sites, days) -> None:
    row = COLLECTION_TIERS[tier]
    assert (row.minimum_receivers, row.minimum_hardware_families, row.minimum_sites, row.minimum_days) == (count, families, sites, days)


@pytest.mark.parametrize("token", ["class", "label", "transmitter", "device", "jammer", "occupancy", "technology", "target"])
def test_target_bearing_paths_rejected(token: str) -> None:
    with pytest.raises(ValueError, match="target-bearing"):
        assert_target_neutral_path(f"raw/{token}/00000000-0000-0000-0000-000000000000.sigmf-data")


@pytest.mark.parametrize("path", ["raw/campaign-00/session-00/00000000-0000-0000-0000-000000000000.sigmf-data", "raw/c-a/s-b/a3f4c5d6-1111-2222-3333-444455556666.sigmf-meta"])
def test_neutral_paths_allowed(path: str) -> None:
    assert_target_neutral_path(path)


@pytest.mark.parametrize("path", ["/tmp/a.sigmf-data", "../a.sigmf-data", "raw/../../a.sigmf-data"])
def test_unsafe_paths_rejected(path: str) -> None:
    with pytest.raises(ValueError, match="safe and relative"):
        assert_target_neutral_path(path)


@pytest.mark.parametrize("tier", ["SMALL", "MEDIUM", "FULL"])
def test_synthetic_collection_passes_each_tier(tmp_path, tier: str) -> None:
    records, provenance = write_synthetic_collection(tmp_path / tier, tier=tier)
    report = validate_collection(records, tier=tier, annotation_sample_ids=(), provenance_by_capture=provenance)
    assert report.status == "PASS"
    assert training_authorization_gate(report)["authorized"] is True
    assert training_authorization_gate(report)["scientific_evidence"] is False


def _valid_records(tmp_path):
    return write_synthetic_collection(tmp_path / "base", tier="SMALL")


@pytest.mark.parametrize("field,value,pattern", [("session_role", "TRAIN", "session_role"), ("sample_count", 0, "counter/count"), ("sample_counter_start", -1, "counter/count"), ("sample_rate_hz", 0, "positive"), ("center_frequency_hz", -1, "positive"), ("sample_format", "int16", "unsupported"), ("timestamp_start_utc", "2026-01-01T00:00:00", "UTC"), ("timestamp_end_utc", "2025-01-01T00:00:00Z", "follow"), ("clock_authority", "", "clock"), ("clock_reset_id", "", "clock")])
def test_capture_validation_failures(tmp_path, field: str, value, pattern: str) -> None:
    records, _ = _valid_records(tmp_path)
    with pytest.raises(ValueError, match=pattern):
        replace(records[0], **{field: value}).validate()


@pytest.mark.parametrize("field", ["capture_uuid", "session_uuid"])
@pytest.mark.parametrize("value", ["", "123", "target", "0000-not-uuid"])
def test_opaque_uuid_required(tmp_path, field: str, value: str) -> None:
    records, _ = _valid_records(tmp_path)
    with pytest.raises(ValueError, match="opaque UUID"):
        replace(records[0], **{field: value}).validate()


def test_filename_must_equal_capture_uuid(tmp_path) -> None:
    records, _ = _valid_records(tmp_path)
    with pytest.raises(ValueError, match="opaque capture UUID"):
        replace(records[0], relative_data_path="raw/campaign/a.sigmf-data").validate()


@pytest.mark.parametrize("tier", ["", "small", "LARGE", "UNKNOWN"])
def test_unknown_tier_rejected(tier: str) -> None:
    with pytest.raises(ValueError, match="unknown collection tier"):
        validate_collection([], tier=tier)


@pytest.mark.parametrize("field", ["receiver_id", "hardware_family", "site_id"])
def test_diversity_shortfall_fails(tmp_path, field: str) -> None:
    records, provenance = _valid_records(tmp_path)
    report = validate_collection([replace(row, **{field: "one"}) for row in records], tier="SMALL", provenance_by_capture=provenance)
    assert report.status == "FAIL"


def test_medium_day_shortfall_fails(tmp_path) -> None:
    records, provenance = write_synthetic_collection(tmp_path / "medium", tier="MEDIUM")
    report = validate_collection(
        [replace(row, day_id="one") for row in records], tier="MEDIUM", provenance_by_capture=provenance
    )
    assert report.status == "FAIL"


@pytest.mark.parametrize("role", ["CALIBRATION", "QUERY"])
def test_missing_role_for_receiver_fails(tmp_path, role: str) -> None:
    records, provenance = _valid_records(tmp_path)
    receiver = records[0].receiver_id
    rows = [row for row in records if not (row.receiver_id == receiver and row.session_role == role)]
    report = validate_collection(rows, tier="SMALL", provenance_by_capture=provenance)
    assert any(role.lower() in issue.lower() for issue in report.issues)


def test_duplicate_capture_fails(tmp_path) -> None:
    records, provenance = _valid_records(tmp_path)
    report = validate_collection([*records, records[0]], tier="SMALL", provenance_by_capture=provenance)
    assert any("duplicate capture" in issue for issue in report.issues)


def test_overlapping_source_namespaces_fail(tmp_path) -> None:
    records, provenance = _valid_records(tmp_path)
    calibration = next(row for row in records if row.session_role == "CALIBRATION")
    index = next(i for i, row in enumerate(records) if row.receiver_id == calibration.receiver_id and row.session_role == "QUERY")
    rows = list(records)
    rows[index] = replace(rows[index], source_record_namespace=calibration.source_record_namespace)
    assert not validate_collection(rows, tier="SMALL", provenance_by_capture=provenance).disjoint_source_records


def test_missing_provenance_fails(tmp_path) -> None:
    records, provenance = _valid_records(tmp_path)
    provenance.pop(records[0].capture_uuid)
    report = validate_collection(records, tier="SMALL", provenance_by_capture=provenance)
    assert not report.provenance_complete and training_authorization_gate(report)["authorized"] is False


@pytest.mark.parametrize("sample_format,bytes_per_sample", [("ci8", 2), ("ci16_le", 4), ("cf32_le", 8), ("cf64_le", 16)])
def test_storage_estimator_exact_raw(sample_format: str, bytes_per_sample: int) -> None:
    result = estimate_collection_storage(receivers=2, transmitters=3, sample_rate_hz=1000, sample_format=sample_format, capture_duration_seconds=2, sessions_per_receiver=2, sites=1, days=1)
    assert result["raw_bytes"] == 2 * 2 * 1 * 1 * 2 * 1000 * bytes_per_sample
    assert result["minimum_disk_reserve_bytes"] > result["raw_bytes"]


@pytest.mark.parametrize("field", ["receivers", "transmitters", "sample_rate_hz", "capture_duration_seconds", "sessions_per_receiver", "sites", "days", "captures_per_session"])
def test_storage_estimator_rejects_nonpositive(field: str) -> None:
    values = dict(receivers=2, transmitters=3, sample_rate_hz=1000, sample_format="ci16_le", capture_duration_seconds=2, sessions_per_receiver=2, sites=1, days=1, captures_per_session=1)
    values[field] = 0
    with pytest.raises(ValueError, match="positive"):
        estimate_collection_storage(**values)


@pytest.mark.parametrize("sample_format", ["", "int16", "float32", "cf16", "pickle"])
def test_storage_estimator_rejects_unknown_format(sample_format: str) -> None:
    with pytest.raises(ValueError, match="unknown sample format"):
        estimate_collection_storage(receivers=2, transmitters=3, sample_rate_hz=1000, sample_format=sample_format, capture_duration_seconds=2, sessions_per_receiver=2, sites=1, days=1)
