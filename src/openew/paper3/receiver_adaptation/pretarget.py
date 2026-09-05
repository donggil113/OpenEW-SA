"""Create-once pre-target execution freeze."""

from __future__ import annotations
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from .frozen import sha256_file


def tree_hash(repository: str | Path, prefixes: Iterable[str]) -> str:
    repository = Path(repository)
    files: list[Path] = []
    for prefix in prefixes:
        root = repository / prefix
        files.extend(path for path in root.rglob("*") if path.is_file() and "__pycache__" not in path.parts)
    digest = hashlib.sha256()
    for path in sorted(set(files)):
        digest.update(path.relative_to(repository).as_posix().encode())
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


def create_pretarget_freeze(repository: str | Path, output: str | Path, *, preregistration: str | Path, config: str | Path, frozen_integrity: str | Path) -> dict[str, object]:
    repository, output = Path(repository), Path(output)
    if output.exists():
        raise FileExistsError("pre-target freeze already exists")
    status = subprocess.run(["git", "status", "--porcelain"], cwd=repository, check=True, capture_output=True, text=True).stdout
    if status.strip():
        raise RuntimeError("pre-target freeze requires clean repository")
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repository, check=True, capture_output=True, text=True).stdout.strip()
    frozen = json.loads(Path(frozen_integrity).read_text(encoding="utf-8"))
    if frozen.get("status") != "PASS" or frozen.get("run_count") != 2080:
        raise RuntimeError("frozen V2 integrity gate has not passed")
    payload = {
        "schema_version": 1,
        "status": "FROZEN_BEFORE_NEW_TARGET_PREDICTIONS",
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "git_sha": sha,
        "preregistration_sha256": sha256_file(preregistration),
        "config_sha256": sha256_file(config),
        "analysis_code_tree_sha256": tree_hash(repository, ("src/openew/paper3/receiver_adaptation", "scripts/paper3/receiver_adaptation")),
        "frozen_v2_integrity_sha256": sha256_file(frozen_integrity),
        "frozen_v2_prediction_manifest_sha256": frozen["prediction_manifest_sha256"],
        "frozen_v2_checkpoint_manifest_sha256": frozen["checkpoint_manifest_sha256"],
        "expected_oracle_records": 160,
        "expected_budget_records": 160,
        "expected_new_adaptation_evaluations": 1280,
        "target_metrics_blinded": True,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, output)
    return payload
