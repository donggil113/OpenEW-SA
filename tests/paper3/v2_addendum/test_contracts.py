from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from openew.paper3.v2_addendum.contracts import (
    ADDENDUM_SEEDS,
    SUPPORT_BUDGETS,
    EvidenceCategory,
    classify_condition,
    require_posthoc_output_path,
    require_unique,
    validate_seed,
    validate_support_budget,
)


class ContractTests(unittest.TestCase):
    def test_seed_count_is_five(self) -> None:
        self.assertEqual(len(ADDENDUM_SEEDS), 5)

    def test_seed_order_is_frozen(self) -> None:
        self.assertEqual(ADDENDUM_SEEDS, (829, 1829, 2829, 3829, 4829))

    def test_budget_order_is_frozen(self) -> None:
        self.assertEqual(SUPPORT_BUDGETS, (16, 32, 64, 128, 256))

    def test_invalid_seed_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_seed(1)

    def test_invalid_budget_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_support_budget(127)

    def test_unknown_condition_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            classify_condition("best_result")

    def test_unique_preserves_string_identifiers(self) -> None:
        self.assertEqual(require_unique(["001", "01"], name="ids"), ("001", "01"))

    def test_duplicate_identifier_rejected(self) -> None:
        with self.assertRaises(ValueError):
            require_unique(["001", "001"], name="ids")

    def test_output_inside_frozen_root_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            frozen = Path(tmp) / "v2"
            with self.assertRaises(ValueError):
                require_posthoc_output_path(frozen / "analysis" / "new", frozen)

    def test_frozen_root_itself_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            frozen = Path(tmp) / "v2"
            with self.assertRaises(ValueError):
                require_posthoc_output_path(frozen, frozen)

    def test_external_output_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(require_posthoc_output_path(root / "addendum", root / "v2"), (root / "addendum").resolve())


def _seed_test(seed: int):
    def test(self: ContractTests) -> None:
        self.assertEqual(validate_seed(seed), seed)
    return test


for _seed in ADDENDUM_SEEDS:
    setattr(ContractTests, f"test_frozen_seed_{_seed}", _seed_test(_seed))


def _budget_test(budget: int):
    def test(self: ContractTests) -> None:
        self.assertEqual(validate_support_budget(budget), budget)
    return test


for _budget in SUPPORT_BUDGETS:
    setattr(ContractTests, f"test_frozen_budget_{_budget}", _budget_test(_budget))


def _category_test(condition: str, category: EvidenceCategory):
    def test(self: ContractTests) -> None:
        self.assertIs(classify_condition(condition), category)
    return test


for _condition, _category in {
    "DISJOINT_NATURAL": EvidenceCategory.DEPLOYABLE_METHOD,
    "NATURAL": EvidenceCategory.DEPLOYABLE_METHOD,
    "QUERY_COUPLED_CHUNK": EvidenceCategory.LABEL_FREE_CONTROL,
    "FULL_RECEIVER_PARTITION": EvidenceCategory.LABEL_FREE_CONTROL,
    "SHUFFLED": EvidenceCategory.LABEL_FREE_CONTROL,
    "NULL": EvidenceCategory.LABEL_FREE_CONTROL,
    "MISMATCHED_RX": EvidenceCategory.LABEL_FREE_CONTROL,
    "SAME_CLASS_EXCLUDED_ORACLE": EvidenceCategory.ORACLE_DIAGNOSTIC,
    "SAME_CLASS_ONLY_ORACLE": EvidenceCategory.ORACLE_DIAGNOSTIC,
    "TRANSMITTER_PURE_ORACLE": EvidenceCategory.ORACLE_DIAGNOSTIC,
}.items():
    setattr(ContractTests, f"test_category_{_condition.lower()}", _category_test(_condition, _category))


if __name__ == "__main__":
    unittest.main()
