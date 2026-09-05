"""Receiver-adaptation benchmark, Shen adapter, and collection QA."""

from .contracts import (
    BENCHMARK_SEEDS,
    PRIMARY_SUPPORT_BUDGET,
    SUPPORT_BUDGETS,
    EvidenceCategory,
    InformationRegime,
    MethodSpec,
    method_registry,
)
from .frozen import FrozenV2Audit, verify_frozen_v2

__all__ = [
    "BENCHMARK_SEEDS",
    "PRIMARY_SUPPORT_BUDGET",
    "SUPPORT_BUDGETS",
    "EvidenceCategory",
    "FrozenV2Audit",
    "InformationRegime",
    "MethodSpec",
    "method_registry",
    "verify_frozen_v2",
]
