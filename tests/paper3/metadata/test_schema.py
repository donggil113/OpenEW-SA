from __future__ import annotations

import unittest

from openew.paper3.metadata.schema import (
    AcquisitionRecord,
    AnnotationRecord,
    SCHEMA_VERSION,
    acquisition_field_names,
    annotation_field_names,
)


class SchemaTests(unittest.TestCase):
    def base(self) -> dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "sample_id": "000123",
            "acquisition_session_id": "session-01",
            "capture_id": "capture-01",
            "within_capture_index": 0,
        }

    def test_valid_minimal_row(self) -> None:
        row = AcquisitionRecord.from_mapping(self.base())
        self.assertEqual(row.sample_id, "000123")

    def test_missing_required_field_rejected(self) -> None:
        value = self.base(); value.pop("capture_id")
        with self.assertRaises(ValueError):
            AcquisitionRecord.from_mapping(value)

    def test_optional_fields_are_optional(self) -> None:
        self.assertIsNone(AcquisitionRecord.from_mapping(self.base()).receiver_id)

    def test_bad_timestamp_rejected(self) -> None:
        value = self.base(); value["timestamp_utc"] = "not-time"
        with self.assertRaises(ValueError):
            AcquisitionRecord.from_mapping(value)

    def test_non_utc_timestamp_rejected(self) -> None:
        value = self.base(); value["timestamp_utc"] = "2026-01-01T00:00:00+09:00"
        with self.assertRaises(ValueError):
            AcquisitionRecord.from_mapping(value)

    def test_bad_frequency_order_rejected(self) -> None:
        value = self.base(); value.update(lower_frequency_hz=2.0, upper_frequency_hz=1.0)
        with self.assertRaises(ValueError):
            AcquisitionRecord.from_mapping(value)

    def test_center_outside_band_rejected(self) -> None:
        value = self.base(); value.update(lower_frequency_hz=1.0, center_frequency_hz=3.0, upper_frequency_hz=2.0)
        with self.assertRaises(ValueError):
            AcquisitionRecord.from_mapping(value)

    def test_bad_sampling_rate_rejected(self) -> None:
        value = self.base(); value["sample_rate_hz"] = 0
        with self.assertRaises(ValueError):
            AcquisitionRecord.from_mapping(value)

    def test_leading_zero_identifier_preserved(self) -> None:
        self.assertEqual(AcquisitionRecord.from_mapping(self.base()).sample_id, "000123")

    def test_numeric_identifier_rejected(self) -> None:
        value = self.base(); value["sample_id"] = 123
        with self.assertRaises(TypeError):
            AcquisitionRecord.from_mapping(value)

    def test_unicode_identifier_preserved(self) -> None:
        value = self.base(); value["receiver_id"] = "수신기-01"
        self.assertEqual(AcquisitionRecord.from_mapping(value).receiver_id, "수신기-01")

    def test_large_identifier_preserved(self) -> None:
        value = self.base(); value["sample_id"] = "9" * 100
        self.assertEqual(len(AcquisitionRecord.from_mapping(value).sample_id), 100)

    def test_unknown_field_fails_closed(self) -> None:
        value = self.base(); value["mystery"] = "value"
        with self.assertRaises(ValueError):
            AcquisitionRecord.from_mapping(value)

    def test_annotation_like_field_rejected(self) -> None:
        value = self.base(); value["target_label"] = "x"
        with self.assertRaises(ValueError):
            AcquisitionRecord.from_mapping(value)

    def test_annotation_schema_is_separate(self) -> None:
        self.assertTrue(set(acquisition_field_names()).isdisjoint({"target_label", "task_name"}))
        self.assertIn("target_label", annotation_field_names())

    def test_annotation_requires_string_target(self) -> None:
        with self.assertRaises(TypeError):
            AnnotationRecord.from_mapping({"sample_id": "s", "task_name": "t", "target_label": 1, "annotation_source": "human"})


if __name__ == "__main__":
    unittest.main()
