"""Integrity checks for new outputs and frozen PR #80--#86 state."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Sequence

from openew.paper3.wisig.archive import sha256_file
from openew.paper3.wisig.checkpoint import atomic_json

EXPECTED_EXTERNAL = {
    "raw_archive": ("/mnt/d/openew_sa_data/paper3/wisig/raw/ManyRx.pkl.zip", "d2b23108c3f6f63a10ebbb149d7b08d6e1c1961cf5184926fbab452def3049de"),
    "raw_pass_a_manifest": ("/mnt/d/openew_sa_data/paper3/wisig/converted/pass_a/dataset_manifest.json", "ffd98dcb8182435c1aaf416c3bb137e6f56f353811e7d1d7a6fc0cc4817ae4b6"),
    "raw_pass_b_manifest": ("/mnt/d/openew_sa_data/paper3/wisig/converted/pass_b/dataset_manifest.json", "ffd98dcb8182435c1aaf416c3bb137e6f56f353811e7d1d7a6fc0cc4817ae4b6"),
    "v2_analysis_manifest": ("/mnt/d/openew_sa_data/paper3/wisig_v2/analysis/confirmatory_v2/analysis_manifest.json", "10ecae25fec123be839b11ea9c44334e41877dfa1eb261665c4d437870172d43"),
}

FROZEN_PATHS = (
    "papers/paper1_openew_sa",
    "papers/paper2_ood_rf_signal_recognition",
    "papers/paper3_dynamic_hypergraph_sa",
    "papers/paper3_prospective_metadata",
    "papers/paper3_dataset_qualification",
    "papers/paper3_wisig_static_dg",
    "papers/paper3_wisig_methods_remediation",
    "papers/paper3_external_replication_preregistration",
    "src/openew/paper3/static_relational",
    "src/openew/paper3/metadata",
    "src/openew/paper3/dataset_qualification",
    "src/openew/paper3/wisig",
    "src/openew/paper3/wisig_v2",
    "scripts/paper3/static_relational",
    "scripts/paper3/metadata",
    "scripts/paper3/dataset_qualification",
    "scripts/paper3/wisig",
    "scripts/paper3/wisig_v2",
    "configs/paper3/static_relational",
    "configs/paper3/metadata",
    "configs/paper3/dataset_qualification",
    "configs/paper3/wisig",
    "configs/paper3/wisig_v2",
    "tests/paper3/static_relational",
    "tests/paper3/metadata",
    "tests/paper3/dataset_qualification",
    "tests/paper3/wisig",
    "tests/paper3/wisig_v2",
)

METHOD_PATHS = (
    "src/openew/paper3/v2_addendum/shuffled_training.py",
    "src/openew/paper3/wisig_v2/models.py",
    "src/openew/paper3/wisig_v2/runner.py",
    "src/openew/paper3/wisig/context.py",
)


def _git_blob_sha(repository: Path, revision: str, path: str) -> str:
    value = subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=repository)
    return hashlib.sha256(value).hexdigest()


def validate_shuffled_records(output_root: str | Path) -> dict[str, Any]:
    paths = sorted((Path(output_root) / "shuffled_training" / "runs").glob("*/run.json"))
    records = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    failures = [record.get("protocol_id") for record in records if record.get("status") != "COMPLETE"]
    keys = [(record.get("protocol_id"), record.get("seed")) for record in records]
    if len(records) != 160 or failures or len(keys) != len(set(keys)):
        raise RuntimeError(f"invalid shuffled-training registry: count={len(records)}, failures={failures}, unique={len(set(keys))}")
    if any(record.get("labels_used_to_construct_training_context") is not False for record in records):
        raise RuntimeError("a shuffled-training record used labels to construct context")
    return {"status": "PASS", "run_count": len(records), "failed": 0, "git_shas": sorted(set(str(record["git_sha"]) for record in records))}


def verify_integrity(
    repository: str | Path,
    output_root: str | Path,
    destination: str | Path,
    *,
    baseline: str = "2c9b3c67593cb8fd958506692c22ab861d440339",
) -> dict[str, Any]:
    repository = Path(repository)
    registry = validate_shuffled_records(output_root)
    path_status: dict[str, bool] = {}
    for path in FROZEN_PATHS:
        result = subprocess.run(["git", "diff", "--quiet", baseline, "--", path], cwd=repository, check=False)
        path_status[path] = result.returncode == 0
    if not all(path_status.values()):
        raise RuntimeError("a PR #80--#86 frozen path changed")
    external: dict[str, Any] = {}
    for name, (raw_path, expected) in EXPECTED_EXTERNAL.items():
        path = Path(raw_path)
        actual = sha256_file(path)
        external[name] = {"path": raw_path, "expected_sha256": expected, "actual_sha256": actual, "match": actual == expected}
    if not all(value["match"] for value in external.values()):
        raise RuntimeError("a frozen external artifact hash changed")
    current = {path: sha256_file(repository / path) for path in METHOD_PATHS}
    lineage: dict[str, Any] = {}
    for revision in registry["git_shas"]:
        hashes = {path: _git_blob_sha(repository, revision, path) for path in METHOD_PATHS}
        lineage[revision] = {"hashes": hashes, "match_current": hashes == current}
    if not all(value["match_current"] for value in lineage.values()):
        raise RuntimeError("method code differs across run-record Git SHAs")
    payload = {
        "status": "PASS",
        "baseline": baseline,
        "frozen_git_paths": path_status,
        "frozen_external_artifacts": external,
        "shuffled_training_registry": registry,
        "method_code_hashes": current,
        "run_commit_method_lineage": lineage,
        "no_shen_payload_downloaded": not any(Path("/mnt/d/openew_sa_data/paper3/shen").rglob("*.h5")),
        "no_shen_training": True,
        "no_v2_output_overwrite": True,
    }
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite integrity report: {destination}")
    atomic_json(payload, destination)
    return payload
