from __future__ import annotations

import unittest

from openew.paper3.wisig_v2.decision import MechanismEvidence, evaluate_mechanism_go


def evidence(**changes):
    values = {
        "mean_deltas": {
            "P2_MINUS_P0": 0.01,
            "P2_MINUS_P0_WIDE": 0.01,
            "P2_MINUS_P2_SHUFFLED": 0.01,
            "P2_MINUS_P2_MISMATCHED_RX": 0.01,
            "P2_MINUS_BEST_TTA": 0.0,
        },
        "positive_p2_minus_p0_receivers": 17,
        "positive_hardware_families": 2,
        "same_class_excluded_minus_p0": 0.001,
        "same_class_excluded_full_coverage": True,
        "integrity_pass": True,
        "disjoint_support_query_pass": True,
    }
    values.update(changes)
    return MechanismEvidence(**values)


class DecisionTests(unittest.TestCase):
    def test_all_criteria_go(self) -> None:
        self.assertEqual(evaluate_mechanism_go(evidence())["verdict"], "GO")

    def test_mechanism_failure_is_conditional_when_p2_beats_p0(self) -> None:
        self.assertEqual(evaluate_mechanism_go(evidence(same_class_excluded_minus_p0=-0.1))["verdict"], "CONDITIONAL_GO")

    def test_no_p0_gain_is_no_go(self) -> None:
        deltas = dict(evidence().mean_deltas); deltas["P2_MINUS_P0"] = 0.0
        self.assertEqual(evaluate_mechanism_go(evidence(mean_deltas=deltas))["verdict"], "NO_GO")

    def test_integrity_failure_is_no_go(self) -> None:
        self.assertEqual(evaluate_mechanism_go(evidence(integrity_pass=False))["verdict"], "NO_GO")

    def test_disjoint_failure_is_no_go(self) -> None:
        self.assertEqual(evaluate_mechanism_go(evidence(disjoint_support_query_pass=False))["verdict"], "NO_GO")

    def test_missing_metric_rejected(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_mechanism_go(evidence(mean_deltas={"P2_MINUS_P0": 1.0}))

    def test_receiver_majority_boundary(self) -> None:
        self.assertEqual(evaluate_mechanism_go(evidence(positive_p2_minus_p0_receivers=16))["verdict"], "CONDITIONAL_GO")

    def test_one_hardware_family_insufficient(self) -> None:
        self.assertEqual(evaluate_mechanism_go(evidence(positive_hardware_families=1))["verdict"], "CONDITIONAL_GO")

    def test_best_tta_tie_is_competitive(self) -> None:
        self.assertTrue(evaluate_mechanism_go(evidence())["checks"]["P2_COMPETITIVE_WITH_BEST_TTA"])

    def test_failed_checks_are_reported(self) -> None:
        result = evaluate_mechanism_go(evidence(positive_hardware_families=0))
        self.assertIn("MULTIPLE_HARDWARE_FAMILIES_POSITIVE", result["failed_checks"])

    def test_partial_same_class_excluded_coverage_is_not_go(self) -> None:
        self.assertEqual(evaluate_mechanism_go(evidence(same_class_excluded_full_coverage=False))["verdict"], "CONDITIONAL_GO")


if __name__ == "__main__":
    unittest.main()
