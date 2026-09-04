#!/usr/bin/env python3
"""Emit the fail-closed Shen qualification decision without payload access."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from openew.paper3.shen.qualification import current_official_evidence_qualification


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite qualification record: {output}")
    payload = {
        "schema_version": 1,
        "dataset_doi": "10.21227/D6VX-R538",
        "paper_doi": "10.1109/TMC.2023.3340039",
        "qualification": current_official_evidence_qualification().to_dict(),
        "payload_downloaded": False,
        "model_training_authorized": False,
        "target_metrics_opened": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
