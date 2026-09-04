from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from openew.paper3.wisig_v2.analysis import DESCRIPTIVE_COMPARISONS, collect_primary_records, source_only_selections, validate_blind_archive_expected, validate_record_blind_archive, validate_target_receiver_diagnostic, verify_primary_completion
from openew.paper3.wisig_v2.blinding import write_blind_predictions
from openew.paper3.wisig_v2.hashing import sha256_file
from openew.paper3.wisig_v2.statistics import clustered_bootstrap, descriptive_summary, holm_adjust, receiver_average, receiver_bootstrap, receiver_sign_flip


class StatisticsAnalysisTests(unittest.TestCase):
    def test_receiver_normalization_has_source_normalization_comparator(self) -> None:
        self.assertEqual(DESCRIPTIVE_COMPARISONS["RX_NORM_MINUS_SOURCE_NORM"], ("RX_NORM", "SOURCE_NORM"))

    def test_target_diagnostic_rejects_support_query_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); protocol = root / "receiver_loso_00"; protocol.mkdir()
            (protocol / "split_summary.json").write_text(json.dumps({"assignment_metadata": {"test_receiver": "rx0", "test_receiver_hardware": "N210"}}), encoding="utf-8")
            record = {
                "run_id": "overlap",
                "protocol_id": "receiver_loso_00",
                "model_stage": "P0",
                "config": {"seed": 829},
                "target_prediction_count": 2,
                "target_receiver_diagnostics": {"rx0": {"support_count": 128, "query_count": 2, "requested_budget": 128, "full_budget_met": True, "support_query_overlap": 1, "support_fraction": 0.5}},
            }
            with self.assertRaises(RuntimeError):
                validate_target_receiver_diagnostic(record, root)

    def test_receiver_average_first_averages_seeds(self) -> None:
        self.assertEqual(receiver_average({"a": [1.0, 3.0], "b": [2.0, 4.0]}), {"a": 2.0, "b": 3.0})

    def test_receiver_average_rejects_empty(self) -> None:
        with self.assertRaises(ValueError):
            receiver_average({})

    def test_bootstrap_deterministic(self) -> None:
        self.assertEqual(receiver_bootstrap([1, 2, 3], replicates=100, seed=7), receiver_bootstrap([1, 2, 3], replicates=100, seed=7))

    def test_bootstrap_receiver_count(self) -> None:
        self.assertEqual(receiver_bootstrap([1, 2, 3], replicates=100)["receiver_count"], 3)

    def test_bootstrap_rejects_one_receiver(self) -> None:
        with self.assertRaises(ValueError):
            receiver_bootstrap([1.0])

    def test_bootstrap_rejects_nonfinite(self) -> None:
        with self.assertRaises(ValueError):
            receiver_bootstrap([1.0, np.nan])

    def test_cluster_bootstrap_deterministic(self) -> None:
        values = {"A": [1.0, 2.0], "B": [3.0], "C": [4.0, 5.0]}
        self.assertEqual(clustered_bootstrap(values, replicates=100, seed=7), clustered_bootstrap(values, replicates=100, seed=7))

    def test_cluster_bootstrap_preserves_receiver_count(self) -> None:
        result = clustered_bootstrap({"A": [1.0, 2.0], "B": [3.0]}, replicates=20)
        self.assertEqual(result["receiver_count"], 3)

    def test_cluster_bootstrap_rejects_one_cluster(self) -> None:
        with self.assertRaises(ValueError):
            clustered_bootstrap({"A": [1.0, 2.0]})

    def test_cluster_bootstrap_rejects_empty_cluster(self) -> None:
        with self.assertRaises(ValueError):
            clustered_bootstrap({"A": [1.0], "B": []})

    def test_signflip_deterministic(self) -> None:
        self.assertEqual(receiver_sign_flip([1, 2, 3], permutations=100, seed=7), receiver_sign_flip([1, 2, 3], permutations=100, seed=7))

    def test_signflip_two_sided(self) -> None:
        self.assertIn("two-sided", receiver_sign_flip([1, 2, 3], permutations=100)["method"])

    def test_signflip_probability_bounds(self) -> None:
        value = receiver_sign_flip([1, -1, 2], permutations=100)["p_value"]
        self.assertGreaterEqual(value, 0); self.assertLessEqual(value, 1)

    def test_holm_monotone_ordered(self) -> None:
        adjusted = holm_adjust({"a": 0.01, "b": 0.02, "c": 0.5})
        self.assertLessEqual(adjusted["a"], adjusted["b"]); self.assertLessEqual(adjusted["b"], adjusted["c"])

    def test_holm_caps_at_one(self) -> None:
        self.assertLessEqual(max(holm_adjust({"a": 0.9, "b": 1.0}).values()), 1.0)

    def test_holm_rejects_bad_p(self) -> None:
        with self.assertRaises(ValueError):
            holm_adjust({"a": 1.1})

    def test_summary_values(self) -> None:
        result = descriptive_summary([1, 2, 3])
        self.assertEqual(result["mean"], 2.0); self.assertEqual(result["count"], 3)

    def test_summary_rejects_empty(self) -> None:
        with self.assertRaises(ValueError):
            descriptive_summary([])

    def test_collect_filters_primary_settings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); run = root / "runs/receiver_loso_00__p0/run.json"; run.parent.mkdir(parents=True)
            run.write_text(json.dumps({"config": {"support_budget": 128, "context_k": 32, "context_retention": 1.0, "data_variant": "raw"}}), encoding="utf-8")
            extra = root / "runs/receiver_loso_00__other/run.json"; extra.parent.mkdir(parents=True)
            extra.write_text(json.dumps({"config": {"support_budget": 16, "context_k": 16, "context_retention": 1.0, "data_variant": "raw"}}), encoding="utf-8")
            self.assertEqual(len(collect_primary_records(root)), 1)

    def test_completion_rejects_wrong_count(self) -> None:
        with self.assertRaises(RuntimeError):
            verify_primary_completion([])

    def test_source_selection_uses_only_validation(self) -> None:
        records = [
            {"run_id": "tta", "model_stage": "T3A", "source_validation_metrics": {"macro_f1": 0.9, "per_receiver_macro_f1": {"a": 0.2, "b": 0.2}}},
            {"run_id": "coral", "model_stage": "DG_CORAL", "source_validation_metrics": {"macro_f1": 0.9, "per_receiver_macro_f1": {"a": 0.1, "b": 0.1}}},
            {"run_id": "groupdro", "model_stage": "DG_GROUPDRO", "source_validation_metrics": {"macro_f1": 0.9, "per_receiver_macro_f1": {"a": 0.2, "b": 0.2}}},
            {"run_id": "dann", "model_stage": "DG_DANN", "source_validation_metrics": {"macro_f1": 0.1, "per_receiver_macro_f1": {"a": 0.3, "b": 0.3}}},
        ]
        with tempfile.TemporaryDirectory() as directory:
            payload = source_only_selections(records, Path(directory) / "selection.json")
        self.assertFalse(payload["selection_uses_target_metrics"])
        self.assertEqual(payload["groups"]["source_dg"]["selected"], "DG_DANN")
        self.assertIn("equal-weight", payload["groups"]["source_dg"]["selection_metric"])

    def test_source_selection_rejects_missing_receiver_metrics(self) -> None:
        records = [{"run_id": "bad", "model_stage": "T3A", "source_validation_metrics": {"macro_f1": 0.5}}]
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(RuntimeError):
            source_only_selections(records, Path(directory) / "selection.json")

    def test_blind_archive_preflight_uses_frozen_queries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); split = root / "split/receiver_loso_00"; run = root / "run"
            split.mkdir(parents=True); run.mkdir()
            ids = np.asarray([f"s{index}" for index in range(6)])
            (split / "split_manifest.csv").write_text("sample_id,split\n" + "".join(f"{value},test\n" for value in ids), encoding="utf-8")
            (split / "split_summary.json").write_text(json.dumps({"assignment_metadata": {"test_receiver": "rx"}, "eligible_transmitter_count": 2}), encoding="utf-8")
            from openew.paper3.wisig_v2.support import freeze_support_query
            frozen = freeze_support_query(np.arange(6), ids, np.asarray(["rx"] * 6), receiver_id="rx", support_budget=2, seed=829)
            query_ids = ids[np.asarray(frozen.query_indices)]
            prediction_path = run / "predictions_blind.npz"
            write_blind_predictions(prediction_path, query_ids, np.full((4, 2), 0.5, dtype=np.float32))
            record = {"run_id": "test", "protocol_id": "receiver_loso_00", "config": {"support_budget": 2, "seed": 829}, "record_path": str(run / "run.json"), "target_prediction_sha256": sha256_file(prediction_path)}
            result = validate_record_blind_archive(record, root / "split")
            self.assertTrue(result["support_query_disjoint"]); self.assertFalse(result["labels_read"])

    def test_blind_archive_preflight_rejects_wrong_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); split = root / "split/receiver_loso_00"; run = root / "run"
            split.mkdir(parents=True); run.mkdir()
            (split / "split_manifest.csv").write_text("sample_id,split\ns0,test\ns1,test\ns2,test\n", encoding="utf-8")
            (split / "split_summary.json").write_text(json.dumps({"assignment_metadata": {"test_receiver": "rx"}, "eligible_transmitter_count": 2}), encoding="utf-8")
            prediction_path = run / "predictions_blind.npz"; write_blind_predictions(prediction_path, np.asarray(["wrong", "s2"]), np.full((2, 2), 0.5, dtype=np.float32))
            record = {"run_id": "test", "protocol_id": "receiver_loso_00", "config": {"support_budget": 1, "seed": 829}, "record_path": str(run / "run.json"), "target_prediction_sha256": sha256_file(prediction_path)}
            with self.assertRaises(RuntimeError):
                validate_record_blind_archive(record, root / "split")

    def test_blind_archive_preflight_rejects_wrong_class_dimension(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "predictions_blind.npz"
            write_blind_predictions(path, np.asarray(["s0", "s1"]), np.full((2, 3), 1 / 3, dtype=np.float32))
            record = {"run_id": "test", "target_prediction_sha256": sha256_file(path)}
            with self.assertRaises(RuntimeError):
                validate_blind_archive_expected(record, path, {"s0", "s1"}, 2)

    def test_blind_archive_preflight_rejects_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "predictions_blind.npz"
            write_blind_predictions(path, np.asarray(["s0"]), np.asarray([[0.5, 0.5]], dtype=np.float32))
            record = {"run_id": "test", "target_prediction_sha256": "0" * 64}
            with self.assertRaises(RuntimeError):
                validate_blind_archive_expected(record, path, {"s0"}, 2)


def _constant_bootstrap_test(value: float):
    def test(self: StatisticsAnalysisTests) -> None:
        result = receiver_bootstrap([value] * 4, replicates=50, seed=3)
        self.assertAlmostEqual(result["ci95_lower"], value)
        self.assertAlmostEqual(result["ci95_upper"], value)
    return test


for _index, _value in enumerate((-1.0, -0.5, 0.0, 0.25, 1.0)):
    setattr(StatisticsAnalysisTests, f"test_constant_bootstrap_{_index}", _constant_bootstrap_test(_value))


if __name__ == "__main__":
    unittest.main()
