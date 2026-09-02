from __future__ import annotations

import unittest
import tempfile

import numpy as np
import pandas as pd

from openew.paper3.wisig.analysis import audit_run_completeness, descriptive_summary, go_no_go, hierarchical_fold_bootstrap, paired_differences, postfreeze_error_diagnostics, select_primary


def primary_fixture(delta: float = 0.02) -> pd.DataFrame:
    rows=[]
    models=["P0","P0_WIDE","P1","P2","P2_SHUFFLED","P2_NULL"]
    for fold in range(5):
        for seed in (829,1829):
            for model in models:
                base=.5 + fold*.01
                add={"P0":0,"P0_WIDE":.005,"P1":.01,"P2":delta,"P2_SHUFFLED":.002,"P2_NULL":.001}[model]
                rows.append({"protocol_id":f"receiver_fold_{fold}","protocol_type":"receiver_holdout","fold_index":fold,"seed":seed,"model_stage":model,"context_size":32,"relation_retention":0.0 if model=="P2_NULL" else 1.0,"source_validation_macro_f1":base+add,"held_out_macro_f1":base+add,"held_out_balanced_accuracy":base,"held_out_accuracy":base,"held_out_ece":.1})
    return pd.DataFrame(rows)


class AnalysisTests(unittest.TestCase):
    def test_completeness_empty_root_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            result = audit_run_completeness(directory)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["expected_unique_runs"], 530)
        self.assertEqual(result["actual_unique_config_hashes"], 0)
        self.assertFalse(result["checks"]["all_checkpoint_files_present"])

    def test_completeness_exact_frozen_grid_passes(self):
        import json
        from pathlib import Path
        from openew.paper3.wisig.suite import deduplicate_plan, full_suite_plan
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, (_, config) in enumerate(deduplicate_plan(full_suite_plan())):
                run_id = f"run_{index:04d}"
                target = root / "runs" / run_id
                target.mkdir(parents=True)
                prediction = target / "predictions.csv"
                prediction.write_text("sample_id,prediction\n",encoding="utf-8")
                (target / "checkpoint.pt").write_bytes(b"checkpoint")
                import hashlib
                prediction_hash = hashlib.sha256(prediction.read_bytes()).hexdigest()
                (target / "run.json").write_text(json.dumps({"run_id":run_id,"config":config.__dict__,"config_hash":config.config_hash,"status":"COMPLETE","git_sha":"frozen","data_manifest_sha256":"data","prediction_sha256":prediction_hash}),encoding="utf-8")
            result = audit_run_completeness(root)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["actual_unique_config_hashes"], 530)

    def test_postfreeze_empty_run_root_is_explicit(self):
        with tempfile.TemporaryDirectory() as run_root, tempfile.TemporaryDirectory() as converted_root:
            # A minimal converted-table fixture is still required; no prediction rows are fabricated.
            import json
            from pathlib import Path
            root = Path(converted_root)
            shard = root / "shards" / "shard_00000"
            shard.mkdir(parents=True)
            pd.DataFrame([{"sample_id":"001","receiver_id":"rx","day_id":"d","packet_index":0,"source_record_index":0,"center_frequency_hz":1,"bandwidth_hz":1,"sample_rate_hz":1,"data_quality_flags":"OK","feature_shard":"shard_00000","feature_row":0}]).to_csv(shard/"acquisition_metadata.csv",index=False)
            pd.DataFrame([{"sample_id":"001","task_name":"rf_fingerprinting","transmitter_id":"tx"}]).to_csv(shard/"annotations.csv",index=False)
            (root/"dataset_manifest.json").write_text(json.dumps({"shards":[{"name":"shard_00000"}]}),encoding="utf-8")
            detail, summary = postfreeze_error_diagnostics(run_root, converted_root)
        self.assertTrue(detail.empty)
        self.assertTrue(summary["diagnostic_only"])
        self.assertFalse(summary["used_for_model_redesign"])

    def test_primary_selects_all_models(self): self.assertEqual(len(select_primary(primary_fixture(),"receiver_holdout")),60)
    def test_summary_has_model_rows(self): self.assertEqual(len(descriptive_summary(primary_fixture(),["model_stage"])),6)
    def test_paired_comparisons_present(self): self.assertIn("P2-P0",set(paired_differences(primary_fixture()).comparison))
    def test_paired_delta_exact(self):
        values=paired_differences(primary_fixture(.02)); self.assertAlmostEqual(values[values.comparison=="P2-P0"].held_out_macro_f1_delta.mean(),.02)
    def test_bootstrap_replicate_count(self):
        result=hierarchical_fold_bootstrap(paired_differences(primary_fixture()),replicates=25); self.assertTrue((result.bootstrap_replicates==25).all())
    def test_bootstrap_is_deterministic(self):
        diff=paired_differences(primary_fixture()); a=hierarchical_fold_bootstrap(diff,replicates=25); b=hierarchical_fold_bootstrap(diff,replicates=25); pd.testing.assert_frame_equal(a,b)
    def test_bootstrap_cluster_unit(self):
        result=hierarchical_fold_bootstrap(paired_differences(primary_fixture()),replicates=10); self.assertTrue((result.cluster_unit=="receiver_fold").all())
    def test_go_fixture(self): self.assertEqual(go_no_go(primary_fixture(),paired_differences(primary_fixture()),leakage_gate_passed=True)["verdict"],"GO")
    def test_nogo_shuffled_equivalent(self):
        frame=primary_fixture(); frame.loc[frame.model_stage=="P2_SHUFFLED","held_out_macro_f1"] = frame.loc[frame.model_stage=="P2","held_out_macro_f1"].to_numpy(); self.assertNotEqual(go_no_go(frame,paired_differences(frame),leakage_gate_passed=True)["verdict"],"GO")
    def test_no_significance_claim(self): self.assertFalse(go_no_go(primary_fixture(),paired_differences(primary_fixture()),leakage_gate_passed=True)["statistical_significance_claimed"])
    def test_leakage_failure_forces_no_go(self):
        frame=primary_fixture(); decision=go_no_go(frame,paired_differences(frame),leakage_gate_passed=False)
        self.assertEqual(decision["verdict"],"NO-GO"); self.assertFalse(decision["criteria"]["leakage_gate"])
