"""Dataset licence gate; repository-code licences never imply data rights."""

from __future__ import annotations

from dataclasses import dataclass

from .candidate_schema import TriState


@dataclass(frozen=True)
class LicenseGateResult:
    status: str
    permits_download: bool
    permits_derived_artifacts: bool | None
    permits_redistribution: bool | None
    reasons: tuple[str, ...]


def evaluate_license(
    *,
    license_name: str | None,
    verified: TriState,
    applies_to_dataset_payload: TriState,
    permits_research_use: TriState,
    permits_derived_artifacts: TriState,
    permits_redistribution: TriState,
    use_restrictions: tuple[str, ...] = (),
) -> LicenseGateResult:
    if verified is not TriState.TRUE or applies_to_dataset_payload is not TriState.TRUE:
        return LicenseGateResult(
            "UNRESOLVED",
            False,
            None,
            None,
            ("dataset-payload licence is not independently verified",),
        )
    if not license_name:
        return LicenseGateResult("UNRESOLVED", False, None, None, ("licence name is absent",))
    if permits_research_use is TriState.FALSE:
        return LicenseGateResult(
            "RESTRICTED", False, False, False, ("verified terms do not permit research use",)
        )
    if permits_research_use is TriState.UNKNOWN:
        return LicenseGateResult(
            "UNRESOLVED", False, None, None, ("research-use permission is unresolved",)
        )
    restrictions = tuple(item.strip() for item in use_restrictions if item.strip())
    status = (
        "CLEAR"
        if permits_derived_artifacts is TriState.TRUE and not restrictions
        else "RESTRICTED"
    )
    reasons = [
        "verified dataset terms permit research access",
        "redistribution and derived-artifact rights are evaluated separately",
    ]
    if restrictions:
        reasons.append("use restrictions: " + ", ".join(restrictions))
    return LicenseGateResult(
        status,
        True,
        _optional_bool(permits_derived_artifacts),
        _optional_bool(permits_redistribution),
        tuple(reasons),
    )


def _optional_bool(value: TriState) -> bool | None:
    if value is TriState.UNKNOWN:
        return None
    return value is TriState.TRUE
