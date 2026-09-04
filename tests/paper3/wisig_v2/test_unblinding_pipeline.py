from __future__ import annotations

import json
import tempfile
import unittest
import warnings
from pathlib import Path
from unittest.mock import patch

import numpy as np

from openew.paper3.wisig.data import ManyRxBundle
from openew.paper3.wisig_v2 import analysis
from openew.paper3.wisig_v2.blinding import write_blind_predictions
from openew.paper3.wisig_v2.hashing import sha256_file
from openew.paper3.wisig_v2.support import freeze_support_query


class SyntheticUnblindingPipelineTests(unittest.TestCase):
    def test_full_receiver_seed_pipeline_keeps_receiver_as_unit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); split_root = root / "splits"; run_root = root / "runs_root"; analysis_root = root / "analysis"
            models = ("P0", "P2", "T3A", "DG_CORAL")
            seeds = (829, 1829, 2829, 3829, 4829)
            all_ids = ["global_train", "global_validation"]
            receiver_by_id = {"global_train": "source", "global_validation": "validation"}
            label_by_id = {"global_train": 0, "global_validation": 1}
            for receiver_index in range(32):
                protocol = f"receiver_loso_{receiver_index:02d}"; receiver = f"rx{receiver_index:02d}"
                destination = split_root / protocol; destination.mkdir(parents=True)
                test_ids = [f"{receiver}_s{index:03d}" for index in range(130)]
                all_ids.extend(test_ids); receiver_by_id.update({value: receiver for value in test_ids}); label_by_id.update({value: index % 2 for index, value in enumerate(test_ids)})
                (destination / "split_manifest.csv").write_text("sample_id,split\nglobal_train,train\nglobal_validation,validation\n" + "".join(f"{value},test\n" for value in test_ids), encoding="utf-8")
                (destination / "split_summary.json").write_text(json.dumps({"assignment_metadata": {"test_receiver": receiver, "test_receiver_hardware": ("A", "B", "C")[receiver_index % 3]}, "eligible_transmitter_ids": ["t0", "t1"], "eligible_transmitter_count": 2}), encoding="utf-8")
                for seed in seeds:
                    ids = np.asarray(test_ids); frozen = freeze_support_query(np.arange(130), ids, np.asarray([receiver] * 130), receiver_id=receiver, support_budget=128, seed=seed)
                    query_ids = ids[np.asarray(frozen.query_indices)]; truth = np.asarray([label_by_id[str(value)] for value in query_ids])
                    probabilities = np.full((2, 2), 0.1, dtype=np.float32); probabilities[np.arange(2), truth] = 0.9
                    for model in models:
                        run_id = f"{protocol}__{model.lower()}__s{seed}__b128__k32__r100__raw"; destination_run = run_root / "runs" / run_id; destination_run.mkdir(parents=True)
                        path = destination_run / "predictions_blind.npz"; write_blind_predictions(path, query_ids, probabilities)
                        validation_score = {"P0": 0.1, "P2": 0.2, "T3A": 0.3, "DG_CORAL": 0.25}[model]
                        record = {"run_id": run_id, "status": "COMPLETE", "protocol_id": protocol, "model_stage": model, "config": {"seed": seed, "support_budget": 128, "context_k": 32, "context_retention": 1.0, "data_variant": "raw"}, "held_out_metrics": None, "target_labels_loaded_for_metrics": False, "target_prediction_sha256": sha256_file(path), "target_prediction_count": 2, "source_validation_metrics": {"macro_f1": validation_score, "per_receiver_macro_f1": {"val": validation_score}}, "parameter_count": 10, "wall_seconds": 1.0, "peak_gpu_memory_bytes": 0, "target_receiver_diagnostics": {receiver: {"support_count": 128, "query_count": 2, "requested_budget": 128, "full_budget_met": True, "support_query_overlap": 0, "context_retention": 1.0, "context_k": 32, "isolated_query_count": 0, "attention_entropy_mean": 1.0, "effective_peer_count_mean": 2.0, "inference_seconds": 0.1, "samples_per_second": 20.0, "support_fraction": 128 / 130}}}
                        (destination_run / "run.json").write_text(json.dumps(record), encoding="utf-8")
            sample_ids = np.asarray(all_ids); receiver_ids = np.asarray([receiver_by_id[value] for value in all_ids]); labels = np.asarray([label_by_id[value] for value in all_ids])
            bundle = ManyRxBundle(np.zeros((len(all_ids), 2, 2), dtype=np.float32), sample_ids, receiver_ids, np.asarray(["d"] * len(all_ids)), labels, ("t0", "t1"), {value: index for index, value in enumerate(all_ids)}, "manifest")
            (run_root / "frozen_run_plan.json").write_text("{}", encoding="utf-8"); prereg = root / "prereg.md"; prereg.write_text("frozen", encoding="utf-8")
            comparisons = {"P2_MINUS_P0": ("P2", "P0"), "P2_MINUS_T3A": ("P2", "T3A")}
            with patch.object(analysis, "PRIMARY_MODELS", models), patch.object(analysis, "PRIMARY_RUN_COUNT", 32 * len(models) * 5), patch.object(analysis, "PRIMARY_COMPARISONS", comparisons), patch.object(analysis, "DESCRIPTIVE_COMPARISONS", comparisons), patch.object(analysis.ManyRxBundle, "load", return_value=bundle), warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                result = analysis.unblind_primary(root / "unused", split_root, run_root, analysis_root, prereg)
            self.assertEqual(result["primary_runs"], 32 * len(models) * 5)
            import pandas as pd
            receiver_results = pd.read_csv(analysis_root / "primary_receiver_averaged_results.csv")
            self.assertEqual(len(receiver_results), 32 * len(models)); self.assertTrue((receiver_results["seed_count"] == 5).all())
            inference = json.loads((analysis_root / "receiver_level_inference.json").read_text(encoding="utf-8"))
            self.assertEqual(inference["comparisons"]["P2_MINUS_P0"]["bootstrap"]["receiver_count"], 32)
            context = pd.read_csv(analysis_root / "context_receiver_seed_diagnostics.csv")
            self.assertEqual(len(context), 32 * len(models) * 5)
            self.assertTrue((context["support_query_overlap"] == 0).all())

    def test_day_unblinding_source_has_create_once_and_blind_record_guards(self) -> None:
        source = (Path(__file__).resolve().parents[3] / "src/openew/paper3/wisig_v2/analysis.py").read_text(encoding="utf-8")
        start = source.index("def unblind_day_secondary(")
        stop = source.index("def unblind_equalized_diagnostic(")
        function = source[start:stop]
        self.assertIn('raise FileExistsError("day secondary already unblinded")', function)
        self.assertIn('record.get("held_out_metrics") is not None', function)
        self.assertIn('record.get("target_labels_loaded_for_metrics") is not False', function)


if __name__ == "__main__":
    unittest.main()
