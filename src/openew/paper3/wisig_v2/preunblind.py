"""Immutable pre-unblinding freeze for the complete blind primary suite."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from .analysis import collect_primary_records, validate_record_blind_archive, validate_target_receiver_diagnostic, verify_primary_completion
from .contracts import PRIMARY_SEEDS
from .hashing import canonical_json_bytes, sha256_file
from .suite import PRIMARY_MODELS


DERIVED_BASE_STAGE = {
    "P2_SHUFFLED": "P2",
    "P2_NULL": "P2",
    "P2_MISMATCHED_RX": "P2",
    "RX_NORM": "SOURCE_NORM",
    "T3A": "P0",
}

ANALYSIS_CODE_ROOTS = (
    "configs/paper3/wisig_v2",
    "scripts/paper3/wisig_v2",
    "src/openew/paper3/wisig_v2",
)


def hash_file_registry(entries: dict[str, str]) -> str:
    """Hash an ordered logical-file registry without embedding host paths."""

    return __import__("hashlib").sha256(canonical_json_bytes(dict(sorted(entries.items())))).hexdigest()


def hash_analysis_code_tree(repository: str | Path) -> dict[str, Any]:
    """Hash the committed V2 analysis/config/CLI tree used at unblinding."""

    repository = Path(repository).resolve()
    files: dict[str, str] = {}
    for relative_root in ANALYSIS_CODE_ROOTS:
        root = repository / relative_root
        if not root.is_dir():
            raise FileNotFoundError(f"analysis code root is missing: {relative_root}")
        for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
            if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
                continue
            relative = path.relative_to(repository).as_posix()
            files[relative] = sha256_file(path)
    if not files:
        raise RuntimeError("analysis code tree is empty")
    return {
        "roots": list(ANALYSIS_CODE_ROOTS),
        "file_count": len(files),
        "sha256": hash_file_registry(files),
        "files": files,
    }


def validate_primary_grid(records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Require the exact preregistered receiver/model/seed primary grid."""

    expected = {
        (f"receiver_loso_{receiver:02d}", model, seed)
        for receiver in range(32)
        for model in PRIMARY_MODELS
        for seed in PRIMARY_SEEDS
    }
    observed = [
        (str(record.get("protocol_id")), str(record.get("model_stage")), int(record.get("config", {}).get("seed", -1)))
        for record in records
    ]
    observed_set = set(observed)
    if len(observed) != len(observed_set):
        raise RuntimeError("primary grid contains duplicate receiver/model/seed conditions")
    missing = sorted(expected - observed_set)
    unexpected = sorted(observed_set - expected)
    if missing or unexpected:
        raise RuntimeError(f"primary grid mismatch: missing={missing[:5]}, unexpected={unexpected[:5]}")
    for record in records:
        config = record.get("config", {})
        if (
            int(config.get("support_budget", -1)) != 128
            or int(config.get("context_k", -1)) != 32
            or float(config.get("context_retention", -1.0)) != 1.0
            or str(config.get("data_variant")) != "raw"
            or config.get("blind_target_metrics") is not True
            or config.get("evaluate_target_predictions") is not True
        ):
            raise RuntimeError(f"primary configuration contract mismatch in {record.get('run_id', '<unknown>')}")
        if int(record.get("target_prediction_count", 0)) <= 0:
            raise RuntimeError(f"primary blind archive is empty in {record.get('run_id', '<unknown>')}")
    config_hashes = {str(record.get("config_hash")) for record in records}
    if len(config_hashes) != len(expected) or "None" in config_hashes:
        raise RuntimeError("primary config hashes are missing or non-unique")
    return {
        "status": "PASS",
        "condition_count": len(observed),
        "receiver_count": 32,
        "model_count": len(PRIMARY_MODELS),
        "seed_count": len(PRIMARY_SEEDS),
    }


def validate_checkpoint_lineage(records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Verify every derived condition used the matching frozen base checkpoint."""

    base_records = {
        (str(record.get("protocol_id")), int(record.get("config", {}).get("seed", -1)), str(record.get("model_stage"))): record
        for record in records
        if str(record.get("model_stage")) not in DERIVED_BASE_STAGE
    }
    base_hashes: dict[tuple[str, int, str], str] = {}
    for key, record in base_records.items():
        record_path = Path(str(record.get("record_path", "")))
        checkpoint_path = record_path.parent / "checkpoint.pt"
        if not record_path.is_file() or not checkpoint_path.is_file():
            raise RuntimeError(f"missing trained checkpoint lineage artifact for {key}")
        base_hashes[key] = sha256_file(checkpoint_path)
    derived_count = 0
    for record in records:
        stage = str(record.get("model_stage"))
        if stage not in DERIVED_BASE_STAGE:
            continue
        key = (str(record.get("protocol_id")), int(record.get("config", {}).get("seed", -1)), DERIVED_BASE_STAGE[stage])
        if key not in base_hashes:
            raise RuntimeError(f"missing base checkpoint record for derived stage {stage}: {key}")
        if str(record.get("base_checkpoint_sha256")) != base_hashes[key]:
            raise RuntimeError(f"base checkpoint hash mismatch for derived stage {stage}: {record.get('run_id', '<unknown>')}")
        derived_count += 1
    return {
        "status": "PASS",
        "trained_checkpoint_count": len(base_hashes),
        "derived_lineage_count": derived_count,
        "derived_base_stages": dict(sorted(DERIVED_BASE_STAGE.items())),
        "trained_checkpoint_manifest_sha256": __import__("hashlib").sha256(canonical_json_bytes({"|".join(map(str, key)): value for key, value in sorted(base_hashes.items())})).hexdigest(),
    }


def create_preunblinding_freeze(
    repository: str | Path,
    run_root: str | Path,
    split_root: str | Path,
    split_manifest: str | Path,
    protocol_paths: Sequence[str | Path],
    destination: str | Path,
) -> dict[str, Any]:
    repository, run_root, split_root, destination = Path(repository), Path(run_root), Path(split_root), Path(destination)
    if destination.exists():
        raise FileExistsError("pre-unblinding freeze already exists")
    records = collect_primary_records(run_root); verify_primary_completion(records)
    primary_grid = validate_primary_grid(records)
    checkpoint_lineage = validate_checkpoint_lineage(records)
    execution_shas = sorted({str(record["git_sha"]) for record in records})
    if len(execution_shas) != 1:
        raise RuntimeError(f"primary records span multiple execution Git SHAs: {execution_shas}")
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=repository, text=True)
    if status.strip():
        raise RuntimeError("repository must be clean before the pre-unblinding freeze")
    analysis_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repository, text=True).strip()
    analysis_code_tree = hash_analysis_code_tree(repository)
    archive_preflight = [validate_record_blind_archive(record, split_root) for record in records]
    diagnostic_preflight = [validate_target_receiver_diagnostic(record, split_root) for record in records]
    prediction_hashes = {record["run_id"]: str(record["target_prediction_sha256"]) for record in records}
    run_registry_hashes = {str(record["run_id"]): sha256_file(Path(str(record["record_path"]))) for record in records}
    paths = [Path(split_manifest), run_root / "frozen_run_plan.json", *map(Path, protocol_paths)]
    file_hashes = {str(path): sha256_file(path) for path in paths}
    data_manifest_hashes = sorted({str(record["data_manifest_sha256"]) for record in records})
    if len(data_manifest_hashes) != 1:
        raise RuntimeError(f"primary records span multiple data-manifest hashes: {data_manifest_hashes}")
    protocol_hashes = {str(path): file_hashes[str(Path(path))] for path in map(Path, protocol_paths)}
    payload = {
        "schema_version": 1,
        "status": "FROZEN_BEFORE_TARGET_UNBLINDING",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "primary_run_count": len(records),
        "primary_grid": primary_grid,
        "checkpoint_lineage": checkpoint_lineage,
        "execution_git_sha": execution_shas[0],
        "analysis_freeze_git_sha": analysis_sha,
        "all_target_metrics_null": all(record.get("held_out_metrics") is None for record in records),
        "all_target_labels_not_loaded_for_metrics": all(record.get("target_labels_loaded_for_metrics") is False for record in records),
        "unique_split_hashes": sorted({str(record["split_sha256"]) for record in records}),
        "unique_data_manifest_hashes": data_manifest_hashes,
        "data_manifest_sha256": data_manifest_hashes[0],
        "config_hash_count": len({str(record["config_hash"]) for record in records}),
        "primary_run_registry_sha256": hash_file_registry(run_registry_hashes),
        "analysis_code_tree": analysis_code_tree,
        "split_freeze_sha256": file_hashes[str(Path(split_manifest))],
        "preregistration_file_hashes": protocol_hashes,
        "blind_archive_preflight": {
            "status": "PASS",
            "record_count": len(archive_preflight),
            "total_query_count": sum(int(row["query_count"]) for row in archive_preflight),
            "labels_read": False,
            "prediction_manifest_sha256": hash_file_registry(prediction_hashes),
        },
        "target_receiver_diagnostic_preflight": {
            "status": "PASS",
            "record_count": len(diagnostic_preflight),
            "receiver_count": len({str(row["receiver_id"]) for row in diagnostic_preflight}),
            "support_query_overlap_count": sum(int(row["support_query_overlap"]) for row in diagnostic_preflight),
            "labels_read": False,
        },
        "file_hashes": file_hashes,
        "git_worktree_clean": True,
    }
    destination.parent.mkdir(parents=True, exist_ok=True); destination.write_bytes(canonical_json_bytes(payload))
    return payload
