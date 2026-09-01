from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from openew.paper3.metadata.enums import Confidence, ReadinessLevel, TemporalVerdict
from openew.paper3.metadata.provenance import (
    FieldProvenance,
    ProvenanceSidecar,
    read_sidecar,
    write_sidecar,
)
from openew.paper3.metadata.readiness import RelationReadiness, build_readiness_scorecard
from openew.paper3.metadata.schema import AnnotationRecord
from openew.paper3.metadata.serialization import (
    read_acquisition_records,
    read_annotation_records,
    write_acquisition_records,
    write_annotation_records,
)
from openew.paper3.metadata.validation import validate_records

from common import changed, record, records


class ValidationReadinessTests(unittest.TestCase):
    def codes(self, rows: list[object], **kwargs: object) -> set[str]:
        return {issue.code for issue in validate_records(rows, **kwargs).issues}

    def test_duplicate_sample_id(self) -> None:
        rows = records(); rows[1] = changed(rows[1], sample_id=rows[0].sample_id)
        self.assertIn("DUPLICATE_SAMPLE_ID", self.codes(rows))

    def test_duplicate_session_capture_index(self) -> None:
        rows = records(); rows[1] = changed(rows[1], within_capture_index=rows[0].within_capture_index)
        self.assertIn("DUPLICATE_SESSION_CAPTURE_INDEX", self.codes(rows))

    def test_single_item_session_warning(self) -> None:
        self.assertIn("SINGLE_ROW_SESSION", self.codes([record()]))

    def test_over_large_session_warning(self) -> None:
        self.assertIn("OVER_LARGE_SESSION", self.codes(records(4), max_session_size=1))

    def test_missing_receiver_warning(self) -> None:
        rows = [changed(record(0), receiver_id=None, site_id=None)]
        self.assertIn("MISSING_RECEIVER_ID", self.codes(rows))

    def test_duplicate_timestamp_warning(self) -> None:
        rows = [record(0), changed(record(1), timestamp_utc=record(0).timestamp_utc)]
        self.assertIn("DUPLICATE_TIMESTAMP", self.codes(rows))

    def test_negative_gap_error(self) -> None:
        rows = [record(0), changed(record(1), timestamp_utc="2025-01-01T00:00:00Z")]
        self.assertIn("NEGATIVE_TIME_GAP", self.codes(rows))

    def test_target_bearing_source_id_rejected(self) -> None:
        self.assertIn("TARGET_BEARING_SOURCE_FILE_ID", self.codes([changed(record(), source_file_id="reactive_jammer.bin")]))

    def test_missing_provenance_warning(self) -> None:
        self.assertIn("PROVENANCE_SIDECAR_MISSING", self.codes([record()]))

    def test_incomplete_provenance_error(self) -> None:
        sidecar = ProvenanceSidecar("1", "test", "1", {}, (), ())
        self.assertIn("FIELD_PROVENANCE_INCOMPLETE", self.codes([record()], provenance=sidecar))

    def test_provenance_roundtrip(self) -> None:
        item = FieldProvenance("sample_id", "generated", "fixture", "1", "direct", ("test",), Confidence.VERIFIED)
        sidecar = ProvenanceSidecar("1", "test", "1", {"fixture": "abc"}, (item,), ())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sidecar.json"; write_sidecar(path, sidecar)
            self.assertEqual(read_sidecar(path), sidecar)

    def test_csv_string_preservation(self) -> None:
        row = changed(record(), sample_id="0000123", receiver_id="0007")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "metadata.csv"; write_acquisition_records(path, [row])
            recovered = read_acquisition_records(path)[0]
            self.assertEqual((recovered.sample_id, recovered.receiver_id), ("0000123", "0007"))

    def test_json_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "metadata.json"; write_acquisition_records(path, records())
            self.assertEqual(read_acquisition_records(path), records())

    def test_annotation_load_does_not_mutate_acquisition(self) -> None:
        acquisition = records(); before = tuple(row.to_mapping() for row in acquisition)
        annotations = [AnnotationRecord(row.sample_id, "task", str(i % 2), "fixture") for i, row in enumerate(acquisition)]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "annotations.csv"; write_annotation_records(path, annotations)
            self.assertEqual(read_annotation_records(path), annotations)
        self.assertEqual(tuple(row.to_mapping() for row in acquisition), before)

    def test_independent_only_scorecard(self) -> None:
        score = build_readiness_scorecard([], temporal_verdict=TemporalVerdict.NO_TEMPORAL_METADATA, mixed_target_episode_fraction=0)
        self.assertIs(score.highest_level, ReadinessLevel.INDEPENDENT_SAMPLE_ONLY)

    def test_static_relational_scorecard(self) -> None:
        relation = RelationReadiness("receiver_id", 1, 1, True, True)
        score = build_readiness_scorecard([relation], temporal_verdict=TemporalVerdict.NO_TEMPORAL_METADATA, mixed_target_episode_fraction=0)
        self.assertIs(score.highest_level, ReadinessLevel.STATIC_RELATIONAL)

    def test_static_hypergraph_scorecard(self) -> None:
        relations = [RelationReadiness(name, 1, 1, True, True) for name in ("receiver_id", "site_id")]
        score = build_readiness_scorecard(relations, temporal_verdict=TemporalVerdict.NO_TEMPORAL_METADATA, mixed_target_episode_fraction=0)
        self.assertIs(score.highest_level, ReadinessLevel.STATIC_HYPERGRAPH)

    def test_temporal_scorecard(self) -> None:
        relation = RelationReadiness("receiver_id", 1, 1, True, True)
        score = build_readiness_scorecard([relation], temporal_verdict=TemporalVerdict.VALID_TEMPORAL_CONTEXT, mixed_target_episode_fraction=1)
        self.assertIs(score.highest_level, ReadinessLevel.TEMPORAL_RELATIONAL)

    def test_dynamic_scorecard(self) -> None:
        relations = [RelationReadiness(name, 1, 1, True, True) for name in ("receiver_id", "site_id")]
        score = build_readiness_scorecard(relations, temporal_verdict=TemporalVerdict.VALID_TEMPORAL_CONTEXT, mixed_target_episode_fraction=1)
        self.assertIs(score.highest_level, ReadinessLevel.DYNAMIC_HYPERGRAPH)

    def test_unsafe_relation_not_counted(self) -> None:
        relation = RelationReadiness("receiver_id", 1, 1, False, True)
        score = build_readiness_scorecard([relation], temporal_verdict=TemporalVerdict.NO_TEMPORAL_METADATA, mixed_target_episode_fraction=0)
        self.assertEqual(score.relation_count, 0)


if __name__ == "__main__":
    unittest.main()
