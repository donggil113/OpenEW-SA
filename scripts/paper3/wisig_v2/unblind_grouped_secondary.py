#!/usr/bin/env python3
"""Unblind the repeated grouped-receiver secondary after LOSO primary."""

from __future__ import annotations

import argparse
import json

from openew.paper3.wisig_v2.analysis import unblind_grouped_secondary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--converted-root", required=True)
    parser.add_argument("--split-root", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--analysis-root", required=True)
    parser.add_argument("--primary-analysis-root", required=True)
    args = parser.parse_args()
    print(json.dumps(unblind_grouped_secondary(args.converted_root, args.split_root, args.run_root, args.analysis_root, args.primary_analysis_root), indent=2))


if __name__ == "__main__":
    main()
