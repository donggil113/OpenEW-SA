"""Performance-independent public RF dataset qualification."""

from .adoption_decision import AdoptionDecision, decide_adoption
from .candidate_schema import CandidateEvidence, TriState
from .license_gate import LicenseGateResult, evaluate_license
from .metadata_gate import CandidateRelationEvidence, evaluate_metadata_readiness
from .storage_gate import DownloadKind, StorageGateResult, evaluate_download
from .temporal_gate import CandidateTemporalEvidence, CandidateTemporalStatus, evaluate_temporal

__all__ = [
    "AdoptionDecision",
    "CandidateEvidence",
    "CandidateRelationEvidence",
    "CandidateTemporalEvidence",
    "CandidateTemporalStatus",
    "DownloadKind",
    "LicenseGateResult",
    "StorageGateResult",
    "TriState",
    "decide_adoption",
    "evaluate_download",
    "evaluate_license",
    "evaluate_metadata_readiness",
    "evaluate_temporal",
]
