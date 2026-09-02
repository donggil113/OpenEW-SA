#!/usr/bin/env python3
"""Qualify one candidate dataset without consulting model performance."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import yaml

from openew.paper3.dataset_qualification.adoption_decision import decide_adoption
from openew.paper3.dataset_qualification.candidate_schema import AccessStatus, CandidateEvidence, TriState
from openew.paper3.dataset_qualification.license_gate import evaluate_license
from openew.paper3.dataset_qualification.metadata_gate import (
    CandidateRelationEvidence,
    evaluate_metadata_readiness,
)
from openew.paper3.dataset_qualification.official_evidence import (
    EvidenceItem,
    evaluate_official_evidence,
)
from openew.paper3.dataset_qualification.storage_gate import DownloadKind, evaluate_download
from openew.paper3.dataset_qualification.target_proxy_gate import evaluate_target_proxy_fields
from openew.paper3.dataset_qualification.temporal_gate import (
    CandidateTemporalEvidence,
    evaluate_temporal,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--free-bytes", required=True, type=int)
    args = parser.parse_args()
    config = _read_mapping(Path(args.config))
    candidate = CandidateEvidence.from_mapping(config["candidate"])
    official_items = tuple(EvidenceItem(**item) for item in config.get("official_evidence", []))
    official = evaluate_official_evidence(official_items)
    licence = evaluate_license(
        license_name=candidate.license,
        verified=candidate.license_verified,
        applies_to_dataset_payload=TriState(config["license_evidence"]["applies_to_dataset_payload"]),
        permits_research_use=TriState(config["license_evidence"]["permits_research_use"]),
        permits_derived_artifacts=TriState(config["license_evidence"]["permits_derived_artifacts"]),
        permits_redistribution=TriState(config["license_evidence"]["permits_redistribution"]),
        use_restrictions=tuple(config["license_evidence"].get("use_restrictions", [])),
    )
    storage = evaluate_download(
        kind=DownloadKind(config["download"]["kind"]),
        requested_bytes=candidate.download_size_bytes,
        free_bytes=args.free_bytes,
        license_verified=licence.permits_download,
        official_source_verified=official.passed,
        secret_required=bool(config["download"].get("secret_required", False)),
    )
    proxy = evaluate_target_proxy_fields(
        tuple(candidate.relation_allowed_fields),
        independently_verified_target_neutral=tuple(config["proxy_evidence"].get("verified_target_neutral", [])),
        path=config["proxy_evidence"].get("example_path"),
        target_tokens=tuple(config["proxy_evidence"].get("target_tokens", [])),
    )
    temporal = evaluate_temporal(CandidateTemporalEvidence(**config["temporal_evidence"]))
    relations = tuple(CandidateRelationEvidence(**item) for item in config.get("relations", []))
    readiness = evaluate_metadata_readiness(
        relations,
        temporal_status=temporal.status,
        mixed_target_episode_fraction=float(config.get("mixed_target_episode_fraction", 0.0)),
    )
    adoption = decide_adoption(
        access_status=AccessStatus(candidate.access_status),
        official_evidence=official,
        license_gate=licence,
        storage_gate=storage,
        proxy_gate=proxy,
        temporal_gate=temporal,
        readiness_highest=str(readiness["highest_level"]),
        split_protocol_frozen=bool(config.get("split_protocol_frozen", False)),
        task_distinct=bool(config.get("task_distinct", False)),
    )
    result: dict[str, Any] = {
        "schema_version": 1,
        "candidate": candidate.to_mapping(),
        "official_evidence_gate": official.__dict__,
        "license_gate": licence.__dict__,
        "storage_gate": storage.__dict__,
        "target_proxy_gate": proxy.__dict__,
        "temporal_gate": {"status": temporal.status.value, "reasons": list(temporal.reasons)},
        "metadata_readiness": readiness,
        "adoption_decision": adoption.to_mapping(),
        "performance_metrics_used": False,
    }
    _write_json_atomic(Path(args.output), result)
    print(json.dumps(result, indent=2, default=list, sort_keys=True))


def _read_mapping(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        if path.suffix.lower() in {".yaml", ".yml"}:
            value = yaml.safe_load(handle)
        else:
            value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("Qualification config must contain a mapping")
    return value


def _write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, default=list, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


if __name__ == "__main__":
    main()
