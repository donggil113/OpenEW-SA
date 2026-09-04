from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from openew.paper3.wisig_v2.decision_analysis import build_decision_summary


class DecisionAnalysisTests(unittest.TestCase):
    def test_complete_evidence_builds_frozen_go_decision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            comparisons = {
                "P2_MINUS_P0": 0.03,
                "P2_MINUS_P0_WIDE": 0.02,
                "P2_MINUS_P2_SHUFFLED": 0.01,
                "P2_MINUS_P2_MISMATCHED_RX": 0.01,
                "P2_MINUS_T3A": 0.005,
            }
            receivers = [f"rx{index:02d}" for index in range(32)]
            pd.DataFrame(
                [
                    {"comparison": comparison, "receiver_id": receiver, "difference": value}
                    for comparison, value in comparisons.items()
                    for receiver in receivers
                ]
            ).to_csv(root / "paired_receiver_averaged_differences.csv", index=False)
            pd.DataFrame(
                [{"comparison": comparison, "count": 32, "mean": value, "std": 0.0, "median": value, "min": value, "max": value} for comparison, value in comparisons.items()]
            ).to_csv(root / "paired_difference_summary.csv", index=False)
            pd.DataFrame(
                [{"receiver_id": receiver, "model": "P0", "macro_f1": 0.6} for receiver in receivers]
            ).to_csv(root / "primary_receiver_seed_results.csv", index=False)
            pd.DataFrame(
                [
                    {"receiver_id": receiver, "hardware_family": ("A", "B")[index % 2], "model": model, "macro_f1": 0.6 + (0.03 if model == "P2" else 0.0)}
                    for index, receiver in enumerate(receivers)
                    for model in ("P0", "P2")
                ]
            ).to_csv(root / "primary_receiver_averaged_results.csv", index=False)
            pd.DataFrame(
                [{"receiver_id": receiver, "condition": "SAME_CLASS_EXCLUDED_ORACLE", "evaluable_query_count": 10, "query_count": 10, "macro_f1": 0.62} for receiver in receivers]
            ).to_csv(root / "composition_oracle_results.csv", index=False)
            (root / "source_validation_method_selection.json").write_text(json.dumps({"groups": {"same_information_tta": {"selected": "T3A"}}}), encoding="utf-8")
            (root / "blind_archive_preflight.json").write_text(json.dumps({"status": "PASS", "labels_read": False}), encoding="utf-8")
            integrity = root / "integrity.json"; integrity.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
            result = build_decision_summary(root, integrity, root / "decision.json")
            self.assertEqual(result["decision"]["verdict"], "GO")
            self.assertEqual(result["positive_p2_minus_p0_receivers"], 32)

    def test_missing_selected_tta_comparison_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pd.DataFrame([{"comparison": "P2_MINUS_P0", "receiver_id": "rx", "difference": 0.1}]).to_csv(root / "paired_receiver_averaged_differences.csv", index=False)
            pd.DataFrame([{"comparison": "P2_MINUS_P0", "mean": 0.1}]).to_csv(root / "paired_difference_summary.csv", index=False)
            pd.DataFrame([{"receiver_id": "rx", "model": "P0", "macro_f1": 0.1}]).to_csv(root / "primary_receiver_seed_results.csv", index=False)
            pd.DataFrame([{"receiver_id": "rx", "hardware_family": "A", "model": "P0", "macro_f1": 0.1}]).to_csv(root / "primary_receiver_averaged_results.csv", index=False)
            pd.DataFrame([{"receiver_id": "rx", "condition": "SAME_CLASS_EXCLUDED_ORACLE", "evaluable_query_count": 1, "query_count": 1, "macro_f1": 0.1}]).to_csv(root / "composition_oracle_results.csv", index=False)
            (root / "source_validation_method_selection.json").write_text(json.dumps({"groups": {"same_information_tta": {"selected": "T3A"}}}), encoding="utf-8")
            (root / "blind_archive_preflight.json").write_text(json.dumps({"status": "PASS", "labels_read": False}), encoding="utf-8")
            integrity = root / "integrity.json"; integrity.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
            with self.assertRaises(RuntimeError):
                build_decision_summary(root, integrity, root / "decision.json")


if __name__ == "__main__":
    unittest.main()
