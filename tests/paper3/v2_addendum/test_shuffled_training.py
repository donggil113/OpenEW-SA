from __future__ import annotations

import unittest

from openew.paper3.v2_addendum.shuffled_training import ShuffledTrainingConfig


class ShuffledTrainingConfigTests(unittest.TestCase):
    def test_valid_frozen_config(self) -> None:
        self.assertIsInstance(ShuffledTrainingConfig("receiver_loso_00", 829).validate(), ShuffledTrainingConfig)

    def test_non_loso_protocol_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ShuffledTrainingConfig("day_lodo_0", 829).validate()

    def test_unknown_seed_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ShuffledTrainingConfig("receiver_loso_00", 42).validate()

    def test_epoch_change_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ShuffledTrainingConfig("receiver_loso_00", 829, max_epochs=29).validate()

    def test_patience_change_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ShuffledTrainingConfig("receiver_loso_00", 829, patience=9).validate()

    def test_learning_rate_change_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ShuffledTrainingConfig("receiver_loso_00", 829, learning_rate=1e-3).validate()

    def test_weight_decay_change_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ShuffledTrainingConfig("receiver_loso_00", 829, weight_decay=0).validate()

    def test_batch_change_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ShuffledTrainingConfig("receiver_loso_00", 829, sample_batch_size=512).validate()

    def test_node_budget_change_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ShuffledTrainingConfig("receiver_loso_00", 829, episode_node_budget=1000).validate()

    def test_context_k_change_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ShuffledTrainingConfig("receiver_loso_00", 829, context_k=16).validate()

    def test_support_budget_change_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ShuffledTrainingConfig("receiver_loso_00", 829, support_budget=256).validate()

    def test_hash_is_deterministic(self) -> None:
        a = ShuffledTrainingConfig("receiver_loso_00", 829)
        b = ShuffledTrainingConfig("receiver_loso_00", 829)
        self.assertEqual(a.config_hash, b.config_hash)

    def test_hash_changes_by_receiver(self) -> None:
        a = ShuffledTrainingConfig("receiver_loso_00", 829)
        b = ShuffledTrainingConfig("receiver_loso_01", 829)
        self.assertNotEqual(a.config_hash, b.config_hash)

    def test_hash_changes_by_seed(self) -> None:
        a = ShuffledTrainingConfig("receiver_loso_00", 829)
        b = ShuffledTrainingConfig("receiver_loso_00", 1829)
        self.assertNotEqual(a.config_hash, b.config_hash)


def _seed_config_test(seed: int):
    def test(self: ShuffledTrainingConfigTests) -> None:
        value = ShuffledTrainingConfig("receiver_loso_31", seed).validate()
        self.assertEqual(value.seed, seed)
    return test


for _seed in (829, 1829, 2829, 3829, 4829):
    setattr(ShuffledTrainingConfigTests, f"test_frozen_seed_{_seed}", _seed_config_test(_seed))


if __name__ == "__main__":
    unittest.main()
