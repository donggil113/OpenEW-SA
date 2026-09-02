from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from openew.paper3.dataset_qualification.adoption_decision import decide_adoption
from openew.paper3.dataset_qualification.candidate_schema import AccessStatus, TriState
from openew.paper3.dataset_qualification.license_gate import evaluate_license
from openew.paper3.dataset_qualification.manifest import build_metadata_manifest
from openew.paper3.dataset_qualification.official_evidence import OfficialEvidenceGate
from openew.paper3.dataset_qualification.planning import estimate_collection_storage, plan_structural_coverage
from openew.paper3.dataset_qualification.storage_gate import StorageGateResult
from openew.paper3.dataset_qualification.target_proxy_gate import ProxyGateResult
from openew.paper3.dataset_qualification.temporal_gate import CandidateTemporalStatus, TemporalGateResult


class PlanningTests(unittest.TestCase):
    def test_raw_storage_exact(self): self.assertEqual(estimate_collection_storage(sample_rate_hz=1, sample_format="complex64", channels=1, duration_seconds=1, receivers=1, sessions=1, captures_per_session=1).raw_bytes, 8)
    def test_unknown_format_rejected(self):
        with self.assertRaises(ValueError): estimate_collection_storage(sample_rate_hz=1, sample_format="x", channels=1, duration_seconds=1, receivers=1, sessions=1, captures_per_session=1)
    def test_nonpositive_dimension_rejected(self):
        with self.assertRaises(ValueError): estimate_collection_storage(sample_rate_hz=0, sample_format="complex64", channels=1, duration_seconds=1, receivers=1, sessions=1, captures_per_session=1)
    def test_bad_compression_rejected(self):
        with self.assertRaises(ValueError): estimate_collection_storage(sample_rate_hz=1, sample_format="complex64", channels=1, duration_seconds=1, receivers=1, sessions=1, captures_per_session=1, compression_low_ratio=.9, compression_high_ratio=.8)
    def test_headroom_increases_recommendation(self): self.assertGreater(estimate_collection_storage(sample_rate_hz=1, sample_format="complex64", channels=1, duration_seconds=1, receivers=1, sessions=1, captures_per_session=1).recommended_total_disk_bytes, 8)
    def test_structural_total(self): self.assertEqual(plan_structural_coverage(receivers=2, sessions=4, campaigns=2, samples_per_session=10, expected_intra_session_correlation=.1, seed_count=5, mixed_label_sessions=4).total_samples, 40)
    def test_receiver_holdout_support(self): self.assertTrue(plan_structural_coverage(receivers=2, sessions=4, campaigns=2, samples_per_session=10, expected_intra_session_correlation=.1, seed_count=5, mixed_label_sessions=8).receiver_holdout_supported)
    def test_single_receiver_no_holdout(self): self.assertFalse(plan_structural_coverage(receivers=1, sessions=4, campaigns=2, samples_per_session=10, expected_intra_session_correlation=.1, seed_count=5, mixed_label_sessions=8).receiver_holdout_supported)
    def test_mixed_sessions_gate(self): self.assertFalse(plan_structural_coverage(receivers=2, sessions=4, campaigns=2, samples_per_session=10, expected_intra_session_correlation=.1, seed_count=5, mixed_label_sessions=7).mixed_label_session_requirement_met)
    def test_invalid_correlation(self):
        with self.assertRaises(ValueError): plan_structural_coverage(receivers=2, sessions=4, campaigns=2, samples_per_session=10, expected_intra_session_correlation=1.0, seed_count=5, mixed_label_sessions=8)


class ManifestTests(unittest.TestCase):
    def test_manifest_hash_and_size(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "README.md").write_text("official", encoding="utf-8")
            result = build_metadata_manifest(directory, source_urls=("https://example.edu",), license_evidence="unresolved", source_versions={"repo": "abc"})
            self.assertEqual(result["file_count"], 1); self.assertEqual(result["total_size_bytes"], 8)
    def test_existing_manifest_excluded(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "metadata_manifest.json").write_text("{}", encoding="utf-8")
            self.assertEqual(build_metadata_manifest(directory, source_urls=(), license_evidence="none", source_versions={})["file_count"], 0)


class AdoptionTests(unittest.TestCase):
    def decision(self, **updates):
        licence=evaluate_license(license_name="CC", verified=TriState.TRUE, applies_to_dataset_payload=TriState.TRUE, permits_research_use=TriState.TRUE, permits_derived_artifacts=TriState.TRUE, permits_redistribution=TriState.TRUE)
        values=dict(access_status=AccessStatus.PUBLIC_DIRECT, official_evidence=OfficialEvidenceGate(True,1,("ok",)), license_gate=licence, storage_gate=StorageGateResult(True,1000,10,("ok",)), proxy_gate=ProxyGateResult(("receiver_id",),(),(),(),True), temporal_gate=TemporalGateResult(CandidateTemporalStatus.VALID_TEMPORAL_CONTEXT,("ok",)), readiness_highest="STATIC_RELATIONAL", split_protocol_frozen=True, task_distinct=True)
        values.update(updates); return decide_adoption(**values)
    def test_go_authorizes(self): self.assertTrue(self.decision().next_model_experiment_authorized)
    def test_unfrozen_split_blocks(self): self.assertFalse(self.decision(split_protocol_frozen=False).next_model_experiment_authorized)
    def test_task_not_distinct_blocks(self): self.assertFalse(self.decision(task_distinct=False).next_model_experiment_authorized)
    def test_independent_only_blocks(self): self.assertFalse(self.decision(readiness_highest="INDEPENDENT_SAMPLE_ONLY").next_model_experiment_authorized)
    def test_proxy_failure_blocks(self): self.assertFalse(self.decision(proxy_gate=ProxyGateResult((),("tx_id",),(),(),False)).next_model_experiment_authorized)
    def test_storage_failure_blocks(self): self.assertFalse(self.decision(storage_gate=StorageGateResult(False,1000,2000,("too large",))).next_model_experiment_authorized)
    def test_metadata_only_access_conditional(self): self.assertEqual(self.decision(access_status=AccessStatus.PUBLIC_METADATA_ONLY).access, "CONDITIONAL GO")
    def test_unknown_access_no_go(self): self.assertEqual(self.decision(access_status=AccessStatus.UNKNOWN).access, "NO-GO")


if __name__ == "__main__": unittest.main()
