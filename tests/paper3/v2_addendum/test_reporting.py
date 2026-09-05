from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from openew.paper3.v2_addendum.reporting import _hardware_summary, collect_shuffled_training, hash_addendum_analysis


def _record(protocol: str, receiver: str, seed: int) -> dict:
    evaluations = {}
    for stage, condition in (("P2","NATURAL"),("P2_SHUFFLED","SHUFFLED"),("P2_NULL","NULL")):
        evaluations[stage] = {
            "condition": condition,
            "evidence_category": "DEPLOYABLE_METHOD" if condition == "NATURAL" else "LABEL_FREE_CONTROL",
            "query_count": 10,
            "metrics": {"macro_f1": .8, "accuracy": .8, "balanced_accuracy": .8, "ece": .1},
            "receiver_diagnostics": {receiver: {}},
        }
    return {"status":"COMPLETE","analysis_status":"POSTHOC_MECHANISTIC","protocol_id":protocol,"seed":seed,"labels_used_to_construct_training_context":False,"best_epoch":3,"best_source_validation_macro_f1":.7,"wall_seconds":1.0,"evaluations":evaluations}


class ReportingTests(unittest.TestCase):
    def test_missing_records_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(RuntimeError):
            collect_shuffled_training(tmp)

    def test_complete_grid_has_480_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for receiver in range(32):
                for seed in (829,1829,2829,3829,4829):
                    path = root / "shuffled_training" / "runs" / f"r{receiver}__s{seed}" / "run.json"
                    path.parent.mkdir(parents=True)
                    path.write_text(json.dumps(_record(f"receiver_loso_{receiver:02d}",f"r{receiver}",seed)))
            frame = collect_shuffled_training(root)
            self.assertEqual(len(frame), 480)
            self.assertEqual(frame.receiver_id.nunique(), 32)

    def test_incomplete_record_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for receiver in range(32):
                for seed in (829,1829,2829,3829,4829):
                    value = _record(f"receiver_loso_{receiver:02d}",f"r{receiver}",seed)
                    if receiver == 0 and seed == 829: value["status"] = "FAILED"
                    path = root / "shuffled_training" / "runs" / f"r{receiver}__s{seed}" / "run.json"
                    path.parent.mkdir(parents=True); path.write_text(json.dumps(value))
            with self.assertRaises(RuntimeError): collect_shuffled_training(root)

    def test_label_dependent_training_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for receiver in range(32):
                for seed in (829,1829,2829,3829,4829):
                    value = _record(f"receiver_loso_{receiver:02d}",f"r{receiver}",seed)
                    if receiver == 0 and seed == 829: value["labels_used_to_construct_training_context"] = True
                    path = root / "shuffled_training" / "runs" / f"r{receiver}__s{seed}" / "run.json"
                    path.parent.mkdir(parents=True); path.write_text(json.dumps(value))
            with self.assertRaises(RuntimeError): collect_shuffled_training(root)

    def test_hardware_summary_uses_receiver_units(self) -> None:
        rows=[]
        for family,receiver in (("a","r1"),("a","r2"),("b","r3")):
            for model,value in (("P0",.7),("P2",.8),("T3A",.9)):
                for seed in (1,2): rows.append({"hardware_family":family,"receiver_id":receiver,"model":model,"seed":seed,"macro_f1":value})
        result=_hardware_summary(pd.DataFrame(rows))
        self.assertEqual(set(result.comparison),{"P2_MINUS_P0","T3A_MINUS_P0","P2_MINUS_T3A"})
        self.assertEqual(len(result),6)

    def test_manifest_create_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/"x.csv").write_text("a\n1\n")
            a=hash_addendum_analysis(root); b=hash_addendum_analysis(root)
            self.assertEqual(a,b)

    def test_manifest_detects_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); path=root/"x.csv"; path.write_text("a\n1\n")
            hash_addendum_analysis(root); path.write_text("a\n2\n")
            with self.assertRaises(RuntimeError): hash_addendum_analysis(root)

    def test_manifest_excludes_record_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); path=root/"records"/"x.json"; path.parent.mkdir(); path.write_text("{}")
            payload=hash_addendum_analysis(root)
            self.assertEqual(payload["file_count"],0)


if __name__ == "__main__": unittest.main()
