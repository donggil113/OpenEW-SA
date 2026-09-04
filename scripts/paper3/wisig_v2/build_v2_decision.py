#!/usr/bin/env python3
"""Apply the pre-unblinding V2 mechanism decision rule."""

from __future__ import annotations

import argparse
import json

from openew.paper3.wisig_v2.decision_analysis import build_decision_summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis-root", required=True)
    parser.add_argument("--integrity-report", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(build_decision_summary(args.analysis_root, args.integrity_report, args.output), indent=2))


if __name__ == "__main__":
    main()
