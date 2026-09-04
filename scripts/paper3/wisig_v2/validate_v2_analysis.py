#!/usr/bin/env python3
"""Validate V2 analysis grain, bounds, completeness, and diagnostic labeling."""

from __future__ import annotations

import argparse
import json

from openew.paper3.wisig_v2.analysis_quality import validate_analysis_outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--day-csv")
    parser.add_argument("--grouped-csv")
    parser.add_argument("--equalized-csv")
    args = parser.parse_args()
    print(json.dumps(validate_analysis_outputs(args.analysis_root, args.output, day_csv=args.day_csv, grouped_csv=args.grouped_csv, equalized_csv=args.equalized_csv), indent=2))


if __name__ == "__main__":
    main()
