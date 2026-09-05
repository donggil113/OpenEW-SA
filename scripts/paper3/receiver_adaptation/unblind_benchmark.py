#!/usr/bin/env python3
"""Perform the create-once receiver benchmark unblinding."""

from __future__ import annotations
import argparse
import json
import subprocess
from openew.paper3.receiver_adaptation.analysis import unblind_benchmark


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--converted-root", required=True)
    parser.add_argument("--split-root", required=True)
    parser.add_argument("--frozen-analysis-root", required=True)
    parser.add_argument("--addendum-root", required=True)
    parser.add_argument("--benchmark-root", required=True)
    parser.add_argument("--preregistration", required=True)
    args = parser.parse_args()
    status = subprocess.run(["git", "status", "--porcelain"], cwd=args.repository, check=True, capture_output=True, text=True).stdout
    if status.strip():
        raise RuntimeError("unblinding requires a clean committed repository")
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=args.repository, check=True, capture_output=True, text=True).stdout.strip()
    result = unblind_benchmark(converted_root=args.converted_root, split_root=args.split_root, frozen_analysis_root=args.frozen_analysis_root, addendum_root=args.addendum_root, benchmark_root=args.benchmark_root, preregistration_path=args.preregistration, expected_git_sha=sha)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
