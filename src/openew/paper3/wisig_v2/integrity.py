"""Immutable-history and external WiSig artifact checks for V2."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Sequence

from .hashing import canonical_json_bytes, sha256_file


FROZEN_GIT_PATHS = (
    "papers/paper1_openew_sa",
    "papers/paper2_ood_rf_signal_recognition",
    "papers/paper3_dynamic_hypergraph_sa",
    "papers/paper3_prospective_metadata",
    "papers/paper3_dataset_qualification",
    "papers/paper3_wisig_static_dg",
    "src/openew/paper3/static_relational",
    "src/openew/paper3/metadata",
    "src/openew/paper3/dataset_qualification",
    "src/openew/paper3/wisig",
    "scripts/paper3/static_relational",
    "scripts/paper3/metadata",
    "scripts/paper3/dataset_qualification",
    "scripts/paper3/wisig",
    "tests/paper3/static_relational",
    "tests/paper3/metadata",
    "tests/paper3/dataset_qualification",
    "tests/paper3/wisig",
    "configs/paper3/static_relational",
    "configs/paper3/metadata",
    "configs/paper3/dataset_qualification",
    "configs/paper3/wisig",
)

ALLOWED_V2_PATH_PREFIXES = (
    "papers/paper3_wisig_methods_remediation/",
    "configs/paper3/wisig_v2/",
    "scripts/paper3/wisig_v2/",
    "src/openew/paper3/wisig_v2/",
    "tests/paper3/wisig_v2/",
)


def git_paths_unchanged(repository: str | Path, baseline: str, paths: Sequence[str] = FROZEN_GIT_PATHS) -> dict[str, bool]:
    repository = Path(repository)
    return {
        path: subprocess.run(["git", "diff", "--quiet", baseline, "--", path], cwd=repository, check=False).returncode == 0
        for path in paths
    }


def changed_paths_since(repository: str | Path, baseline: str) -> list[str]:
    result = subprocess.check_output(
        ["git", "diff", "--name-only", f"{baseline}...HEAD"],
        cwd=Path(repository),
        text=True,
    )
    return sorted(value.strip() for value in result.splitlines() if value.strip())


def only_v2_paths_changed(paths: Sequence[str]) -> bool:
    return all(any(path.startswith(prefix) for prefix in ALLOWED_V2_PATH_PREFIXES) for path in paths)


def verify_tree_manifest(root: str | Path, manifest_path: str | Path) -> dict[str, Any]:
    """Verify an immutable small-file tree against a previously frozen manifest."""

    root = Path(root).resolve()
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    expected = {str(row["relative_path"]): row for row in manifest.get("files", [])}
    actual_paths = sorted(path for path in root.rglob("*") if path.is_file())
    actual_names = {path.relative_to(root).as_posix() for path in actual_paths}
    expected_names = set(expected)
    mismatches: list[dict[str, Any]] = []
    for path in actual_paths:
        name = path.relative_to(root).as_posix()
        row = expected.get(name)
        if row is None:
            continue
        size = path.stat().st_size
        digest = sha256_file(path)
        if size != int(row["size_bytes"]) or digest != str(row["sha256"]):
            mismatches.append({"relative_path": name, "expected_size": int(row["size_bytes"]), "actual_size": size, "expected_sha256": str(row["sha256"]), "actual_sha256": digest})
    return {
        "status": "PASS" if actual_names == expected_names and not mismatches else "FAIL",
        "expected_file_count": len(expected_names),
        "actual_file_count": len(actual_names),
        "missing_paths": sorted(expected_names - actual_names),
        "unexpected_paths": sorted(actual_names - expected_names),
        "mismatches": mismatches,
    }


def verify_v2_integrity(
    repository: str | Path,
    *,
    baseline: str,
    v1_root: str | Path,
    destination: str | Path,
    pr84_analysis_snapshot: str | Path | None = None,
) -> dict[str, Any]:
    v1_root = Path(v1_root)
    prior = json.loads((v1_root / "analysis/final_v1/integrity_report.json").read_text(encoding="utf-8"))
    archive = v1_root / "raw/ManyRx.pkl.zip"
    pass_a = v1_root / "converted/pass_a/dataset_manifest.json"
    pass_b = v1_root / "converted/pass_b/dataset_manifest.json"
    current = {
        "archive_sha256": sha256_file(archive),
        "pass_a_manifest_sha256": sha256_file(pass_a),
        "pass_b_manifest_sha256": sha256_file(pass_b),
    }
    git_checks = git_paths_unchanged(repository, baseline)
    changed_paths = changed_paths_since(repository, baseline)
    prior_analysis = None
    if pr84_analysis_snapshot is not None:
        prior_analysis = verify_tree_manifest(v1_root / "analysis/final_v1", pr84_analysis_snapshot)
    checks = {
        "raw_archive_matches_pr84": current["archive_sha256"] == prior["archive_sha256"],
        "pass_a_manifest_matches_pr84": current["pass_a_manifest_sha256"] == prior["pass_a_manifest_sha256"],
        "pass_b_manifest_matches_pr84": current["pass_b_manifest_sha256"] == prior["pass_b_manifest_sha256"],
        "all_pr80_through_pr84_git_paths_unchanged": all(git_checks.values()),
        "all_committed_changes_confined_to_v2_paths": only_v2_paths_changed(changed_paths),
        "pr84_final_analysis_tree_unchanged": prior_analysis is None or prior_analysis["status"] == "PASS",
    }
    payload = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "baseline_ref": baseline,
        "checks": checks,
        "current_hashes": current,
        "prior_hashes": {key: prior[key] for key in current},
        "frozen_git_paths": git_checks,
        "committed_paths_since_pr84": changed_paths,
        "allowed_v2_path_prefixes": list(ALLOWED_V2_PATH_PREFIXES),
        "pr84_final_analysis_tree": prior_analysis,
        "no_pr84_overwrite": True,
        "no_target_dependent_selection": True,
        "no_dynamic_or_temporal_model": True,
        "no_neuro_symbolic_model": True,
    }
    destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(canonical_json_bytes(payload))
    if payload["status"] != "PASS":
        raise RuntimeError("V2 integrity verification failed")
    return payload
