#!/usr/bin/env python3
"""Unblind the fixed official-equalized diagnostic after raw primary V2."""

from __future__ import annotations

import argparse
import json

from openew.paper3.wisig_v2.analysis import unblind_equalized_diagnostic


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--converted-root", required=True)
    parser.add_argument("--split-root", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--analysis-root", required=True)
    parser.add_argument("--primary-analysis-root", required=True)
    args = parser.parse_args()
    result = unblind_equalized_diagnostic(args.converted_root, args.split_root, args.run_root, args.analysis_root, args.primary_analysis_root)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
