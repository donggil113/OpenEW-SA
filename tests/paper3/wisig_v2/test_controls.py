from __future__ import annotations

import inspect
import unittest

import numpy as np

from openew.paper3.wisig_v2.controls import (
    choose_mismatched_receiver,
    day_matched_support,
    oracle_support_for_query,
    shuffled_receiver_support,
    transmitter_pure_oracle_pool,
)


class ControlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.indices = list(range(30))
        self.sample_ids = [f"s{i}" for i in self.indices]
        self.receivers = ["a"] * 10 + ["b"] * 10 + ["c"] * 10
        self.days = ["d0", "d1"] * 15
        self.labels = np.asarray([i % 3 for i in self.indices])

    def test_mismatch_excludes_target(self) -> None:
        self.assertNotEqual(choose_mismatched_receiver("a", ["a", "b", "c"], seed=829), "a")

    def test_mismatch_deterministic(self) -> None:
        self.assertEqual(choose_mismatched_receiver("a", ["a", "b", "c"], seed=829), choose_mismatched_receiver("a", ["c", "b", "a"], seed=829))

    def test_mismatch_needs_donor(self) -> None:
        with self.assertRaises(ValueError):
            choose_mismatched_receiver("a", ["a"], seed=829)

    def test_day_match_no_labels_argument(self) -> None:
        self.assertNotIn("labels", inspect.signature(day_matched_support).parameters)

    def test_day_match_budget(self) -> None:
        result = day_matched_support(self.indices, ["d0", "d1"] * 3, self.sample_ids, self.days, budget=8, seed=829, namespace="test")
        self.assertEqual(len(result), 8)

    def test_day_match_unique(self) -> None:
        result = day_matched_support(self.indices, ["d0", "d1"] * 3, self.sample_ids, self.days, budget=8, seed=829, namespace="test")
        self.assertEqual(len(result), len(set(result)))

    def test_day_match_deterministic(self) -> None:
        left = day_matched_support(self.indices, ["d0", "d1"], self.sample_ids, self.days, budget=8, seed=829, namespace="test")
        right = day_matched_support(self.indices[::-1], ["d0", "d1"], self.sample_ids, self.days, budget=8, seed=829, namespace="test")
        self.assertEqual(left, right)

    def test_shuffled_excludes_target_receiver(self) -> None:
        result = shuffled_receiver_support(self.indices, self.receivers, self.sample_ids, self.days, ["d0", "d1"], excluded_receiver="a", budget=8, seed=829)
        self.assertTrue(all(self.receivers[index] != "a" for index in result))

    def test_shuffled_label_permutation_invariant(self) -> None:
        before = shuffled_receiver_support(self.indices, self.receivers, self.sample_ids, self.days, ["d0", "d1"], excluded_receiver="a", budget=8, seed=829)
        np.random.default_rng(4).shuffle(self.labels)
        after = shuffled_receiver_support(self.indices, self.receivers, self.sample_ids, self.days, ["d0", "d1"], excluded_receiver="a", budget=8, seed=829)
        self.assertEqual(before, after)

    def test_oracle_signature_makes_labels_explicit(self) -> None:
        self.assertIn("labels", inspect.signature(oracle_support_for_query).parameters)

    def test_same_class_excluded(self) -> None:
        result = oracle_support_for_query(self.indices, self.labels, query_label=1, mode="same_class_excluded", sample_ids=self.sample_ids, seed=829, k=10)
        self.assertTrue(all(self.labels[index] != 1 for index in result))

    def test_same_class_only(self) -> None:
        result = oracle_support_for_query(self.indices, self.labels, query_label=1, mode="same_class_only", sample_ids=self.sample_ids, seed=829, k=10)
        self.assertTrue(all(self.labels[index] == 1 for index in result))

    def test_unknown_oracle_mode_rejected(self) -> None:
        with self.assertRaises(ValueError):
            oracle_support_for_query(self.indices, self.labels, query_label=1, mode="bad", sample_ids=self.sample_ids, seed=829, k=10)

    def test_pure_oracle_one_label(self) -> None:
        result = transmitter_pure_oracle_pool(self.indices, self.labels, self.sample_ids, budget=8, seed=829)
        self.assertEqual(len(set(self.labels[list(result)])), 1)

    def test_pure_oracle_deterministic(self) -> None:
        left = transmitter_pure_oracle_pool(self.indices, self.labels, self.sample_ids, budget=8, seed=829)
        right = transmitter_pure_oracle_pool(self.indices[::-1], self.labels, self.sample_ids, budget=8, seed=829)
        self.assertEqual(left, right)


if __name__ == "__main__":
    unittest.main()
