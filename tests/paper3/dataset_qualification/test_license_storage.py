from __future__ import annotations

import unittest

from openew.paper3.dataset_qualification.candidate_schema import TriState
from openew.paper3.dataset_qualification.license_gate import evaluate_license
from openew.paper3.dataset_qualification.storage_gate import (
    DownloadKind,
    METADATA_LIMIT_BYTES,
    SAMPLE_LIMIT_BYTES,
    evaluate_download,
)


def license_result(**updates):
    values = dict(license_name="CC-BY-4.0", verified=TriState.TRUE, applies_to_dataset_payload=TriState.TRUE, permits_research_use=TriState.TRUE, permits_derived_artifacts=TriState.TRUE, permits_redistribution=TriState.TRUE)
    values.update(updates); return evaluate_license(**values)


class LicenseGateTests(unittest.TestCase):
    def test_clear_license(self): self.assertEqual(license_result().status, "CLEAR")
    def test_unknown_license(self): self.assertEqual(license_result(verified=TriState.UNKNOWN).status, "UNRESOLVED")
    def test_code_license_not_payload(self): self.assertFalse(license_result(applies_to_dataset_payload=TriState.FALSE).permits_download)
    def test_missing_license_name(self): self.assertEqual(license_result(license_name=None).status, "UNRESOLVED")
    def test_research_forbidden(self): self.assertEqual(license_result(permits_research_use=TriState.FALSE).status, "RESTRICTED")
    def test_research_unknown(self): self.assertEqual(license_result(permits_research_use=TriState.UNKNOWN).status, "UNRESOLVED")
    def test_derived_unknown_is_restricted(self): self.assertEqual(license_result(permits_derived_artifacts=TriState.UNKNOWN).status, "RESTRICTED")
    def test_redistribution_false_does_not_forbid_research_download(self): self.assertTrue(license_result(permits_redistribution=TriState.FALSE).permits_download)
    def test_redistribution_unknown_preserved(self): self.assertIsNone(license_result(permits_redistribution=TriState.UNKNOWN).permits_redistribution)
    def test_noncommercial_restriction_is_restricted(self): self.assertEqual(license_result(use_restrictions=("NONCOMMERCIAL",)).status, "RESTRICTED")


class StorageGateTests(unittest.TestCase):
    def gate(self, **updates):
        values = dict(kind=DownloadKind.METADATA, requested_bytes=1000, free_bytes=100_000_000_000, license_verified=False, official_source_verified=True, secret_required=False)
        values.update(updates); return evaluate_download(**values)

    def test_metadata_allowed_without_payload_license(self): self.assertTrue(self.gate().allowed)
    def test_metadata_limit_enforced(self): self.assertFalse(self.gate(requested_bytes=METADATA_LIMIT_BYTES+1).allowed)
    def test_sample_limit_enforced(self): self.assertFalse(self.gate(kind=DownloadKind.SAMPLE, requested_bytes=SAMPLE_LIMIT_BYTES+1, license_verified=True).allowed)
    def test_ten_percent_free_limit_enforced(self): self.assertFalse(self.gate(requested_bytes=101, free_bytes=1000).allowed)
    def test_unknown_size_fails_closed(self): self.assertFalse(self.gate(requested_bytes=None).allowed)
    def test_unofficial_source_rejected(self): self.assertFalse(self.gate(official_source_verified=False).allowed)
    def test_sample_needs_license(self): self.assertFalse(self.gate(kind=DownloadKind.SAMPLE).allowed)
    def test_sample_with_license_allowed(self): self.assertTrue(self.gate(kind=DownloadKind.SAMPLE, license_verified=True).allowed)
    def test_full_dataset_never_automatic(self): self.assertFalse(self.gate(kind=DownloadKind.FULL_DATASET, license_verified=True).allowed)
    def test_secret_required_rejected(self): self.assertFalse(self.gate(secret_required=True).allowed)
    def test_negative_request_rejected(self):
        with self.assertRaises(ValueError): self.gate(requested_bytes=-1)
    def test_negative_free_rejected(self):
        with self.assertRaises(ValueError): self.gate(free_bytes=-1)


if __name__ == "__main__": unittest.main()
