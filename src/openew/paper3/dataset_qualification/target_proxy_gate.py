"""Fail-closed field and path target-proxy gate."""

from __future__ import annotations

from dataclasses import dataclass
import re


SAFE_RELATION_NAMES = frozenset(
    {
        "receiver_id",
        "site_id",
        "day_id",
        "acquisition_session_id",
        "capture_id",
        "channel_id",
        "campaign_id",
    }
)
FORBIDDEN_FIELD_TOKENS = frozenset(
    {
        "target",
        "label",
        "class",
        "transmitter",
        "tx",
        "device",
        "ood",
        "prediction",
        "correctness",
        "attack",
        "jammer",
        "occupancy",
    }
)


@dataclass(frozen=True)
class ProxyGateResult:
    allowed_fields: tuple[str, ...]
    rejected_fields: tuple[str, ...]
    unresolved_fields: tuple[str, ...]
    target_bearing_path_tokens: tuple[str, ...]
    passed: bool


def evaluate_target_proxy_fields(
    requested_fields: tuple[str, ...],
    *,
    independently_verified_target_neutral: tuple[str, ...],
    path: str | None = None,
    target_tokens: tuple[str, ...] = (),
) -> ProxyGateResult:
    verified = frozenset(independently_verified_target_neutral)
    allowed: list[str] = []
    rejected: list[str] = []
    unresolved: list[str] = []
    for field in requested_fields:
        tokens = set(_tokens(field))
        if tokens & FORBIDDEN_FIELD_TOKENS:
            rejected.append(field)
        elif field not in SAFE_RELATION_NAMES or field not in verified:
            unresolved.append(field)
        else:
            allowed.append(field)
    path_tokens = target_bearing_tokens(path or "", target_tokens)
    return ProxyGateResult(
        tuple(allowed),
        tuple(rejected),
        tuple(unresolved),
        path_tokens,
        not rejected and not unresolved and not path_tokens,
    )


def target_bearing_tokens(path: str, target_tokens: tuple[str, ...]) -> tuple[str, ...]:
    tokens = set(_tokens(path))
    forbidden = FORBIDDEN_FIELD_TOKENS | {token.lower() for token in target_tokens}
    return tuple(sorted(tokens & forbidden))


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(token for token in re.split(r"[^a-z0-9]+", value.lower()) if token)
