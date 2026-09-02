from __future__ import annotations

import unittest

import numpy as np
import torch

from openew.paper3.wisig_v2.models import (
    DANNClassifier,
    ReceiverSupportClassifier,
    T3AAdapter,
    apply_iq_normalization,
    batchnorm_module_count,
    estimate_iq_normalization,
    make_model,
    trainable_parameter_count,
)


class ModelTests(unittest.TestCase):
    def setUp(self) -> None:
        torch.manual_seed(4)
        self.anchors = torch.randn(3, 256, 2)
        self.peers = torch.randn(3, 5, 256, 2)
        self.mask = torch.ones(3, 5, dtype=torch.bool)

    def test_mean_shape(self) -> None:
        self.assertEqual(ReceiverSupportClassifier(6, attention=False)(self.anchors, self.peers, self.mask).logits.shape, (3, 6))

    def test_attention_shape(self) -> None:
        output = ReceiverSupportClassifier(6, attention=True)(self.anchors, self.peers, self.mask)
        self.assertEqual(output.logits.shape, (3, 6)); self.assertEqual(output.attention.shape, (3, 5))

    def test_attention_sums_to_one(self) -> None:
        weights = ReceiverSupportClassifier(6, attention=True)(self.anchors, self.peers, self.mask).attention
        torch.testing.assert_close(weights.sum(dim=1), torch.ones(3))

    def test_permutation_invariance(self) -> None:
        model = ReceiverSupportClassifier(6, attention=True).eval()
        left = model(self.anchors, self.peers, self.mask).logits
        permutation = torch.tensor([4, 2, 0, 3, 1])
        right = model(self.anchors, self.peers[:, permutation], self.mask[:, permutation]).logits
        torch.testing.assert_close(left, right)

    def test_null_context_finite(self) -> None:
        output = ReceiverSupportClassifier(6, attention=True)(self.anchors, self.peers, torch.zeros_like(self.mask))
        self.assertTrue(torch.isfinite(output.logits).all())

    def test_isolated_source_episode_finite(self) -> None:
        model = ReceiverSupportClassifier(6, attention=True)
        output = model.forward_source_episodes(self.anchors[:1, None], torch.ones(1, 1, dtype=torch.bool))
        self.assertTrue(torch.isfinite(output.logits).all())

    def test_source_episode_excludes_self(self) -> None:
        model = ReceiverSupportClassifier(6, attention=True).eval()
        output = model.forward_source_episodes(self.anchors[:1, None], torch.ones(1, 1, dtype=torch.bool))
        self.assertEqual(float(output.attention.detach().sum()), 0.0)

    def test_no_receiver_value_embedding(self) -> None:
        names = [name.lower() for name, _ in ReceiverSupportClassifier(6, attention=True).named_parameters()]
        self.assertFalse(any("receiver" in name or "embedding_table" in name for name in names))

    def test_backbone_has_no_batchnorm(self) -> None:
        self.assertEqual(batchnorm_module_count(make_model("P0", 6)), 0)

    def test_dann_shapes(self) -> None:
        labels, domains = DANNClassifier(6, 28)(self.anchors, reversal=0.1)
        self.assertEqual(labels.shape, (3, 6)); self.assertEqual(domains.shape, (3, 28))

    def test_dann_needs_multiple_domains(self) -> None:
        with self.assertRaises(ValueError):
            make_model("DG_DANN", 6, source_domain_count=1)

    def test_unknown_model_rejected(self) -> None:
        with self.assertRaises(ValueError):
            make_model("P2_NULL", 6)

    def test_parameter_count_positive(self) -> None:
        self.assertGreater(trainable_parameter_count(make_model("P2", 6)), 0)

    def test_normalization_zero_mean(self) -> None:
        features = np.arange(80, dtype=np.float32).reshape(4, 10, 2)
        stats = estimate_iq_normalization(features)
        normalized = apply_iq_normalization(features, stats)
        np.testing.assert_allclose(normalized.mean(axis=(0, 1)), np.zeros(2), atol=1e-6)

    def test_normalization_finite(self) -> None:
        features = np.ones((4, 10, 2), dtype=np.float32)
        self.assertTrue(np.isfinite(apply_iq_normalization(features, estimate_iq_normalization(features))).all())

    def test_bad_normalization_shape_rejected(self) -> None:
        with self.assertRaises(ValueError):
            estimate_iq_normalization(np.ones((3, 4), dtype=np.float32))

    def test_nonfinite_normalization_rejected(self) -> None:
        values = np.ones((2, 3, 2), dtype=np.float32); values[0, 0, 0] = np.nan
        with self.assertRaises(ValueError):
            estimate_iq_normalization(values)

    def test_t3a_shape(self) -> None:
        model = make_model("P0", 6)
        adapter = T3AAdapter(model.classifier, 5)
        logits = adapter.predict(torch.randn(7, 64), torch.randn(20, 64))
        self.assertEqual(logits.shape, (7, 6))

    def test_t3a_deterministic(self) -> None:
        model = make_model("P0", 6); query = torch.randn(7, 64); support = torch.randn(20, 64)
        adapter = T3AAdapter(model.classifier, 5)
        torch.testing.assert_close(adapter.predict(query, support), adapter.predict(query, support))

    def test_t3a_requires_linear(self) -> None:
        with self.assertRaises(TypeError):
            T3AAdapter(torch.nn.Sequential(torch.nn.Linear(2, 2)), 5)

    def test_t3a_bad_filter_rejected(self) -> None:
        with self.assertRaises(ValueError):
            T3AAdapter(torch.nn.Linear(2, 2), 0)


if __name__ == "__main__":
    unittest.main()
