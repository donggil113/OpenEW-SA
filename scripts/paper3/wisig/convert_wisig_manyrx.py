#!/usr/bin/env python3
"""CLI for deterministic, separated WiSig ManyRx conversion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from openew.paper3.wisig.converter import ConversionConfig, convert_manyrx


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-pickle", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--source-archive-sha256", required=True)
    parser.add_argument("--equalized-index", type=int, default=0)
    parser.add_argument("--shard-size", type=int, default=8192)
    args = parser.parse_args()
    manifest = convert_manyrx(
        args.source_pickle,
        args.output_root,
        source_archive_sha256=args.source_archive_sha256,
        config=ConversionConfig(equalized_index=args.equalized_index, shard_size=args.shard_size),
    )
    print(json.dumps({"status": manifest["status"], "sample_count": manifest["sample_count"], "shard_count": manifest["shard_count"], "config_hash": manifest["config_hash"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
