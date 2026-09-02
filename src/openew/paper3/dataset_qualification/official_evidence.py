"""Primary-source evidence records and official-source gate."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class EvidenceItem:
    requirement: str
    source_title: str
    url: str
    exact_location: str
    evidence: str
    primary_source: bool
    official_source: bool
    verified: bool
    accessed_at_utc: str

    def validate(self) -> None:
        parsed = urlparse(self.url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("Evidence URL must be a complete HTTPS URL")
        if not all((self.requirement, self.source_title, self.exact_location, self.evidence)):
            raise ValueError("Evidence fields must not be empty")

    def to_mapping(self) -> dict[str, object]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class OfficialEvidenceGate:
    passed: bool
    verified_primary_count: int
    reasons: tuple[str, ...]


def evaluate_official_evidence(items: tuple[EvidenceItem, ...]) -> OfficialEvidenceGate:
    for item in items:
        item.validate()
    verified = [
        item
        for item in items
        if item.primary_source and item.official_source and item.verified
    ]
    if verified:
        return OfficialEvidenceGate(True, len(verified), ("verified official primary evidence exists",))
    reasons = ("no independently verified official primary evidence",)
    return OfficialEvidenceGate(False, 0, reasons)
