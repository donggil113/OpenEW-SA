import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from bootstrap_ood_statistics import (  # noqa: E402
    best_detection_accuracy,
    bootstrap_dataset,
    compute_metrics,
    percentile_interval,
)
from ood_detection_metrics import compute_ood_metrics  # noqa: E402


class BootstrapOODStatisticsTests(unittest.TestCase):
    def test_perfect_metrics(self):
        labels = np.array([0, 0, 1, 1])
        scores = np.array([0.1, 0.2, 0.8, 0.9])
        metrics = compute_metrics(labels, scores)
        self.assertEqual(metrics["auroc"], 1.0)
        self.assertEqual(metrics["aupr_ood"], 1.0)
        self.assertEqual(metrics["fpr95"], 0.0)
        self.assertEqual(metrics["detection_accuracy"], 1.0)

    def test_detection_accuracy_is_evaluation_best(self):
        accuracy, threshold = best_detection_accuracy(
            np.array([0, 1, 0, 1]), np.array([0.1, 0.9, 0.8, 0.7])
        )
        self.assertEqual(accuracy, 0.75)
        self.assertEqual(threshold, 0.7)

    def test_metrics_match_existing_paper2_implementation_with_ties(self):
        labels = np.array([0, 1, 0, 1, 1, 0])
        scores = np.array([0.1, 0.5, 0.5, 0.5, 0.9, 0.1])
        expected = compute_ood_metrics(labels, scores)
        actual = compute_metrics(labels, scores)
        for metric in ("auroc", "aupr_ood", "fpr95", "detection_accuracy"):
            self.assertAlmostEqual(actual[metric], expected[metric], places=15)

    def test_percentile_interval(self):
        low, high = percentile_interval(np.arange(101), level=0.90)
        self.assertAlmostEqual(low, 5.0)
        self.assertAlmostEqual(high, 95.0)

    def test_bootstrap_is_paired_and_resumable(self):
        labels = np.array([0, 0, 0, 1, 1, 1])
        scores = {"a": np.arange(6.0), "b": np.arange(6.0)}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = bootstrap_dataset("electrosense", labels, scores, root, 2, 7, 1)
            second = bootstrap_dataset("electrosense", labels, scores, root, 4, 7, 1)
            self.assertEqual(len(first), 4)
            self.assertEqual(len(second), 8)
            pivot = second.pivot(index="replicate", columns="method", values="auroc")
            np.testing.assert_allclose(pivot.a, pivot.b)
            self.assertEqual(sorted(second.replicate.unique().tolist()), [0, 1, 2, 3])

    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):
            compute_metrics(np.array([0, 1]), np.array([0.0, np.nan]))


if __name__ == "__main__":
    unittest.main()
