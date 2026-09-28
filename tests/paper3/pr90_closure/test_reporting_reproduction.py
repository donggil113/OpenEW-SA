"""Versioned PR90 reporting snapshot safety checks, without RF payloads."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from openew.paper3.pr90_closure.report_repro import (
    audit_pdf, registry, sha256, validate_registry,
)


def test_reporting_registry_detects_modified_source(tmp_path: Path) -> None:
    source = tmp_path / "manuscript.tex"
    source.write_text("frozen")
    expected = registry(tmp_path, [Path("manuscript.tex")])
    validate_registry(tmp_path, expected)
    source.write_text("post-hoc edit")
    with pytest.raises(ValueError, match="source changed"):
        validate_registry(tmp_path, expected)


@pytest.mark.parametrize("name", ["/etc/passwd", "../unrelated", ""])
def test_reporting_registry_rejects_unsafe_or_empty_paths(tmp_path: Path, name: str) -> None:
    with pytest.raises(ValueError):
        validate_registry(tmp_path, {name: "0" * 64})


def test_pdf_audit_requires_actual_table_page(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pdf = tmp_path / "main.pdf"
    pdf.write_bytes(b"mock")
    log = tmp_path / "main.log"
    log.write_text("")
    def command(args: list[str], **_: object) -> str:
        if args[0] == "pdfinfo":
            return "Pages: 2\n"
        if args[0] == "pdffonts":
            return "name type encoding emb sub uni object ID\n---- ---- ---- --- --- --- ------ --\nMock Type1 Custom yes yes yes 1 0\n"
        if args[0] == "pdftotext":
            return "No table here"
        raise AssertionError(args)
    monkeypatch.setattr("openew.paper3.pr90_closure.report_repro.subprocess.check_output", command)
    with pytest.raises(ValueError, match="composition table missing"):
        audit_pdf(pdf, log, composition=True)


def test_pdf_audit_records_table_page(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pdf = tmp_path / "main.pdf"
    pdf.write_bytes(b"mock")
    log = tmp_path / "main.log"
    log.write_text("")
    def command(args: list[str], **_: object) -> str:
        if args[0] == "pdfinfo":
            return "Pages: 2\n"
        if args[0] == "pdffonts":
            return "name type encoding emb sub uni object ID\n---- ---- ---- --- --- --- ------ --\nMock Type1 Custom yes yes yes 1 0\n"
        if args[0] == "pdftotext":
            return "POST-HOC ORACLE COMPOSITION DIAGNOSTIC" if args[2] == "2" else "No table"
        raise AssertionError(args)
    monkeypatch.setattr("openew.paper3.pr90_closure.report_repro.subprocess.check_output", command)
    assert audit_pdf(pdf, log, composition=True)["composition_table_pages"] == [2]
