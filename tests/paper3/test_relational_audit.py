from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from openew.paper3.relational_audit import (
    AUDIT_COLUMNS,
    DATASET_SUMMARY_COLUMNS,
    RELATION_COVERAGE_COLUMNS,
    audit_artifact,
    read_metadata_preserve_strings,
    run_audit,
    validate_relation_fields,
)


METADATA_COLUMNS = [
    "sample_id",
    "dataset_source",
    "input_type",
    "time_index",
    "frequency_band",
    "tx_id",
    "rx_id",
    "modulation_label",
    "occupancy_label",
    "abnormal_event_label",
    "domain_id",
    "synthetic_mission_context",
    "situation_label",
    "threat_level",
    "human_review_required",
]


class RelationalAuditTests(unittest.TestCase):
    def test_forbidden_target_fields_are_rejected(self) -> None:
        for field in ("occupancy_label", "ood_label", "test_correct"):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, "Forbidden"):
                    validate_relation_fields("deepsense", [field], [field])

    def test_allowed_field_whitelist_is_enforced(self) -> None:
        self.assertEqual(
            validate_relation_fields("jamshield", ["rx_id"], ["rx_id"]), ("rx_id",)
        )
        with self.assertRaisesRegex(ValueError, "exceeds reviewed"):
            validate_relation_fields("jamshield", ["domain_id"], ["domain_id"])
        with self.assertRaisesRegex(ValueError, "not explicitly whitelisted"):
            validate_relation_fields("jamshield", ["rx_id"], [])

    def test_deepsense_symbolic_strings_retain_leading_zeros(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "metadata.csv"
            pd.DataFrame({"occupancy_label": ["0001", "0010"]}).to_csv(path, index=False)
            frame = read_metadata_preserve_strings(path)
            self.assertEqual(frame["occupancy_label"].tolist(), ["0001", "0010"])

    def test_missing_and_empty_metadata_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.csv"
            with self.assertRaisesRegex(FileNotFoundError, "metadata.csv not found"):
                read_metadata_preserve_strings(missing)
            empty = Path(directory) / "metadata.csv"
            empty.write_text("", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "metadata.csv is empty"):
                read_metadata_preserve_strings(empty)

    def test_audit_does_not_mutate_source_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact = self._make_deepsense_artifact(Path(directory))
            before = self._hashes(artifact)
            audit, summary = audit_artifact("deepsense", artifact, [])
            after = self._hashes(artifact)
            self.assertEqual(before, after)
            self.assertEqual(summary["metadata_rows"], 2)
            self.assertFalse(audit.empty)

    def test_generated_audit_schema_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = self._make_deepsense_artifact(root / "source")
            result = run_audit(
                {"deepsense": artifact},
                root / "outputs",
                relation_whitelists={"deepsense": []},
            )
            self.assertEqual(result["audit"].columns.tolist(), AUDIT_COLUMNS)
            self.assertEqual(result["coverage"].columns.tolist(), RELATION_COVERAGE_COLUMNS)
            self.assertEqual(
                result["dataset_summary"].columns.tolist(), DATASET_SUMMARY_COLUMNS
            )
            for path in result["outputs"].values():
                self.assertTrue(Path(path).is_file())

    @staticmethod
    def _make_deepsense_artifact(root: Path) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        rows = [
            {
                "sample_id": "deepsense_00000000",
                "dataset_source": "deepsense",
                "input_type": "iq_features",
                "time_index": "0",
                "frequency_band": "wifi_20mhz_4ch",
                "tx_id": "",
                "rx_id": "deepsense_receiver",
                "modulation_label": "",
                "occupancy_label": "0001",
                "abnormal_event_label": "",
                "domain_id": "day1",
                "synthetic_mission_context": "spectrum_monitoring",
                "situation_label": "occupied",
                "threat_level": "low",
                "human_review_required": "False",
            },
            {
                "sample_id": "deepsense_00000001",
                "dataset_source": "deepsense",
                "input_type": "iq_features",
                "time_index": "0",
                "frequency_band": "wifi_20mhz_4ch",
                "tx_id": "",
                "rx_id": "deepsense_receiver",
                "modulation_label": "",
                "occupancy_label": "0010",
                "abnormal_event_label": "",
                "domain_id": "day2",
                "synthetic_mission_context": "spectrum_monitoring",
                "situation_label": "occupied",
                "threat_level": "low",
                "human_review_required": "False",
            },
        ]
        pd.DataFrame(rows, columns=METADATA_COLUMNS).to_csv(root / "metadata.csv", index=False)
        np.save(root / "features.npy", np.zeros((2, 2, 4), dtype=np.float32))
        labels = {
            "label_column": "occupancy_label",
            "num_samples": 2,
            "source_files": [
                {
                    "path": "0001_day1.bin",
                    "occupancy_label": "0001",
                    "domain_id": "day1",
                    "row_count": 1,
                },
                {
                    "path": "0010_day2.bin",
                    "occupancy_label": "0010",
                    "domain_id": "day2",
                    "row_count": 1,
                },
            ],
        }
        (root / "labels.json").write_text(json.dumps(labels), encoding="utf-8")
        return root

    @staticmethod
    def _hashes(root: Path) -> dict[str, str]:
        return {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.iterdir())
            if path.is_file()
        }


if __name__ == "__main__":
    unittest.main()
