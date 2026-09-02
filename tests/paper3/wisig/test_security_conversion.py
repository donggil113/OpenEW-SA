from __future__ import annotations

import io
import os
import pickle
import stat
import tempfile
import unittest
import zipfile
from pathlib import Path

import numpy as np

from openew.paper3.wisig.archive import ArchiveSafetyError, extract_zip_once, inspect_zip, sha256_file, write_raw_manifest
from openew.paper3.wisig.converter import ConversionConfig, convert_manyrx, validate_compact_structure
from openew.paper3.wisig.ids import opaque_sample_id
from openew.paper3.wisig.restricted_loader import RestrictedPickleError, restricted_load
from openew.paper3.wisig.schema import AcquisitionRow, AnnotationRow, assert_model_visible_fields, assert_relation_fields
from openew.paper3.wisig.validation import compare_deterministic_passes, run_sample_level_qa

from .common import compact_fixture


class Evil:
    def __reduce__(self):
        return os.system, ("echo unsafe",)


class TestRestrictedLoader(unittest.TestCase):
    def test_numpy_container_allowed(self):
        value = {"x": np.arange(4, dtype=np.float32), "ids": ["001"]}
        loaded = restricted_load(io.BytesIO(pickle.dumps(value, protocol=4)))
        np.testing.assert_array_equal(loaded["x"], value["x"])

    def test_arbitrary_global_rejected(self):
        with self.assertRaises(RestrictedPickleError):
            restricted_load(io.BytesIO(pickle.dumps(Evil())))

    def test_trailing_bytes_rejected(self):
        with self.assertRaises(RestrictedPickleError):
            restricted_load(io.BytesIO(pickle.dumps({"x": 1}) + b"x"))

    def test_object_array_rejected(self):
        with self.assertRaises(RestrictedPickleError):
            restricted_load(io.BytesIO(pickle.dumps(np.asarray([object()], dtype=object))))

    def test_invalid_type_rejected(self):
        with self.assertRaises(TypeError):
            restricted_load(42)  # type: ignore[arg-type]

    def test_missing_path_raises(self):
        with self.assertRaises(FileNotFoundError):
            restricted_load("definitely_missing.pkl")


class TestArchiveSafety(unittest.TestCase):
    def _zip(self, name: str, mode: int = 0o100644) -> Path:
        root = Path(self.temp.name)
        path = root / "test.zip"
        with zipfile.ZipFile(path, "w") as archive:
            info = zipfile.ZipInfo(name)
            info.external_attr = mode << 16
            archive.writestr(info, b"payload")
        return path

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp.cleanup()

    def test_regular_member_passes(self):
        self.assertEqual(inspect_zip(self._zip("file.pkl"))["safety_status"], "PASS")

    def test_parent_traversal_rejected(self):
        with self.assertRaises(ArchiveSafetyError): inspect_zip(self._zip("../file"))

    def test_absolute_path_rejected(self):
        with self.assertRaises(ArchiveSafetyError): inspect_zip(self._zip("/file"))

    def test_symlink_rejected(self):
        with self.assertRaises(ArchiveSafetyError): inspect_zip(self._zip("link", stat.S_IFLNK | 0o777))

    def test_executable_rejected(self):
        with self.assertRaises(ArchiveSafetyError): inspect_zip(self._zip("run", stat.S_IFREG | 0o755))

    def test_extract_refuses_existing_destination(self):
        destination = Path(self.temp.name) / "existing"; destination.mkdir()
        with self.assertRaises(FileExistsError): extract_zip_once(self._zip("file.pkl"), destination)

    def test_extract_and_manifest(self):
        root = Path(self.temp.name); destination = root / "new"
        extract_zip_once(self._zip("file.pkl"), destination)
        report = write_raw_manifest(destination, root / "manifest.csv", root / "sums.txt")
        self.assertEqual(report["file_count"], 1)
        self.assertEqual(sha256_file(destination / "file.pkl"), sha256_file(destination / "file.pkl"))


class TestIdsAndSchema(unittest.TestCase):
    def test_opaque_id_deterministic(self):
        source = {"transmitter_index": 1, "receiver_index": 2}
        self.assertEqual(opaque_sample_id(source), opaque_sample_id(source))

    def test_opaque_id_changes_with_namespace(self):
        source = {"transmitter_index": 1}
        self.assertNotEqual(opaque_sample_id(source), opaque_sample_id(source, namespace="other"))

    def test_opaque_id_hides_source_token(self):
        value = opaque_sample_id({"transmitter_id": "target-01"})
        self.assertNotIn("target", value); self.assertEqual(len(value), 32)

    def test_leading_zero_receiver_preserved(self):
        row = AcquisitionRow("a", "001", "day", 0, 0, 1, 1, 1, "", "s", 0).validate()
        self.assertEqual(row.receiver_id, "001")

    def test_annotation_target_separate(self):
        row = AnnotationRow("a", "transmitter_fingerprinting", "01").to_dict()
        self.assertEqual(row["transmitter_id"], "01")

    def test_outer_whitespace_rejected(self):
        with self.assertRaises(ValueError): AcquisitionRow(" a", "001", "day", 0, 0, 1, 1, 1, "", "s", 0).validate()

    def test_negative_index_rejected(self):
        with self.assertRaises(ValueError): AcquisitionRow("a", "001", "day", -1, 0, 1, 1, 1, "", "s", 0).validate()

    def test_bad_task_rejected(self):
        with self.assertRaises(ValueError): AnnotationRow("a", "bad", "01").validate()

    def test_receiver_relation_allowed(self):
        assert_relation_fields({"receiver_id"})

    def test_day_relation_rejected(self):
        with self.assertRaises(ValueError): assert_relation_fields({"day_id"})

    def test_target_model_field_rejected(self):
        with self.assertRaises(ValueError): assert_model_visible_fields({"transmitter_id"})


class TestConverter(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source.pkl"
        self.source.write_bytes(pickle.dumps(compact_fixture(), protocol=4))
        self.config = ConversionConfig(shard_size=5, expected_signal_length=4)

    def tearDown(self): self.temp.cleanup()

    def test_structure_count(self):
        report = validate_compact_structure(compact_fixture(), self.config)
        self.assertEqual(report["packet_count"], 24)

    def test_structure_wrong_key_rejected(self):
        value = compact_fixture(); value["bad"] = 1
        with self.assertRaises(ValueError): validate_compact_structure(value, self.config)

    def test_structure_object_array_rejected(self):
        value = compact_fixture(); value["data"][0][0][0][0] = np.asarray([object()], dtype=object)  # type: ignore[index]
        with self.assertRaises(ValueError): validate_compact_structure(value, self.config)

    def test_conversion_separates_target(self):
        convert_manyrx(self.source, self.root / "a", source_archive_sha256="0" * 64, config=self.config)
        header = (self.root / "a/shards/shard_00000/acquisition_metadata.csv").read_text().splitlines()[0]
        self.assertNotIn("transmitter", header)

    def test_conversion_resume_returns_manifest(self):
        first = convert_manyrx(self.source, self.root / "a", source_archive_sha256="0" * 64, config=self.config)
        second = convert_manyrx(self.source, self.root / "a", source_archive_sha256="0" * 64, config=self.config)
        self.assertEqual(first, second)

    def test_two_pass_deterministic(self):
        convert_manyrx(self.source, self.root / "a", source_archive_sha256="0" * 64, config=self.config)
        convert_manyrx(self.source, self.root / "b", source_archive_sha256="0" * 64, config=self.config)
        self.assertTrue(compare_deterministic_passes(self.root / "a", self.root / "b")["byte_identical"])

    def test_full_qa_passes(self):
        convert_manyrx(self.source, self.root / "a", source_archive_sha256="0" * 64, config=self.config)
        self.assertEqual(run_sample_level_qa(self.root / "a")["status"], "PASS")

    def test_incompatible_resume_rejected(self):
        convert_manyrx(self.source, self.root / "a", source_archive_sha256="0" * 64, config=self.config)
        with self.assertRaises(RuntimeError):
            convert_manyrx(self.source, self.root / "a", source_archive_sha256="1" * 64, config=self.config)


def _make_forbidden_test(field: str):
    def test(self):
        with self.assertRaises(ValueError): assert_model_visible_fields({field})
    return test


for _field in ["target", "target_label", "label", "class", "transmitter_id", "source_path", "source_filename", "domain_id", "day_id"]:
    setattr(TestIdsAndSchema, f"test_forbidden_model_field_{_field}", _make_forbidden_test(_field))
