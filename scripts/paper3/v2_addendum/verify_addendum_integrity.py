#!/usr/bin/env python3
"""Verify frozen history, external hashes, and addendum run lineage."""

from __future__ import annotations

import argparse
import json

from openew.paper3.v2_addendum.integrity import verify_integrity


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--baseline", default="2c9b3c67593cb8fd958506692c22ab861d440339")
    args = parser.parse_args()
    print(json.dumps(verify_integrity(args.repository, args.output_root, args.output, baseline=args.baseline), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
