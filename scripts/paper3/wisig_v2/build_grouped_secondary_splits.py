#!/usr/bin/env python3
"""Materialize the frozen repeated grouped-receiver secondary splits."""

from __future__ import annotations

import argparse
import json

from openew.paper3.wisig_v2.splits import build_grouped_secondary_splits, load_hardware_map


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--converted-root", required=True)
    parser.add_argument("--primary-split-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--hardware-map", required=True)
    args = parser.parse_args()
    result = build_grouped_secondary_splits(args.converted_root, args.primary_split_root, args.output_root, load_hardware_map(args.hardware_map))
    print(json.dumps({"status": result["status"], "protocol_count": result["protocol_count"], "sha256": result["sha256"]}, indent=2))


if __name__ == "__main__":
    main()
