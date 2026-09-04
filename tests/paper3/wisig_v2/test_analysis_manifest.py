from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from openew.paper3.wisig_v2.analysis_manifest import write_analysis_manifest


class AnalysisManifestTests(unittest.TestCase):
    def test_manifest_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / "a.txt").write_text("a", encoding="utf-8"); (root / "nested").mkdir(); (root / "nested/b.txt").write_text("b", encoding="utf-8")
            first = write_analysis_manifest(root, root / "manifest.json"); second = write_analysis_manifest(root, root / "manifest.json")
            self.assertEqual(first, second); self.assertEqual(first["file_count"], 2)

    def test_manifest_uses_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / "a.txt").write_text("a", encoding="utf-8")
            result = write_analysis_manifest(root, root / "manifest.json")
            self.assertEqual(result["files"][0]["relative_path"], "a.txt")

    def test_empty_root_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                write_analysis_manifest(directory, Path(directory) / "manifest.json")

    def test_missing_root_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                write_analysis_manifest(Path(directory) / "missing", Path(directory) / "manifest.json")


if __name__ == "__main__":
    unittest.main()
