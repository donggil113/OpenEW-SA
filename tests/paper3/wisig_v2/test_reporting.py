from __future__ import annotations

import unittest
from pathlib import Path
import json
import tempfile

import pandas as pd
from openew.paper3.wisig_v2.figure_audit import EXPECTED_FIGURES, audit_figure_exports
from openew.paper3.wisig_v2.reporting import _information_access_rows, _receiver_mean_sem, generate_figures, generate_tables
from openew.paper3.wisig_v2.suite import PRIMARY_MODELS


class ReportingInformationBudgetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = {row["model"]: row for row in _information_access_rows(["P0", "P2", "P2_SHUFFLED", "P2_MISMATCHED_RX", "P2_NULL", "RX_NORM", "T3A"])}

    def test_inductive_model_has_no_support(self) -> None:
        self.assertEqual(self.rows["P0"]["target_receiver_support"], 0)
        self.assertEqual(self.rows["P0"]["source_validation_donor_support"], 0)

    def test_p2_receives_target_receiver_support(self) -> None:
        self.assertEqual(self.rows["P2"]["target_receiver_support"], 128)
        self.assertEqual(self.rows["P2"]["source_validation_donor_support"], 0)

    def test_shuffled_and_mismatched_use_disclosed_donor_support(self) -> None:
        for model in ("P2_SHUFFLED", "P2_MISMATCHED_RX"):
            self.assertEqual(self.rows[model]["target_receiver_support"], 0)
            self.assertEqual(self.rows[model]["source_validation_donor_support"], 128)

    def test_null_context_uses_no_support(self) -> None:
        self.assertEqual(self.rows["P2_NULL"]["target_receiver_support"], 0)
        self.assertEqual(self.rows["P2_NULL"]["source_validation_donor_support"], 0)

    def test_t3a_and_rx_norm_disclose_updates(self) -> None:
        self.assertEqual(self.rows["T3A"]["test_update"], "Prototype")
        self.assertEqual(self.rows["RX_NORM"]["test_update"], "Statistics")

    def test_no_query_samples_or_labels_are_used_as_support(self) -> None:
        for row in self.rows.values():
            self.assertFalse(row["query_samples_used_as_support"])
            self.assertFalse(row["target_labels"])

    def test_generated_information_budget_exposes_update_channels(self) -> None:
        for row in self.rows.values():
            self.assertIn("test_gradient_updates", row)
            self.assertIn("test_batch_stat_updates", row)
            self.assertIn("test_prototype_updates", row)
            self.assertIn("extra_parameters", row)
        self.assertTrue(self.rows["T3A"]["test_prototype_updates"])
        self.assertFalse(self.rows["P2"]["test_gradient_updates"])

    def test_unknown_model_fails_closed(self) -> None:
        with self.assertRaises(KeyError):
            _information_access_rows(["UNKNOWN"])

    def test_sensitivity_uncertainty_uses_receiver_not_seed_as_unit(self) -> None:
        frame = pd.DataFrame(
            {
                "receiver_id": ["a", "a", "b", "b"],
                "budget": [128, 128, 128, 128],
                "score": [0.0, 1.0, 0.5, 0.5],
            }
        )
        result = _receiver_mean_sem(frame, "budget", "score").iloc[0]
        self.assertEqual(result["count"], 2)
        self.assertAlmostEqual(result["mean"], 0.5)

    def test_sensitivity_uncertainty_requires_receiver_id(self) -> None:
        with self.assertRaises(ValueError):
            _receiver_mean_sem(pd.DataFrame({"budget": [128], "score": [0.5]}), "budget", "score")

    def test_generate_tables_uses_observed_models_and_keeps_source_norm(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "analysis"
            split_root = Path(temporary) / "splits"
            root.mkdir()
            protocol = split_root / "receiver_loso_00"
            protocol.mkdir(parents=True)
            (protocol / "split_summary.json").write_text(
                json.dumps(
                    {
                        "protocol_id": "receiver_loso_00",
                        "assignment_metadata": {"test_receiver": "rx0", "test_receiver_hardware": "N210"},
                        "split_counts": {"train": 10, "validation": 2, "test": 3},
                        "eligible_transmitter_count": 6,
                    }
                ),
                encoding="utf-8",
            )
            models = ["P0", "P0_WIDE", "P1", "P2", "P2_SHUFFLED", "P2_NULL", "P2_MISMATCHED_RX", "RX_NORM", "T3A", "SOURCE_NORM", "DG_CORAL", "DG_GROUPDRO", "DG_DANN"]
            pd.DataFrame({"model": models, "receiver_id": ["rx0"] * len(models), "seed": [829] * len(models), "macro_f1": [0.5] * len(models)}).to_csv(root / "primary_receiver_seed_results.csv", index=False)
            pd.DataFrame({"model": models, "macro_f1_mean": [0.5] * len(models)}).to_csv(root / "primary_receiver_level_summary.csv", index=False)
            pd.DataFrame({"comparison": ["P2_MINUS_P0"], "receiver_id": ["rx0"], "difference": [0.0]}).to_csv(root / "paired_receiver_seed_differences.csv", index=False)

            outputs = generate_tables(root, split_root)

            information = pd.read_csv(outputs["table2"])
            baselines = pd.read_csv(outputs["table5"])
            self.assertEqual(set(information["model"]), set(models))
            self.assertIn("SOURCE_NORM", set(baselines["model"]))

    def test_generate_all_nine_figures_from_receiver_grain_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            receivers = [f"rx{index:02d}" for index in range(32)]
            primary = pd.DataFrame(
                [
                    {
                        "receiver_id": receiver,
                        "hardware_family": ("B210", "N210", "X310")[index % 3],
                        "model": model,
                        "seed": 829,
                        "macro_f1": 0.55 + 0.001 * index + (0.01 if model == "P2" else 0.0),
                        "parameter_count": 65000,
                        "wall_seconds": 1.0,
                        "peak_gpu_memory_bytes": 1024,
                    }
                    for index, receiver in enumerate(receivers)
                    for model in PRIMARY_MODELS
                ]
            )
            primary.to_csv(root / "primary_receiver_seed_results.csv", index=False)
            pd.DataFrame(
                [{"comparison": "P2_MINUS_P0", "receiver_id": receiver, "seed": 829, "difference": 0.01} for receiver in receivers]
            ).to_csv(root / "paired_receiver_seed_differences.csv", index=False)
            pd.DataFrame(
                [{"receiver_id": receiver, "class_entropy_nats": 1.0 + 0.01 * index, "p2_minus_p0_macro_f1": 0.01} for index, receiver in enumerate(receivers)]
            ).to_csv(root / "support_composition_audit.csv", index=False)
            pd.DataFrame(
                [{"receiver_id": receiver, "support_budget": budget, "macro_f1": 0.6 + budget / 10000} for receiver in receivers for budget in (16, 32, 64, 128, 256)]
            ).to_csv(root / "support_budget_results.csv", index=False)
            pd.DataFrame(
                [{"receiver_id": receiver, "context_k": k, "macro_f1": 0.6 + k / 10000} for receiver in receivers for k in (8, 16, 32, 64)]
            ).to_csv(root / "context_k_results.csv", index=False)
            pd.DataFrame(
                [{"test_day": day, "model": model, "equal_weight_receiver_macro_f1": 0.6 + (0.01 if model == "P2" else 0.0)} for day in range(4) for model in ("P0", "P2")]
            ).to_csv(root / "day_receiver_seed_results.csv", index=False)
            pd.DataFrame(
                [{"model": model, "latency_seconds_median": 0.1 + 0.001 * index} for index, model in enumerate(PRIMARY_MODELS)]
            ).to_csv(root / "standardized_inference_benchmark_summary.csv", index=False)

            generated = generate_figures(root)

            self.assertEqual(set(generated), set(EXPECTED_FIGURES))
            for name in EXPECTED_FIGURES:
                self.assertGreater((root / f"{name}.png").stat().st_size, 0)
                self.assertGreater((root / f"{name}.pdf").stat().st_size, 0)
            audit = audit_figure_exports(root, root / "figure_audit.json")
            self.assertEqual(audit["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
