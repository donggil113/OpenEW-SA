#!/usr/bin/env python3
"""Execute the frozen WiSig receiver/day/context study sequentially."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from openew.paper3.wisig.suite import execute_suite, plan_summary


PHASES = ("receiver_primary", "day_secondary", "retention", "context_size", "stress_secondary")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--converted-root", type=Path, required=True)
    parser.add_argument("--split-root", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--phase", action="append", choices=PHASES)
    parser.add_argument("--plan-only", action="store_true")
    args = parser.parse_args()
    if args.plan_only:
        print(json.dumps(plan_summary(), indent=2, sort_keys=True)); return 0
    result = execute_suite(args.repository, args.converted_root, args.split_root, args.run_root, phases=set(args.phase) if args.phase else None)
    print(json.dumps({key: result[key] for key in ("status", "planned_unique_runs", "completed_runs", "failed_runs")}, indent=2))
    return 0 if result["failed_runs"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
