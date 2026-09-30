"""The submission branch may change presentation, never frozen science."""

from pathlib import Path
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/paper3/submission_finalization/scientific_freeze.py"
SPEC = importlib.util.spec_from_file_location("scientific_freeze", SCRIPT)
assert SPEC and SPEC.loader
freeze = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(freeze)


def test_annotated_tag_peels_to_frozen_commit():
    assert freeze.freeze_commit(ROOT) == freeze.EXPECTED_COMMIT
    assert freeze.git(ROOT, "rev-parse", freeze.TAG).decode().strip() != freeze.EXPECTED_COMMIT


def test_manifest_matches_tag_and_worktree():
    result = freeze.verify(ROOT, ROOT / freeze.MANIFEST)
    assert result["status"] == "PASS"
    assert result["scientific_files"] >= 60


def test_manifest_covers_required_science():
    entries = json.loads((ROOT / freeze.MANIFEST).read_text())["files"]
    assert freeze.SCIENTIFIC_EXACT <= entries.keys()
    assert any("/manuscript/tables/" in path for path in entries)
    assert any("/manuscript/figures/" in path for path in entries)
    assert any("/evidence/" in path for path in entries)


def test_metadata_include_is_outside_scientific_frozen_paths():
    assert not freeze.is_scientific(
        "papers/paper3_reviewer_remediation/manuscript/shared/submission_metadata.tex"
    )


def test_changed_scientific_byte_is_detected(tmp_path):
    relative = "papers/paper3_reviewer_remediation/manuscript/numbers.tex"
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_bytes(b"tampered")
    assert freeze.check_entries(tmp_path, {relative: {"sha256": freeze.sha256(b"frozen"), "bytes": 6}}) == [
        f"scientific drift: {relative}"
    ]


def test_missing_scientific_file_is_detected(tmp_path):
    relative = "papers/paper3_reviewer_remediation/manuscript/numbers.tex"
    assert freeze.check_entries(tmp_path, {relative: {"sha256": "0" * 64, "bytes": 0}}) == [
        f"missing: {relative}"
    ]


def test_new_scientific_table_is_detected(tmp_path):
    relative = "papers/paper3_reviewer_remediation/manuscript/tables/extra.tex"
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_text("new scientific result")
    assert freeze.check_entries(tmp_path, {}) == [f"unfrozen scientific file: {relative}"]
