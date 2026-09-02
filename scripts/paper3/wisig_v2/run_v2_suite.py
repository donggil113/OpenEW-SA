#!/usr/bin/env python3
"""Run the WiSig V2 source-only smoke or target-blinded experiment suite."""

from __future__ import annotations

import argparse
import json

from openew.paper3.wisig_v2.suite import execute_suite, plan_summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--converted-root", required=True)
    parser.add_argument("--split-root", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--phase", action="append", choices=["primary_loso", "day_secondary", "support_budget", "context_k"])
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--plan-only", action="store_true")
    args = parser.parse_args()
    if args.plan_only:
        print(json.dumps(plan_summary(), indent=2))
        return
    result = execute_suite(args.repository, args.converted_root, args.split_root, args.run_root, phases=set(args.phase) if args.phase else None, smoke=args.smoke)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
