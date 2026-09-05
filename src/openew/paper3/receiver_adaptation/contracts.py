"""Frozen information and method contracts for the receiver benchmark."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

BENCHMARK_SEEDS = (829, 1829, 2829, 3829, 4829)
PRIMARY_SUPPORT_BUDGET = 128
PRIMARY_CONTEXT_K = 32
SUPPORT_BUDGETS = (0, 16, 32, 64, 128, 256)
PRIMARY_RECEIVER_COUNT = 32
CATASTROPHIC_MACRO_F1_DROP = 0.05
INFERENCE_RNG_SEED = 20_260_903
BOOTSTRAP_REPLICATES = 10_000
SIGN_FLIP_PERMUTATIONS = 100_000


class InformationRegime(str, Enum):
    SOURCE_ONLY = "R0_SOURCE_ONLY"
    UNLABELED_CALIBRATION = "R1_UNLABELED_TARGET_RECEIVER_CALIBRATION"
    SUPERVISED_ORACLE = "R2_SUPERVISED_TARGET_ADAPTATION_ORACLE"


class EvidenceCategory(str, Enum):
    FROZEN_REFERENCE = "FROZEN_REFERENCE"
    DEPLOYABLE_METHOD = "DEPLOYABLE_METHOD"
    LABEL_FREE_CONTROL = "LABEL_FREE_CONTROL"
    LABEL_DEPENDENT_ORACLE = "LABEL_DEPENDENT_ORACLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    EXCLUDED_UNFAITHFUL = "EXCLUDED_UNFAITHFUL"


@dataclass(frozen=True)
class MethodSpec:
    code: str
    scientific_name: str
    regime: InformationRegime
    evidence: EvidenceCategory
    source_labels: bool
    source_receiver_ids: bool
    source_validation: bool
    target_support_packets: int
    target_labels: bool
    target_receiver_id: bool
    query_access_during_adaptation: bool
    test_gradient_updates: bool
    batch_stat_updates: bool
    prototype_updates: bool
    extra_parameters: bool
    adapted_parameter_scope: str
    status: str = "IMPLEMENTED"
    note: str = ""

    def validate(self) -> "MethodSpec":
        if self.target_support_packets < 0:
            raise ValueError(f"negative support budget for {self.code}")
        if self.query_access_during_adaptation:
            raise ValueError(f"query leakage is forbidden for {self.code}")
        if self.target_labels and self.regime is not InformationRegime.SUPERVISED_ORACLE:
            raise ValueError(f"target labels are oracle-only: {self.code}")
        if self.regime is InformationRegime.SOURCE_ONLY and self.target_support_packets:
            raise ValueError(f"source-only method has target support: {self.code}")
        return self

    def to_dict(self) -> dict[str, Any]:
        row = asdict(self)
        row["regime"] = self.regime.value
        row["evidence"] = self.evidence.value
        return row


def _source(code: str, name: str, *, extra: bool = False) -> MethodSpec:
    return MethodSpec(
        code, name, InformationRegime.SOURCE_ONLY, EvidenceCategory.FROZEN_REFERENCE,
        True, True, True, 0, False, False, False, False, False, False, extra, "none",
    )


def method_registry() -> dict[str, MethodSpec]:
    """Return the preregistered registry; unknown method names fail closed."""
    rows = [
        _source("P0", "Independent ERM"),
        _source("P0_WIDE", "Capacity-Matched Independent ERM", extra=True),
        _source("DG_CORAL", "CORAL-Style Source-Domain Alignment"),
        _source("DG_DANN", "Source-Receiver Domain-Adversarial Training", extra=True),
        _source("DG_GROUPDRO", "Source-Receiver GroupDRO"),
        MethodSpec("RX_NORM", "Target-Receiver Input Normalization", InformationRegime.UNLABELED_CALIBRATION, EvidenceCategory.FROZEN_REFERENCE, True, True, True, 128, False, True, False, False, False, False, False, "input statistics"),
        MethodSpec("T3A", "Test-Time Template Adjustment", InformationRegime.UNLABELED_CALIBRATION, EvidenceCategory.FROZEN_REFERENCE, True, True, True, 128, False, True, False, False, False, True, False, "class prototypes"),
        MethodSpec("P2", "Attentive Receiver-Context Conditioning", InformationRegime.UNLABELED_CALIBRATION, EvidenceCategory.FROZEN_REFERENCE, True, True, True, 128, False, True, False, False, False, False, True, "none; frozen conditional inference"),
        MethodSpec("SUP_FT_128", "Supervised Target-Receiver Fine-Tuning", InformationRegime.SUPERVISED_ORACLE, EvidenceCategory.LABEL_DEPENDENT_ORACLE, True, True, True, 128, True, True, False, True, False, False, False, "linear classifier only", note="Diagnostic ceiling; excluded from deployable comparisons and Holm family."),
        MethodSpec("ADABN_128", "Adaptive Batch Normalization", InformationRegime.UNLABELED_CALIBRATION, EvidenceCategory.NOT_APPLICABLE, True, True, True, 128, False, True, False, False, True, False, False, "BatchNorm statistics", status="NOT_APPLICABLE", note="Frozen backbone has GroupNorm and zero BatchNorm modules."),
        MethodSpec("TENT_128", "Tent Entropy Minimization", InformationRegime.UNLABELED_CALIBRATION, EvidenceCategory.NOT_APPLICABLE, True, True, True, 128, False, True, False, True, True, False, False, "normalization affine parameters", status="NOT_APPLICABLE", note="Official Tent requires adaptable normalization; BatchNorm may not be retrofitted."),
        MethodSpec("SHEN_GRL", "Shen Receiver-Adversarial RFFI", InformationRegime.SOURCE_ONLY, EvidenceCategory.EXCLUDED_UNFAITHFUL, True, True, True, 0, False, False, False, False, False, False, True, "full source network", status="EXCLUDED_UNFAITHFUL", note="Official 52x126 channel-independent spectrogram CNN is incompatible with frozen 256-IQ input."),
        MethodSpec("OTHER_TTA", "Additional Prototype/Classifier TTA", InformationRegime.UNLABELED_CALIBRATION, EvidenceCategory.EXCLUDED_UNFAITHFUL, True, True, True, 128, False, True, False, False, False, True, False, "unfrozen", status="NOT_SELECTED", note="No second method passed faithfulness and bounded-support applicability gates."),
        MethodSpec("OTHER_RF", "Additional RF Receiver-Robust Baseline", InformationRegime.SOURCE_ONLY, EvidenceCategory.EXCLUDED_UNFAITHFUL, True, True, True, 0, False, False, False, False, False, False, True, "unfrozen", status="NOT_SELECTED", note="Published candidates lacked a faithful 256-IQ implementation under the frozen protocol."),
    ]
    registry = {row.code: row.validate() for row in rows}
    if len(registry) != len(rows):
        raise RuntimeError("duplicate method code")
    return registry


def require_method(code: str) -> MethodSpec:
    try:
        return method_registry()[str(code)]
    except KeyError as exc:
        raise ValueError(f"unknown benchmark method fails closed: {code}") from exc


def information_budget_rows() -> list[dict[str, Any]]:
    return [method_registry()[code].to_dict() for code in sorted(method_registry())]


def validate_support_budget(budget: int) -> int:
    if int(budget) not in SUPPORT_BUDGETS:
        raise ValueError(f"support budget is not frozen: {budget}")
    return int(budget)
