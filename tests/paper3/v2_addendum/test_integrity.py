from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from openew.paper3.v2_addendum.integrity import validate_shuffled_records


def record(protocol: str, seed: int, *, status: str = "COMPLETE", labels: bool = False) -> dict:
    return {"protocol_id": protocol, "seed": seed, "status": status, "git_sha": "abc", "labels_used_to_construct_training_context": labels}


def write_grid(root: Path, *, failed: bool = False, labels: bool = False, duplicate: bool = False) -> None:
    offset = 0
    for receiver in range(32):
        for seed in (829,1829,2829,3829,4829):
            protocol=f"receiver_loso_{receiver:02d}"
            value=record(protocol,seed,status="FAILED" if failed and offset==0 else "COMPLETE",labels=labels and offset==0)
            path=root/"shuffled_training"/"runs"/f"run_{offset}"/"run.json"
            path.parent.mkdir(parents=True); path.write_text(json.dumps(value))
            offset+=1
    if duplicate:
        first=root/"shuffled_training"/"runs"/"run_0"/"run.json"
        second=root/"shuffled_training"/"runs"/"run_1"/"run.json"
        second.write_text(first.read_text())


class IntegrityTests(unittest.TestCase):
    def test_complete_registry_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); write_grid(root)
            result=validate_shuffled_records(root)
            self.assertEqual(result["run_count"],160)
            self.assertEqual(result["failed"],0)

    def test_missing_registry_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(RuntimeError):
            validate_shuffled_records(tmp)

    def test_failed_registry_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); write_grid(root,failed=True)
            with self.assertRaises(RuntimeError): validate_shuffled_records(root)

    def test_label_dependent_registry_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); write_grid(root,labels=True)
            with self.assertRaises(RuntimeError): validate_shuffled_records(root)

    def test_duplicate_protocol_seed_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); write_grid(root,duplicate=True)
            with self.assertRaises(RuntimeError): validate_shuffled_records(root)

    def test_git_sha_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); write_grid(root)
            self.assertEqual(validate_shuffled_records(root)["git_shas"],["abc"])


if __name__ == "__main__": unittest.main()
