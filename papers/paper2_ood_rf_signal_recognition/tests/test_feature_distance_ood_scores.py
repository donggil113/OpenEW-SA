"""End-to-end smoke tests for train-only feature-distance scores."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT = Path(__file__).parents[1] / "scripts" / "feature_distance_ood_scores.py"
sys.path.insert(0, str(SCRIPT.parent))
from feature_distance_ood_scores import _resolve_feature_paths  # noqa: E402
from report_v0_results import _infer_metadata  # noqa: E402
from train_baseline_classifier import SplitFrame  # noqa: E402

METHODS = ("nearest_centroid_euclidean", "nearest_centroid_cosine", "mahalanobis")
REQUIRED = ["sample_id", "true_label", "ood_label", "ood_score", "nearest_class", "method"]


class FeatureDistanceSmokeTest(unittest.TestCase):
    def test_windows_feature_paths_are_resolved_under_wsl(self) -> None:
        split = SplitFrame("test", pd.DataFrame({"feature_path": [r"D:\openew_sa_data\processed\deepsense\features.npy"]}))
        resolved = _resolve_feature_paths(split, "feature_path")
        self.assertEqual("/mnt/d/openew_sa_data/processed/deepsense/features.npy", resolved.frame.loc[0, "feature_path"])

    def test_reporter_recognizes_v2_score_filenames(self) -> None:
        for method in METHODS:
            inferred = _infer_metadata(Path(f"deepsense_day2_ood_{method}_ood_metrics.json"), {})
            self.assertEqual(method, inferred["score_method"])
            self.assertEqual("deepsense", inferred["dataset"])
            self.assertEqual("day2_ood", inferred["protocol"])
            self.assertEqual("feature_distance", inferred["model"])

    def test_all_methods_preserve_labels_and_separate_representative_ood(self) -> None:
        with tempfile.TemporaryDirectory(prefix="paper2_distance_smoke_") as temporary:
            root = Path(temporary)
            features = np.asarray([
                [1.0, 0.0], [1.0, 0.1], [0.9, -0.1],
                [0.0, 1.0], [0.1, 1.0], [-0.1, 0.9],
                [1.0, 0.02], [0.02, 1.0], [-8.0, -8.0], [-9.0, -7.0],
            ], dtype=np.float32)
            feature_path = root / "features.npy"
            np.save(feature_path, features)
            train = pd.DataFrame({
                "sample_id": [f"train-{i}" for i in range(6)],
                "label": ["0000"] * 3 + ["0001"] * 3,
                "feature_path": str(feature_path), "feature_index": range(6),
            })
            evaluation = pd.DataFrame({
                "sample_id": ["id-0", "id-1", "ood-0", "ood-1"],
                "label": ["0000", "0001", "1111", "1111"],
                "ood_label": ["0", "0", "1", "1"],
                "feature_path": str(feature_path), "feature_index": range(6, 10),
            })
            train_csv, eval_csv = root / "train.csv", root / "eval.csv"
            train.to_csv(train_csv, index=False)
            evaluation.to_csv(eval_csv, index=False)
            for method in METHODS:
                output, metadata = root / f"{method}.csv", root / f"{method}.json"
                subprocess.run([
                    sys.executable, str(SCRIPT), "--train-csv", str(train_csv), "--eval-csv", str(eval_csv),
                    "--output", str(output), "--metadata-output", str(metadata), "--method", method,
                    "--batch-size", "2", "--max-train-samples-per-class", "2", "--seed", "7",
                ], check=True, capture_output=True, text=True)
                scores = pd.read_csv(output, dtype=str, keep_default_na=False)
                self.assertEqual(REQUIRED, scores.columns.tolist())
                self.assertEqual(["0000", "0001", "1111", "1111"], scores["true_label"].tolist())
                numeric = scores["ood_score"].astype(float).to_numpy()
                self.assertTrue(np.isfinite(numeric).all())
                self.assertGreater(numeric[2:].min(), numeric[:2].max(), method)
                payload = json.loads(metadata.read_text(encoding="utf-8"))
                self.assertEqual(2, payload["feature_dim"])
                self.assertEqual({"0000": 3, "0001": 3}, payload["class_counts"])
                self.assertEqual(2, payload["batch_size"])

    def test_id_only_validation_manifest_does_not_require_ood_label(self) -> None:
        with tempfile.TemporaryDirectory(prefix="paper2_distance_validation_") as temporary:
            root = Path(temporary)
            features = np.asarray([[1, 0], [0, 1], [0.9, 0.1]], dtype=np.float32)
            feature_path = root / "features.npy"
            np.save(feature_path, features)
            common = {"feature_path": str(feature_path)}
            train = pd.DataFrame({
                "sample_id": ["t0", "t1"], "label": ["0000", "0001"],
                "feature_index": [0, 1], **common,
            })
            validation = pd.DataFrame({
                "sample_id": ["v0"], "label": ["0000"], "feature_index": [2], **common,
            })
            train_path, validation_path, output = root / "train.csv", root / "val.csv", root / "scores.csv"
            train.to_csv(train_path, index=False)
            validation.to_csv(validation_path, index=False)
            subprocess.run([
                sys.executable, str(SCRIPT), "--train-csv", str(train_path), "--eval-csv", str(validation_path),
                "--output", str(output), "--method", "nearest_centroid_cosine",
            ], check=True, capture_output=True, text=True)
            result = pd.read_csv(output, dtype=str)
            self.assertEqual(["sample_id", "true_label", "ood_score", "nearest_class", "method"], result.columns.tolist())
            self.assertEqual("0000", result.loc[0, "true_label"])


if __name__ == "__main__":
    unittest.main()
