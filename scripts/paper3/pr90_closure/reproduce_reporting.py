#!/usr/bin/env python3
"""Freeze or reproduce the PR90 closure's versioned reporting-only package."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from openew.paper3.pr90_closure.report_repro import (
    DOC, CLOSURE, CAPTION, audit_pdf, create_manifest, sha256, validate_manifest,
)


def execute(command: list[str], *, cwd: Path, env: dict[str, str], log: Path) -> None:
    result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True)
    log.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError("reporting reproduction failed; inspect " + str(log))


def run(repo: Path, manifest_path: Path, output: Path, access_template: Path | None) -> dict:
    report = validate_manifest(repo, manifest_path)
    resolved = output.resolve()
    if resolved.is_relative_to(repo.resolve()):
        raise ValueError("output must be outside the repository")
    output.mkdir(parents=True, exist_ok=False)
    stage = output / "staged_repository"
    stage_doc = stage / DOC
    stage_doc.parent.mkdir(parents=True)
    shutil.copytree(repo / DOC, stage_doc)
    for relative in sorted((repo / CLOSURE).glob("composition_*")):
        if relative.is_file():
            dest = stage / CLOSURE / relative.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(relative, dest)
    env = {**os.environ, "PYTHONPATH": str(repo / "src")}
    execute(
        [sys.executable, str(repo / "scripts/paper3/reviewer_remediation/render_release_assets.py"),
         "--repository", str(stage), "--png-output", str(output / "figures_png")],
        cwd=repo, env=env, log=output / "render.log",
    )
    # Generated reports and figures must reproduce the frozen source bytes.
    for relative, expected in report["source_files"].items():
        if relative.startswith(DOC.as_posix() + "/"):
            staged = stage / relative
            if not staged.is_file() or sha256(staged) != expected:
                raise ValueError("reporting renderer drift: " + relative)
    command = [
        sys.executable, str(repo / "scripts/paper3/reviewer_remediation/build_pdfs.py"),
        "--repository", str(stage), "--output", str(output / "pdf"),
    ]
    if access_template is not None:
        command.extend(["--access-template", str(access_template.resolve())])
    execute(command, cwd=repo, env=env, log=output / "build.log")
    pdfs = {}
    for name in ("main_tmlcn", "supplementary", "main_access"):
        pdf = output / "pdf" / (name + ".pdf")
        if pdf.is_file():
            pdfs[name] = audit_pdf(
                pdf, output / "pdf/source" / (name + ".log"),
                composition=name.startswith("main_"),
            )
    if "main_tmlcn" not in pdfs or "supplementary" not in pdfs:
        raise RuntimeError("required main or supplementary PDF absent")
    result = {
        "status": "PASS",
        "scope": "A_PAYLOAD_ABSENT_REPORTING_ONLY",
        "rf_payload_loaded": False,
        "new_target_evaluation": False,
        "full_scientific_reproduction": False,
        "snapshot_sha256": sha256(manifest_path),
        "prior_pr90_expected_checksums_sha256": report["prior_pr90_expected_checksums_sha256"],
        "regenerated_figures_tables_match_snapshot": True,
        "composition_marker": CAPTION,
        "pdfs": pdfs,
    }
    (output / "report.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze", "run"))
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="New external output directory for run")
    parser.add_argument("--access-template", type=Path, help="Optional official verified IEEE Access ZIP")
    args = parser.parse_args()
    repo = args.repository.resolve()
    if args.command == "freeze":
        if args.output is not None:
            parser.error("--output is for run only")
        print(json.dumps(create_manifest(repo, args.manifest), sort_keys=True, indent=2))
    else:
        if args.output is None:
            parser.error("--output is required for run")
        print(json.dumps(run(repo, args.manifest, args.output, args.access_template), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
