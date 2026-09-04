from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from openew.paper3.wisig_v2.hashing import sha256_file
from openew.paper3.wisig_v2.preunblind import create_preunblinding_freeze, hash_analysis_code_tree, hash_file_registry, validate_checkpoint_lineage, validate_primary_grid
from openew.paper3.wisig_v2.suite import PRIMARY_MODELS


class PreUnblindingFreezeTests(unittest.TestCase):
    def test_freeze_records_exhaustive_label_free_archive_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); run_root = root / "runs"; run_root.mkdir()
            split_manifest = root / "split_manifest.json"; split_manifest.write_text("{}", encoding="utf-8")
            plan = run_root / "frozen_run_plan.json"; plan.write_text("{}", encoding="utf-8")
            protocol = root / "protocol.md"; protocol.write_text("frozen", encoding="utf-8")
            records = [
                {
                    "run_id": f"run-{index}",
                    "git_sha": "execution-sha",
                    "held_out_metrics": None,
                    "target_labels_loaded_for_metrics": False,
                    "split_sha256": "split",
                    "data_manifest_sha256": "data",
                    "config_hash": f"config-{index}",
                    "target_prediction_sha256": str(index) * 64,
                    "record_path": str(root / f"run-{index}.json"),
                }
                for index in (1, 2)
            ]
            for record in records:
                Path(record["record_path"]).write_text(record["run_id"], encoding="utf-8")
            with (
                patch("openew.paper3.wisig_v2.preunblind.collect_primary_records", return_value=records),
                patch("openew.paper3.wisig_v2.preunblind.verify_primary_completion"),
                patch("openew.paper3.wisig_v2.preunblind.validate_primary_grid", return_value={"status": "PASS"}),
                patch("openew.paper3.wisig_v2.preunblind.validate_checkpoint_lineage", return_value={"status": "PASS"}),
                patch("openew.paper3.wisig_v2.preunblind.validate_record_blind_archive", side_effect=[{"query_count": 3}, {"query_count": 4}]) as validate,
                patch("openew.paper3.wisig_v2.preunblind.validate_target_receiver_diagnostic", side_effect=[{"receiver_id": "a", "support_query_overlap": 0}, {"receiver_id": "b", "support_query_overlap": 0}]) as validate_diagnostics,
                patch("openew.paper3.wisig_v2.preunblind.hash_analysis_code_tree", return_value={"roots": [], "file_count": 1, "sha256": "code", "files": {"a.py": "hash"}}),
                patch("openew.paper3.wisig_v2.preunblind.subprocess.check_output", side_effect=["", "analysis-sha\n"]),
            ):
                destination = root / "freeze.json"
                result = create_preunblinding_freeze(root, run_root, root / "splits", split_manifest, [protocol], destination)
            self.assertEqual(validate.call_count, 2)
            self.assertEqual(validate_diagnostics.call_count, 2)
            self.assertEqual(result["blind_archive_preflight"]["record_count"], 2)
            self.assertEqual(result["blind_archive_preflight"]["total_query_count"], 7)
            self.assertFalse(result["blind_archive_preflight"]["labels_read"])
            self.assertEqual(result["target_receiver_diagnostic_preflight"]["receiver_count"], 2)
            self.assertEqual(result["target_receiver_diagnostic_preflight"]["support_query_overlap_count"], 0)
            self.assertEqual(result["data_manifest_sha256"], "data")
            self.assertEqual(result["analysis_code_tree"]["sha256"], "code")
            self.assertEqual(result["primary_run_registry_sha256"], hash_file_registry({record["run_id"]: sha256_file(record["record_path"]) for record in records}))
            self.assertEqual(result["split_freeze_sha256"], sha256_file(split_manifest))
            self.assertIn(str(protocol), result["preregistration_file_hashes"])
            self.assertTrue(result["created_utc"].endswith("+00:00"))
            self.assertEqual(json.loads(destination.read_text(encoding="utf-8"))["status"], "FROZEN_BEFORE_TARGET_UNBLINDING")

    def test_analysis_code_tree_hash_is_stable_and_ignores_bytecode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in ("configs/paper3/wisig_v2", "scripts/paper3/wisig_v2", "src/openew/paper3/wisig_v2"):
                path = root / relative
                path.mkdir(parents=True)
                (path / "source.py").write_text(relative, encoding="utf-8")
                cache = path / "__pycache__"
                cache.mkdir()
                (cache / "source.pyc").write_bytes(b"unstable")
            first = hash_analysis_code_tree(root)
            (root / "scripts/paper3/wisig_v2/__pycache__/source.pyc").write_bytes(b"changed")
            second = hash_analysis_code_tree(root)
            self.assertEqual(first, second)
            self.assertEqual(first["file_count"], 3)

    def test_exact_primary_grid_is_accepted(self) -> None:
        records = []
        for receiver in range(32):
            for model in PRIMARY_MODELS:
                for seed in (829, 1829, 2829, 3829, 4829):
                    records.append(
                        {
                            "run_id": f"receiver_loso_{receiver:02d}-{model}-{seed}",
                            "protocol_id": f"receiver_loso_{receiver:02d}",
                            "model_stage": model,
                            "config_hash": f"hash-{receiver}-{model}-{seed}",
                            "target_prediction_count": 1,
                            "config": {
                                "seed": seed,
                                "support_budget": 128,
                                "context_k": 32,
                                "context_retention": 1.0,
                                "data_variant": "raw",
                                "blind_target_metrics": True,
                                "evaluate_target_predictions": True,
                            },
                        }
                    )
        result = validate_primary_grid(records)
        self.assertEqual(result["condition_count"], 2080)

    def test_primary_grid_rejects_duplicate_substitution(self) -> None:
        records = []
        for receiver in range(32):
            for model in PRIMARY_MODELS:
                for seed in (829, 1829, 2829, 3829, 4829):
                    records.append(
                        {
                            "run_id": f"receiver_loso_{receiver:02d}-{model}-{seed}",
                            "protocol_id": f"receiver_loso_{receiver:02d}",
                            "model_stage": model,
                            "config_hash": f"hash-{receiver}-{model}-{seed}",
                            "target_prediction_count": 1,
                            "config": {"seed": seed, "support_budget": 128, "context_k": 32, "context_retention": 1.0, "data_variant": "raw", "blind_target_metrics": True, "evaluate_target_predictions": True},
                        }
                    )
        records[-1] = dict(records[0])
        with self.assertRaisesRegex(RuntimeError, "duplicate"):
            validate_primary_grid(records)

    def test_primary_grid_rejects_unblinded_config(self) -> None:
        records = []
        for receiver in range(32):
            for model in PRIMARY_MODELS:
                for seed in (829, 1829, 2829, 3829, 4829):
                    records.append(
                        {
                            "run_id": f"receiver_loso_{receiver:02d}-{model}-{seed}",
                            "protocol_id": f"receiver_loso_{receiver:02d}",
                            "model_stage": model,
                            "config_hash": f"hash-{receiver}-{model}-{seed}",
                            "target_prediction_count": 1,
                            "config": {"seed": seed, "support_budget": 128, "context_k": 32, "context_retention": 1.0, "data_variant": "raw", "blind_target_metrics": True, "evaluate_target_predictions": True},
                        }
                    )
        records[0]["config"]["blind_target_metrics"] = False
        with self.assertRaisesRegex(RuntimeError, "configuration contract"):
            validate_primary_grid(records)

    def test_checkpoint_lineage_matches_derived_record(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = root / "p2"; derived = root / "p2_null"
            base.mkdir(); derived.mkdir()
            (base / "run.json").write_text("{}", encoding="utf-8")
            (derived / "run.json").write_text("{}", encoding="utf-8")
            (base / "checkpoint.pt").write_bytes(b"frozen")
            records = [
                {"protocol_id": "receiver_loso_00", "model_stage": "P2", "config": {"seed": 829}, "record_path": str(base / "run.json")},
                {"run_id": "derived", "protocol_id": "receiver_loso_00", "model_stage": "P2_NULL", "config": {"seed": 829}, "record_path": str(derived / "run.json"), "base_checkpoint_sha256": sha256_file(base / "checkpoint.pt")},
            ]
            result = validate_checkpoint_lineage(records)
            self.assertEqual(result["trained_checkpoint_count"], 1)
            self.assertEqual(result["derived_lineage_count"], 1)

    def test_checkpoint_lineage_rejects_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = root / "p0"; derived = root / "t3a"
            base.mkdir(); derived.mkdir()
            (base / "run.json").write_text("{}", encoding="utf-8")
            (derived / "run.json").write_text("{}", encoding="utf-8")
            (base / "checkpoint.pt").write_bytes(b"frozen")
            records = [
                {"protocol_id": "receiver_loso_00", "model_stage": "P0", "config": {"seed": 829}, "record_path": str(base / "run.json")},
                {"run_id": "derived", "protocol_id": "receiver_loso_00", "model_stage": "T3A", "config": {"seed": 829}, "record_path": str(derived / "run.json"), "base_checkpoint_sha256": "bad"},
            ]
            with self.assertRaisesRegex(RuntimeError, "hash mismatch"):
                validate_checkpoint_lineage(records)

    def test_existing_freeze_is_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "freeze.json"; destination.write_text("{}", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                create_preunblinding_freeze(directory, directory, directory, destination, [], destination)


if __name__ == "__main__":
    unittest.main()
