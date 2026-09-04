#!/usr/bin/env python3
"""Build immutable WiSig V2 LOSO/day split manifests before target evaluation."""

from __future__ import annotations

import argparse
import json

from openew.paper3.wisig_v2.splits import build_v2_splits, load_hardware_map


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--converted-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--hardware-map", required=True)
    args = parser.parse_args()
    result = build_v2_splits(args.converted_root, args.output_root, load_hardware_map(args.hardware_map))
    print(json.dumps({"status": result["status"], "protocols": len(result["protocols"]), "sha256": result["split_freeze_manifest_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
