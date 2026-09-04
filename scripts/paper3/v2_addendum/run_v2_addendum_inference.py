#!/usr/bin/env python3
"""Run frozen-checkpoint WiSig V2 post-hoc diagnostics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from openew.paper3.v2_addendum.inference import (
    audit_equalized_intersection,
    run_query_coupling_diagnostic,
    run_t3a_support_budget_diagnostic,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--converted-root", required=True)
    parser.add_argument("--split-root", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--v2-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--equalized-a-root")
    parser.add_argument("--equalized-b-root")
    parser.add_argument("--query-coupling", action="store_true")
    parser.add_argument("--support-budget", action="store_true")
    parser.add_argument("--equalized-intersection", action="store_true")
    args = parser.parse_args()
    result: dict[str, object] = {}
    if args.query_coupling:
        frame = run_query_coupling_diagnostic(args.converted_root, args.split_root, args.run_root, args.output_root, v2_root=args.v2_root)
        result["query_coupling_rows"] = len(frame)
    if args.support_budget:
        frame = run_t3a_support_budget_diagnostic(args.converted_root, args.split_root, args.run_root, args.output_root, v2_root=args.v2_root)
        result["t3a_support_budget_rows"] = len(frame)
    if args.equalized_intersection:
        if not args.equalized_a_root or not args.equalized_b_root:
            parser.error("equalized intersection requires both equalized roots")
        result["equalized_intersection"] = audit_equalized_intersection(
            args.converted_root,
            args.equalized_a_root,
            args.equalized_b_root,
            args.split_root,
            Path(args.output_root) / "equalized_intersection_audit.json",
        )
    if not result:
        parser.error("select at least one diagnostic")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
