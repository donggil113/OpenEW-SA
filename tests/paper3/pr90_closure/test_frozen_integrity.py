"""Small fail-closed tests for the read-only PR90 checksum recheck."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path


def _script():
    path = Path(__file__).resolve().parents[3] / "scripts/paper3/pr90_closure/verify_frozen_integrity.py"
    spec = importlib.util.spec_from_file_location("verify_frozen_integrity", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sha256_reads_actual_bytes(tmp_path):
    payload = tmp_path / "record.bin"
    payload.write_bytes(b"\x00WiSig\xff")
    assert _script().sha256(payload) == hashlib.sha256(payload.read_bytes()).hexdigest()


def test_verify_map_passes_only_exact_content(tmp_path):
    first = tmp_path / "a" / "run.json"
    first.parent.mkdir()
    first.write_bytes(b"{\"status\":\"COMPLETE\"}")
    relative = "a/run.json"
    expected = hashlib.sha256(first.read_bytes()).hexdigest()
    assert _script().verify_map(tmp_path, {relative: expected}) == (1, [])


def test_verify_map_flags_missing_and_changed_content(tmp_path):
    first = tmp_path / "a" / "run.json"
    first.parent.mkdir()
    first.write_bytes(b"changed")
    relative = "a/run.json"
    expected = hashlib.sha256(b"original").hexdigest()
    count, errors = _script().verify_map(tmp_path, {relative: expected, "b/missing.npz": expected})
    assert count == 2
    assert set(errors) == {"sha256:a/run.json", "missing:b/missing.npz"}
