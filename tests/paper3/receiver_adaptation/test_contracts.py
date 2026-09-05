from __future__ import annotations
import pytest
from openew.paper3.receiver_adaptation.contracts import BENCHMARK_SEEDS, CATASTROPHIC_MACRO_F1_DROP, EvidenceCategory, InformationRegime, MethodSpec, SUPPORT_BUDGETS, information_budget_rows, method_registry, require_method, validate_support_budget


@pytest.mark.parametrize("seed", [829, 1829, 2829, 3829, 4829])
def test_seed_is_frozen(seed: int) -> None:
    assert seed in BENCHMARK_SEEDS


@pytest.mark.parametrize("budget", [0, 16, 32, 64, 128, 256])
def test_support_budget_is_frozen(budget: int) -> None:
    assert validate_support_budget(budget) == budget


@pytest.mark.parametrize("budget", [-1, 1, 8, 31, 129, 512])
def test_support_budget_rejects_unfrozen_value(budget: int) -> None:
    with pytest.raises(ValueError, match="not frozen"):
        validate_support_budget(budget)


@pytest.mark.parametrize("code", ["P0", "P0_WIDE", "DG_CORAL", "DG_DANN", "DG_GROUPDRO", "RX_NORM", "T3A", "P2", "SUP_FT_128", "ADABN_128", "TENT_128", "SHEN_GRL", "OTHER_TTA", "OTHER_RF"])
def test_every_registry_method_validates(code: str) -> None:
    assert require_method(code).code == code


@pytest.mark.parametrize("code", ["", "tent", "P3", "SHEN", "UNKNOWN", "label"])
def test_unknown_method_fails_closed(code: str) -> None:
    with pytest.raises(ValueError, match="fails closed"):
        require_method(code)


@pytest.mark.parametrize("code", ["P0", "P0_WIDE", "DG_CORAL", "DG_DANN", "DG_GROUPDRO"])
def test_source_only_methods_have_no_target_support(code: str) -> None:
    row = require_method(code)
    assert row.regime is InformationRegime.SOURCE_ONLY and row.target_support_packets == 0 and not row.target_labels


@pytest.mark.parametrize("code", ["RX_NORM", "T3A", "P2"])
def test_unlabeled_methods_share_information_budget(code: str) -> None:
    row = require_method(code)
    assert row.target_support_packets == 128 and not row.target_labels and not row.query_access_during_adaptation


@pytest.mark.parametrize("code", ["ADABN_128", "TENT_128"])
def test_batchnorm_methods_not_applicable(code: str) -> None:
    row = require_method(code)
    assert row.evidence is EvidenceCategory.NOT_APPLICABLE and row.status == "NOT_APPLICABLE"


@pytest.mark.parametrize("code", ["SHEN_GRL", "OTHER_TTA", "OTHER_RF"])
def test_unfaithful_methods_not_implemented(code: str) -> None:
    assert require_method(code).evidence is EvidenceCategory.EXCLUDED_UNFAITHFUL


def test_target_labels_fail_outside_oracle() -> None:
    with pytest.raises(ValueError, match="oracle-only"):
        MethodSpec("BAD", "bad", InformationRegime.UNLABELED_CALIBRATION, EvidenceCategory.DEPLOYABLE_METHOD, True, True, True, 128, True, True, False, False, False, False, False, "none").validate()


def test_query_access_always_fails() -> None:
    with pytest.raises(ValueError, match="query leakage"):
        MethodSpec("BAD", "bad", InformationRegime.UNLABELED_CALIBRATION, EvidenceCategory.DEPLOYABLE_METHOD, True, True, True, 128, False, True, True, False, False, False, False, "none").validate()


def test_source_method_cannot_receive_support() -> None:
    with pytest.raises(ValueError, match="source-only"):
        MethodSpec("BAD", "bad", InformationRegime.SOURCE_ONLY, EvidenceCategory.DEPLOYABLE_METHOD, True, True, True, 1, False, False, False, False, False, False, False, "none").validate()


def test_information_ledger_stable_and_unique() -> None:
    rows = information_budget_rows()
    assert len(rows) == len(method_registry()) == 14
    assert len({row["code"] for row in rows}) == 14
    assert rows == sorted(rows, key=lambda row: row["code"])


def test_catastrophic_threshold_frozen() -> None:
    assert CATASTROPHIC_MACRO_F1_DROP == 0.05 and SUPPORT_BUDGETS == (0, 16, 32, 64, 128, 256)
