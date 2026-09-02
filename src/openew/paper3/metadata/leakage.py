"""Fail-closed field eligibility and target-bearing path detection."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Mapping

from .enums import Eligibility


TARGET_TOKENS = frozenset(
    {
        "attack",
        "benign",
        "class",
        "correct",
        "jammer",
        "label",
        "modulation",
        "occupancy",
        "ood",
        "prediction",
        "target",
        "technology",
        "threat",
    }
)


@dataclass(frozen=True)
class EligibilityEngine:
    policy: Mapping[str, Eligibility]

    def eligibility(self, field: str) -> Eligibility:
        return self.policy.get(field, Eligibility.UNRESOLVED)

    def require(self, field: str, expected: Eligibility) -> None:
        actual = self.eligibility(field)
        if actual is Eligibility.UNRESOLVED:
            raise ValueError(f"Unknown field {field!r} fails closed")
        if actual is not expected:
            raise ValueError(f"Field {field!r} is {actual.value}, not {expected.value}")

    def require_relation_fields(
        self, requested: Iterable[str], explicit_whitelist: Iterable[str]
    ) -> tuple[str, ...]:
        whitelist = frozenset(explicit_whitelist)
        fields = tuple(requested)
        if not fields:
            return ()
        for field in fields:
            if field not in whitelist:
                raise ValueError(f"Relation field {field!r} is not explicitly whitelisted")
            self.require(field, Eligibility.RELATION_ALLOWED)
        return fields


def default_eligibility_engine() -> EligibilityEngine:
    relation = {
        "acquisition_session_id",
        "capture_id",
        "clock_reset_id",
        "receiver_id",
        "station_id",
        "site_id",
        "sensor_id",
        "channel_id",
        "location_id",
        "environment_context_id",
        "operational_context_id",
    }
    model = {
        "timestamp_utc",
        "timestamp_source",
        "timestamp_resolution_ns",
        "timestamp_uncertainty_ns",
        "center_frequency_hz",
        "lower_frequency_hz",
        "upper_frequency_hz",
        "bandwidth_hz",
        "sample_rate_hz",
        "antenna_id",
        "antenna_configuration",
    }
    split = {
        "campaign_id",
        "hardware_model",
        "hardware_serial_hash",
        "firmware_version",
        "location_precision_class",
        "domain_id",
    }
    audit = {
        "schema_version",
        "sample_id",
        "within_capture_index",
        "source_file_id",
        "source_record_index",
        "metadata_missing_mask",
        "metadata_quality_flags",
        "clock_domain",
    }
    policy: dict[str, Eligibility] = {}
    policy.update({field: Eligibility.RELATION_ALLOWED for field in relation})
    policy.update({field: Eligibility.MODEL_FEATURE_ALLOWED for field in model})
    policy.update({field: Eligibility.SPLIT_ONLY for field in split})
    policy.update({field: Eligibility.AUDIT_ONLY for field in audit})
    for field in (
        "target_label",
        "true_label",
        "attack_label",
        "occupancy_label",
        "situation_label",
        "ood_label",
    ):
        policy[field] = Eligibility.FORBIDDEN_LABEL
    for field in ("prediction", "correctness", "heldout_performance", "scenario_target"):
        policy[field] = Eligibility.FORBIDDEN_TARGET_PROXY
    return EligibilityEngine(policy)


def target_bearing_path_tokens(path: str, extra_tokens: Iterable[str] = ()) -> tuple[str, ...]:
    path_parts = [token for token in re.split(r"[^a-z0-9]+", path.lower()) if token]
    tokens = {
        token
        for token in path_parts
        if token and (token in TARGET_TOKENS or token in set(extra_tokens))
    }
    if any(re.fullmatch(r"[01]{4}", token) for token in path_parts):
        tokens.add("four_bit_occupancy_code")
    return tuple(sorted(tokens))


def assert_target_neutral_path(path: str, extra_tokens: Iterable[str] = ()) -> None:
    tokens = target_bearing_path_tokens(path, extra_tokens)
    if tokens:
        raise ValueError(f"Target-bearing path tokens are forbidden: {tokens}")
