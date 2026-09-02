"""Storage and structural-coverage planning without predictive effect claims."""

from __future__ import annotations

from dataclasses import asdict, dataclass


SAMPLE_FORMAT_BYTES = {
    "complex64": 8,
    "complex_int16": 4,
    "complex_int8": 2,
    "float32": 4,
    "int16": 2,
    "uint8": 1,
}


@dataclass(frozen=True)
class StorageEstimate:
    raw_bytes: int
    compressed_low_bytes: int
    compressed_high_bytes: int
    derived_feature_bytes: int
    recommended_total_disk_bytes: int

    def to_mapping(self) -> dict[str, int]:
        return asdict(self)


def estimate_collection_storage(
    *,
    sample_rate_hz: float,
    sample_format: str,
    channels: int,
    duration_seconds: float,
    receivers: int,
    sessions: int,
    captures_per_session: int,
    compression_low_ratio: float = 0.65,
    compression_high_ratio: float = 0.95,
    derived_feature_ratio: float = 0.10,
    headroom_ratio: float = 1.25,
) -> StorageEstimate:
    if sample_format not in SAMPLE_FORMAT_BYTES:
        raise ValueError(f"Unknown sample format: {sample_format}")
    positives = {
        "sample_rate_hz": sample_rate_hz,
        "channels": channels,
        "duration_seconds": duration_seconds,
        "receivers": receivers,
        "sessions": sessions,
        "captures_per_session": captures_per_session,
    }
    if any(value <= 0 for value in positives.values()):
        raise ValueError("all collection dimensions must be positive")
    if not (0 < compression_low_ratio <= compression_high_ratio <= 1):
        raise ValueError("compression ratios must satisfy 0 < low <= high <= 1")
    if derived_feature_ratio < 0 or headroom_ratio < 1:
        raise ValueError("derived_feature_ratio must be non-negative and headroom at least 1")
    raw = int(
        sample_rate_hz
        * SAMPLE_FORMAT_BYTES[sample_format]
        * channels
        * duration_seconds
        * receivers
        * sessions
        * captures_per_session
    )
    low = int(raw * compression_low_ratio)
    high = int(raw * compression_high_ratio)
    features = int(raw * derived_feature_ratio)
    recommended = int((raw + high + features) * headroom_ratio)
    return StorageEstimate(raw, low, high, features, recommended)


@dataclass(frozen=True)
class StructuralCoveragePlan:
    total_samples: int
    receiver_groups: int
    session_groups: int
    campaign_groups: int
    mean_samples_per_receiver: float
    mean_samples_per_session: float
    mean_sessions_per_campaign: float
    approximate_effective_samples: float
    receiver_holdout_supported: bool
    campaign_holdout_supported: bool
    mixed_label_session_requirement_met: bool
    seed_count: int

    def to_mapping(self) -> dict[str, object]:
        return asdict(self)


def plan_structural_coverage(
    *,
    receivers: int,
    sessions: int,
    campaigns: int,
    samples_per_session: int,
    expected_intra_session_correlation: float,
    seed_count: int,
    mixed_label_sessions: int,
    minimum_mixed_label_sessions: int = 8,
) -> StructuralCoveragePlan:
    integer_values = (receivers, sessions, campaigns, samples_per_session, seed_count)
    if any(value <= 0 for value in integer_values):
        raise ValueError("counts and seed_count must be positive")
    if not 0 <= expected_intra_session_correlation < 1:
        raise ValueError("expected intra-session correlation must be in [0, 1)")
    if mixed_label_sessions < 0 or minimum_mixed_label_sessions < 0:
        raise ValueError("mixed-label session counts must be non-negative")
    total = sessions * samples_per_session
    design_effect = 1 + (samples_per_session - 1) * expected_intra_session_correlation
    return StructuralCoveragePlan(
        total_samples=total,
        receiver_groups=receivers,
        session_groups=sessions,
        campaign_groups=campaigns,
        mean_samples_per_receiver=total / receivers,
        mean_samples_per_session=float(samples_per_session),
        mean_sessions_per_campaign=sessions / campaigns,
        approximate_effective_samples=total / design_effect,
        receiver_holdout_supported=receivers >= 2,
        campaign_holdout_supported=campaigns >= 2,
        mixed_label_session_requirement_met=mixed_label_sessions >= minimum_mixed_label_sessions,
        seed_count=seed_count,
    )
