from __future__ import annotations

import unittest

from openew.paper3.wisig_v2.contracts import (
    CONTEXT_K_VALUES,
    FORBIDDEN_SUPPORT_FIELDS,
    PRIMARY_SEEDS,
    SUPPORT_BUDGETS,
    MethodRegime,
    method_registry,
    validate_support_fields,
)
from openew.paper3.wisig_v2.runner import RunConfig


class ContractTests(unittest.TestCase):
    def test_registry_codes_are_unique(self) -> None:
        registry = method_registry()
        self.assertEqual(len(registry), len(set(registry)))

    def test_p2_is_receiver_calibration(self) -> None:
        self.assertEqual(method_registry()["P2"].regime, MethodRegime.R1_RECEIVER_CALIBRATION)

    def test_t3a_is_tta(self) -> None:
        self.assertEqual(method_registry()["T3A"].regime, MethodRegime.R2_TEST_TIME_ADAPTATION)

    def test_shuffled_and_mismatched_support_is_not_target_receiver_support(self) -> None:
        registry = method_registry()
        for model in ("P2_SHUFFLED", "P2_MISMATCHED_RX"):
            self.assertEqual(registry[model].target_support_count, 0)
            self.assertEqual(registry[model].source_validation_donor_support_count, 128)

    def test_null_context_has_zero_support(self) -> None:
        spec = method_registry()["P2_NULL"]
        self.assertEqual(spec.target_support_count, 0)
        self.assertEqual(spec.source_validation_donor_support_count, 0)

    def test_p0_is_pure_inductive(self) -> None:
        self.assertEqual(method_registry()["P0"].regime, MethodRegime.R0_PURE_INDUCTIVE)

    def test_adabn_not_applicable(self) -> None:
        self.assertEqual(method_registry()["ADABN"].status, "NOT_APPLICABLE")

    def test_tent_not_applicable(self) -> None:
        self.assertEqual(method_registry()["TENT"].status, "NOT_APPLICABLE")

    def test_query_support_coupling_rejected(self) -> None:
        spec = method_registry()["P2"]
        with self.assertRaises(ValueError):
            type(spec)(**{**spec.__dict__, "query_samples_used_as_support": True}).validate()

    def test_deployable_target_label_rejected(self) -> None:
        spec = method_registry()["P2"]
        with self.assertRaises(ValueError):
            type(spec)(**{**spec.__dict__, "target_labels": True}).validate()

    def test_support_whitelist_accepts_required_fields(self) -> None:
        self.assertEqual(validate_support_fields(["sample_id", "receiver_id"]), ("sample_id", "receiver_id"))

    def test_unknown_support_field_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            validate_support_fields(["sample_id", "receiver_id", "mystery"])

    def test_missing_sample_id_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_support_fields(["receiver_id"])

    def test_missing_receiver_id_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_support_fields(["sample_id"])

    def test_nonprimary_seed_rejected(self) -> None:
        with self.assertRaises(ValueError):
            RunConfig("receiver_loso_00", "P0", 1).validate()

    def test_unblinded_execution_rejected(self) -> None:
        with self.assertRaises(ValueError):
            RunConfig("receiver_loso_00", "P0", 829, blind_target_metrics=False).validate()

    def test_unknown_data_variant_rejected(self) -> None:
        with self.assertRaises(ValueError):
            RunConfig("receiver_loso_00", "P0", 829, data_variant="mystery").validate()

    def test_context_larger_than_support_rejected(self) -> None:
        with self.assertRaises(ValueError):
            RunConfig("receiver_loso_00", "P2", 829, support_budget=16, context_k=32).validate()


def _forbidden_test(field: str):
    def test(self: ContractTests) -> None:
        with self.assertRaises(ValueError):
            validate_support_fields(["sample_id", "receiver_id", field])
    return test


for _field in sorted(FORBIDDEN_SUPPORT_FIELDS):
    setattr(ContractTests, f"test_forbidden_field_{_field}", _forbidden_test(_field))


def _valid_seed_test(seed: int):
    def test(self: ContractTests) -> None:
        self.assertEqual(RunConfig("receiver_loso_00", "P0", seed).validate().seed, seed)
    return test


for _seed in PRIMARY_SEEDS:
    setattr(ContractTests, f"test_valid_seed_{_seed}", _valid_seed_test(_seed))


def _valid_budget_test(budget: int):
    def test(self: ContractTests) -> None:
        self.assertEqual(RunConfig("receiver_loso_00", "P2", 829, support_budget=budget, context_k=min(8, budget)).validate().support_budget, budget)
    return test


for _budget in SUPPORT_BUDGETS:
    setattr(ContractTests, f"test_valid_budget_{_budget}", _valid_budget_test(_budget))


def _valid_k_test(k: int):
    def test(self: ContractTests) -> None:
        self.assertEqual(RunConfig("receiver_loso_00", "P2", 829, context_k=k).validate().context_k, k)
    return test


for _k in CONTEXT_K_VALUES:
    setattr(ContractTests, f"test_valid_context_k_{_k}", _valid_k_test(_k))


if __name__ == "__main__":
    unittest.main()
