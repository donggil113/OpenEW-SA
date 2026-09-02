#!/usr/bin/env python3
"""Build deterministic support-only receiver/day WiSig protocols."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from openew.paper3.wisig.splits import SupportThresholds, build_all_splits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--converted-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--train-per-class", type=int, default=100)
    parser.add_argument("--validation-per-class", type=int, default=20)
    parser.add_argument("--test-per-class", type=int, default=20)
    args = parser.parse_args()
    freeze = build_all_splits(
        args.converted_root,
        args.output_root,
        SupportThresholds(args.train_per_class, args.validation_per_class, args.test_per_class),
    )
    print(json.dumps({
        "status": freeze["status"],
        "protocol_count": freeze["protocol_count"],
        "receiver_groups": freeze["receiver_groups"],
        "days": freeze["days"],
        "split_freeze_manifest_sha256": freeze["split_freeze_manifest_sha256"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
