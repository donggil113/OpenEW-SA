"""Submission-title rendering must not touch PR90 frozen figures or data."""

from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
MANUSCRIPT = ROOT / "papers/paper3_reviewer_remediation/manuscript"
EVIDENCE = ROOT / "papers/paper3_reviewer_remediation/evidence"
RENDERER = ROOT / "scripts/paper3/reviewer_remediation/render_release_assets.py"


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    return env


def _pdf_text(path: Path) -> str:
    return subprocess.run(
        ["pdftotext", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def test_presentation_figures_are_separate_and_numeric_inputs_unchanged(tmp_path):
    if shutil.which("pdftotext") is None:
        pytest.skip("Poppler pdftotext is required for the figure-title check")

    original_manifest = (MANUSCRIPT / "figure_manifest.json").read_bytes()
    frozen = json.loads(original_manifest)
    evidence_manifest_bytes = (EVIDENCE / "source_manifest.json").read_bytes()
    evidence_manifest = json.loads(evidence_manifest_bytes)
    plot_input_hashes = evidence_manifest["exports"]
    assert all(file_sha(EVIDENCE / name) == digest for name, digest in plot_input_hashes.items())
    frozen_hashes = {
        name: file_sha(MANUSCRIPT / "figures" / f"{name}.pdf")
        for name in frozen["figures"]
    }
    staged = tmp_path / "presentation"
    png = tmp_path / "png"
    subprocess.run(
        [
            sys.executable,
            str(RENDERER),
            "--repository", str(ROOT),
            "--presentation-output", str(staged),
            "--png-output", str(png),
        ],
        cwd=ROOT,
        env=_source_env(),
        check=True,
        capture_output=True,
        text=True,
    )

    assert (MANUSCRIPT / "figure_manifest.json").read_bytes() == original_manifest
    assert (EVIDENCE / "source_manifest.json").read_bytes() == evidence_manifest_bytes
    assert all(file_sha(EVIDENCE / name) == digest for name, digest in plot_input_hashes.items())
    assert all(
        file_sha(MANUSCRIPT / "figures" / f"{name}.pdf") == digest
        for name, digest in frozen_hashes.items()
    )
    staged_manifest = json.loads((staged / "figure_manifest.json").read_text())
    assert staged_manifest["analysis_sha256"] == frozen["analysis_sha256"]
    assert staged_manifest["figures"] == frozen["figures"]
    assert staged_manifest["render_variant"] == "PRESENTATION_TITLES_ONLY"
    assert staged_manifest["frozen_plot_input_manifest_sha256"] == hashlib.sha256(
        evidence_manifest_bytes
    ).hexdigest()
    assert (staged / "numbers.tex").read_bytes() == (MANUSCRIPT / "numbers.tex").read_bytes()
    assert all(
        (staged / "tables" / table.name).read_bytes() == table.read_bytes()
        for table in (MANUSCRIPT / "tables").glob("*.tex")
        if (staged / "tables" / table.name).exists()
    )

    for name in frozen["figures"]:
        rendered = staged / "figures" / f"{name}.pdf"
        assert rendered.is_file()
        assert file_sha(rendered) == staged_manifest["pdf_sha256"][name]
        assert "Post-hoc addendum; frozen references retained" not in _pdf_text(rendered)
    assert "Post-hoc probability quality" not in _pdf_text(
        staged / "figures/probability_quality.pdf"
    )
    assert "Post-hoc timing replay" not in _pdf_text(staged / "figures/compute.pdf")
    assert "Post-hoc reliability" not in _pdf_text(
        staged / "figures/reliability_raw_1.pdf"
    )
    assert "receiver_delta_summary" not in staged_manifest["figures"]


def test_presentation_renderer_refuses_existing_output(tmp_path):
    staged = tmp_path / "existing"
    staged.mkdir()
    png = tmp_path / "png"
    result = subprocess.run(
        [
            sys.executable, str(RENDERER),
            "--repository", str(ROOT),
            "--presentation-output", str(staged),
            "--png-output", str(png),
        ],
        cwd=ROOT,
        env=_source_env(),
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "presentation output must be a new directory" in result.stderr
    assert list(staged.iterdir()) == []
