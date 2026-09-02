from __future__ import annotations

import unittest

from openew.paper3.dataset_qualification.metadata_gate import CandidateRelationEvidence, evaluate_metadata_readiness
from openew.paper3.dataset_qualification.target_proxy_gate import evaluate_target_proxy_fields, target_bearing_tokens
from openew.paper3.dataset_qualification.temporal_gate import CandidateTemporalEvidence, CandidateTemporalStatus, evaluate_temporal


class ProxyGateTests(unittest.TestCase):
    def test_target_bearing_transmitter_rejected(self): self.assertFalse(evaluate_target_proxy_fields(("transmitter_id",), independently_verified_target_neutral=()).passed)
    def test_tx_token_rejected(self): self.assertFalse(evaluate_target_proxy_fields(("tx_id",), independently_verified_target_neutral=()).passed)
    def test_target_neutral_receiver_allowed(self): self.assertTrue(evaluate_target_proxy_fields(("receiver_id",), independently_verified_target_neutral=("receiver_id",)).passed)
    def test_unverified_receiver_unresolved(self): self.assertFalse(evaluate_target_proxy_fields(("receiver_id",), independently_verified_target_neutral=()).passed)
    def test_unknown_field_fails_closed(self): self.assertFalse(evaluate_target_proxy_fields(("room_color",), independently_verified_target_neutral=("room_color",)).passed)
    def test_target_bearing_path_rejected(self): self.assertIn("class", target_bearing_tokens("raw/class/device.bin", ()))
    def test_target_token_parameter_rejected(self): self.assertIn("radio7", target_bearing_tokens("raw/radio7/file.bin", ("radio7",)))
    def test_neutral_path_passes(self): self.assertEqual(target_bearing_tokens("raw/session-uuid/capture.bin", ()), ())
    def test_prediction_field_rejected(self): self.assertFalse(evaluate_target_proxy_fields(("prediction",), independently_verified_target_neutral=()).passed)
    def test_ood_field_rejected(self): self.assertFalse(evaluate_target_proxy_fields(("ood_id",), independently_verified_target_neutral=()).passed)


def temporal(**updates):
    values = dict(explicit_acquisition_timestamp=True, physical_order_preserved=True, session_boundaries_verified=True, clock_reset_semantics_verified=True, gap_meaning_verified=True, inference_time_available=True, coarse_day_only=False, filesystem_mtime_only=False, container_target_pure=False, mixed_target_episode_fraction=0.5)
    values.update(updates); return evaluate_temporal(CandidateTemporalEvidence(**values))


class TemporalGateTests(unittest.TestCase):
    def test_valid_timestamp(self): self.assertIs(temporal().status, CandidateTemporalStatus.VALID_TEMPORAL_CONTEXT)
    def test_filesystem_mtime_rejected(self): self.assertIs(temporal(filesystem_mtime_only=True).status, CandidateTemporalStatus.NO_TEMPORAL_CONTEXT)
    def test_coarse_day_only(self): self.assertIs(temporal(coarse_day_only=True).status, CandidateTemporalStatus.COARSE_DAY_ONLY)
    def test_capture_order_only(self): self.assertIs(temporal(explicit_acquisition_timestamp=False).status, CandidateTemporalStatus.ORDER_ONLY_NO_CLOCK)
    def test_target_pure_capture(self): self.assertIs(temporal(container_target_pure=True).status, CandidateTemporalStatus.TARGET_NESTED_SEQUENCE)
    def test_mixed_label_absent(self): self.assertIs(temporal(mixed_target_episode_fraction=0).status, CandidateTemporalStatus.TARGET_NESTED_SEQUENCE)
    def test_missing_session_unknown(self): self.assertIs(temporal(session_boundaries_verified=None).status, CandidateTemporalStatus.UNKNOWN)
    def test_no_time_no_order(self): self.assertIs(temporal(explicit_acquisition_timestamp=False, physical_order_preserved=False).status, CandidateTemporalStatus.NO_TEMPORAL_CONTEXT)
    def test_unknown_time_order(self): self.assertIs(temporal(explicit_acquisition_timestamp=None, physical_order_preserved=None).status, CandidateTemporalStatus.UNKNOWN)
    def test_clock_reset_unknown(self): self.assertIs(temporal(clock_reset_semantics_verified=None).status, CandidateTemporalStatus.UNKNOWN)


class ReadinessTests(unittest.TestCase):
    def relation(self, **updates):
        values = dict(field="receiver_id", coverage=1.0, repeated_group_fraction=1.0, target_proxy_rejected=True, independently_verified=True)
        values.update(updates); return CandidateRelationEvidence(**values)

    def test_independent_only_without_relations(self): self.assertEqual(evaluate_metadata_readiness((), temporal_status=CandidateTemporalStatus.UNKNOWN, mixed_target_episode_fraction=0)["highest_level"], "INDEPENDENT_SAMPLE_ONLY")
    def test_static_relation(self): self.assertEqual(evaluate_metadata_readiness((self.relation(),), temporal_status=CandidateTemporalStatus.UNKNOWN, mixed_target_episode_fraction=0)["highest_level"], "STATIC_RELATIONAL")
    def test_static_hypergraph_two_relations(self): self.assertEqual(evaluate_metadata_readiness((self.relation(), self.relation(field="site_id")), temporal_status=CandidateTemporalStatus.UNKNOWN, mixed_target_episode_fraction=0)["highest_level"], "STATIC_HYPERGRAPH")
    def test_low_coverage_rejected(self): self.assertEqual(evaluate_metadata_readiness((self.relation(coverage=.79),), temporal_status=CandidateTemporalStatus.UNKNOWN, mixed_target_episode_fraction=0)["highest_level"], "INDEPENDENT_SAMPLE_ONLY")
    def test_low_repetition_rejected(self): self.assertEqual(evaluate_metadata_readiness((self.relation(repeated_group_fraction=.49),), temporal_status=CandidateTemporalStatus.UNKNOWN, mixed_target_episode_fraction=0)["highest_level"], "INDEPENDENT_SAMPLE_ONLY")
    def test_proxy_not_rejected_fails(self): self.assertEqual(evaluate_metadata_readiness((self.relation(target_proxy_rejected=False),), temporal_status=CandidateTemporalStatus.UNKNOWN, mixed_target_episode_fraction=0)["highest_level"], "INDEPENDENT_SAMPLE_ONLY")
    def test_unverified_relation_fails(self): self.assertEqual(evaluate_metadata_readiness((self.relation(independently_verified=False),), temporal_status=CandidateTemporalStatus.UNKNOWN, mixed_target_episode_fraction=0)["highest_level"], "INDEPENDENT_SAMPLE_ONLY")
    def test_temporal_with_one_relation(self): self.assertEqual(evaluate_metadata_readiness((self.relation(),), temporal_status=CandidateTemporalStatus.VALID_TEMPORAL_CONTEXT, mixed_target_episode_fraction=.5)["highest_level"], "TEMPORAL_RELATIONAL")
    def test_dynamic_with_two_relations(self): self.assertEqual(evaluate_metadata_readiness((self.relation(), self.relation(field="site_id")), temporal_status=CandidateTemporalStatus.VALID_TEMPORAL_CONTEXT, mixed_target_episode_fraction=.5)["highest_level"], "DYNAMIC_HYPERGRAPH")
    def test_temporal_requires_mixed_episode(self): self.assertEqual(evaluate_metadata_readiness((self.relation(),), temporal_status=CandidateTemporalStatus.VALID_TEMPORAL_CONTEXT, mixed_target_episode_fraction=0)["highest_level"], "STATIC_RELATIONAL")


if __name__ == "__main__": unittest.main()
