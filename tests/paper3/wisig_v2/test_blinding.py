from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from openew.paper3.wisig_v2.blinding import (
    create_unblinding_manifest,
    read_blind_predictions,
    validate_blind_prediction_payload,
    write_blind_predictions,
)


class BlindingTests(unittest.TestCase):
    def test_valid_payload(self) -> None:
        validate_blind_prediction_payload({"sample_ids": np.asarray(["a"]), "probabilities": np.asarray([[0.3, 0.7]])})

    def test_missing_ids_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_blind_prediction_payload({"probabilities": np.asarray([[1.0]])})

    def test_missing_probabilities_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_blind_prediction_payload({"sample_ids": np.asarray(["a"])})

    def test_label_key_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_blind_prediction_payload({"sample_ids": np.asarray(["a"]), "probabilities": np.asarray([[1.0]]), "labels": np.asarray([0])})

    def test_metric_key_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_blind_prediction_payload({"sample_ids": np.asarray(["a"]), "probabilities": np.asarray([[1.0]]), "macro_f1": 1.0})

    def test_nonfinite_rejected(self) -> None:
        with self.assertRaises(FloatingPointError):
            validate_blind_prediction_payload({"sample_ids": np.asarray(["a"]), "probabilities": np.asarray([[np.nan]])})

    def test_shape_mismatch_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_blind_prediction_payload({"sample_ids": np.asarray(["a", "b"]), "probabilities": np.asarray([[1.0]])})

    def test_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "blind.npz"
            digest = write_blind_predictions(path, np.asarray(["a"]), np.asarray([[0.2, 0.8]]))
            self.assertEqual(len(digest), 64)
            loaded = read_blind_predictions(path)
            self.assertEqual(loaded["sample_ids"].tolist(), ["a"])

    def test_written_archive_has_only_two_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "blind.npz"
            write_blind_predictions(path, np.asarray(["a"]), np.asarray([[1.0]]))
            with np.load(path, allow_pickle=False) as archive:
                self.assertEqual(set(archive.files), {"sample_ids", "probabilities"})

    def test_incomplete_primary_cannot_unblind(self) -> None:
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(RuntimeError):
            create_unblinding_manifest(Path(directory) / "manifest.json", preregistration_sha="a", plan_sha="b", prediction_hashes={}, completed_primary_runs=1, expected_primary_runs=2)

    def test_unblinding_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            create_unblinding_manifest(path, preregistration_sha="a", plan_sha="b", prediction_hashes={"x": "c"}, completed_primary_runs=2, expected_primary_runs=2)
            with self.assertRaises(FileExistsError):
                create_unblinding_manifest(path, preregistration_sha="a", plan_sha="b", prediction_hashes={"x": "c"}, completed_primary_runs=2, expected_primary_runs=2)


if __name__ == "__main__":
    unittest.main()
