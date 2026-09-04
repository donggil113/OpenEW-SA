#!/usr/bin/env python3
"""Perform the single authorized V2 unblinding after all primary runs complete."""

from __future__ import annotations

import argparse
import json

from openew.paper3.wisig_v2.analysis import unblind_day_secondary, unblind_primary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--converted-root", required=True)
    parser.add_argument("--split-root", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--analysis-root", required=True)
    parser.add_argument("--preregistration", required=True)
    parser.add_argument("--day-secondary", action="store_true")
    args = parser.parse_args()
    result = unblind_day_secondary(args.converted_root, args.split_root, args.run_root, args.analysis_root) if args.day_secondary else unblind_primary(args.converted_root, args.split_root, args.run_root, args.analysis_root, args.preregistration)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
