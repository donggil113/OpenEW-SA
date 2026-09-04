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
    parser.add_argument("--phase", action="append", choices=["primary_loso", "day_secondary"])
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--blind-target-metrics", action="store_true", help="Required for every non-smoke execution; target metrics are never emitted by this runner.")
    args = parser.parse_args()
    if args.plan_only:
        print(json.dumps(plan_summary(), indent=2))
        return
    if not args.smoke and not args.phase:
        parser.error("an explicit --phase is required for non-smoke execution")
    if args.smoke and args.phase:
        parser.error("--phase cannot be combined with --smoke")
    if not args.smoke and not args.blind_target_metrics:
        parser.error("--blind-target-metrics is required for non-smoke execution")
    result = execute_suite(args.repository, args.converted_root, args.split_root, args.run_root, phases=set(args.phase) if args.phase else None, smoke=args.smoke)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
