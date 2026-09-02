"""Frozen-work and WiSig source integrity verification."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .archive import sha256_file
from .validation import compare_deterministic_passes


FROZEN_GIT_PATHS = (
    "papers/paper1_openew_sa",
    "papers/paper2_ood_rf_signal_recognition",
    "configs/paper3/relational_feasibility_audit.yaml",
    "papers/paper3_dynamic_hypergraph_sa",
    "scripts/paper3/audit_relational_metadata.py",
    "src/openew/paper3/relational_audit.py",
    "tests/paper3/test_relational_audit.py",
    "configs/paper3/static_relational",
    "scripts/paper3/static_relational",
    "src/openew/paper3/static_relational",
    "tests/paper3/static_relational",
    "configs/paper3/metadata",
    "papers/paper3_prospective_metadata",
    "scripts/paper3/metadata",
    "src/openew/paper3/metadata",
    "tests/paper3/metadata",
    "configs/paper3/dataset_qualification",
    "papers/paper3_dataset_qualification",
    "scripts/paper3/dataset_qualification",
    "src/openew/paper3/dataset_qualification",
    "tests/paper3/dataset_qualification",
    "src/openew/paper3/__init__.py",
    "tests/paper3/__init__.py",
)


def verify_integrity(
    repository: str | Path,
    baseline_ref: str,
    archive: str | Path,
    pass_a: str | Path,
    pass_b: str | Path,
    *,
    expected_archive_sha256: str,
    expected_manifest_sha256: str,
) -> dict[str, Any]:
    repository = Path(repository)
    git_paths: dict[str, dict[str, Any]] = {}
    for path in FROZEN_GIT_PATHS:
        result = subprocess.run(
            ["git", "diff", "--quiet", baseline_ref, "--", path],
            cwd=repository,
            check=False,
        )
        git_paths[path] = {"unchanged": result.returncode == 0, "return_code": result.returncode}
    archive_hash = sha256_file(archive)
    manifest_a = sha256_file(Path(pass_a) / "dataset_manifest.json")
    manifest_b = sha256_file(Path(pass_b) / "dataset_manifest.json")
    deterministic = compare_deterministic_passes(pass_a, pass_b)
    checks = {
        "frozen_git_paths_unchanged": all(value["unchanged"] for value in git_paths.values()),
        "raw_archive_hash_matches": archive_hash == expected_archive_sha256,
        "pass_a_manifest_hash_matches": manifest_a == expected_manifest_sha256,
        "pass_b_manifest_hash_matches": manifest_b == expected_manifest_sha256,
        "conversion_passes_byte_identical": bool(deterministic["byte_identical"]),
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "baseline_ref": baseline_ref,
        "checks": checks,
        "frozen_git_paths": git_paths,
        "archive_sha256": archive_hash,
        "pass_a_manifest_sha256": manifest_a,
        "pass_b_manifest_sha256": manifest_b,
        "conversion_comparison": deterministic,
        "no_pr81_rerun_performed": True,
        "no_dynamic_model_run": True,
        "no_uncertainty_gating_run": True,
        "no_neuro_symbolic_model_run": True,
    }
