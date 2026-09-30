"""Versioned, RF-payload-absent reporting snapshot and reproduction helpers."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


DOC = Path("papers/paper3_reviewer_remediation")
CLOSURE = Path("papers/paper3_pr90_closure")
RELEASE = Path("papers/paper3_receiver_adaptation_manuscript/reproducibility_release")
RENDERER = Path("scripts/paper3/reviewer_remediation/render_release_assets.py")
BUILDER = Path("scripts/paper3/reviewer_remediation/build_pdfs.py")
CLI = Path("scripts/paper3/pr90_closure/reproduce_reporting.py")
LIBRARY = Path("src/openew/paper3/pr90_closure/report_repro.py")
COMPOSITION_TABLE = DOC / "manuscript/tables/composition_oracle.tex"
CAPTION = "POST-HOC ORACLE COMPOSITION DIAGNOSTIC"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def source_files(repo: Path) -> list[Path]:
    required = [
        DOC / "references_verified.bib",
        COMPOSITION_TABLE,
        RENDERER,
        BUILDER,
        CLI,
        LIBRARY,
        RELEASE / "method_hashes.json",
        RELEASE / "expected_checksums.json",
    ]
    for directory in (DOC / "manuscript", DOC / "evidence"):
        if not (repo / directory).is_dir():
            raise FileNotFoundError(directory)
        required.extend(p.relative_to(repo) for p in (repo / directory).rglob("*") if p.is_file())
    required.extend(
        p.relative_to(repo)
        for p in (repo / CLOSURE).glob("composition_*")
        if p.is_file()
    )
    files = sorted(set(required), key=lambda p: p.as_posix())
    for relative in files:
        if not (repo / relative).is_file():
            raise FileNotFoundError(relative)
    return files


def registry(repo: Path, paths: list[Path]) -> dict[str, str]:
    return {p.as_posix(): sha256(repo / p) for p in paths}


def validate_registry(repo: Path, expected: dict[str, str]) -> None:
    if not expected:
        raise ValueError("empty source registry")
    for name, digest in expected.items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("unsafe source path")
        path = repo / relative
        if not path.is_file() or sha256(path) != digest:
            raise ValueError("reporting snapshot source changed: " + name)


def verify_method_hashes(repo: Path) -> int:
    path = repo / RELEASE / "method_hashes.json"
    mapping = json.loads(path.read_text(encoding="utf-8"))
    validate_registry(repo, mapping)
    return len(mapping)


def create_manifest(repo: Path, path: Path) -> dict:
    if path.exists():
        raise FileExistsError("reporting snapshot is create-once")
    if not (repo / DOC / "manuscript/shared/body.tex").is_file():
        raise FileNotFoundError("canonical shared manuscript absent")
    body = (repo / DOC / "manuscript/shared/body.tex").read_text(encoding="utf-8")
    if CAPTION not in body or "tables/composition_oracle" not in body:
        raise ValueError("main-text composition table is not in canonical shared source")
    method_count = verify_method_hashes(repo)
    paths = source_files(repo)
    mapping = registry(repo, paths)
    previous = sha256(repo / RELEASE / "expected_checksums.json")
    report = {
        "schema_version": 1,
        "utc": datetime.now(timezone.utc).isoformat(),
        "scope": "A_PAYLOAD_ABSENT_REPORTING_ONLY",
        "rf_payload_required": False,
        "new_target_metrics": False,
        "prior_pr90_expected_checksums_sha256": previous,
        "frozen_method_count": method_count,
        "source_files": mapping,
        "source_file_count": len(mapping),
        "composition_marker": CAPTION,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, sort_keys=True, indent=2)
        stream.write("\n")
    return report


def validate_manifest(repo: Path, path: Path) -> dict:
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("schema_version") != 1 or report.get("scope") != "A_PAYLOAD_ABSENT_REPORTING_ONLY":
        raise ValueError("wrong reporting snapshot schema/scope")
    if report.get("rf_payload_required") is not False or report.get("new_target_metrics") is not False:
        raise ValueError("reporting snapshot falsely claims scientific reproduction")
    current = {p.as_posix() for p in source_files(repo)}
    expected = set(report["source_files"])
    if current != expected:
        raise ValueError("reporting snapshot source membership changed")
    validate_registry(repo, report["source_files"])
    if sha256(repo / RELEASE / "expected_checksums.json") != report["prior_pr90_expected_checksums_sha256"]:
        raise ValueError("prior PR90 checksum ledger changed")
    if verify_method_hashes(repo) != report["frozen_method_count"]:
        raise ValueError("frozen method ledger changed")
    return report


def audit_pdf(pdf: Path, log: Path, *, composition: bool) -> dict:
    info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
    fonts = subprocess.check_output(["pdffonts", str(pdf)], text=True)
    text = log.read_text(encoding="utf-8", errors="replace")
    pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    embedded = []
    for row in fonts.splitlines()[2:]:
        match = re.search(r"\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$", row)
        if match:
            embedded.append(match.group(1) == "yes")
    result = {
        "pages": pages,
        "sha256": sha256(pdf),
        "all_fonts_embedded": bool(embedded) and all(embedded),
        "type3_fonts": len(re.findall(r"Type 3", fonts)),
        "undefined_citations": len(re.findall(r"Citation .* undefined", text)),
        "undefined_references": len(re.findall(r"Reference .* undefined", text)),
        "overfull_boxes": len(re.findall(r"Overfull", text)),
        "composition_table_pages": [],
    }
    if not result["all_fonts_embedded"] or any(
        result[key] for key in ("type3_fonts", "undefined_citations", "undefined_references", "overfull_boxes")
    ):
        raise ValueError("PDF technical audit failed: " + json.dumps(result))
    if composition:
        for page in range(1, pages + 1):
            page_text = subprocess.check_output(
                ["pdftotext", "-f", str(page), "-l", str(page), str(pdf), "-"],
                text=True,
            )
            if CAPTION in " ".join(page_text.split()):
                result["composition_table_pages"].append(page)
        if not result["composition_table_pages"]:
            raise ValueError("composition table missing from built main PDF")
    return result
