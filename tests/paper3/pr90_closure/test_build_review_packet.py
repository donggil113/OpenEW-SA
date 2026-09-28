"""Focused create-once and scope tests for the PR #90 review packet."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[3] / "scripts/paper3/pr90_closure/build_review_packet.py"
SPEC = importlib.util.spec_from_file_location("build_review_packet", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def command(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.fixture
def packet_inputs(tmp_path: Path) -> tuple[Path, Path, tuple[Path, ...], tuple[Path, ...]]:
    repo = tmp_path / "repo"
    repo.mkdir()
    command(repo, "init", "-q")
    doc = Path("docs/spec.md")
    code = Path("code/tool.py")
    for path, data in ((doc, "frozen spec\n"), (code, "VALUE = 1\n")):
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(data, encoding="utf-8")
    command(repo, "add", ".")
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=Test",
         "-c", "user.email=test@example.invalid", "commit", "-qm", "freeze"],
        check=True, capture_output=True,
    )
    external = tmp_path / "external"
    (external / "reports").mkdir(parents=True)
    report = Path("reports/report.json")
    pdf = Path("reports/main.pdf")
    (external / report).write_text('{"status":"PASS"}\n', encoding="utf-8")
    (external / pdf).write_bytes(b"%PDF-1.4\nsynthetic test fixture\n")
    return repo, external, (doc, code), (report, pdf)


def build(
    inputs: tuple[Path, Path, tuple[Path, ...], tuple[Path, ...]],
    *,
    output: Path | None = None,
    repo_paths: tuple[Path, ...] | None = None,
    external_paths: tuple[Path, ...] | None = None,
) -> dict:
    repo, external, docs, evidence = inputs
    return MODULE.build_packet(
        repo, external, output or external / "packet",
        selected_repo=docs if repo_paths is None else repo_paths,
        selected_external=evidence if external_paths is None else external_paths,
    )


def test_packet_copies_only_selected_files_and_records_head(packet_inputs):
    repo, external, _, _ = packet_inputs
    result = build(packet_inputs)
    packet = external / "packet"
    assert result["file_count"] == 4
    assert result["git_head"] == subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()
    assert result["rf_payload_included"] is False
    assert result["prediction_or_checkpoint_included"] is False
    assert result["new_target_evaluation"] is False
    assert (packet / "files/repository/docs/spec.md").read_text() == "frozen spec\n"
    assert (packet / "files/external/reports/main.pdf").read_bytes().startswith(b"%PDF")
    manifest_bytes = (packet / "manifest.json").read_bytes()
    assert hashlib.sha256(manifest_bytes).hexdigest() in (
        packet / "MANIFEST_SHA256.txt"
    ).read_text()
    assert len((packet / "SHA256SUMS.txt").read_text().splitlines()) == 4
    assert json.loads(manifest_bytes)["files"][0]["origin"] in ("repository", "external")


def test_existing_output_is_never_overwritten(packet_inputs):
    _, external, _, _ = packet_inputs
    output = external / "packet"
    output.mkdir()
    sentinel = output / "keep"
    sentinel.write_text("do not modify", encoding="utf-8")
    with pytest.raises(FileExistsError):
        build(packet_inputs)
    assert sentinel.read_text(encoding="utf-8") == "do not modify"


def test_dirty_repository_rejected_before_output_creation(packet_inputs):
    repo, external, _, _ = packet_inputs
    (repo / "docs/spec.md").write_text("changed\n", encoding="utf-8")
    with pytest.raises(ValueError, match="clean committed"):
        build(packet_inputs)
    assert not (external / "packet").exists()


def test_output_must_be_inside_external_root(packet_inputs, tmp_path):
    with pytest.raises(ValueError, match="external-root"):
        build(packet_inputs, output=tmp_path / "outside")


def test_forbidden_prediction_source_rejected(packet_inputs):
    repo, external, docs, evidence = packet_inputs
    (external / "predictions").mkdir()
    (external / "predictions/secret.csv").write_text("target", encoding="utf-8")
    with pytest.raises(ValueError, match="forbidden"):
        build(packet_inputs, external_paths=evidence + (Path("predictions/secret.csv"),))
    assert not (external / "packet").exists()


def test_large_non_pdf_source_rejected(packet_inputs):
    _, external, _, evidence = packet_inputs
    path = Path("reports/huge.csv")
    (external / path).write_bytes(b"x" * (MODULE.TEXT_LIMIT + 1))
    with pytest.raises(ValueError, match="size limit"):
        build(packet_inputs, external_paths=evidence + (path,))
    assert not (external / "packet").exists()


def test_missing_external_evidence_rejected(packet_inputs):
    _, external, _, evidence = packet_inputs
    with pytest.raises(ValueError, match="missing"):
        build(packet_inputs, external_paths=evidence + (Path("reports/missing.json"),))
    assert not (external / "packet").exists()


def test_symlink_source_rejected(packet_inputs):
    _, external, _, evidence = packet_inputs
    target = Path("reports/linked.csv")
    (external / target).symlink_to("report.json")
    with pytest.raises(ValueError, match="linked"):
        build(packet_inputs, external_paths=evidence + (target,))
    assert not (external / "packet").exists()
