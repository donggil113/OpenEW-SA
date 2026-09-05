from __future__ import annotations

import unittest

import numpy as np
import pandas as pd
import torch

from openew.paper3.v2_addendum.inference import (
    _chunk_peers,
    _full_partition_probabilities,
    _metric_row,
    _probabilities_from_peer_lists,
    summarize_receiver_deltas,
)
from openew.paper3.v2_addendum.contracts import EvidenceCategory
from openew.paper3.wisig_v2.models import ReceiverSupportClassifier


class InferenceTests(unittest.TestCase):
    def setUp(self) -> None:
        torch.manual_seed(7)
        self.model = ReceiverSupportClassifier(3, attention=True)
        self.model.eval()
        self.device = torch.device("cpu")

    def test_chunk_peers_excludes_anchor(self) -> None:
        ids = np.asarray([f"s{i}" for i in range(8)])
        peers = _chunk_peers(np.arange(8), np.asarray(["001"] * 8), ids, np.arange(8), seed=829)
        for anchor, values in enumerate(peers):
            self.assertNotIn(anchor, values)

    def test_chunk_peers_preserves_leading_zero_receiver(self) -> None:
        ids = np.asarray([f"s{i}" for i in range(4)])
        peers = _chunk_peers(np.arange(4), np.asarray(["001"] * 4), ids, np.arange(4), seed=829)
        self.assertEqual({len(row) for row in peers}, {3})

    def test_chunk_peers_deterministic(self) -> None:
        ids = np.asarray([f"s{i}" for i in range(70)])
        args = (np.arange(70), np.asarray(["r"] * 70), ids, np.arange(70))
        self.assertEqual(_chunk_peers(*args, seed=829), _chunk_peers(*args, seed=829))

    def test_chunk_peers_label_free_signature(self) -> None:
        self.assertNotIn("label", _chunk_peers.__annotations__)

    def test_chunk_width_never_exceeds_32(self) -> None:
        ids = np.asarray([f"s{i}" for i in range(100)])
        peers = _chunk_peers(np.arange(100), np.asarray(["r"] * 100), ids, np.arange(100), seed=829)
        self.assertLessEqual(max(map(len, peers)), 32)

    def test_singleton_has_empty_peers(self) -> None:
        peers = _chunk_peers(np.asarray([0]), np.asarray(["r"]), np.asarray(["s"]), np.asarray([0]), seed=829)
        self.assertEqual(peers, [()])

    def test_peer_probability_rejects_missing_row(self) -> None:
        with self.assertRaises(ValueError):
            _probabilities_from_peer_lists(self.model, np.zeros((2, 64), np.float32), np.arange(2), np.arange(2), [(1,)], self.device)

    def test_peer_probability_rejects_foreign_peer(self) -> None:
        with self.assertRaises(ValueError):
            _probabilities_from_peer_lists(self.model, np.zeros((2, 64), np.float32), np.arange(2), np.asarray([0]), [(3,)], self.device)

    def test_peer_probability_rejects_all_empty(self) -> None:
        with self.assertRaises(ValueError):
            _probabilities_from_peer_lists(self.model, np.zeros((2, 64), np.float32), np.arange(2), np.asarray([0]), [()], self.device)

    def test_peer_probabilities_are_finite(self) -> None:
        embeddings = np.random.default_rng(4).normal(size=(4, 64)).astype(np.float32)
        values = _probabilities_from_peer_lists(self.model, embeddings, np.arange(4), np.asarray([0, 1]), [(2, 3), (2, 3)], self.device)
        self.assertTrue(np.isfinite(values).all())
        np.testing.assert_allclose(values.sum(axis=1), 1.0, atol=1e-6)

    def test_full_partition_probabilities_are_finite(self) -> None:
        embeddings = np.random.default_rng(5).normal(size=(7, 64)).astype(np.float32)
        values = _full_partition_probabilities(self.model, embeddings, np.arange(7), np.asarray([0, 2, 6]), self.device)
        self.assertEqual(values.shape, (3, 3))
        self.assertTrue(np.isfinite(values).all())

    def test_full_partition_excludes_anchor(self) -> None:
        embeddings = np.random.default_rng(5).normal(size=(4, 64)).astype(np.float32)
        full = _full_partition_probabilities(self.model, embeddings, np.arange(4), np.asarray([0]), self.device)
        peers = _probabilities_from_peer_lists(self.model, embeddings, np.arange(4), np.asarray([0]), [(1, 2, 3)], self.device)
        np.testing.assert_allclose(full, peers, atol=1e-6)

    def test_metric_row_records_category(self) -> None:
        row = _metric_row(protocol="p", receiver="001", seed=829, condition="NATURAL", labels=np.asarray([0, 1]), probabilities=np.asarray([[.9,.1],[.2,.8]]), query_ids=np.asarray(["a","b"]), category=EvidenceCategory.DEPLOYABLE_METHOD)
        self.assertEqual(row["evidence_category"], "DEPLOYABLE_METHOD")
        self.assertEqual(row["receiver_id"], "001")

    def test_metric_hash_changes_with_probability(self) -> None:
        args = dict(protocol="p", receiver="r", seed=829, condition="NATURAL", labels=np.asarray([0]), query_ids=np.asarray(["a"]), category=EvidenceCategory.DEPLOYABLE_METHOD)
        a = _metric_row(probabilities=np.asarray([[.8,.2]]), **args)
        b = _metric_row(probabilities=np.asarray([[.7,.3]]), **args)
        self.assertNotEqual(a["prediction_payload_sha256"], b["prediction_payload_sha256"])

    def test_summary_averages_seeds_inside_receiver(self) -> None:
        frame = pd.DataFrame([
            {"receiver_id":"r1","seed":1,"condition":"A","macro_f1":.8}, {"receiver_id":"r1","seed":1,"condition":"B","macro_f1":.7},
            {"receiver_id":"r1","seed":2,"condition":"A","macro_f1":.9}, {"receiver_id":"r1","seed":2,"condition":"B","macro_f1":.8},
            {"receiver_id":"r2","seed":1,"condition":"A","macro_f1":.4}, {"receiver_id":"r2","seed":1,"condition":"B","macro_f1":.5},
            {"receiver_id":"r2","seed":2,"condition":"A","macro_f1":.6}, {"receiver_id":"r2","seed":2,"condition":"B","macro_f1":.7},
        ])
        result = summarize_receiver_deltas(frame, "A", "B")
        self.assertAlmostEqual(result["mean"], 0.0)
        self.assertEqual(result["count"], 2)

    def test_summary_rejects_missing_column(self) -> None:
        with self.assertRaises(ValueError):
            summarize_receiver_deltas(pd.DataFrame({"receiver_id": ["r"]}), "A", "B")

    def test_summary_rejects_unpaired(self) -> None:
        frame = pd.DataFrame([{"receiver_id":"r","seed":1,"condition":"A","macro_f1":.5}])
        with self.assertRaises(ValueError):
            summarize_receiver_deltas(frame, "A", "B")


def _determinism_test(seed: int):
    def test(self: InferenceTests) -> None:
        ids = np.asarray([f"s{i}" for i in range(40)])
        args = (np.arange(40), np.asarray(["r"] * 40), ids, np.arange(40))
        self.assertEqual(_chunk_peers(*args, seed=seed), _chunk_peers(*args, seed=seed))
    return test


for _seed in (829, 1829, 2829, 3829, 4829):
    setattr(InferenceTests, f"test_chunk_determinism_seed_{_seed}", _determinism_test(_seed))


if __name__ == "__main__":
    unittest.main()
