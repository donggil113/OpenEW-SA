"""Conservative adoption decision independent of predictive performance."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .candidate_schema import AccessStatus
from .license_gate import LicenseGateResult
from .official_evidence import OfficialEvidenceGate
from .storage_gate import StorageGateResult
from .target_proxy_gate import ProxyGateResult
from .temporal_gate import CandidateTemporalStatus, TemporalGateResult


@dataclass(frozen=True)
class AdoptionDecision:
    access: str
    license: str
    static_domain_generalization: str
    static_relational: str
    temporal: str
    dynamic: str
    next_model_experiment_authorized: bool
    reasons: tuple[str, ...]

    def to_mapping(self) -> dict[str, object]:
        return asdict(self)


def decide_adoption(
    *,
    access_status: AccessStatus,
    official_evidence: OfficialEvidenceGate,
    license_gate: LicenseGateResult,
    storage_gate: StorageGateResult,
    proxy_gate: ProxyGateResult,
    temporal_gate: TemporalGateResult,
    readiness_highest: str,
    split_protocol_frozen: bool,
    task_distinct: bool,
) -> AdoptionDecision:
    access = (
        "GO"
        if access_status is AccessStatus.PUBLIC_DIRECT and official_evidence.passed
        else "CONDITIONAL GO"
        if access_status in {AccessStatus.PUBLIC_METADATA_ONLY, AccessStatus.AUTHENTICATION_REQUIRED}
        and official_evidence.passed
        else "NO-GO"
    )
    license_status = license_gate.status
    readiness = str(readiness_highest)
    static_ready = readiness in {
        "STATIC_RELATIONAL",
        "STATIC_HYPERGRAPH",
        "TEMPORAL_RELATIONAL",
        "DYNAMIC_HYPERGRAPH",
    }
    static_dg = "GO" if task_distinct and split_protocol_frozen else "CONDITIONAL GO" if task_distinct else "NO-GO"
    static_relational = (
        "GO"
        if static_ready and proxy_gate.passed and license_status == "CLEAR" and access == "GO"
        else "CONDITIONAL GO"
        if static_ready and proxy_gate.passed and access != "NO-GO"
        else "NO-GO"
    )
    temporal = (
        "GO"
        if temporal_gate.status is CandidateTemporalStatus.VALID_TEMPORAL_CONTEXT
        and static_relational == "GO"
        else "CONDITIONAL GO"
        if temporal_gate.status is CandidateTemporalStatus.VALID_TEMPORAL_CONTEXT
        else "NO-GO"
    )
    dynamic = (
        "GO" if readiness == "DYNAMIC_HYPERGRAPH" and temporal == "GO" else "CONDITIONAL GO"
        if readiness == "DYNAMIC_HYPERGRAPH" and temporal != "NO-GO"
        else "NO-GO"
    )
    authorized = all(
        (
            static_relational == "GO",
            storage_gate.allowed,
            split_protocol_frozen,
            task_distinct,
            proxy_gate.passed,
        )
    )
    reasons = tuple(
        reason
        for reason in (
            *official_evidence.reasons,
            *license_gate.reasons,
            *storage_gate.reasons,
            *temporal_gate.reasons,
            "target-proxy gate passed" if proxy_gate.passed else "target-proxy gate failed",
            "split protocol frozen" if split_protocol_frozen else "split protocol is not frozen",
            "task distinctness established" if task_distinct else "task distinctness is unresolved or failed",
        )
    )
    return AdoptionDecision(
        access,
        license_status,
        static_dg,
        static_relational,
        temporal,
        dynamic,
        authorized,
        reasons,
    )
