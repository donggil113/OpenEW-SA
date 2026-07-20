"""Tests for validation-normalized OOD score fusion."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_ROOT = Path(__file__).parents[1] / "scripts"
FUSION = SCRIPT_ROOT / "fuse_ood_scores.py"
ENTROPY = SCRIPT_ROOT / "entropy_scores_from_predictions.py"


class FusionTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="paper2_fusion_")
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def _write(self, name, scores, ids=None, labels=None):
        ids = ids or ["a", "b", "c", "d"][:len(scores)]
        frame = pd.DataFrame({"sample_id": ids, "true_label": ["0000"] * len(scores), "ood_score": scores})
        if labels is not None:
            frame["ood_label"] = labels
        path = self.root / name
        frame.to_csv(path, index=False)
        return path

    def _run(self, validation, evaluation, weights=None, normalization="robust_zscore", check=True):
        output, metadata = self.root / "out.csv", self.root / "meta.json"
        command = [sys.executable, str(FUSION)]
        for name, path in validation.items():
            command += ["--validation-component", f"{name}={path}"]
        for name, path in evaluation.items():
            command += ["--evaluation-component", f"{name}={path}"]
        command += ["--output", str(output), "--metadata-output", str(metadata), "--normalization", normalization]
        for value in weights or []:
            command += ["--weights", value]
        result = subprocess.run(command, capture_output=True, text=True)
        if check and result.returncode:
            self.fail(result.stderr)
        return result, output, metadata

    def test_validation_only_normalization_and_equal_weight_fusion(self):
        validation = {"x": self._write("vx.csv", [0, 1, 2, 3]), "y": self._write("vy.csv", [10, 20, 30, 40])}
        evaluation = {
            "x": self._write("ex.csv", [100, 200], ["e1", "e2"], ["0", "1"]),
            "y": self._write("ey.csv", [50, 70], ["e2", "e1"], ["1", "0"]),
        }
        _, output, metadata = self._run(validation, evaluation)
        result = pd.read_csv(output, dtype={"sample_id": str, "ood_label": str})
        # Evaluation order comes from the first component; the second is ID-aligned, not row-aligned.
        np.testing.assert_allclose(result["ood_score"], (result["x_normalized_score"] + result["y_normalized_score"]) / 2)
        payload = json.loads(metadata.read_text())
        self.assertEqual("id_validation_only", payload["normalization_fit_data"])
        self.assertEqual(1.5, payload["normalization_parameters"]["x"]["median"])
        self.assertEqual({"x": 0.5, "y": 0.5}, payload["weights"])

    def test_evaluation_labels_do_not_affect_normalization(self):
        validation = {"x": self._write("v.csv", [1, 2, 3, 4])}
        evaluation = {"x": self._write("e.csv", [100, -100], ["p", "q"], ["1", "0"])}
        _, _, metadata = self._run(validation, evaluation)
        params = json.loads(metadata.read_text())["normalization_parameters"]["x"]
        self.assertEqual(2.5, params["median"])
        self.assertEqual(2.5, params["mean"])

    def test_explicit_weights_are_normalized(self):
        validation = {"x": self._write("vx.csv", [0, 2]), "y": self._write("vy.csv", [0, 2])}
        evaluation = {
            "x": self._write("ex.csv", [3], ["e"], ["1"]),
            "y": self._write("ey.csv", [5], ["e"], ["1"]),
        }
        _, output, metadata = self._run(validation, evaluation, ["x=1", "y=3"])
        payload = json.loads(metadata.read_text())
        self.assertEqual({"x": 0.25, "y": 0.75}, payload["weights"])
        row = pd.read_csv(output).iloc[0]
        self.assertAlmostEqual(row.ood_score, .25 * row.x_normalized_score + .75 * row.y_normalized_score)

    def test_robust_fallback_records_warning(self):
        validation = {"x": self._write("v.csv", [7, 7, 7])}
        evaluation = {"x": self._write("e.csv", [8], ["e"], ["0"])}
        _, _, metadata = self._run(validation, evaluation)
        payload = json.loads(metadata.read_text())
        self.assertEqual(1.0, payload["normalization_parameters"]["x"]["scale"])
        self.assertEqual("unit_fallback", payload["normalization_parameters"]["x"]["scale_source"])
        self.assertEqual(1, len(payload["fallback_warnings"]))

    def test_missing_and_duplicate_ids_are_rejected(self):
        duplicate = self._write("dup.csv", [1, 2], ["a", "a"])
        normal = self._write("normal.csv", [1, 2], ["a", "b"])
        evaluation = self._write("eval.csv", [1, 2], ["e1", "e2"], ["0", "1"])
        result, _, _ = self._run({"x": duplicate}, {"x": evaluation}, check=False)
        self.assertNotEqual(0, result.returncode)
        result, _, _ = self._run(
            {"x": normal, "y": self._write("missing.csv", [1], ["a"])},
            {"x": evaluation, "y": evaluation}, check=False,
        )
        self.assertNotEqual(0, result.returncode)

    def test_inconsistent_evaluation_ood_labels_are_rejected(self):
        validation = {"x": self._write("vx.csv", [1, 2]), "y": self._write("vy.csv", [2, 3])}
        evaluation = {
            "x": self._write("ex.csv", [1, 2], ["a", "b"], ["0", "1"]),
            "y": self._write("ey.csv", [1, 2], ["a", "b"], ["1", "0"]),
        }
        result, _, _ = self._run(validation, evaluation, check=False)
        self.assertNotEqual(0, result.returncode)

    def test_entropy_helper_preserves_deepsense_symbolic_labels_without_ood_label(self):
        predictions = pd.DataFrame({
            "sample_id": ["d1", "d2"], "true_label": ["0000", "0010"],
            "prob_0000": [0.9, 0.2], "prob_0010": [0.1, 0.8],
        })
        source, output = self.root / "predictions_val_calibrated.csv", self.root / "entropy.csv"
        predictions.to_csv(source, index=False)
        subprocess.run([sys.executable, str(ENTROPY), "--predictions", str(source), "--output", str(output)], check=True)
        result = pd.read_csv(output, dtype=str, keep_default_na=False)
        self.assertEqual(["0000", "0010"], result["true_label"].tolist())
        self.assertNotIn("ood_label", result.columns)


if __name__ == "__main__":
    unittest.main()
