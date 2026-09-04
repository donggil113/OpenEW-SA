from __future__ import annotations

from dataclasses import replace
import unittest

import numpy as np
import torch

from openew.paper3.wisig.data import ManyRxBundle
from openew.paper3.wisig_v2.models import IndependentClassifier, ReceiverSupportClassifier
from openew.paper3.wisig_v2.runner import RunConfig, _evaluate_condition_on_role


class TargetLabelIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rng = np.random.default_rng(7)
        count = 260
        cls.bundle = ManyRxBundle(
            features=rng.normal(size=(count, 256, 2)).astype(np.float32),
            sample_ids=np.asarray([f"opaque-{index:04d}" for index in range(count)]),
            receiver_ids=np.asarray(["target"] * 130 + ["donor"] * 130),
            day_ids=np.asarray([f"day-{index % 4}" for index in range(count)]),
            labels=np.asarray([index % 2 for index in range(count)], dtype=np.int64),
            transmitter_ids=("t0", "t1"),
            sample_index={f"opaque-{index:04d}": index for index in range(count)},
            manifest_sha256="synthetic",
        )
        changed = cls.bundle.labels.copy()
        changed[:130] = 1 - changed[:130]
        cls.permuted_target = replace(cls.bundle, labels=changed)
        cls.target = np.arange(130, dtype=np.int64)
        cls.donor = np.arange(130, 260, dtype=np.int64)
        cls.device = torch.device("cpu")

    def _assert_invariant(self, condition: str, model: torch.nn.Module, *, filter_k: int | None = None) -> None:
        config = RunConfig("receiver_loso_test", condition, 829, support_budget=128, context_k=32)
        first_order, first_probability, _ = _evaluate_condition_on_role(
            condition,
            model,
            self.bundle,
            self.target,
            self.donor,
            self.device,
            config,
            t3a_filter_k=filter_k,
        )
        second_order, second_probability, _ = _evaluate_condition_on_role(
            condition,
            model,
            self.permuted_target,
            self.target,
            self.donor,
            self.device,
            config,
            t3a_filter_k=filter_k,
        )
        np.testing.assert_array_equal(first_order, second_order)
        np.testing.assert_array_equal(first_probability, second_probability)

    def test_inductive_prediction_is_target_label_invariant(self) -> None:
        self._assert_invariant("P0", IndependentClassifier(2))

    def test_receiver_context_prediction_is_target_label_invariant(self) -> None:
        self._assert_invariant("P2", ReceiverSupportClassifier(2, attention=True))

    def test_mean_receiver_context_prediction_is_target_label_invariant(self) -> None:
        self._assert_invariant("P1", ReceiverSupportClassifier(2, attention=False))

    def test_shuffled_context_prediction_is_target_label_invariant(self) -> None:
        self._assert_invariant("P2_SHUFFLED", ReceiverSupportClassifier(2, attention=True))

    def test_mismatched_context_prediction_is_target_label_invariant(self) -> None:
        self._assert_invariant("P2_MISMATCHED_RX", ReceiverSupportClassifier(2, attention=True))

    def test_null_context_prediction_is_target_label_invariant(self) -> None:
        self._assert_invariant("P2_NULL", ReceiverSupportClassifier(2, attention=True))

    def test_rx_norm_prediction_is_target_label_invariant(self) -> None:
        self._assert_invariant("RX_NORM", IndependentClassifier(2))

    def test_t3a_prediction_is_target_label_invariant(self) -> None:
        self._assert_invariant("T3A", IndependentClassifier(2), filter_k=20)


if __name__ == "__main__":
    unittest.main()
