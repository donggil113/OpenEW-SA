"""Fail-closed guard for the Paper 3 scientific freeze.

This script reads scientific bytes from the *peeled commit* of the annotated
freeze tag. It never derives expected hashes from the mutable worktree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

TAG = "paper3-scientific-freeze-20260929"
EXPECTED_COMMIT = "676b01ea946dbeff21322db328e4851fbb00e1c4"
MANIFEST = Path("papers/paper3_submission_finalization/scientific_freeze_manifest.json")

SCIENTIFIC_PREFIXES = (
    "papers/paper3_reviewer_remediation/manuscript/tables/",
    "papers/paper3_reviewer_remediation/manuscript/figures/",
    "papers/paper3_reviewer_remediation/evidence/",
    "papers/paper3_receiver_adaptation_manuscript/evidence/",
)
SCIENTIFIC_EXACT = frozenset(
    (
        "papers/paper3_reviewer_remediation/manuscript/numbers.tex",
        "papers/paper3_reviewer_remediation/manuscript/figure_manifest.json",
        "papers/paper3_reviewer_remediation/manuscript/shared/abstract.tex",
        "papers/paper3_reviewer_remediation/manuscript/shared/body.tex",
        "papers/paper3_reviewer_remediation/numerical_traceability_matrix.md",
        "papers/paper3_reviewer_remediation/structural_numerical_traceability.md",
        "papers/paper3_receiver_adaptation_manuscript/numerical_traceability_matrix.md",
        "papers/paper3_receiver_adaptation_manuscript/numerical_structural_traceability.md",
        "papers/paper3_pr90_closure/reporting_snapshot_manifest.json",
        "papers/paper3_pr90_closure/composition_source_audit.md",
        "papers/paper3_pr90_closure/sar_original_execution_audit.md",
        "papers/paper3_pr90_closure/support_budget_interpretation.md",
    )
)


def git(repo: Path, *args: str) -> bytes:
    proc = subprocess.run(
        ["git", *args], cwd=repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    return proc.stdout


def is_scientific(path: str) -> bool:
    return path in SCIENTIFIC_EXACT or path.startswith(SCIENTIFIC_PREFIXES)


def freeze_commit(repo: Path) -> str:
    # An annotated tag's object SHA is not the frozen commit SHA.
    commit = git(repo, "rev-parse", f"{TAG}^{{commit}}").decode().strip()
    if commit != EXPECTED_COMMIT:
        raise RuntimeError(f"freeze tag points to {commit}, expected {EXPECTED_COMMIT}")
    return commit


def tagged_paths(repo: Path, commit: str) -> list[str]:
    names = git(repo, "ls-tree", "-r", "--name-only", commit).decode().splitlines()
    selected = sorted(name for name in names if is_scientific(name))
    if len(selected) < 60:
        raise RuntimeError(f"scientific file selection unexpectedly small: {len(selected)}")
    for required in SCIENTIFIC_EXACT:
        if required not in selected:
            raise RuntimeError(f"missing frozen scientific path: {required}")
    return selected


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def expected_entries(repo: Path, commit: str) -> dict[str, dict[str, int | str]]:
    entries = {}
    for path in tagged_paths(repo, commit):
        data = git(repo, "show", f"{commit}:{path}")
        entries[path] = {"sha256": sha256(data), "bytes": len(data)}
    return entries


def check_entries(repo: Path, entries: dict[str, dict[str, int | str]]) -> list[str]:
    errors = []
    for path, recorded in entries.items():
        file = repo / path
        if not file.is_file():
            errors.append(f"missing: {path}")
        elif sha256(file.read_bytes()) != recorded["sha256"]:
            errors.append(f"scientific drift: {path}")
    extra = sorted(
        p.relative_to(repo).as_posix()
        for prefix in SCIENTIFIC_PREFIXES
        for p in (repo / prefix).rglob("*")
        if p.is_file() and p.relative_to(repo).as_posix() not in entries
        and "__pycache__" not in p.parts
    )
    errors.extend(f"unfrozen scientific file: {path}" for path in extra)
    return errors


def manifest(repo: Path) -> dict:
    commit = freeze_commit(repo)
    entries = expected_entries(repo, commit)
    errors = check_entries(repo, entries)
    if errors:
        raise RuntimeError("\n".join(errors))
    return {
        "schema_version": 1,
        "freeze_tag": TAG,
        "freeze_commit": commit,
        "tag_object_sha": git(repo, "rev-parse", TAG).decode().strip(),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Detect scientific drift; metadata and venue packaging are excluded.",
        "file_count": len(entries),
        "files": entries,
    }


def verify(repo: Path, manifest_path: Path) -> dict:
    saved = json.loads(manifest_path.read_text())
    commit = freeze_commit(repo)
    if saved["freeze_commit"] != commit:
        raise RuntimeError("manifest freeze commit mismatch")
    expected = expected_entries(repo, commit)
    if saved["files"] != expected or saved["file_count"] != len(expected):
        raise RuntimeError("manifest differs from immutable freeze tag")
    errors = check_entries(repo, expected)
    if errors:
        raise RuntimeError("\n".join(errors))
    return {"status": "PASS", "freeze_commit": commit, "scientific_files": len(expected)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    repo = args.repository.resolve()
    path = args.manifest if args.manifest.is_absolute() else repo / args.manifest
    if args.write_manifest:
        if path.exists():
            raise RuntimeError(f"refusing to overwrite freeze manifest: {path}")
        data = manifest(repo)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"status": "CREATED", "file_count": data["file_count"]}))
    else:
        print(json.dumps(verify(repo, path), sort_keys=True))


if __name__ == "__main__":
    main()
