#!/usr/bin/env python3
"""Run diagnostic-only target proxy/error correlations after V2 unblinding."""

from __future__ import annotations

import argparse
import json

from openew.paper3.wisig_v2.postaudit import run_target_proxy_postaudit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--converted-root", required=True)
    parser.add_argument("--split-root", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--analysis-root", required=True)
    args = parser.parse_args()
    print(json.dumps(run_target_proxy_postaudit(args.converted_root, args.split_root, args.run_root, args.analysis_root), indent=2))


if __name__ == "__main__":
    main()
