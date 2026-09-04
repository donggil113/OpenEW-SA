from __future__ import annotations

import unittest

import pandas as pd

from openew.paper3.wisig_v2.report_evidence import _day_receiver_summary, _model_receiver_summary, _oracle_condition_summary, _receiver_setting_summary


class ReportEvidenceTests(unittest.TestCase):
    def test_model_summary_uses_receiver_not_seed_as_unit(self) -> None:
        frame = pd.DataFrame(
            {
                "receiver_id": ["a", "a", "b", "b"],
                "model": ["P2"] * 4,
                "macro_f1": [0.0, 1.0, 0.5, 0.5],
            }
        )
        result = _model_receiver_summary(frame, "macro_f1")["P2"]
        self.assertEqual(result["receiver_count"], 2)
        self.assertAlmostEqual(result["mean"], 0.5)

    def test_model_summary_rejects_nonfinite(self) -> None:
        frame = pd.DataFrame({"receiver_id": ["a"], "model": ["P2"], "macro_f1": [float("nan")]})
        with self.assertRaises(RuntimeError):
            _model_receiver_summary(frame, "macro_f1")

    def test_setting_summary_requires_all_receivers(self) -> None:
        frame = pd.DataFrame({"receiver_id": ["a"], "budget": [128], "macro_f1": [0.5]})
        with self.assertRaises(RuntimeError):
            _receiver_setting_summary(frame, "budget")

    def test_setting_summary_averages_seeds_inside_receiver(self) -> None:
        rows = []
        for receiver in range(32):
            rows.extend(
                [
                    {"receiver_id": f"r{receiver}", "budget": 128, "macro_f1": 0.0},
                    {"receiver_id": f"r{receiver}", "budget": 128, "macro_f1": 1.0},
                ]
            )
        result = _receiver_setting_summary(pd.DataFrame(rows), "budget")[0]
        self.assertEqual(result["receiver_count"], 32)
        self.assertAlmostEqual(result["mean"], 0.5)

    def test_day_summary_expands_serialized_receiver_metrics(self) -> None:
        import json

        receiver_values = {f"r{receiver}": receiver / 31 for receiver in range(32)}
        frame = pd.DataFrame(
            {
                "model": ["P0", "P0"],
                "seed": [829, 1829],
                "test_day": ["day0", "day0"],
                "per_receiver_macro_f1_json": [json.dumps(receiver_values), json.dumps(receiver_values)],
            }
        )
        result = _day_receiver_summary(frame)["P0"]
        self.assertEqual(result["receiver_count"], 32)
        self.assertAlmostEqual(result["mean"], 0.5)

    def test_day_summary_rejects_missing_receiver_map(self) -> None:
        frame = pd.DataFrame({"model": ["P0"], "seed": [829], "test_day": ["day0"]})
        with self.assertRaises(ValueError):
            _day_receiver_summary(frame)

    def test_oracle_summary_preserves_unevaluable_query_coverage(self) -> None:
        frame = pd.DataFrame(
            {
                "receiver_id": ["a", "b"],
                "seed": [829, 829],
                "condition": ["SAME_CLASS_EXCLUDED_ORACLE"] * 2,
                "macro_f1": [0.5, float("nan")],
                "query_count": [10, 10],
                "evaluable_query_count": [10, 0],
            }
        )
        result = _oracle_condition_summary(frame)["SAME_CLASS_EXCLUDED_ORACLE"]
        self.assertEqual(result["receiver_count_total"], 2)
        self.assertEqual(result["receiver_count_evaluable"], 1)
        self.assertEqual(result["evaluable_fraction"], 0.5)
        self.assertFalse(result["deployable"])

    def test_oracle_summary_preserves_transmitter_pure_bias(self) -> None:
        rows = []
        for receiver in range(32):
            for seed in (829, 1829, 2829, 3829, 4829):
                rows.append(
                    {
                        "receiver_id": f"rx{receiver:02d}",
                        "seed": seed,
                        "condition": "TRANSMITTER_PURE_ORACLE",
                        "macro_f1": 0.5,
                        "query_count": 10,
                        "evaluable_query_count": 10,
                        "pure_support_label": receiver % 2,
                        "prediction_fraction_pure_support_label": 0.25,
                    }
                )
        result = _oracle_condition_summary(pd.DataFrame(rows))["TRANSMITTER_PURE_ORACLE"]
        self.assertEqual(result["prediction_fraction_pure_support_label_receiver_mean"], 0.25)
        self.assertEqual(result["prediction_fraction_pure_support_label_receiver_range"], [0.25, 0.25])
        self.assertEqual(sum(result["selected_local_support_label_counts"].values()), 160)

    def test_transmitter_pure_summary_rejects_missing_bias(self) -> None:
        frame = pd.DataFrame(
            {
                "receiver_id": [f"rx{index:02d}" for index in range(32)],
                "seed": [829] * 32,
                "condition": ["TRANSMITTER_PURE_ORACLE"] * 32,
                "macro_f1": [0.5] * 32,
                "query_count": [10] * 32,
                "evaluable_query_count": [10] * 32,
            }
        )
        with self.assertRaisesRegex(RuntimeError, "bias diagnostic"):
            _oracle_condition_summary(frame)


if __name__ == "__main__":
    unittest.main()
