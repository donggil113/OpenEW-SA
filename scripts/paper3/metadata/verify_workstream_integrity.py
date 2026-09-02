#!/usr/bin/env python3
"""Compare frozen content/tree fingerprints with the pre-workstream snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openew.paper3.static_relational.integrity import tree_digest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pre",
        default="/mnt/d/openew_sa_data/paper3/prospective_validation/pre_workstream_integrity.json",
    )
    parser.add_argument(
        "--output",
        default="/mnt/d/openew_sa_data/paper3/prospective_validation/post_workstream_integrity.json",
    )
    parser.add_argument("--repo", default=".")
    args = parser.parse_args()
    expected = json.loads(Path(args.pre).read_text(encoding="utf-8"))
    actual_content = {
        name: tree_digest(value["path"])
        for name, value in expected["content_roots"].items()
    }
    raw = raw_structural_fingerprint(expected["raw_structural_fingerprint"]["path"])
    repo = Path(args.repo).resolve()
    git_trees = {
        "paper1": git(repo, "rev-parse", "HEAD:papers/paper1_openew_sa"),
        "paper2": git(repo, "rev-parse", "HEAD:papers/paper2_ood_rf_signal_recognition"),
        "paper3_pr80_at_merge": git(
            repo, "rev-parse", "3b2159c897b58b538c05b01de2feb23c34fa8fac:papers/paper3_dynamic_hypergraph_sa"
        ),
        "paper3_pr81_at_merge": git(
            repo, "rev-parse", "b2b59d54515f601e5f88156a0d4adc38bbf77016:papers/paper3_dynamic_hypergraph_sa"
        ),
    }
    checks = {
        "content_roots_match": actual_content == expected["content_roots"],
        "raw_structure_match": raw == expected["raw_structural_fingerprint"],
        "git_trees_match": git_trees == expected["git_trees"],
        "paper1_diff_empty": not git(repo, "diff", "main", "--", "papers/paper1_openew_sa"),
        "paper2_diff_empty": not git(repo, "diff", "main", "--", "papers/paper2_ood_rf_signal_recognition"),
        "pr81_path_diff_empty": not git(
            repo, "diff", "main", "--", "papers/paper3_dynamic_hypergraph_sa"
        ),
    }
    result: dict[str, Any] = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "pre_snapshot": str(Path(args.pre)),
        "content_roots": actual_content,
        "raw_structural_fingerprint": raw,
        "git_trees": git_trees,
        "checks": checks,
        "passed": all(checks.values()),
    }
    write_json_atomic(Path(args.output), result)
    print(json.dumps({"passed": result["passed"], "checks": checks}, indent=2, sort_keys=True))
    if not result["passed"]:
        raise SystemExit(2)


def raw_structural_fingerprint(root: str | Path) -> dict[str, Any]:
    path_root = Path(root)
    digest = hashlib.sha256(); count = 0; total = 0
    for path in sorted(item for item in path_root.rglob("*") if item.is_file()):
        stat = path.stat(); relative = path.relative_to(path_root).as_posix()
        digest.update(relative.encode("utf-8")); digest.update(b"\0")
        digest.update(str(stat.st_size).encode("ascii")); digest.update(b"\0")
        digest.update(str(stat.st_mtime_ns).encode("ascii")); digest.update(b"\n")
        count += 1; total += stat.st_size
    return {
        "algorithm": "sha256(relative_path NUL size NUL mtime_ns newline); no payload hashing",
        "file_count": count,
        "path": str(path_root),
        "sha256": digest.hexdigest(),
        "total_bytes": total,
    }


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


if __name__ == "__main__":
    main()
