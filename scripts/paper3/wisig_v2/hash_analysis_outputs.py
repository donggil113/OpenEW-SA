#!/usr/bin/env python3
"""Hash the complete external V2 analysis package deterministically."""

from __future__ import annotations

import argparse
import json

from openew.paper3.wisig_v2.analysis_manifest import write_analysis_manifest


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--analysis-root", required=True); parser.add_argument("--output", required=True); args = parser.parse_args()
    result = write_analysis_manifest(args.analysis_root, args.output)
    print(json.dumps({"file_count": result["file_count"], "total_bytes": result["total_bytes"]}, indent=2))


if __name__ == "__main__":
    main()
