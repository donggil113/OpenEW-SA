#!/usr/bin/env python3
"""Render V2 tables and non-truncated publication figures."""

from __future__ import annotations

import argparse
import json

from openew.paper3.wisig_v2.reporting import generate_figures, generate_tables


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis-root", required=True)
    parser.add_argument("--split-root", required=True)
    args = parser.parse_args()
    print(json.dumps({"figures": generate_figures(args.analysis_root), "tables": generate_tables(args.analysis_root, args.split_root)}, indent=2))


if __name__ == "__main__":
    main()
