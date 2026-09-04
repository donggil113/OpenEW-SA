from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from openew.paper3.wisig_v2.equalized import validate_equalized_manifests


def write_manifest(root: Path, *, status: str = "COMPLETE", index: int = 1, count: int = 10, source: str = "s", archive: str = "a") -> None:
    root.mkdir()
    (root / "dataset_manifest.json").write_text(
        json.dumps({"status": status, "config": {"equalized_index": index}, "sample_count": count, "source_pickle_sha256": source, "source_archive_sha256": archive}),
        encoding="utf-8",
    )


class EqualizedGateTests(unittest.TestCase):
    def test_matching_official_equalized_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); left = root / "a"; right = root / "b"
            write_manifest(left); write_manifest(right)
            self.assertEqual(validate_equalized_manifests(left, right)["status"], "PASS")

    def test_raw_index_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); left = root / "a"; right = root / "b"
            write_manifest(left, index=0); write_manifest(right, index=0)
            self.assertEqual(validate_equalized_manifests(left, right)["status"], "FAIL")

    def test_incomplete_pass_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); left = root / "a"; right = root / "b"
            write_manifest(left); write_manifest(right, status="RUNNING")
            self.assertEqual(validate_equalized_manifests(left, right)["status"], "FAIL")

    def test_mismatched_sample_count_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); left = root / "a"; right = root / "b"
            write_manifest(left, count=10); write_manifest(right, count=11)
            self.assertEqual(validate_equalized_manifests(left, right)["status"], "FAIL")

    def test_mismatched_source_hash_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); left = root / "a"; right = root / "b"
            write_manifest(left, source="one"); write_manifest(right, source="two")
            self.assertEqual(validate_equalized_manifests(left, right)["status"], "FAIL")

    def test_mismatched_archive_hash_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); left = root / "a"; right = root / "b"
            write_manifest(left, archive="one"); write_manifest(right, archive="two")
            self.assertEqual(validate_equalized_manifests(left, right)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
