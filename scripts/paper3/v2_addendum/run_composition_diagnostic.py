#!/usr/bin/env python3
"""Run frozen-checkpoint T3A/RX-NORM oracle composition stresses."""

from __future__ import annotations

import argparse
import json

from openew.paper3.v2_addendum.composition import run_tta_composition_diagnostic


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--converted-root", required=True)
    parser.add_argument("--split-root", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--v2-root", required=True)
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    frame = run_tta_composition_diagnostic(args.converted_root, args.split_root, args.run_root, args.output_root, v2_root=args.v2_root)
    print(json.dumps({"status": "COMPLETE", "rows": len(frame)}, indent=2))


if __name__ == "__main__":
    main()
