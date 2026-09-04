"""Pre-unblinding operationalization of the V2 mechanism GO rule."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class MechanismEvidence:
    mean_deltas: Mapping[str, float]
    positive_p2_minus_p0_receivers: int
    positive_hardware_families: int
    same_class_excluded_minus_p0: float
    same_class_excluded_full_coverage: bool
    integrity_pass: bool
    disjoint_support_query_pass: bool


REQUIRED_POSITIVE = (
    "P2_MINUS_P0",
    "P2_MINUS_P0_WIDE",
    "P2_MINUS_P2_SHUFFLED",
    "P2_MINUS_P2_MISMATCHED_RX",
)


def evaluate_mechanism_go(evidence: MechanismEvidence) -> dict[str, object]:
    """Apply the fixed literal criteria without consulting any tuning choices."""

    missing = [name for name in (*REQUIRED_POSITIVE, "P2_MINUS_BEST_TTA") if name not in evidence.mean_deltas]
    if missing:
        raise ValueError(f"missing decision evidence: {missing}")
    checks: dict[str, bool] = {
        **{name: float(evidence.mean_deltas[name]) > 0.0 for name in REQUIRED_POSITIVE},
        "P2_COMPETITIVE_WITH_BEST_TTA": float(evidence.mean_deltas["P2_MINUS_BEST_TTA"]) >= 0.0,
        "SAME_CLASS_EXCLUDED_SURVIVES": float(evidence.same_class_excluded_minus_p0) > 0.0,
        "SAME_CLASS_EXCLUDED_FULL_COVERAGE": bool(evidence.same_class_excluded_full_coverage),
        "MAJORITY_OF_RECEIVERS_POSITIVE": int(evidence.positive_p2_minus_p0_receivers) >= 17,
        "MULTIPLE_HARDWARE_FAMILIES_POSITIVE": int(evidence.positive_hardware_families) >= 2,
        "INTEGRITY_PASS": bool(evidence.integrity_pass),
        "DISJOINT_SUPPORT_QUERY_PASS": bool(evidence.disjoint_support_query_pass),
    }
    if all(checks.values()):
        verdict = "GO"
    elif checks["INTEGRITY_PASS"] and checks["DISJOINT_SUPPORT_QUERY_PASS"] and checks["P2_MINUS_P0"]:
        verdict = "CONDITIONAL_GO"
    else:
        verdict = "NO_GO"
    return {
        "verdict": verdict,
        "checks": checks,
        "failed_checks": sorted(name for name, passed in checks.items() if not passed),
        "rule_frozen_before_unblinding": True,
    }
