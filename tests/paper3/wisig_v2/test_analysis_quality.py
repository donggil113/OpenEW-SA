from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from openew.paper3.wisig_v2.analysis import DESCRIPTIVE_COMPARISONS, PRIMARY_COMPARISONS
from openew.paper3.wisig_v2.analysis_quality import boolean_column_equals, day_receiver_detail_contract, finite_unit_interval, frame_contract, inference_benchmark_contract, json_compatible, sensitivity_contract, unique_key, validate_analysis_outputs
from openew.paper3.wisig_v2.suite import PRIMARY_MODELS


class AnalysisQualityTests(unittest.TestCase):
    def test_json_compatible_normalizes_numpy_scalars(self) -> None:
        value = json_compatible({"ok": np.bool_(True), "count": np.int64(2), "nested": [np.float64(0.5)]})
        self.assertEqual(value, {"ok": True, "count": 2, "nested": [0.5]})
        self.assertEqual(json.loads(json.dumps(value, allow_nan=False)), value)

    def test_unit_interval_accepts_bounds(self) -> None:
        self.assertTrue(finite_unit_interval(pd.DataFrame({"metric": [0.0, 0.5, 1.0]}), ["metric"]))

    def test_unit_interval_rejects_out_of_bounds(self) -> None:
        self.assertFalse(finite_unit_interval(pd.DataFrame({"metric": [-0.01, 0.5]}), ["metric"]))
        self.assertFalse(finite_unit_interval(pd.DataFrame({"metric": [0.5, 1.01]}), ["metric"]))

    def test_unit_interval_rejects_nonfinite(self) -> None:
        self.assertFalse(finite_unit_interval(pd.DataFrame({"metric": [0.5, np.nan]}), ["metric"]))

    def test_unit_interval_rejects_missing_column(self) -> None:
        self.assertFalse(finite_unit_interval(pd.DataFrame({"other": [0.5]}), ["metric"]))

    def test_unique_key_accepts_distinct_rows(self) -> None:
        self.assertTrue(unique_key(pd.DataFrame({"a": [1, 1], "b": [1, 2]}), ["a", "b"]))

    def test_unique_key_rejects_duplicates(self) -> None:
        self.assertFalse(unique_key(pd.DataFrame({"a": [1, 1], "b": [2, 2]}), ["a", "b"]))

    def test_unique_key_rejects_missing_column(self) -> None:
        self.assertFalse(unique_key(pd.DataFrame({"a": [1]}), ["a", "b"]))

    def test_frame_contract_checks_grain_and_bounds(self) -> None:
        frame = pd.DataFrame({"id": ["a", "b"], "macro_f1": [0.1, 0.2], "accuracy": [0.2, 0.3], "balanced_accuracy": [0.3, 0.4], "ece": [0.4, 0.5]})
        result = frame_contract(frame, expected_rows=2, key=("id",))
        self.assertTrue(result["expected_row_count"])
        self.assertTrue(result["key_unique"])
        self.assertTrue(result["metrics_bounded"])

    def test_frame_contract_rejects_duplicate_grain(self) -> None:
        frame = pd.DataFrame({"id": ["a", "a"], "macro_f1": [0.1, 0.2], "accuracy": [0.2, 0.3], "balanced_accuracy": [0.3, 0.4], "ece": [0.4, 0.5]})
        self.assertFalse(frame_contract(frame, expected_rows=2, key=("id",))["key_unique"])

    def test_boolean_strings_are_not_truthy_by_accident(self) -> None:
        frame = pd.DataFrame({"value": ["False", "false"]})
        self.assertTrue(boolean_column_equals(frame, "value", False))
        self.assertFalse(boolean_column_equals(frame, "value", True))

    def test_unknown_boolean_value_fails_closed(self) -> None:
        self.assertFalse(boolean_column_equals(pd.DataFrame({"value": ["unknown"]}), "value", False))

    def test_sensitivity_contract_uses_exact_receiver_seed_setting_grid(self) -> None:
        rows = []
        for receiver in range(32):
            for seed in (829, 1829, 2829, 3829, 4829):
                for budget in (16, 32):
                    rows.append({"receiver_id": f"rx{receiver}", "seed": seed, "support_budget": budget, "macro_f1": 0.5, "accuracy": 0.5, "balanced_accuracy": 0.5, "ece": 0.1})
        result = sensitivity_contract(pd.DataFrame(rows), "support_budget", (16, 32), 32 * 5 * 2)
        self.assertTrue(all(value for key, value in result.items() if key != "row_count"))

    def test_sensitivity_contract_rejects_missing_setting(self) -> None:
        frame = pd.DataFrame({"receiver_id": ["rx0"], "seed": [829], "support_budget": [16], "macro_f1": [0.5], "accuracy": [0.5], "balanced_accuracy": [0.5], "ece": [0.1]})
        self.assertFalse(sensitivity_contract(frame, "support_budget", (16, 32), 2)["setting_set_exact"])

    def test_inference_benchmark_contract_uses_exact_receiver_model_grid(self) -> None:
        frame = pd.DataFrame(
            [
                {"receiver_id": f"rx{receiver:02d}", "model": model, "seed": 829, "latency_seconds_median": 0.1, "samples_per_second_median": 100.0, "max_probability_reproduction_error": 0.0, "target_labels_read": False}
                for receiver in range(32) for model in PRIMARY_MODELS
            ]
        )
        result = inference_benchmark_contract(frame)
        self.assertTrue(all(value for key, value in result.items() if key != "row_count"))

    def test_inference_benchmark_contract_rejects_target_label_access(self) -> None:
        frame = pd.DataFrame(
            [
                {"receiver_id": f"rx{receiver:02d}", "model": model, "seed": 829, "latency_seconds_median": 0.1, "samples_per_second_median": 100.0, "max_probability_reproduction_error": 0.0, "target_labels_read": receiver == 0 and model == PRIMARY_MODELS[0]}
                for receiver in range(32) for model in PRIMARY_MODELS
            ]
        )
        self.assertFalse(inference_benchmark_contract(frame)["target_labels_not_read"])

    def test_compute_contract_requires_separate_support_statistics_cost(self) -> None:
        source = Path(__file__).resolve().parents[3] / "src/openew/paper3/wisig_v2/analysis_quality.py"
        text = source.read_text(encoding="utf-8")
        self.assertIn('"support_encoding_flops_approx"', text)
        self.assertIn('"support_statistics_ops_approx"', text)

    def test_day_detail_requires_32_receivers_in_every_row(self) -> None:
        complete = {f"rx{index:02d}": 0.5 for index in range(32)}
        frame = pd.DataFrame({"per_receiver_macro_f1_json": [json.dumps(complete), json.dumps(complete)]})
        result = day_receiver_detail_contract(frame)
        self.assertTrue(result["every_row_has_32_receivers"])
        broken = dict(complete); broken.pop("rx31")
        frame.loc[1, "per_receiver_macro_f1_json"] = json.dumps(broken)
        self.assertFalse(day_receiver_detail_contract(frame)["every_row_has_32_receivers"])

    def test_day_detail_requires_stable_receiver_keys(self) -> None:
        first = {f"rx{index:02d}": 0.5 for index in range(32)}
        second = dict(first); second.pop("rx31"); second["other"] = 0.5
        frame = pd.DataFrame({"per_receiver_macro_f1_json": [json.dumps(first), json.dumps(second)]})
        self.assertFalse(day_receiver_detail_contract(frame)["receiver_key_set_stable"])

    def test_day_detail_rejects_nonfinite_or_malformed_values(self) -> None:
        values = {f"rx{index:02d}": 0.5 for index in range(32)}
        values["rx00"] = float("nan")
        frame = pd.DataFrame({"per_receiver_macro_f1_json": [json.dumps(values)]})
        self.assertFalse(day_receiver_detail_contract(frame)["receiver_metrics_bounded"])
        malformed = pd.DataFrame({"per_receiver_macro_f1_json": ["not-json"]})
        self.assertFalse(day_receiver_detail_contract(malformed)["every_row_has_32_receivers"])

    def test_complete_receiver_grain_fixture_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); receivers = [f"rx{index:02d}" for index in range(32)]; seeds = [829, 1829, 2829, 3829, 4829]
            primary = pd.DataFrame(
                [
                    {"receiver_id": receiver, "model": model, "seed": seed, "macro_f1": 0.5, "accuracy": 0.5, "balanced_accuracy": 0.5, "ece": 0.1}
                    for receiver in receivers for model in PRIMARY_MODELS for seed in seeds
                ]
            )
            primary.to_csv(root / "primary_receiver_seed_results.csv", index=False)
            receiver = primary.groupby(["receiver_id", "model"], as_index=False).agg(macro_f1=("macro_f1", "mean"), accuracy=("accuracy", "mean"), balanced_accuracy=("balanced_accuracy", "mean"), ece=("ece", "mean"), seed_count=("seed", "nunique"))
            receiver.to_csv(root / "primary_receiver_averaged_results.csv", index=False)
            comparisons = [*DESCRIPTIVE_COMPARISONS, "P2_MINUS_BEST_SOURCE_DG"]
            paired = pd.DataFrame([{"comparison": name, "receiver_id": receiver_id, "seed": seed, "difference": 0.01} for name in comparisons for receiver_id in receivers for seed in seeds])
            paired.to_csv(root / "paired_receiver_seed_differences.csv", index=False)
            paired.groupby(["comparison", "receiver_id"], as_index=False)["difference"].mean().to_csv(root / "paired_receiver_averaged_differences.csv", index=False)
            inference = {
                "primary_unit": "receiver",
                "seed_aggregation": "mean within receiver before inference",
                "comparisons": {
                    name: {"bootstrap": {"receiver_count": 32, "replicates": 10_000}, "sign_flip": {"receiver_count": 32, "permutations": 100_000}}
                    for name in PRIMARY_COMPARISONS
                },
            }
            (root / "receiver_level_inference.json").write_text(json.dumps(inference), encoding="utf-8")
            (root / "blind_archive_preflight.json").write_text(json.dumps({"status": "PASS", "record_count": len(primary), "labels_read": False}), encoding="utf-8")
            (root / "unblinding_manifest.json").write_text(json.dumps({"completed_primary_runs": len(primary), "expected_primary_runs": len(primary)}), encoding="utf-8")
            selection = {"selection_uses_target_metrics": False, "groups": {name: {"selection_metric": "equal-weight mean of per-receiver source-validation macro-F1"} for name in ("same_information_tta", "source_dg")}}
            (root / "source_validation_method_selection.json").write_text(json.dumps(selection), encoding="utf-8")
            pd.DataFrame(
                [
                    {
                        "receiver_id": receiver_id,
                        "model": model,
                        "seed": seed,
                        "support_count": 128 if model == "P2" else 0,
                        "query_count": 100,
                        "isolated_query_count": 0,
                        "attention_entropy_mean": 1.0,
                        "effective_peer_count_mean": 2.0,
                        "inference_seconds": 0.1,
                        "samples_per_second": 1000.0,
                        "support_query_overlap": 0,
                        "context_k": 32,
                    }
                    for receiver_id in receivers for model in PRIMARY_MODELS for seed in seeds
                ]
            ).to_csv(root / "context_receiver_seed_diagnostics.csv", index=False)
            result = validate_analysis_outputs(root, root / "quality.json")
            self.assertEqual(result["status"], "PASS")
            self.assertFalse(result["packet_level_inference_used"])


if __name__ == "__main__":
    unittest.main()
