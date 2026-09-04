#!/usr/bin/env python3
"""Build the compact V2 evidence ledger used by final scientific reports."""

from __future__ import annotations

import argparse
import json

from openew.paper3.wisig_v2.report_evidence import build_report_evidence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis-root", required=True)
    parser.add_argument("--integrity-report", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--grouped-results")
    parser.add_argument("--equalized-results")
    args = parser.parse_args()
    payload = build_report_evidence(
        args.analysis_root,
        args.integrity_report,
        args.output,
        grouped_results=args.grouped_results,
        equalized_results=args.equalized_results,
    )
    print(json.dumps({"status": "PASS", "output": args.output, "primary_models": len(payload["primary_macro_f1"])}, indent=2))


if __name__ == "__main__":
    main()
