#!/usr/bin/env python3
"""Validate target-free prospective RF acquisition metadata."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from openew.paper3.metadata.enums import TemporalVerdict
from openew.paper3.metadata.leakage import default_eligibility_engine
from openew.paper3.metadata.provenance import read_sidecar
from openew.paper3.metadata.proxy_audit import audit_fields
from openew.paper3.metadata.readiness import RelationReadiness, build_readiness_scorecard
from openew.paper3.metadata.serialization import (
    read_acquisition_records,
    read_annotation_records,
)
from openew.paper3.metadata.validation import validate_records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--acquisition", required=True)
    parser.add_argument("--annotations")
    parser.add_argument("--provenance")
    parser.add_argument("--output", required=True)
    parser.add_argument("--relation-field", action="append", default=[])
    parser.add_argument("--relation-whitelist", action="append", default=[])
    parser.add_argument(
        "--verified-relation-field",
        action="append",
        default=[],
        help="Relation field with separately reviewed source evidence",
    )
    parser.add_argument(
        "--temporal-verdict",
        choices=[item.value for item in TemporalVerdict],
        default=TemporalVerdict.NO_TEMPORAL_METADATA.value,
    )
    parser.add_argument("--mixed-target-episode-fraction", type=float, default=0.0)
    parser.add_argument("--max-session-size", type=int, default=100_000)
    args = parser.parse_args()

    records = read_acquisition_records(args.acquisition)
    sidecar = read_sidecar(args.provenance) if args.provenance else None
    validation = validate_records(
        records, provenance=sidecar, max_session_size=args.max_session_size
    )
    eligibility = default_eligibility_engine()
    requested = eligibility.require_relation_fields(
        args.relation_field, args.relation_whitelist
    )
    verified = frozenset(args.verified_relation_field)
    if not verified.issubset(requested):
        raise ValueError("Verified relation fields must also be requested and whitelisted")

    proxy_diagnostics: list[dict[str, object]] = []
    proxy_safe: dict[str, bool] = {field: False for field in requested}
    annotation_count = 0
    if args.annotations:
        annotations = read_annotation_records(args.annotations)
        annotation_count = len(annotations)
        diagnostics = audit_fields(
            records, annotations, requested, eligibility=eligibility
        )
        proxy_diagnostics = [item.to_mapping() for item in diagnostics]
        proxy_safe = {
            item.field: item.classification == "ALLOWED_RELATION" for item in diagnostics
        }

    relations = [
        RelationReadiness(
            field=field,
            coverage=_coverage(records, field),
            repeated_group_fraction=_repeated_fraction(records, field),
            target_proxy_rejected=proxy_safe[field],
            independently_verified=field in verified,
            true_multi_node_relation=True,
        )
        for field in requested
    ]
    # The CLI never silently promotes provenance to independent scientific
    # verification. That determination belongs in a reviewed collection record.
    scorecard = build_readiness_scorecard(
        relations,
        temporal_verdict=TemporalVerdict(args.temporal_verdict),
        mixed_target_episode_fraction=args.mixed_target_episode_fraction,
    )
    output = {
        "schema_version": 1,
        "acquisition_path": str(Path(args.acquisition)),
        "annotation_path": str(Path(args.annotations)) if args.annotations else None,
        "provenance_path": str(Path(args.provenance)) if args.provenance else None,
        "annotation_count": annotation_count,
        "validation": validation.to_mapping(),
        "relation_fields_requested": list(requested),
        "proxy_diagnostics": proxy_diagnostics,
        "metadata_readiness_scorecard": scorecard.to_mapping(),
        "scientific_verification_required": True,
    }
    write_json_atomic(Path(args.output), output)
    print(json.dumps(output, indent=2, sort_keys=True))
    if not validation.passed:
        raise SystemExit(2)


def _coverage(records: list[object], field: str) -> float:
    if not records:
        return 0.0
    return sum(getattr(record, field, None) not in (None, "") for record in records) / len(records)


def _repeated_fraction(records: list[object], field: str) -> float:
    values = [getattr(record, field, None) for record in records]
    counts: dict[object, int] = {}
    for value in values:
        if value not in (None, ""):
            counts[value] = counts.get(value, 0) + 1
    populated = sum(counts.values())
    return (
        sum(count for count in counts.values() if count > 1) / populated
        if populated
        else 0.0
    )


def write_json_atomic(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


if __name__ == "__main__":
    main()
