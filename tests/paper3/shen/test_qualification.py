from __future__ import annotations

import unittest

from openew.paper3.shen.qualification import (
    GateStatus,
    ShenQualification,
    current_official_evidence_qualification,
    evaluate_qualification,
)


def qualification(**overrides: GateStatus) -> ShenQualification:
    values = {name: GateStatus.PASS for name in ShenQualification.__dataclass_fields__}
    values.update(overrides)
    return ShenQualification(**values)


class QualificationTests(unittest.TestCase):
    def test_all_pass_authorizes_every_path(self) -> None:
        value = qualification()
        self.assertTrue(value.payload_authorized)
        self.assertTrue(value.bounded_benchmark_authorized)
        self.assertTrue(value.exact_replication_authorized)

    def test_current_evidence_blocks_payload(self) -> None:
        value = current_official_evidence_qualification()
        self.assertFalse(value.payload_authorized)
        self.assertFalse(value.bounded_benchmark_authorized)
        self.assertFalse(value.exact_replication_authorized)

    def test_current_evidence_preserves_provenance_pass(self) -> None:
        self.assertIs(current_official_evidence_qualification().official_provenance, GateStatus.PASS)

    def test_current_evidence_marks_episode_fail(self) -> None:
        self.assertIs(current_official_evidence_qualification().acquired_calibration_episode, GateStatus.FAIL)

    def test_current_evidence_marks_proxy_not_run(self) -> None:
        self.assertIs(current_official_evidence_qualification().target_proxy, GateStatus.NOT_RUN)

    def test_missing_fields_fail_closed(self) -> None:
        value = evaluate_qualification({"official_provenance": "PASS"})
        self.assertIs(value.licence, GateStatus.UNKNOWN)
        self.assertFalse(value.payload_authorized)

    def test_unknown_gate_name_rejected(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_qualification({"model_accuracy": "PASS"})

    def test_invalid_status_rejected(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_qualification({"licence": "MAYBE"})

    def test_status_case_is_normalized(self) -> None:
        self.assertIs(evaluate_qualification({"licence": "pass"}).licence, GateStatus.PASS)

    def test_dict_contains_boolean_decisions(self) -> None:
        value = qualification(acquired_calibration_episode=GateStatus.FAIL).to_dict()
        self.assertTrue(value["bounded_benchmark_authorized"])
        self.assertFalse(value["exact_replication_authorized"])


def _make_payload_gate_test(field: str, status: GateStatus):
    def test(self: QualificationTests) -> None:
        value = qualification(**{field: status})
        self.assertFalse(value.payload_authorized)
    return test


for _field in ("official_provenance", "licence", "access", "storage", "task_compatibility", "raw_iq_conversion"):
    for _status in (GateStatus.FAIL, GateStatus.UNKNOWN, GateStatus.NOT_RUN):
        setattr(QualificationTests, f"test_payload_gate_{_field}_{_status.value.lower()}", _make_payload_gate_test(_field, _status))


def _make_safety_gate_test(field: str):
    def test(self: QualificationTests) -> None:
        value = qualification(**{field: GateStatus.FAIL})
        self.assertTrue(value.payload_authorized)
        self.assertFalse(value.bounded_benchmark_authorized)
    return test


for _field in ("target_proxy", "split_integrity"):
    setattr(QualificationTests, f"test_benchmark_gate_{_field}", _make_safety_gate_test(_field))


if __name__ == "__main__":
    unittest.main()
