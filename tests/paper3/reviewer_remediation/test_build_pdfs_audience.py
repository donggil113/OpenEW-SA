"""Submission identity is staged, while the canonical scientific source stays shared."""

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/paper3/reviewer_remediation/build_pdfs.py"
MANUSCRIPT = ROOT / "papers/paper3_reviewer_remediation/manuscript"
EVIDENCE_MANIFEST = ROOT / "papers/paper3_reviewer_remediation/evidence/source_manifest.json"
spec = importlib.util.spec_from_file_location("build_pdfs_audience", SCRIPT)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_presentation_manifest(figures: Path) -> None:
    frozen = json.loads((MANUSCRIPT / "figure_manifest.json").read_text())
    frozen["pdf_sha256"] = {
        name.removesuffix(".pdf"): sha(figures / name)
        for name in builder.SUBMISSION_FIGURES
    }
    frozen["render_variant"] = "PRESENTATION_TITLES_ONLY"
    frozen["frozen_plot_input_manifest_sha256"] = sha(EVIDENCE_MANIFEST)
    (figures.parent / "figure_manifest.json").write_text(json.dumps(frozen))


def test_submission_staging_only_changes_identity_and_presentation(tmp_path):
    stage = tmp_path / "source"
    shutil.copytree(MANUSCRIPT, stage)
    original = {
        name: sha(MANUSCRIPT / name)
        for name in (
            "main_tmlcn.tex",
            "main_access.tex",
            "supplementary.tex",
            "shared/preamble.tex",
            "shared/body.tex",
            "tables/composition_oracle_journal.tex",
            "figures/receiver_delta_summary.pdf",
        )
    }
    figures = tmp_path / "presentation_figures"
    figures.mkdir()
    for name in builder.SUBMISSION_FIGURES:
        (figures / name).write_bytes(("presentation:" + name).encode())
    write_presentation_manifest(figures)

    builder.prepare_submission_stage(stage, figures, EVIDENCE_MANIFEST)

    for name, digest in original.items():
        assert sha(MANUSCRIPT / name) == digest
    for name in ("tables/composition_oracle_journal.tex",):
        assert sha(stage / name) == original[name]
    source_body = (MANUSCRIPT / "shared/body.tex").read_text()
    staged_body = (stage / "shared/body.tex").read_text()
    assert staged_body.split(r"\SubmissionDataCodeAvailability")[0] == source_body.split(
        r"\subsection{Data and Code Availability}"
    )[0]
    assert staged_body.split(r"\section{Conclusion}")[1].split(
        r"\section*{Acknowledgments}"
    )[0] == source_body.split(r"\section{Conclusion}")[1].split(
        r"\section*{Acknowledgments}"
    )[0]
    assert r"\SubmissionAIDisclosure" in staged_body
    assert sha(stage / "figures/receiver_delta_summary.pdf") == original[
        "figures/receiver_delta_summary.pdf"
    ]
    for name in builder.SUBMISSION_FIGURES:
        assert (stage / "figures" / name).read_bytes() == (
            "presentation:" + name
        ).encode()
    assert json.loads((stage / "figure_manifest.json").read_text())[
        "pdf_sha256"
    ] == json.loads((figures.parent / "figure_manifest.json").read_text())["pdf_sha256"]
    for name in ("main_tmlcn.tex", "main_access.tex", "supplementary.tex"):
        text = (stage / name).read_text()
        assert "OpenEW-SA Internal Review" not in text
        assert "Internal-review" not in text
    tmlcn = (stage / "main_tmlcn.tex").read_text()
    access = (stage / "main_access.tex").read_text()
    assert r"\author{\SubmissionAuthors}" in tmlcn
    assert r"\address{\SubmissionAffiliations}" in access
    assert r"\corresp{\SubmissionCorrespondingAuthor}" in access
    metadata = (stage / "shared/submission_metadata.tex").read_text()
    assert not any(token in metadata for token in builder.METADATA_SENTINELS)
    assert r"\newcommand{\SubmissionAuthors}{}" in metadata
    assert "HUMAN_REQUIRED" in (MANUSCRIPT / "shared/submission_metadata.tex").read_text()
    assert r"\history{Internal-review draft only." not in access
    assert r"\tfootnote{\draftnotice}" not in access
    assert "Internal Review" not in access
    assert r"\section*{Author biographies}" not in access
    supplement = (stage / "supplementary.tex").read_text()
    assert "PR \\#" not in supplement
    assert "closure" not in supplement.casefold()
    assert "post-hoc relative to the earlier" in supplement
    assert not (stage / "shared/access_draft_layout.tex").exists()
    assert (stage / "shared/access_submission_layout.tex").exists()
    assert "OpenEW-SA Internal Review" in (MANUSCRIPT / "main_tmlcn.tex").read_text()


def test_submission_staging_rejects_incomplete_figure_set(tmp_path):
    stage = tmp_path / "source"
    shutil.copytree(MANUSCRIPT, stage)
    figures = tmp_path / "presentation_figures"
    figures.mkdir()
    with pytest.raises(RuntimeError, match="figure set differs"):
        builder.prepare_submission_stage(stage, figures, EVIDENCE_MANIFEST)


def test_submission_staging_rejects_identity_drift(tmp_path):
    stage = tmp_path / "source"
    shutil.copytree(MANUSCRIPT, stage)
    figures = tmp_path / "presentation_figures"
    figures.mkdir()
    for name in builder.SUBMISSION_FIGURES:
        (figures / name).write_bytes(b"%PDF-1.4\n")
    write_presentation_manifest(figures)
    tmlcn = stage / "main_tmlcn.tex"
    tmlcn.write_text(tmlcn.read_text().replace("OpenEW-SA Internal Review", "Unexpected label"))
    with pytest.raises(RuntimeError, match="expected one identity marker"):
        builder.prepare_submission_stage(stage, figures, EVIDENCE_MANIFEST)


def test_submission_staging_rejects_figure_hash_drift(tmp_path):
    stage = tmp_path / "source"
    shutil.copytree(MANUSCRIPT, stage)
    figures = tmp_path / "presentation_figures"
    figures.mkdir()
    for name in builder.SUBMISSION_FIGURES:
        (figures / name).write_bytes(b"%PDF-1.4\n")
    write_presentation_manifest(figures)
    (figures / "benchmark.pdf").write_bytes(b"changed")
    with pytest.raises(RuntimeError, match="figure hash mismatch"):
        builder.prepare_submission_stage(stage, figures, EVIDENCE_MANIFEST)


def test_submission_staging_rejects_plot_input_manifest_drift(tmp_path):
    stage = tmp_path / "source"
    shutil.copytree(MANUSCRIPT, stage)
    figures = tmp_path / "presentation_figures"
    figures.mkdir()
    for name in builder.SUBMISSION_FIGURES:
        (figures / name).write_bytes(b"%PDF-1.4\n")
    write_presentation_manifest(figures)
    path = figures.parent / "figure_manifest.json"
    manifest = json.loads(path.read_text())
    manifest["frozen_plot_input_manifest_sha256"] = "0" * 64
    path.write_text(json.dumps(manifest))
    with pytest.raises(RuntimeError, match="frozen evidence"):
        builder.prepare_submission_stage(stage, figures, EVIDENCE_MANIFEST)


def test_build_requires_submission_figures_before_creating_output(tmp_path):
    from argparse import Namespace

    output = tmp_path / "build"
    with pytest.raises(RuntimeError, match="required"):
        builder.build(
            Namespace(
                repository=ROOT,
                output=output,
                access_template=None,
                audience="submission",
                submission_figures=None,
            )
        )
    assert not output.exists()


def test_access_target_requires_official_template_before_creating_output(tmp_path):
    from argparse import Namespace

    output = tmp_path / "build"
    with pytest.raises(RuntimeError, match="access-template is required"):
        builder.build(
            Namespace(
                repository=ROOT,
                output=output,
                access_template=None,
                audience="internal",
                submission_figures=None,
                target="access",
            )
        )
    assert not output.exists()


def test_submission_stage_keeps_human_values_when_supplied(tmp_path):
    stage = tmp_path / "source"
    shutil.copytree(MANUSCRIPT, stage)
    metadata_path = stage / "shared/submission_metadata.tex"
    metadata_path.write_text(
        metadata_path.read_text().replace("AUTHOR_1", "Verified Human Name")
    )
    figures = tmp_path / "presentation_figures"
    figures.mkdir()
    for name in builder.SUBMISSION_FIGURES:
        (figures / name).write_bytes(("presentation:" + name).encode())
    write_presentation_manifest(figures)
    pending = builder.prepare_submission_stage(stage, figures, EVIDENCE_MANIFEST)
    assert "AUTHOR_1" not in pending
    assert "FUNDING_STATEMENT_HUMAN_REQUIRED" in pending
    assert r"\newcommand{\SubmissionAuthors}{Verified Human Name}" in metadata_path.read_text()
    assert "HUMAN_REQUIRED" not in metadata_path.read_text()


@pytest.mark.skipif(
    shutil.which("latexmk") is None or shutil.which("pdftotext") is None,
    reason="LaTeX or Poppler is unavailable",
)
def test_internal_and_submission_pdf_identity(tmp_path):
    figures = tmp_path / "presentation_figures"
    figures.mkdir()
    for name in builder.SUBMISSION_FIGURES:
        shutil.copyfile(MANUSCRIPT / "figures" / name, figures / name)
    write_presentation_manifest(figures)
    internal = tmp_path / "internal"
    submission = tmp_path / "submission"
    common = [sys.executable, str(SCRIPT), "--repository", str(ROOT)]
    subprocess.run(common + ["--output", str(internal), "--audience", "internal"], check=True)
    subprocess.run(
        common
        + [
            "--output",
            str(submission),
            "--audience",
            "submission",
            "--submission-figures",
            str(figures),
        ],
        check=True,
    )
    for name in ("main_tmlcn", "supplementary"):
        internal_text = subprocess.check_output(
            ["pdftotext", str(internal / f"{name}.pdf"), "-"], text=True
        )
        submission_text = subprocess.check_output(
            ["pdftotext", str(submission / f"{name}.pdf"), "-"], text=True
        )
        assert "OpenEW-SA Internal Review" in internal_text
        assert "OpenEW-SA Internal Review" not in submission_text
        assert "require human confirmation" not in submission_text.casefold()
        assert "draft disclosure" not in submission_text.casefold()
        assert "Data and Code Availability" not in submission_text or name == "main_tmlcn"
