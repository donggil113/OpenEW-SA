from __future__ import annotations

import inspect
import unittest

import numpy as np

from openew.paper3.v2_addendum.composition import ORACLE_CONDITIONS, oracle_supports_by_label


class CompositionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.support = tuple(range(12))
        self.labels = np.asarray([0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2])
        self.sample_ids = np.asarray([f"s{i:03d}" for i in range(12)])

    def test_three_oracle_conditions_are_fixed(self) -> None:
        self.assertEqual(len(ORACLE_CONDITIONS), 3)

    def test_builder_requires_labels_explicitly(self) -> None:
        self.assertIn("labels", inspect.signature(oracle_supports_by_label).parameters)

    def test_builder_has_no_predictions_argument(self) -> None:
        self.assertNotIn("predictions", inspect.signature(oracle_supports_by_label).parameters)

    def test_deterministic(self) -> None:
        a = oracle_supports_by_label(self.support, self.labels, self.sample_ids, seed=829)
        b = oracle_supports_by_label(self.support, self.labels, self.sample_ids, seed=829)
        self.assertEqual(a, b)

    def test_same_class_excluded(self) -> None:
        values = oracle_supports_by_label(self.support, self.labels, self.sample_ids, seed=829)["SAME_CLASS_EXCLUDED_ORACLE"]
        for label, indices in values.items():
            self.assertTrue(all(self.labels[index] != label for index in indices))

    def test_same_class_only(self) -> None:
        values = oracle_supports_by_label(self.support, self.labels, self.sample_ids, seed=829)["SAME_CLASS_ONLY_ORACLE"]
        for label, indices in values.items():
            self.assertTrue(all(self.labels[index] == label for index in indices))

    def test_transmitter_pure_same_pool_for_queries(self) -> None:
        values = oracle_supports_by_label(self.support, self.labels, self.sample_ids, seed=829)["TRANSMITTER_PURE_ORACLE"]
        pools = list(values.values())
        self.assertTrue(all(pool == pools[0] for pool in pools))

    def test_support_width_capped(self) -> None:
        values = oracle_supports_by_label(self.support, self.labels, self.sample_ids, seed=829, k=2)
        self.assertTrue(all(len(v) <= 2 for group in values.values() for v in group.values()))

    def test_identifiers_do_not_change(self) -> None:
        original = self.sample_ids.copy()
        oracle_supports_by_label(self.support, self.labels, self.sample_ids, seed=829)
        np.testing.assert_array_equal(original, self.sample_ids)

    def test_labels_do_not_change(self) -> None:
        original = self.labels.copy()
        oracle_supports_by_label(self.support, self.labels, self.sample_ids, seed=829)
        np.testing.assert_array_equal(original, self.labels)


def _seed_oracle_test(seed: int):
    def test(self: CompositionTests) -> None:
        result = oracle_supports_by_label(self.support, self.labels, self.sample_ids, seed=seed, k=3)
        self.assertEqual(set(result), set(ORACLE_CONDITIONS))
    return test


for _seed in (829, 1829, 2829, 3829, 4829):
    setattr(CompositionTests, f"test_oracles_seed_{_seed}", _seed_oracle_test(_seed))


if __name__ == "__main__":
    unittest.main()
