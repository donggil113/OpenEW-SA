#!/usr/bin/env python3
"""Create a compact, immutable-by-convention PR #90 closure review packet.

Run only after committing the closure code and reports. The packet contains
selected tracked text/code, small external audit summaries, and the three
final reporting PDFs. It never contains RF payloads, checkpoints, blind
predictions, or a new target evaluation. An existing output path is an error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
from datetime import datetime, timezone
from pathlib import Path


CLOSURE = Path("papers/paper3_pr90_closure")
MANUSCRIPT = Path("papers/paper3_reviewer_remediation/manuscript")
REVIEW_DOCS = (
    "pr90_issue_closure_matrix.md",
    "composition_source_audit.md",
    "sar_original_execution_audit.md",
    "sar_state_machine_fidelity.md",
    "sar_source_only_diagnostic.md",
    "sar_limited_rerun_plan.md",
    "shot_im_disposition.md",
    "manuscript_change_summary.md",
    "reproducibility_levels.md",
    "closure_handoff.md",
    "human_decisions.md",
    "ai_disclosure_evidence.md",
    "pdf_technical_audit.md",
    "statistical_wording_audit.md",
    "support_budget_interpretation.md",
    "reporting_snapshot_manifest.json",
)
REPO_EVIDENCE = (
    Path("configs/paper3/pr90_closure/sar_source_only_v1.json"),
    Path("papers/paper3_reviewer_remediation/reviewer_remediation_preregistration.md"),
    Path("papers/paper3_reviewer_remediation/numerical_traceability_matrix.md"),
    Path("papers/paper3_reviewer_remediation/references_verified.bib"),
    Path("papers/paper3_reviewer_remediation/references_additional_verified.bib"),
    Path("papers/paper3_reviewer_remediation/evidence/source_manifest.json"),
    Path("papers/paper3_reviewer_remediation/evidence/analysis_validation.json"),
    Path("papers/paper3_reviewer_remediation/evidence/receiver_inference.json"),
    Path("papers/paper3_reviewer_remediation/evidence/primary_summary.csv"),
    Path("papers/paper3_receiver_adaptation_manuscript/reproducibility_release/method_hashes.json"),
    Path("papers/paper3_receiver_adaptation_manuscript/reproducibility_release/split_hashes.json"),
    Path("papers/paper3_receiver_adaptation_manuscript/reproducibility_release/expected_checksums.json"),
    Path("scripts/paper3/reviewer_remediation/render_release_assets.py"),
    Path("scripts/paper3/reviewer_remediation/build_pdfs.py"),
)
EXTERNAL_EVIDENCE = (
    Path("composition/composition_receiver_equal_summary.csv"),
    Path("composition/composition_source_manifest.json"),
    Path("budget/matched_p0_budget_audit.json"),
    Path("budget/matched_p0_budget_summary.csv"),
    Path("sar/original/sar_original_primary160.csv"),
    Path("sar/original/sar_original_summary.json"),
    Path("sar/source_only_checkpointed/source_only_freeze.json"),
    Path("sar/source_only_checkpointed/source_only_selected.csv"),
    Path("sar/source_only_checkpointed/source_only_summary.json"),
    Path("sar/source_only_a1_parity.json"),
    Path("sar/upstream_state_probe.json"),
    Path("sar/sar_limited_rerun_plan.json"),
    Path("frozen_integrity_recheck_checkpoints.json"),
    Path("reporting_final_v1/report.json"),
    Path("reporting_final_v1/pdf/main_tmlcn.pdf"),
    Path("reporting_final_v1/pdf/main_access.pdf"),
    Path("reporting_final_v1/pdf/supplementary.pdf"),
)
FORBIDDEN_PARTS = {"raw", "predictions", "checkpoints", "payload", "packets"}
ALLOWED_SUFFIXES = {".md", ".json", ".csv", ".py", ".tex", ".bib", ".pdf"}
TEXT_LIMIT = 2 * 1024 * 1024
PDF_LIMIT = 25 * 1024 * 1024


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args], text=True, stderr=subprocess.PIPE
    ).strip()


def repo_sources(repo: Path) -> tuple[Path, ...]:
    paths = {CLOSURE / name for name in REVIEW_DOCS}
    paths.update(REPO_EVIDENCE)
    for directory, pattern in (
        (MANUSCRIPT, "*.tex"),
        (Path("scripts/paper3/pr90_closure"), "*.py"),
        (Path("src/openew/paper3/pr90_closure"), "*.py"),
        (Path("tests/paper3/pr90_closure"), "*.py"),
    ):
        paths.update(p.relative_to(repo) for p in (repo / directory).rglob(pattern))
    paths.add(MANUSCRIPT / "figure_manifest.json")
    return tuple(sorted(paths, key=lambda p: p.as_posix()))


def validated_source(root: Path, relative: Path, *, repository: bool) -> tuple[Path, int]:
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ValueError(f"unsafe packet source path: {relative}")
    if any(part.casefold() in FORBIDDEN_PARTS for part in relative.parts):
        raise ValueError(f"forbidden payload/prediction/checkpoint path: {relative}")
    if relative.suffix.lower() not in ALLOWED_SUFFIXES:
        raise ValueError(f"unsupported packet source type: {relative}")
    source = root / relative
    if not source.is_file() or source.is_symlink():
        raise ValueError(f"missing or linked packet source: {relative}")
    if not source.resolve(strict=True).is_relative_to(root):
        raise ValueError(f"packet source escapes its root: {relative}")
    if not stat.S_ISREG(source.stat(follow_symlinks=False).st_mode):
        raise ValueError(f"non-regular packet source: {relative}")
    size = source.stat().st_size
    limit = PDF_LIMIT if relative.suffix.lower() == ".pdf" else TEXT_LIMIT
    if size > limit:
        raise ValueError(f"packet source exceeds size limit: {relative}")
    if repository:
        try:
            git(root, "ls-files", "--error-unmatch", "--", relative.as_posix())
        except subprocess.CalledProcessError as exc:
            raise ValueError(f"uncommitted packet source: {relative}") from exc
    return source, size


def _write_exclusive(path: Path, data: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def build_packet(
    repository: Path,
    external_root: Path,
    output: Path,
    *,
    selected_repo: tuple[Path, ...] | None = None,
    selected_external: tuple[Path, ...] | None = None,
) -> dict:
    """Preflight first; create a unique output only after all sources qualify."""
    if not repository.is_absolute() or not external_root.is_absolute() or not output.is_absolute():
        raise ValueError("repository, external-root and output must be absolute")
    repo = repository.resolve(strict=True)
    external = external_root.resolve(strict=True)
    destination = output.resolve(strict=False)
    if git(repo, "rev-parse", "--show-toplevel") != str(repo):
        raise ValueError("repository must be the Git top level")
    if external.is_relative_to(repo) or not destination.is_relative_to(external) or destination == external:
        raise ValueError("external-root and new output must be outside the repository")
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"review packet output already exists: {destination}")
    if git(repo, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError("review packet requires a clean committed worktree")
    head = git(repo, "rev-parse", "HEAD")
    repo_paths = selected_repo if selected_repo is not None else repo_sources(repo)
    external_paths = selected_external if selected_external is not None else EXTERNAL_EVIDENCE
    if not repo_paths or not external_paths:
        raise ValueError("review packet source selection cannot be empty")
    if len(set(repo_paths)) != len(repo_paths) or len(set(external_paths)) != len(external_paths):
        raise ValueError("duplicate review packet source")
    sources: list[tuple[str, Path, Path, int, str]] = []
    for kind, root, relatives in (
        ("repository", repo, repo_paths),
        ("external", external, external_paths),
    ):
        for relative in relatives:
            source, size = validated_source(root, relative, repository=kind == "repository")
            sources.append((kind, relative, source, size, sha256(source)))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir(exist_ok=False)
    entries = []
    for kind, relative, source, size, digest in sources:
        packet_relative = Path("files") / kind / relative
        target = destination / packet_relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with source.open("rb") as inp, target.open("xb") as out:
            shutil.copyfileobj(inp, out, length=1024 * 1024)
            out.flush()
            os.fsync(out.fileno())
        if target.stat().st_size != size or sha256(target) != digest or sha256(source) != digest:
            raise RuntimeError(f"review packet source changed while copying: {relative}")
        entries.append({
            "origin": kind,
            "source_path": relative.as_posix(),
            "packet_path": packet_relative.as_posix(),
            "size_bytes": size,
            "sha256": digest,
        })
    if git(repo, "rev-parse", "HEAD") != head or git(repo, "status", "--porcelain", "--untracked-files=all"):
        raise RuntimeError("repository changed during packet creation")
    checksums = "".join(f"{entry['sha256']}  {entry['packet_path']}\n" for entry in entries)
    _write_exclusive(destination / "SHA256SUMS.txt", checksums.encode("utf-8"))
    manifest = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "git_head": head,
        "scope": "PR90_CLOSURE_REVIEW_PACKET",
        "rf_payload_included": False,
        "prediction_or_checkpoint_included": False,
        "new_target_evaluation": False,
        "file_count": len(entries),
        "total_file_bytes": sum(entry["size_bytes"] for entry in entries),
        "files": entries,
    }
    manifest_bytes = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode("utf-8")
    _write_exclusive(destination / "manifest.json", manifest_bytes)
    digest_lines = (
        f"{sha256(destination / 'manifest.json')}  manifest.json\n"
        f"{sha256(destination / 'SHA256SUMS.txt')}  SHA256SUMS.txt\n"
    )
    _write_exclusive(destination / "MANIFEST_SHA256.txt", digest_lines.encode("utf-8"))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--external-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="Nonexistent directory inside external-root")
    args = parser.parse_args()
    manifest = build_packet(args.repository, args.external_root, args.output)
    print(json.dumps({
        "status": "COMPLETE",
        "git_head": manifest["git_head"],
        "file_count": manifest["file_count"],
        "manifest_sha256": sha256(args.output / "manifest.json"),
        "output": str(args.output),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
