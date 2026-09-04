#!/usr/bin/env python3
"""Verify Paper 1/2, PR #80-#84, and raw WiSig immutability."""

from __future__ import annotations

import argparse
import json

from openew.paper3.wisig_v2.integrity import verify_v2_integrity


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--baseline", default="53bcf41471c11cdd7a96f949fcfcb24b117deccd")
    parser.add_argument("--v1-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--pr84-analysis-snapshot", required=True)
    args = parser.parse_args()
    print(json.dumps(verify_v2_integrity(args.repository, baseline=args.baseline, v1_root=args.v1_root, destination=args.output, pr84_analysis_snapshot=args.pr84_analysis_snapshot), indent=2))


if __name__ == "__main__":
    main()
