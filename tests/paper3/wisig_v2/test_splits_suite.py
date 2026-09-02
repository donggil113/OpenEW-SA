from __future__ import annotations

import json
import unittest
from pathlib import Path

from openew.paper3.wisig_v2.splits import load_hardware_map, select_validation_receivers
from openew.paper3.wisig_v2.suite import (
    PRIMARY_MODELS,
    context_k_plan,
    day_secondary_plan,
    deduplicate_plan,
    plan_summary,
    primary_loso_plan,
    support_budget_plan,
)


REPOSITORY = Path(__file__).resolve().parents[3]


class SplitSuiteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.hardware = {"a": "A", "b": "B", "c": "C", "d": "A", "e": "B", "f": "C"}

    def test_validation_count(self) -> None:
        result = select_validation_receivers(list(self.hardware), "a", self.hardware)
        self.assertEqual(len(result), 3)

    def test_validation_excludes_test(self) -> None:
        self.assertNotIn("a", select_validation_receivers(list(self.hardware), "a", self.hardware))

    def test_validation_covers_hardware(self) -> None:
        result = select_validation_receivers(list(self.hardware), "a", self.hardware)
        self.assertEqual({self.hardware[value] for value in result}, {"A", "B", "C"})

    def test_validation_deterministic(self) -> None:
        left = select_validation_receivers(list(self.hardware), "a", self.hardware)
        right = select_validation_receivers(list(reversed(self.hardware)), "a", self.hardware)
        self.assertEqual(left, right)

    def test_not_enough_receivers_rejected(self) -> None:
        with self.assertRaises(ValueError):
            select_validation_receivers(["a", "b"], "a", {"a": "A", "b": "B"})

    def test_hardware_config_has_32_receivers(self) -> None:
        mapping = load_hardware_map(REPOSITORY / "configs/paper3/wisig_v2/receiver_hardware_v1.json")
        self.assertEqual(len(mapping), 32)

    def test_hardware_config_families(self) -> None:
        mapping = load_hardware_map(REPOSITORY / "configs/paper3/wisig_v2/receiver_hardware_v1.json")
        self.assertEqual(set(mapping.values()), {"B210", "N210", "X310"})

    def test_primary_plan_count(self) -> None:
        self.assertEqual(len(primary_loso_plan()), 32 * len(PRIMARY_MODELS) * 5)

    def test_day_plan_count(self) -> None:
        self.assertEqual(len(day_secondary_plan()), 4 * len(PRIMARY_MODELS) * 5)

    def test_support_plan_count(self) -> None:
        self.assertEqual(len(support_budget_plan()), 32 * 5 * 5)

    def test_context_k_plan_count(self) -> None:
        self.assertEqual(len(context_k_plan()), 32 * 4 * 5)

    def test_all_primary_blinded(self) -> None:
        self.assertTrue(all(config.blind_target_metrics for _, config in primary_loso_plan()))

    def test_all_primary_five_seeds(self) -> None:
        self.assertEqual({config.seed for _, config in primary_loso_plan()}, {829, 1829, 2829, 3829, 4829})

    def test_primary_support_128(self) -> None:
        self.assertEqual({config.support_budget for _, config in primary_loso_plan()}, {128})

    def test_primary_k_32(self) -> None:
        self.assertEqual({config.context_k for _, config in primary_loso_plan()}, {32})

    def test_support_16_uses_k16(self) -> None:
        values = [config.context_k for _, config in support_budget_plan() if config.support_budget == 16]
        self.assertEqual(set(values), {16})

    def test_dedup_reuses_primary_p2(self) -> None:
        rows = primary_loso_plan() + support_budget_plan() + context_k_plan()
        self.assertLess(len(deduplicate_plan(rows)), len(rows))

    def test_plan_summary_primary_unit(self) -> None:
        self.assertTrue(plan_summary()["receiver_is_primary_evaluation_unit"])

    def test_preregistration_has_no_dynamic_claim(self) -> None:
        text = (REPOSITORY / "papers/paper3_wisig_methods_remediation/methods_remediation_preregistration_v2.md").read_text(encoding="utf-8").lower()
        self.assertIn("no dynamic", text)

    def test_information_matrix_denies_labels(self) -> None:
        text = (REPOSITORY / "papers/paper3_wisig_methods_remediation/information_budget_matrix.md").read_text(encoding="utf-8")
        self.assertNotIn("| Yes | Yes | Yes |", text)


if __name__ == "__main__":
    unittest.main()
