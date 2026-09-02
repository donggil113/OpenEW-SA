from __future__ import annotations

import unittest

from openew.paper3.metadata.enums import Eligibility
from openew.paper3.metadata.leakage import (
    EligibilityEngine,
    assert_target_neutral_path,
    default_eligibility_engine,
    target_bearing_path_tokens,
)


class LeakageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = default_eligibility_engine()

    def test_label_field_rejected(self) -> None:
        with self.assertRaises(ValueError): self.engine.require("target_label", Eligibility.RELATION_ALLOWED)

    def test_ood_field_rejected(self) -> None:
        with self.assertRaises(ValueError): self.engine.require("ood_label", Eligibility.RELATION_ALLOWED)

    def test_prediction_field_rejected(self) -> None:
        with self.assertRaises(ValueError): self.engine.require("prediction", Eligibility.RELATION_ALLOWED)

    def test_correctness_field_rejected(self) -> None:
        with self.assertRaises(ValueError): self.engine.require("correctness", Eligibility.RELATION_ALLOWED)

    def test_domain_is_split_only(self) -> None:
        self.assertIs(self.engine.eligibility("domain_id"), Eligibility.SPLIT_ONLY)

    def test_unknown_field_fails_closed(self) -> None:
        self.assertIs(self.engine.eligibility("invented"), Eligibility.UNRESOLVED)
        with self.assertRaises(ValueError): self.engine.require("invented", Eligibility.RELATION_ALLOWED)

    def test_explicit_whitelist_enforced(self) -> None:
        with self.assertRaises(ValueError): self.engine.require_relation_fields(["receiver_id"], [])

    def test_allowed_relation_passes_whitelist(self) -> None:
        self.assertEqual(self.engine.require_relation_fields(["receiver_id"], ["receiver_id"]), ("receiver_id",))

    def test_frequency_not_relation_by_default(self) -> None:
        with self.assertRaises(ValueError): self.engine.require_relation_fields(["lower_frequency_hz"], ["lower_frequency_hz"])

    def test_target_bearing_path_flagged(self) -> None:
        self.assertIn("jammer", target_bearing_path_tokens("raw/reactive_jammer/capture.bin"))

    def test_binary_occupancy_path_flagged(self) -> None:
        self.assertIn("four_bit_occupancy_code", target_bearing_path_tokens("0001_day1.bin"))

    def test_opaque_path_allowed(self) -> None:
        assert_target_neutral_path("raw/campaign-uuid/session-uuid/550e8400-e29b.bin")

    def test_custom_extra_token_flagged(self) -> None:
        with self.assertRaises(ValueError): assert_target_neutral_path("raw/square/c.bin", ["square"])

    def test_engine_does_not_infer_from_field_name(self) -> None:
        engine = EligibilityEngine({"innocent_name": Eligibility.FORBIDDEN_TARGET_PROXY})
        with self.assertRaises(ValueError): engine.require("innocent_name", Eligibility.RELATION_ALLOWED)


if __name__ == "__main__":
    unittest.main()
