"""Predeclared automatic acquisition limits."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


METADATA_LIMIT_BYTES = 500_000_000
SAMPLE_LIMIT_BYTES = 5_000_000_000
FREE_SPACE_FRACTION_LIMIT = 0.10


class DownloadKind(str, Enum):
    METADATA = "METADATA"
    SAMPLE = "SAMPLE"
    FULL_DATASET = "FULL_DATASET"


@dataclass(frozen=True)
class StorageGateResult:
    allowed: bool
    maximum_allowed_bytes: int
    requested_bytes: int | None
    reasons: tuple[str, ...]


def evaluate_download(
    *,
    kind: DownloadKind,
    requested_bytes: int | None,
    free_bytes: int,
    license_verified: bool,
    official_source_verified: bool,
    secret_required: bool = False,
) -> StorageGateResult:
    if free_bytes < 0:
        raise ValueError("free_bytes must be non-negative")
    fraction_limit = int(free_bytes * FREE_SPACE_FRACTION_LIMIT)
    kind_limit = METADATA_LIMIT_BYTES if kind is DownloadKind.METADATA else SAMPLE_LIMIT_BYTES
    maximum = min(kind_limit, fraction_limit)
    reasons: list[str] = []
    if requested_bytes is None:
        reasons.append("download size is unknown")
    elif requested_bytes < 0:
        raise ValueError("requested_bytes must be non-negative")
    elif requested_bytes > maximum:
        reasons.append("requested bytes exceed the smaller of the kind and free-space limits")
    if kind is DownloadKind.FULL_DATASET:
        reasons.append("full dataset payloads are never downloaded automatically")
    if not official_source_verified:
        reasons.append("official source is not verified")
    if kind is not DownloadKind.METADATA and not license_verified:
        reasons.append("dataset-payload licence is not verified")
    if secret_required:
        reasons.append("authentication secret is required")
    return StorageGateResult(not reasons, maximum, requested_bytes, tuple(reasons or ["all gates pass"]))
