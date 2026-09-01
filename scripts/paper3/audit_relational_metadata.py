#!/usr/bin/env python
"""Audit Paper 3 relational metadata without modifying source artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from openew.paper3.relational_audit import (
    DEFAULT_ARTIFACT_DIRS,
    DEFAULT_RELATION_WHITELISTS,
    run_audit,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Profile deployment-available relation metadata and leakage risks for Paper 3."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/paper3/relational_feasibility_audit.yaml"),
        help="YAML file containing artifact paths, output path, and explicit whitelists.",
    )
    parser.add_argument("--output-dir", type=Path, help="Override the external audit output directory.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Run the full audit without writing output CSVs."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = _load_config(args.config)
    artifact_dirs = {
        dataset: Path(path)
        for dataset, path in config.get("artifact_dirs", DEFAULT_ARTIFACT_DIRS).items()
    }
    relation_whitelists = {
        dataset: tuple(fields)
        for dataset, fields in config.get(
            "allowed_relation_field_whitelist", DEFAULT_RELATION_WHITELISTS
        ).items()
    }
    output_dir = args.output_dir or Path(
        config.get("output_dir", "/mnt/d/openew_sa_data/paper3/audits")
    )
    result = run_audit(
        artifact_dirs=artifact_dirs,
        output_dir=output_dir,
        relation_whitelists=relation_whitelists,
        write_outputs=not args.dry_run,
    )
    summary: dict[str, Any] = {
        "dry_run": bool(args.dry_run),
        "datasets": result["dataset_summary"].to_dict(orient="records"),
        "outputs": result["outputs"],
        "source_signatures": {
            item["dataset"]: item["source_signature"] for item in result["artifact_summaries"]
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


def _load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Paper 3 audit config not found: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Paper 3 audit config must be a mapping: {path}")
    return payload


if __name__ == "__main__":
    main()
