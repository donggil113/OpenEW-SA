from __future__ import annotations

import inspect
import unittest

import numpy as np

from openew.paper3.wisig_v2.support import (
    build_query_context_indices,
    freeze_all_test_receivers,
    freeze_support_query,
    support_query_statistics,
)


class SupportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.indices = np.arange(40, dtype=np.int64)
        self.sample_ids = np.asarray([f"s{value:03d}" for value in self.indices])
        self.receiver_ids = np.asarray(["01" if value < 25 else "02" for value in self.indices])

    def test_signature_does_not_accept_labels(self) -> None:
        self.assertNotIn("labels", inspect.signature(freeze_support_query).parameters)

    def test_support_query_disjoint(self) -> None:
        split = freeze_support_query(self.indices, self.sample_ids, self.receiver_ids, receiver_id="01", support_budget=8)
        self.assertFalse(set(split.support_indices) & set(split.query_indices))

    def test_every_receiver_sample_preserved(self) -> None:
        split = freeze_support_query(self.indices, self.sample_ids, self.receiver_ids, receiver_id="01", support_budget=8)
        self.assertEqual(set(split.support_indices) | set(split.query_indices), set(range(25)))

    def test_fixed_budget(self) -> None:
        split = freeze_support_query(self.indices, self.sample_ids, self.receiver_ids, receiver_id="01", support_budget=8)
        self.assertEqual(split.support_count, 8)

    def test_short_receiver_leaves_query(self) -> None:
        split = freeze_support_query([0, 1], self.sample_ids, self.receiver_ids, receiver_id="01", support_budget=8)
        self.assertEqual((split.support_count, split.query_count), (1, 1))

    def test_empty_receiver_rejected(self) -> None:
        with self.assertRaises(ValueError):
            freeze_support_query(self.indices, self.sample_ids, self.receiver_ids, receiver_id="missing", support_budget=8)

    def test_nonpositive_budget_rejected(self) -> None:
        with self.assertRaises(ValueError):
            freeze_support_query(self.indices, self.sample_ids, self.receiver_ids, receiver_id="01", support_budget=0)

    def test_same_seed_deterministic(self) -> None:
        left = freeze_support_query(self.indices, self.sample_ids, self.receiver_ids, receiver_id="01", support_budget=8, seed=829)
        right = freeze_support_query(self.indices[::-1], self.sample_ids, self.receiver_ids, receiver_id="01", support_budget=8, seed=829)
        self.assertEqual(left, right)

    def test_label_permutation_cannot_change_support(self) -> None:
        before = freeze_support_query(self.indices, self.sample_ids, self.receiver_ids, receiver_id="01", support_budget=8, seed=829)
        labels = np.arange(len(self.indices)) % 3
        np.random.default_rng(9).shuffle(labels)
        after = freeze_support_query(self.indices, self.sample_ids, self.receiver_ids, receiver_id="01", support_budget=8, seed=829)
        self.assertEqual(before.support_indices, after.support_indices)

    def test_symbolic_receiver_preserved(self) -> None:
        split = freeze_support_query(self.indices, self.sample_ids, self.receiver_ids, receiver_id="01", support_budget=8)
        self.assertEqual(split.receiver_id, "01")

    def test_context_uses_only_support(self) -> None:
        split = freeze_support_query(self.indices, self.sample_ids, self.receiver_ids, receiver_id="01", support_budget=8)
        context = build_query_context_indices(split.query_indices, split.support_indices, self.sample_ids, "01", k=4)
        self.assertTrue(set(context.ravel()).issubset(set(split.support_indices)))

    def test_context_excludes_queries(self) -> None:
        split = freeze_support_query(self.indices, self.sample_ids, self.receiver_ids, receiver_id="01", support_budget=8)
        context = build_query_context_indices(split.query_indices, split.support_indices, self.sample_ids, "01", k=4)
        self.assertFalse(set(context.ravel()) & set(split.query_indices))

    def test_context_shape(self) -> None:
        split = freeze_support_query(self.indices, self.sample_ids, self.receiver_ids, receiver_id="01", support_budget=8)
        self.assertEqual(build_query_context_indices(split.query_indices, split.support_indices, self.sample_ids, "01", k=4).shape, (17, 4))

    def test_context_deterministic(self) -> None:
        split = freeze_support_query(self.indices, self.sample_ids, self.receiver_ids, receiver_id="01", support_budget=8)
        left = build_query_context_indices(split.query_indices, split.support_indices, self.sample_ids, "01", k=4)
        right = build_query_context_indices(split.query_indices, split.support_indices, self.sample_ids, "01", k=4)
        np.testing.assert_array_equal(left, right)

    def test_zero_retention_preserves_shape(self) -> None:
        split = freeze_support_query(self.indices, self.sample_ids, self.receiver_ids, receiver_id="01", support_budget=8)
        context = build_query_context_indices(split.query_indices, split.support_indices, self.sample_ids, "01", k=4, retention=0.0)
        self.assertEqual(context.shape, (17, 4)); self.assertTrue((context == -1).all())

    def test_half_retention(self) -> None:
        split = freeze_support_query(self.indices, self.sample_ids, self.receiver_ids, receiver_id="01", support_budget=8)
        context = build_query_context_indices(split.query_indices, split.support_indices, self.sample_ids, "01", k=4, retention=0.5)
        self.assertTrue(((context >= 0).sum(axis=1) == 2).all())

    def test_bad_retention_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_query_context_indices([0], [1], self.sample_ids, "01", k=1, retention=0.33)

    def test_no_support_rejected_for_nonzero_context(self) -> None:
        with self.assertRaises(ValueError):
            build_query_context_indices([0], [], self.sample_ids, "01", k=1)

    def test_all_receivers_frozen(self) -> None:
        splits = freeze_all_test_receivers(self.indices, self.sample_ids, self.receiver_ids, budget=4, seed=829)
        self.assertEqual(set(splits), {"01", "02"})

    def test_statistics_report_zero_overlap(self) -> None:
        split = freeze_support_query(self.indices, self.sample_ids, self.receiver_ids, receiver_id="01", support_budget=8)
        self.assertEqual(support_query_statistics(split)["support_query_overlap"], 0)


def _receiver_string_test(receiver: str):
    def test(self: SupportTests) -> None:
        receiver_ids = np.asarray([receiver] * 5)
        split = freeze_support_query(np.arange(5), np.asarray([f"x{i}" for i in range(5)]), receiver_ids, receiver_id=receiver, support_budget=2)
        self.assertEqual(split.receiver_id, receiver)
    return test


for _receiver in ("001", "0007", "rx-A", "한글수신기", "18446744073709551616", "01-02", "0", "RX_09", "ä", "space id"):
    setattr(SupportTests, "test_preserve_receiver_" + str(abs(hash(_receiver))), _receiver_string_test(_receiver))


if __name__ == "__main__":
    unittest.main()
