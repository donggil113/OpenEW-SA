"""Fail-closed scientific contracts for WiSig V2 methods and information access."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


PRIMARY_SEEDS = (829, 1829, 2829, 3829, 4829)
PRIMARY_SUPPORT_BUDGET = 128
PRIMARY_CONTEXT_K = 32
SUPPORT_BUDGETS = (16, 32, 64, 128, 256)
CONTEXT_K_VALUES = (8, 16, 32, 64)


class MethodRegime(str, Enum):
    R0_PURE_INDUCTIVE = "R0_PURE_INDUCTIVE"
    R1_RECEIVER_CALIBRATION = "R1_RECEIVER_CALIBRATION"
    R2_TEST_TIME_ADAPTATION = "R2_TEST_TIME_ADAPTATION"
    DIAGNOSTIC_ORACLE = "DIAGNOSTIC_ORACLE"


@dataclass(frozen=True)
class MethodSpec:
    code: str
    scientific_name: str
    regime: MethodRegime
    source_train: bool
    source_validation: bool
    target_support_count: int
    query_samples_used_as_support: bool
    target_labels: bool
    gradient_updates_at_test: bool
    batch_stat_updates: bool
    prototype_updates: bool
    extra_parameters: bool
    source_validation_donor_support_count: int = 0
    status: str = "IMPLEMENTED"
    note: str = ""

    def validate(self) -> "MethodSpec":
        if self.target_support_count < 0 or self.source_validation_donor_support_count < 0:
            raise ValueError(f"support counts must be nonnegative for {self.code}")
        if self.target_labels and self.regime is not MethodRegime.DIAGNOSTIC_ORACLE:
            raise ValueError(f"deployable method {self.code} cannot receive target labels")
        if self.query_samples_used_as_support:
            raise ValueError(f"V2 forbids query-query support coupling for {self.code}")
        if self.regime is MethodRegime.R0_PURE_INDUCTIVE and self.target_support_count:
            raise ValueError(f"R0 method {self.code} cannot receive target support")
        return self

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["regime"] = self.regime.value
        return payload


def method_registry() -> dict[str, MethodSpec]:
    support = PRIMARY_SUPPORT_BUDGET
    rows = [
        MethodSpec("P0", "Independent ERM", MethodRegime.R0_PURE_INDUCTIVE, True, True, 0, False, False, False, False, False, False),
        MethodSpec("P0_WIDE", "Capacity-Matched Independent ERM", MethodRegime.R0_PURE_INDUCTIVE, True, True, 0, False, False, False, False, False, True),
        MethodSpec("DG_CORAL", "CORAL-Style Source-Domain Alignment", MethodRegime.R0_PURE_INDUCTIVE, True, True, 0, False, False, False, False, False, False),
        MethodSpec("DG_GROUPDRO", "Source-Receiver GroupDRO", MethodRegime.R0_PURE_INDUCTIVE, True, True, 0, False, False, False, False, False, False),
        MethodSpec("DG_DANN", "Source-Receiver Domain-Adversarial Training", MethodRegime.R0_PURE_INDUCTIVE, True, True, 0, False, False, False, False, False, True),
        MethodSpec("P1", "Mean Receiver-Context Conditioning", MethodRegime.R1_RECEIVER_CALIBRATION, True, True, support, False, False, False, False, False, True),
        MethodSpec("P2", "Attentive Receiver-Context Conditioning", MethodRegime.R1_RECEIVER_CALIBRATION, True, True, support, False, False, False, False, False, True),
        MethodSpec("P2_SHUFFLED", "Attentive Shuffled-Receiver Support", MethodRegime.R1_RECEIVER_CALIBRATION, True, True, 0, False, False, False, False, False, True, source_validation_donor_support_count=support),
        MethodSpec("P2_NULL", "Attentive Null Context", MethodRegime.R1_RECEIVER_CALIBRATION, True, True, 0, False, False, False, False, False, True),
        MethodSpec("P2_MISMATCHED_RX", "Attentive Mismatched-Receiver Support", MethodRegime.R1_RECEIVER_CALIBRATION, True, True, 0, False, False, False, False, False, True, source_validation_donor_support_count=support),
        MethodSpec("RX_NORM", "Target-Receiver Input Normalization", MethodRegime.R1_RECEIVER_CALIBRATION, True, True, support, False, False, False, False, False, False),
        MethodSpec("SOURCE_NORM", "Source-Only Input Normalization", MethodRegime.R0_PURE_INDUCTIVE, True, True, 0, False, False, False, False, False, False),
        MethodSpec("T3A", "Test-Time Template Adjustment", MethodRegime.R2_TEST_TIME_ADAPTATION, True, True, support, False, False, False, False, True, False),
        MethodSpec("ADABN", "Adaptive Batch Normalization", MethodRegime.R2_TEST_TIME_ADAPTATION, True, True, support, False, False, False, True, False, False, status="NOT_APPLICABLE", note="Frozen backbone uses GroupNorm and contains no BatchNorm."),
        MethodSpec("TENT", "Tent Entropy Minimization", MethodRegime.R2_TEST_TIME_ADAPTATION, True, True, support, False, False, True, True, False, False, status="NOT_APPLICABLE", note="Official Tent adapts normalization statistics/affine parameters; frozen backbone has GroupNorm only and BatchNorm may not be retrofitted."),
    ]
    return {row.code: row.validate() for row in rows}


FORBIDDEN_SUPPORT_FIELDS = frozenset(
    {
        "transmitter_id",
        "target",
        "target_label",
        "label",
        "class",
        "ood",
        "ood_label",
        "prediction",
        "correctness",
        "source_path",
        "source_filename",
    }
)


def validate_support_fields(fields: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    normalized = tuple(str(field) for field in fields)
    forbidden = sorted(set(normalized) & FORBIDDEN_SUPPORT_FIELDS)
    if forbidden:
        raise ValueError(f"forbidden support fields: {forbidden}")
    allowed = {"sample_id", "receiver_id", "day_id"}
    unknown = sorted(set(normalized) - allowed)
    if unknown:
        raise ValueError(f"support fields fail closed: {unknown}")
    if "sample_id" not in normalized or "receiver_id" not in normalized:
        raise ValueError("support selection requires sample_id and receiver_id")
    return normalized
