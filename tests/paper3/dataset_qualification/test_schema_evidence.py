from __future__ import annotations

import unittest

from openew.paper3.dataset_qualification.candidate_schema import CandidateEvidence, TriState
from openew.paper3.dataset_qualification.official_evidence import EvidenceItem, evaluate_official_evidence

from tests.paper3.dataset_qualification.common import candidate_mapping


class CandidateSchemaTests(unittest.TestCase):
    def test_valid_candidate(self):
        self.assertEqual(CandidateEvidence.from_mapping(candidate_mapping()).candidate_id, "cand-001")

    def test_unknown_field_fails_closed(self):
        row = candidate_mapping(); row["mystery"] = 1
        with self.assertRaises(ValueError): CandidateEvidence.from_mapping(row)

    def test_missing_field_fails(self):
        row = candidate_mapping(); row.pop("task")
        with self.assertRaises(ValueError): CandidateEvidence.from_mapping(row)

    def test_unknown_license_preserved(self):
        row = candidate_mapping(); row["license_verified"] = "UNKNOWN"
        self.assertIs(CandidateEvidence.from_mapping(row).license_verified, TriState.UNKNOWN)

    def test_missing_size_preserved(self):
        row = candidate_mapping(); row["download_size_bytes"] = None
        self.assertIsNone(CandidateEvidence.from_mapping(row).download_size_bytes)

    def test_negative_size_rejected(self):
        row = candidate_mapping(); row["download_size_bytes"] = -1
        with self.assertRaises(ValueError): CandidateEvidence.from_mapping(row)

    def test_float_count_rejected(self):
        row = candidate_mapping(); row["receiver_count"] = 2.0
        with self.assertRaises(TypeError): CandidateEvidence.from_mapping(row)

    def test_boolean_count_rejected(self):
        row = candidate_mapping(); row["day_count"] = True
        with self.assertRaises(TypeError): CandidateEvidence.from_mapping(row)

    def test_empty_identifier_rejected(self):
        row = candidate_mapping(); row["candidate_id"] = ""
        with self.assertRaises(ValueError): CandidateEvidence.from_mapping(row)

    def test_target_field_stays_string(self):
        row = candidate_mapping(); row["target_field"] = "0007"
        self.assertEqual(CandidateEvidence.from_mapping(row).target_field, "0007")

    def test_roundtrip_mapping(self):
        row = candidate_mapping()
        self.assertEqual(CandidateEvidence.from_mapping(row).to_mapping(), row)

    def test_bad_enum_rejected(self):
        row = candidate_mapping(); row["access_status"] = "MAYBE"
        with self.assertRaises(ValueError): CandidateEvidence.from_mapping(row)

    def test_non_sequence_proxy_fields_rejected(self):
        row = candidate_mapping(); row["target_proxy_fields"] = "transmitter_id"
        with self.assertRaises(TypeError): CandidateEvidence.from_mapping(row)

    def test_null_optional_urls(self):
        row = candidate_mapping(); row["official_paper"] = None
        self.assertIsNone(CandidateEvidence.from_mapping(row).official_paper)

    def test_schema_version_rejected(self):
        row = candidate_mapping(); row["schema_version"] = "2.0.0"
        with self.assertRaises(ValueError): CandidateEvidence.from_mapping(row)


class OfficialEvidenceTests(unittest.TestCase):
    def item(self, **updates):
        values = dict(requirement="receiver count", source_title="Official", url="https://example.edu", exact_location="Table 1", evidence="two receivers", primary_source=True, official_source=True, verified=True, accessed_at_utc="2026-09-02T00:00:00Z")
        values.update(updates); return EvidenceItem(**values)

    def test_verified_primary_passes(self):
        self.assertTrue(evaluate_official_evidence((self.item(),)).passed)

    def test_unofficial_mirror_does_not_pass(self):
        self.assertFalse(evaluate_official_evidence((self.item(official_source=False),)).passed)

    def test_unverified_source_does_not_pass(self):
        self.assertFalse(evaluate_official_evidence((self.item(verified=False),)).passed)

    def test_secondary_source_does_not_pass(self):
        self.assertFalse(evaluate_official_evidence((self.item(primary_source=False),)).passed)

    def test_http_source_rejected(self):
        with self.assertRaises(ValueError): evaluate_official_evidence((self.item(url="http://example.edu"),))

    def test_empty_evidence_rejected(self):
        with self.assertRaises(ValueError): evaluate_official_evidence((self.item(evidence=""),))


if __name__ == "__main__": unittest.main()
