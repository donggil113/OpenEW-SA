#!/usr/bin/env python3
"""Build receiver-level post-hoc V2 addendum summaries and figures."""

from __future__ import annotations

import argparse
import json

from openew.paper3.v2_addendum.reporting import build_addendum_analysis, hash_addendum_analysis


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--addendum-root", required=True)
    parser.add_argument("--frozen-analysis-root", required=True)
    parser.add_argument("--freeze-manifest", action="store_true")
    args = parser.parse_args()
    payload = build_addendum_analysis(args.addendum_root, args.frozen_analysis_root)
    if args.freeze_manifest:
        payload["analysis_manifest"] = hash_addendum_analysis(args.addendum_root)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
