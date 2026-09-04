from __future__ import annotations

import unittest

from openew.paper3.wisig_v2.integrity import FROZEN_GIT_PATHS, only_v2_paths_changed, verify_tree_manifest


class IntegrityTests(unittest.TestCase):
    def test_v2_paths_are_allowed(self) -> None:
        self.assertTrue(
            only_v2_paths_changed(
                [
                    "papers/paper3_wisig_methods_remediation/report.md",
                    "configs/paper3/wisig_v2/config.yaml",
                    "scripts/paper3/wisig_v2/run.py",
                    "src/openew/paper3/wisig_v2/analysis.py",
                    "tests/paper3/wisig_v2/test_analysis.py",
                ]
            )
        )

    def test_tree_manifest_detects_changed_file(self) -> None:
        import hashlib
        import json
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "tree"; root.mkdir()
            artifact = root / "result.csv"; artifact.write_bytes(b"a,b\n1,2\n")
            manifest = Path(directory) / "manifest.json"
            manifest.write_text(json.dumps({"files": [{"relative_path": "result.csv", "size_bytes": artifact.stat().st_size, "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest()}]}), encoding="utf-8")
            self.assertEqual(verify_tree_manifest(root, manifest)["status"], "PASS")
            artifact.write_bytes(b"a,b\n1,3\n")
            self.assertEqual(verify_tree_manifest(root, manifest)["status"], "FAIL")

    def test_tree_manifest_detects_extra_file(self) -> None:
        import hashlib
        import json
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "tree"; root.mkdir()
            artifact = root / "result.csv"; artifact.write_bytes(b"x\n")
            manifest = Path(directory) / "manifest.json"
            manifest.write_text(json.dumps({"files": [{"relative_path": "result.csv", "size_bytes": 2, "sha256": hashlib.sha256(b"x\n").hexdigest()}]}), encoding="utf-8")
            (root / "unexpected.txt").write_text("unexpected", encoding="utf-8")
            result = verify_tree_manifest(root, manifest)
            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["unexpected_paths"], ["unexpected.txt"])

    def test_empty_change_set_is_safe(self) -> None:
        self.assertTrue(only_v2_paths_changed([]))

    def test_prior_paper_path_is_rejected(self) -> None:
        self.assertFalse(only_v2_paths_changed(["papers/paper2_ood_rf_signal_recognition/main.tex"]))

    def test_near_prefix_is_rejected(self) -> None:
        self.assertFalse(only_v2_paths_changed(["src/openew/paper3/wisig_v20/not_allowed.py"]))

    def test_all_prior_config_trees_are_frozen(self) -> None:
        for path in ("configs/paper3/static_relational", "configs/paper3/metadata", "configs/paper3/dataset_qualification", "configs/paper3/wisig"):
            self.assertIn(path, FROZEN_GIT_PATHS)


if __name__ == "__main__":
    unittest.main()
