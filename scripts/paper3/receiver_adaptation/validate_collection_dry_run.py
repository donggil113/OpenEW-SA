#!/usr/bin/env python3
"""Create and validate the prospective collection contract fixture."""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from openew.paper3.receiver_adaptation.collection import training_authorization_gate, validate_collection, write_synthetic_collection


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--tier", choices=("SMALL", "MEDIUM", "FULL"), default="SMALL")
    args = parser.parse_args()
    root = Path(args.output_root)
    if root.exists() and any(root.iterdir()):
        raise FileExistsError("dry-run output root must be new or empty")
    records, provenance = write_synthetic_collection(root, tier=args.tier)
    report = validate_collection(records, tier=args.tier, annotation_sample_ids=(), provenance_by_capture=provenance)
    payload = {"validation": report.to_dict(), "training_gate": training_authorization_gate(report), "payload": "SYNTHETIC_CONTRACT_FIXTURE_ONLY", "scientific_evidence": False}
    (root / "dry_run_report.json").write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
